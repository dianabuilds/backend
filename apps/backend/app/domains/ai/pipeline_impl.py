from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.ai.application.circuit_service import llm_circuit
from app.domains.ai.application.pricing_service import estimate_cost_usd
from app.domains.ai.application.usage_recorder import record_usage
from app.domains.ai.infrastructure.models.ai_settings import AISettings  # type: ignore
from app.domains.ai.infrastructure.models.generation_models import (
    GenerationJob,  # type: ignore
)
from app.domains.ai.infrastructure.models.world_models import (  # type: ignore
    Character,
    WorldTemplate,
)
from app.domains.ai.logs import save_stage_log
from app.domains.ai.providers import (
    AnthropicProvider,
    OpenAICompatibleProvider,
    OpenAIProvider,
)
from app.domains.telemetry.application.metrics_registry import llm_metrics
from app.domains.telemetry.application.ports.llm_metrics_port import LLMCallLabels

logger = logging.getLogger(__name__)


@dataclass
class StageLog:
    stage: str
    provider: str
    model: str
    prompt: str
    raw_response: str
    usage: dict[str, int] = field(default_factory=dict)
    cost: float = 0.0
    status: str = "ok"


def _build_fallback_chain(preferred: str | None = None, ai: AISettings | None = None):
    primary = (preferred or os.getenv("AI_PROVIDER") or "openai").lower().strip().replace("-", "_")

    def _make(name: str):
        if name == "openai":
            return OpenAIProvider(
                api_key=(ai.api_key if ai and (ai.provider or "").lower() == "openai" else None),
                base_url=(ai.base_url if ai and (ai.provider or "").lower() == "openai" else None),
            )
        if name == "openai_compatible":
            prov_name = (ai.provider or "").lower().replace("-", "_") if ai else ""
            return OpenAICompatibleProvider(
                api_key=(ai.api_key if prov_name == "openai_compatible" else None),
                base_url=(ai.base_url if prov_name == "openai_compatible" else None),
            )
        if name == "anthropic":
            return AnthropicProvider(
                api_key=(ai.api_key if ai and (ai.provider or "").lower() == "anthropic" else None),
                base_url=(
                    ai.base_url if ai and (ai.provider or "").lower() == "anthropic" else None
                ),
            )
        return None

    order = ["openai", "openai_compatible", "anthropic"]
    providers = []
    for name in [primary] + [p for p in order if p != primary]:
        prov = _make(name)
        if prov:
            providers.append(prov)
    return providers


async def _estimate_cost_pre_call(
    providers,
    *,
    model: str,
    prompt: str,
    system: str,
    max_tokens: int,
):
    if not providers:
        return None
    prov = providers[0]
    try:
        tokens = await prov.count_tokens(model=model, prompt=prompt, system=system)
        if tokens is not None:
            return estimate_cost_usd(model, tokens, max_tokens)
    except Exception:
        pass
    return None


async def _call_with_fallback(
    *,
    prompt: str,
    system: str,
    model: str | list[str],
    json_mode: bool,
    preferred_provider: str | None,
    ai_settings: AISettings | None,
    max_tokens: int = 2048,
    providers: list | None = None,
):
    models = [model] if isinstance(model, str) else list(model)
    last_err: Exception | None = None
    rate_skipped_any = False
    for m in models:
        chain = providers or _build_fallback_chain(preferred_provider, ai_settings)
        for prov in chain:
            pname = getattr(prov, "name", "unknown")
            if not llm_circuit.allow(pname):
                try:
                    labels = LLMCallLabels(provider=pname, model=m, stage="unknown")
                    llm_metrics.inc("skipped", labels, 1)
                except Exception:
                    pass
                logger.info("Skipping provider %s due to open circuit", pname)
                continue

            # Rate limit: сперва по модели (если задан), затем по провайдеру
            from app.domains.ai.rate_limit import try_acquire_for

            allowed = True
            reason = None
            try:
                allowed, reason = await try_acquire_for(pname, m, amount=1)
            except Exception:
                allowed, reason = (
                    True,
                    None,
                )  # в случае ошибки лимитера не блокируем вызов
            if not allowed:
                rate_skipped_any = True
                try:
                    labels = LLMCallLabels(provider=pname, model=m, stage="unknown")
                    llm_metrics.inc("skipped", labels, 1)
                    if reason == "model":
                        llm_metrics.inc_error(labels, "rate_limit_model", 1)
                    else:
                        llm_metrics.inc_error(labels, "rate_limit_provider", 1)
                except Exception:
                    pass
                logger.info(
                    "Skipping provider %s due to local rate-limit (%s)",
                    pname,
                    reason or "provider",
                )
                continue

            try:
                res = await prov.complete(
                    model=m,
                    prompt=prompt,
                    system=system,
                    json_mode=json_mode,
                    max_tokens=max_tokens,
                    timeout=60.0,
                )
                llm_circuit.on_success(pname)
                return prov, res
            except Exception as e:
                from app.domains.ai.providers.base import (
                    LLMRateLimit,
                    LLMServerError,
                )  # lazy import to avoid cycles

                logger.warning("Provider %s failed (%s), trying next...", pname, e)
                llm_circuit.on_failure(pname)
                try:
                    labels = LLMCallLabels(provider=pname, model=m, stage="unknown")
                    llm_metrics.inc("failure", labels, 1)
                    if isinstance(e, LLMRateLimit):
                        llm_metrics.inc_error(labels, "rate_limit", 1)
                    elif isinstance(e, LLMServerError):
                        llm_metrics.inc_error(labels, "server", 1)
                    else:
                        llm_metrics.inc_error(labels, "other", 1)
                except Exception:
                    pass
                last_err = e
                continue
    if last_err:
        raise last_err
    if rate_skipped_any:
        from app.domains.ai.providers.base import LLMRateLimit  # lazy import

        raise LLMRateLimit("rate_limited_all_providers")
    raise RuntimeError("No providers configured")


async def run_full_generation(db: AsyncSession, job: GenerationJob) -> dict[str, Any]:
    params = job.params or {}
    workspace_id_raw = params.get("workspace_id")
    try:
        workspace_uuid = UUID(str(workspace_id_raw)) if workspace_id_raw else None
    except Exception:
        workspace_uuid = None
    world_template_id = params.get("world_template_id")
    structure = params.get("structure", "vn_branching")
    length = params.get("length", "short")
    tone = params.get("tone", "light")
    genre = params.get("genre", "fantasy")
    locale = params.get("locale") or "en"

    # load AI settings
    ai_settings: AISettings | None = None
    try:
        _res = await db.execute(select(AISettings).limit(1))
        ai_settings = _res.scalars().first()
    except Exception as _e:
        logger.warning("Failed to load AISettings: %s", _e)

    # models per stage
    allowed_models = (
        [str(m) for m in params.get("allowed_models", [])]
        if isinstance(params.get("allowed_models"), list)
        else []
    )
    model_default = (
        job.model
        or (ai_settings.model if ai_settings and ai_settings.model else os.getenv("AI_MODEL"))
        or "gpt-4o-mini"
    ).strip()
    if allowed_models and model_default not in allowed_models:
        model_default = allowed_models[0]
    models_param = (params.get("models") or {}) if isinstance(params.get("models"), dict) else {}
    model_beats = (
        models_param.get("beats") or os.getenv("AI_MODEL_BEATS") or model_default
    ).strip()
    model_chapters = (
        models_param.get("chapters") or os.getenv("AI_MODEL_CHAPTERS") or model_default
    ).strip()
    model_nodes = (
        models_param.get("nodes") or os.getenv("AI_MODEL_NODES") or model_default
    ).strip()

    preferred_provider = (
        getattr(job, "provider", None)
        or (
            ai_settings.provider
            if ai_settings and ai_settings.provider
            else os.getenv("AI_PROVIDER")
        )
        or "openai"
    ).strip()
    maxtok_beats = int(os.getenv("AI_MAXTOK_BEATS", "1200"))
    maxtok_chapters = int(os.getenv("AI_MAXTOK_CHAPTERS", "3000"))
    maxtok_nodes = int(os.getenv("AI_MAXTOK_NODES", "6000"))
    budget_usd = float(os.getenv("AI_JOB_BUDGET_USD", "0") or 0.0)

    # world slice
    world_slice = None
    if world_template_id:
        try:
            _w = await db.execute(
                select(WorldTemplate).where(WorldTemplate.id == world_template_id)
            )
            wt = _w.scalars().first()
            if wt:
                _c = await db.execute(
                    select(Character).where(Character.world_id == wt.id).limit(12)
                )
                chars = [
                    {"name": c.name, "role": c.role, "description": c.description}
                    for c in _c.scalars().all()
                ]
                world_slice = {
                    "title": wt.title,
                    "locale": wt.locale,
                    "description": wt.description,
                    "meta": wt.meta,
                    "characters": chars,
                }
        except Exception as _e:
            logger.warning("Failed to load world slice: %s", _e)
    world_ctx = json.dumps(world_slice, ensure_ascii=False)[:2000] if world_slice else ""

    stage_logs: list[StageLog] = []
    total_prompt = 0
    total_completion = 0
    total_cost = 0.0
    result_quest_id = None
    result_version_id = None

    # progress
    try:
        job.progress = max(int(job.progress or 0), 5)
        job.updated_at = datetime.utcnow()
        await db.flush()
    except Exception:
        pass

    # Stage 1: beats
    system_beats = (
        f"You are narrative planner. Locale: {locale}. "
        "Use the provided world slice. "
        "Output JSON with 12-15 beats.\n"
        f"World slice: {world_ctx}"
    )
    prompt_beats = f"Structure={structure}; Length={length}; Tone={tone}; Genre={genre}"
    providers = _build_fallback_chain(preferred_provider, ai_settings)
    est = await _estimate_cost_pre_call(
        providers,
        model=model_beats,
        prompt=prompt_beats,
        system=system_beats,
        max_tokens=maxtok_beats,
    )
    if budget_usd > 0 and est is not None and (total_cost + est) > budget_usd:
        raise RuntimeError(f"budget_exceeded:{(total_cost + est):.4f}>{budget_usd:.4f}")
    start = time.perf_counter()
    prov, res = await _call_with_fallback(
        prompt=prompt_beats,
        system=system_beats,
        model=[model_beats] + [m for m in allowed_models if m != model_beats],
        json_mode=True,
        preferred_provider=preferred_provider,
        ai_settings=ai_settings,
        max_tokens=maxtok_beats,
        providers=providers,
    )
    cost = estimate_cost_usd(res.model, res.usage.prompt_tokens, res.usage.completion_tokens)
    if workspace_uuid:
        await record_usage(
            db,
            workspace_id=workspace_uuid,
            user_id=job.created_by,
            provider=getattr(prov, "name", "?"),
            model=res.model,
            usage=res.usage,
            cost=cost,
        )
    if budget_usd > 0 and (total_cost + cost) > budget_usd:
        try:
            labels = LLMCallLabels(
                provider=getattr(prov, "name", "?"), model=res.model, stage="beats"
            )
            llm_metrics.inc_error(labels, "budget_exceeded", 1)
        except Exception:
            pass
        raise RuntimeError(f"budget_exceeded:{(total_cost + cost):.4f}>{budget_usd:.4f}")
    try:
        stage_labels = LLMCallLabels(
            provider=getattr(prov, "name", "?"), model=res.model, stage="beats"
        )
        llm_metrics.inc("success", stage_labels, 1)
        llm_metrics.observe_tokens(
            stage_labels, res.usage.prompt_tokens, res.usage.completion_tokens
        )
        llm_metrics.observe_cost(stage_labels, cost)
        ms = (time.perf_counter() - start) * 1000
        try:
            from app.domains.telemetry.application.worker_metrics_facade import (
                worker_metrics,
            )

            worker_metrics.observe_stage("beats", ms)
        except Exception:
            pass
    except Exception:
        pass
    total_prompt += res.usage.prompt_tokens
    total_completion += res.usage.completion_tokens
    total_cost += cost
    beats_json = res.text
    await save_stage_log(
        db,
        job_id=job.id,
        stage="beats",
        provider=getattr(prov, "name", "?"),
        model=res.model,
        prompt=prompt_beats,
        raw_response=json.dumps(res.raw or {}, ensure_ascii=False),
        usage={
            "prompt": res.usage.prompt_tokens,
            "completion": res.usage.completion_tokens,
            "total": res.usage.total_tokens,
        },
        cost=cost,
    )
    try:
        job.progress = 33
        job.updated_at = datetime.utcnow()
        await db.flush()
    except Exception:
        pass

    # Stage 2: chapters
    system_ch = (
        f"You expand beats into chapters with entry/exit. Locale: {locale}. "
        "Keep consistency with world slice.\n"
        f"World slice: {world_ctx}\n"
        "Output JSON with entries/exits."
    )
    prompt_ch = f"Beats JSON:\n{beats_json}\nConstraints: structure={structure}"
    providers = _build_fallback_chain(preferred_provider, ai_settings)
    est = await _estimate_cost_pre_call(
        providers,
        model=model_chapters,
        prompt=prompt_ch,
        system=system_ch,
        max_tokens=maxtok_chapters,
    )
    if budget_usd > 0 and est is not None and (total_cost + est) > budget_usd:
        raise RuntimeError(f"budget_exceeded:{(total_cost + est):.4f}>{budget_usd:.4f}")
    start = time.perf_counter()
    prov, res = await _call_with_fallback(
        prompt=prompt_ch,
        system=system_ch,
        model=[model_chapters] + [m for m in allowed_models if m != model_chapters],
        json_mode=True,
        preferred_provider=preferred_provider,
        ai_settings=ai_settings,
        max_tokens=maxtok_chapters,
        providers=providers,
    )
    cost = estimate_cost_usd(res.model, res.usage.prompt_tokens, res.usage.completion_tokens)
    if workspace_uuid:
        await record_usage(
            db,
            workspace_id=workspace_uuid,
            user_id=job.created_by,
            provider=getattr(prov, "name", "?"),
            model=res.model,
            usage=res.usage,
            cost=cost,
        )
    if budget_usd > 0 and (total_cost + cost) > budget_usd:
        try:
            labels = LLMCallLabels(
                provider=getattr(prov, "name", "?"), model=res.model, stage="chapters"
            )
            llm_metrics.inc_error(labels, "budget_exceeded", 1)
        except Exception:
            pass
        raise RuntimeError(f"budget_exceeded:{(total_cost + cost):.4f}>{budget_usd:.4f}")
    try:
        stage_labels = LLMCallLabels(
            provider=getattr(prov, "name", "?"), model=res.model, stage="chapters"
        )
        llm_metrics.inc("success", stage_labels, 1)
        llm_metrics.observe_tokens(
            stage_labels, res.usage.prompt_tokens, res.usage.completion_tokens
        )
        llm_metrics.observe_cost(stage_labels, cost)
        ms = (time.perf_counter() - start) * 1000
        try:
            from app.domains.telemetry.application.worker_metrics_facade import (
                worker_metrics,
            )

            worker_metrics.observe_stage("chapters", ms)
        except Exception:
            pass
    except Exception:
        pass
    total_prompt += res.usage.prompt_tokens
    total_completion += res.usage.completion_tokens
    total_cost += cost
    chapters_json = res.text
    await save_stage_log(
        db,
        job_id=job.id,
        stage="chapters",
        provider=getattr(prov, "name", "?"),
        model=res.model,
        prompt=prompt_ch,
        raw_response=json.dumps(res.raw or {}, ensure_ascii=False),
        usage={
            "prompt": res.usage.prompt_tokens,
            "completion": res.usage.completion_tokens,
            "total": res.usage.total_tokens,
        },
        cost=cost,
    )
    try:
        job.progress = 66
        job.updated_at = datetime.utcnow()
        await db.flush()
    except Exception:
        pass

    # Stage 3: nodes
    system_nodes = (
        f"You write narrative nodes with choices. Locale: {locale}. "
        "Maintain coherence with world slice.\n"
        f"World slice: {world_ctx}\n"
        "Output JSON graph nodes/edges."
    )
    prompt_nodes = f"Chapters JSON:\n{chapters_json}"
    providers = _build_fallback_chain(preferred_provider, ai_settings)
    est = await _estimate_cost_pre_call(
        providers,
        model=model_nodes,
        prompt=prompt_nodes,
        system=system_nodes,
        max_tokens=maxtok_nodes,
    )
    if budget_usd > 0 and est is not None and (total_cost + est) > budget_usd:
        raise RuntimeError(f"budget_exceeded:{(total_cost + est):.4f}>{budget_usd:.4f}")
    start = time.perf_counter()
    prov, res = await _call_with_fallback(
        prompt=prompt_nodes,
        system=system_nodes,
        model=[model_nodes] + [m for m in allowed_models if m != model_nodes],
        json_mode=True,
        preferred_provider=preferred_provider,
        ai_settings=ai_settings,
        max_tokens=maxtok_nodes,
        providers=providers,
    )
    cost = estimate_cost_usd(res.model, res.usage.prompt_tokens, res.usage.completion_tokens)
    if workspace_uuid:
        await record_usage(
            db,
            workspace_id=workspace_uuid,
            user_id=job.created_by,
            provider=getattr(prov, "name", "?"),
            model=res.model,
            usage=res.usage,
            cost=cost,
        )
    if budget_usd > 0 and (total_cost + cost) > budget_usd:
        try:
            labels = LLMCallLabels(
                provider=getattr(prov, "name", "?"), model=res.model, stage="nodes"
            )
            llm_metrics.inc_error(labels, "budget_exceeded", 1)
        except Exception:
            pass

        raise RuntimeError(f"budget_exceeded:{(total_cost + cost):.4f}>{budget_usd:.4f}")
    try:
        stage_labels = LLMCallLabels(
            provider=getattr(prov, "name", "?"), model=res.model, stage="nodes"
        )
        llm_metrics.inc("success", stage_labels, 1)
        llm_metrics.observe_tokens(
            stage_labels, res.usage.prompt_tokens, res.usage.completion_tokens
        )
        llm_metrics.observe_cost(stage_labels, cost)
        ms = (time.perf_counter() - start) * 1000
        try:
            from app.domains.telemetry.application.worker_metrics_facade import (
                worker_metrics,
            )

            worker_metrics.observe_stage("nodes", ms)
        except Exception:
            pass
    except Exception:
        pass
    total_prompt += res.usage.prompt_tokens
    total_completion += res.usage.completion_tokens
    total_cost += cost

    from app.domains.ai.persist import persist_generated_quest
    from app.domains.ai.validation import validate_version_graph

    try:
        result_quest_id, result_version_id = await persist_generated_quest(db, job, res.text)
        try:
            await validate_version_graph(db, result_version_id)
        except Exception as ve:
            logger.warning("Validation failed (non-fatal): %s", ve)
    except Exception as e:
        logger.exception("Persisting generated quest failed: %s", e)
        raise

    await save_stage_log(
        db,
        job_id=job.id,
        stage="nodes",
        provider=getattr(prov, "name", "?"),
        model=res.model,
        prompt=prompt_nodes,
        raw_response=json.dumps(res.raw or {}, ensure_ascii=False),
        usage={
            "prompt": res.usage.prompt_tokens,
            "completion": res.usage.completion_tokens,
            "total": res.usage.total_tokens,
        },
        cost=cost,
    )
    try:
        job.progress = 99
        job.updated_at = datetime.utcnow()
        await db.flush()
    except Exception:
        pass

    token_usage = {
        "stages": stage_logs
        and [
            {
                "stage": s.stage,
                "usage": s.usage,
                "cost": s.cost,
                "provider": s.provider,
                "model": s.model,
            }
            for s in stage_logs
        ]
        or [],
        "total": {
            "prompt": total_prompt,
            "completion": total_completion,
            "total": total_prompt + total_completion,
        },
    }

    return {
        "result_quest_id": result_quest_id,
        "result_version_id": result_version_id,
        "cost": round(total_cost, 6),
        "token_usage": token_usage,
        "logs": [],
        "last_provider": None,
        "last_model": model_nodes,
    }
