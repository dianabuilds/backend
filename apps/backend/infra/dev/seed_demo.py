from __future__ import annotations

r"""
Seed demo data into the database: creates N users and M nodes.

Usage (PowerShell/Windows):
  set APP_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app
  .venv\Scripts\python.exe apps\backend\infra\dev\seed_demo.py --users 10 --nodes 50

Environment:
  - APP_DATABASE_URL or DATABASE_URL must be set. Async or sync Postgres URLs are accepted.

Notes:
  - The script is idempotent for generated usernames/emails (ON CONFLICT/UPSERT where possible).
  - Nodes now include sample HTML content, canonical tags, cover images sourced from /static, and embeddings (API-backed with deterministic fallback).
  - Tag catalog, tag usage counters, and node association cache are updated when corresponding tables are available.
  - It detects optional columns (username/display_name/role/password_hash) and tables (user_roles).
  - If pgcrypto is available, seeds password_hash using crypt() for password "pass123".
"""

import argparse
import hashlib
import logging
import math
import os
import random
import re
import secrets
import string
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger("seed_demo")


def _normalize_for_asyncpg(s: str) -> str:
    """Ensure DSN is asyncpg and strip/convert sslmode (case-insensitive)."""
    # Ensure driver
    if s.startswith("postgresql+asyncpg://"):
        out = s
    elif s.startswith("postgresql://"):
        out = "postgresql+asyncpg://" + s[len("postgresql://") :]
    else:
        out = s
    try:
        u = urlsplit(out)
        pairs = parse_qsl(u.query, keep_blank_values=True)
        ssl_mode_val = None
        new_pairs = []
        for k, v in pairs:
            if k.lower() == "sslmode":
                ssl_mode_val = v
                continue
            new_pairs.append((k, v))
        if ssl_mode_val is not None:
            mode = str(ssl_mode_val).strip().lower()
            if mode in {"require", "verify-full", "verify-ca"}:
                new_pairs.append(("ssl", "true"))
            elif mode in {"disable", "allow", "prefer", "0", "false"}:
                new_pairs.append(("ssl", "false"))
            else:
                new_pairs.append(("ssl", "false"))
        query = urlencode(new_pairs)
        out = urlunsplit((u.scheme, u.netloc, u.path, query, u.fragment))
    except Exception:
        pass
    # Final guard: strip any lingering sslmode by regex (case-insensitive)
    try:
        out = re.sub(
            r"([?&])sslmode=[^&]*(&|$)",
            lambda m: m.group(1) if m.group(2) == "&" else "",
            out,
            flags=re.IGNORECASE,
        )
        # Remove dangling ? or & at end
        out = re.sub(r"[?&]$", "", out)
    except Exception:
        pass
    return out


def _to_async_dsn(url: str) -> str:
    out = url
    try:
        from packages.core.config import to_async_dsn as _conv  # type: ignore

        out = _conv(url)  # type: ignore
    except Exception:
        pass
    # Always run our normalizer to be safe
    return _normalize_for_asyncpg(out)


def _load_dotenv(path: str) -> None:
    try:
        if not os.path.exists(path):
            return
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ.setdefault(k, v)
    except Exception:
        pass


def _load_env_files_nearby() -> None:
    # Walk up a few levels to find .env and apps/backend/.env
    here = os.path.abspath(__file__)
    cur = os.path.dirname(here)
    for _ in range(6):
        root_env = os.path.join(cur, ".env")
        app_env = os.path.join(cur, "apps", "backend", ".env")
        _load_dotenv(root_env)
        _load_dotenv(app_env)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent


async def _column_exists(engine: AsyncEngine, table: str, column: str) -> bool:
    sql = text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = :t
          AND column_name = :c
        LIMIT 1
        """
    )
    async with engine.begin() as conn:
        row = (await conn.execute(sql, {"t": table, "c": column})).first()
        return bool(row)


async def _table_exists(engine: AsyncEngine, table: str) -> bool:
    sql = text(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = current_schema() AND table_name = :t
        LIMIT 1
        """
    )
    async with engine.begin() as conn:
        row = (await conn.execute(sql, {"t": table})).first()
        return bool(row)


def _rand(n: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


@dataclass
class CreatedUser:
    id: str
    email: str
    username: str


async def _ensure_pgcrypto(engine: AsyncEngine) -> None:
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
    except Exception:
        pass


async def seed_users(engine: AsyncEngine, count: int = 10) -> list[CreatedUser]:
    await _ensure_pgcrypto(engine)
    have_username = await _column_exists(engine, "users", "username")
    have_display = await _column_exists(engine, "users", "display_name")
    have_role_col = await _column_exists(engine, "users", "role")
    have_pwd = await _column_exists(engine, "users", "password_hash")
    have_user_roles = await _table_exists(engine, "user_roles")

    created: list[CreatedUser] = []
    async with engine.begin() as conn:
        for i in range(count):
            uname = f"user_{_rand(6)}_{i+1}"
            email = f"{uname}@example.com"
            # Build dynamic INSERT
            cols: list[str] = []
            vals: list[str] = []
            params: dict[str, object] = {"email": email, "uname": uname}
            cols.append("email")
            vals.append(":email")
            # If both columns exist, set both; else set what exists
            if have_username:
                cols.append("username")
                vals.append(":uname")
            if have_display:
                cols.append("display_name")
                vals.append(":uname")
            cols.append("is_active")
            vals.append("true")
            if have_role_col:
                cols.append("role")
                vals.append("'user'::user_role")
            if have_pwd:
                cols.append("password_hash")
                vals.append("crypt(:pwd, gen_salt('bf'))")
                params["pwd"] = "pass123"
            updates: list[str] = []
            if have_username:
                updates.append("username = EXCLUDED.username")
            if have_display:
                updates.append("display_name = EXCLUDED.display_name")
            updates.append("is_active = EXCLUDED.is_active")
            name_expr = (
                "username" if have_username else ("display_name" if have_display else "email")
            )
            sql = text(
                f"""
                INSERT INTO users ({', '.join(cols)})
                VALUES ({', '.join(vals)})
                ON CONFLICT (email) DO UPDATE SET {', '.join(updates)}
                RETURNING id::text, coalesce({name_expr}, email) as uname
                """
            )
            row = (await conn.execute(sql, params)).mappings().first()
            if not row:
                continue
            uid = str(row["id"])  # type: ignore[index]
            created.append(CreatedUser(id=uid, email=email, username=str(row["uname"])))
            # user_roles M2M if present
            if have_user_roles:
                await conn.execute(
                    text(
                        "INSERT INTO user_roles (user_id, role) VALUES (cast(:uid as uuid), 'user'::user_role) ON CONFLICT DO NOTHING"
                    ),
                    {"uid": uid},
                )
    return created


@dataclass
class NodeSeedData:
    author_id: str
    title: str
    tags: list[str]
    is_public: bool
    status: str | None
    publish_at: str | None
    unpublish_at: str | None
    content_html: str
    cover_url: str | None
    embedding: list[float] | None


@dataclass
class CreatedNode:
    id: int
    author_id: str
    tags: list[str]
    embedding: list[float] | None
    is_public: bool


_CONTENT_TOPICS = [
    {
        "title": "Vector Index Warmup",
        "summary": "Step-by-step process to verify pgvector indexes before shipping semantic navigation updates.",
        "tags": ["vector-search", "pgvector", "ops"],
        "insights": [
            "Shadow traffic reveals recall dips before they hit production.",
            "Track ivfflat list counts versus dataset growth to keep recall above 0.90.",
            "Fallback to brute force search if coverage drops below the guardrail.",
            "Record index rebuild duration to size maintenance windows realistically.",
            "Run ANALYZE after bulk embedding writes so the planner keeps fresh stats.",
        ],
    },
    {
        "title": "Cold Start Recommendations",
        "summary": "Blend curated picks with embeddings to avoid empty states for new explorers.",
        "tags": ["navigation", "personalization", "experimentation"],
        "insights": [
            "Serve a curated mix while embeddings backfill to keep bounce rates low.",
            "Mirror user actions into tag usage counters for quick personalization wins.",
            "Use epsilon-greedy exploration so the model keeps collecting feedback.",
            "Expire cached suggestions after major taxonomy changes to avoid drift.",
        ],
    },
    {
        "title": "Quality Review Workflow",
        "summary": "How the team inspects embedding drift and approves model upgrades.",
        "tags": ["qa", "telemetry", "embeddings"],
        "insights": [
            "Compare offline cosine scores against human labels every sprint.",
            "Alert when embedding latency or failure rates spike above thresholds.",
            "Annotate recompute jobs with pipeline version and rollout owner.",
            "Keep a golden set of regression prompts for quick smoke tests.",
        ],
    },
    {
        "title": "Semantic Search UX",
        "summary": "Turn qualitative search feedback into measurable UX upgrades.",
        "tags": ["ux", "search", "content"],
        "insights": [
            "Explain scores with tag and embedding factors so editors trust the output.",
            "Track zero-result queries and feed them into weekly copy reviews.",
            "Expose cover art and summaries that match the intent of the query.",
            "Cache last-good queries to keep latency steady during provider hiccups.",
        ],
    },
    {
        "title": "Metrics & Telemetry",
        "summary": "Dashboards that keep navigation quality visible to product and ops.",
        "tags": ["telemetry", "observability", "ops"],
        "insights": [
            "Break down navigation pool usage by provider and temperature.",
            "Layer SLO budgets on embedding latency to catch degradations early.",
            "Store query vectors for replay when investigating regressions.",
            "Share weekly scorecards with product so trade-offs stay explicit.",
        ],
    },
    {
        "title": "Tag Hygiene Sprint",
        "summary": "Keep the taxonomy tidy so semantic signals stay rich.",
        "tags": ["tags", "taxonomy", "moderation"],
        "insights": [
            "Merge low-signal tags and retire aliases every cycle.",
            "Lock critical tags behind review to prevent accidental drift.",
            "Use usage counters to spot stale topics that need refresh.",
            "Pair editors with data partners to agree on definitions early.",
        ],
    },
    {
        "title": "Prompt Engineering Clinics",
        "summary": "Share prompt experiments that lifted generation quality for copy blocks.",
        "tags": ["ai", "prompting", "workflow"],
        "insights": [
            "Document prompt templates alongside measured win rates.",
            "Sandbox major prompt changes before rolling into live assistants.",
            "Track token budgets so experiments stay within plan limits.",
            "Rotate reviewers so we keep fresh eyes on hallucination edge cases.",
        ],
    },
    {
        "title": "Retention Journey",
        "summary": "Use embeddings to surface journeys that retain new storytellers.",
        "tags": ["retention", "product", "growth"],
        "insights": [
            "Blend cohort data with semantic neighbors to highlight success paths.",
            "Instrument feature adoption milestones directly in the navigation payload.",
            "Spot leading indicators when creators fall off and trigger nudge campaigns.",
            "A/B test recommendation mixes before committing to long-lived slots.",
        ],
    },
    {
        "title": "Feedback Loop Acceleration",
        "summary": "Fast ways to harvest qualitative feedback into the ranking backlog.",
        "tags": ["feedback", "analytics", "loop"],
        "insights": [
            "Route thumbs-down events straight into moderation triage channels.",
            "Summarize qualitative notes with embeddings to cluster pain points.",
            "Close the loop by notifying reporters when fixes land.",
            "Tag feedback by persona so product can prioritise fairly.",
        ],
    },
    {
        "title": "Knowledge Base Migration",
        "summary": "Lessons from moving legacy docs into the new node system.",
        "tags": ["migration", "documentation", "ops"],
        "insights": [
            "Stage migrations in batches so embeddings recompute steadily.",
            "Keep old slugs alive with redirects to protect SEO equity.",
            "Audit covers and alt text to maintain accessibility compliance.",
            "Diff rendered HTML to catch formatting regressions early.",
        ],
    },
]

_CONTENT_FRAMES = [
    {
        "label": "Field Guide",
        "lead": "Field guide for {topic} so teams can move from experimentation to steady-state faster.",
        "tags": ["guide", "playbook", "field-notes"],
    },
    {
        "label": "Weekly Digest",
        "lead": "Weekly digest capturing what changed around {topic} and why it matters right now.",
        "tags": ["digest", "updates", "newsletter"],
    },
    {
        "label": "Experiment Memo",
        "lead": "Experiment memo outlining the latest iteration on {topic} and the data behind it.",
        "tags": ["experiment", "analysis", "lab"],
    },
    {
        "label": "Leadership Brief",
        "lead": "Leadership brief to align stakeholders on the direction of {topic}.",
        "tags": ["leadership", "strategy", "brief"],
    },
    {
        "label": "War Story",
        "lead": "War story retelling how we recovered from a {topic} outage and hardened safeguards.",
        "tags": ["story", "incident", "resilience"],
    },
    {
        "label": "Launch Checklist",
        "lead": "Practical checklist that teams can follow when rolling out {topic} changes.",
        "tags": ["checklist", "ops", "launch"],
    },
]

_GENERAL_INSIGHTS = [
    "Schedule weekly pairing with support to replay tough navigation tickets.",
    "Surface explainability metrics so editors see why a node shows up.",
    "Automate smoke tests against /v1/navigation/next before every release.",
    "Track editor throughput and celebrate the wins in weekly demos.",
    "Keep a backlog label for quick wins discovered during review triage.",
]

_CTA_LIBRARY = [
    "Roll this out behind a feature flag and review metrics after 48 hours.",
    "Link this node inside the editor handbook so newcomers can find it.",
    "Pair with the recompute script to prove the uplift before scaling to all regions.",
    "Document open questions directly in the node comments to keep async collaboration tidy.",
    "Share the wins during Friday demo so adoption keeps momentum.",
    "Drop a note in #navigation to gather extra feedback before GA.",
]

_SPOTLIGHT_QUOTES = [
    "The semantic pool finally feels aligned with editor instincts; the drift alerts saved us twice this month.",
    "Embedding recompute now finishes in under an hour, which keeps experimentation nimble.",
    "Editors loved seeing explainability metrics next to every recommendation.",
    "Cold start flows no longer feel random -- the curated mix plus embeddings did the trick.",
    "We caught a regression before launch because the checklist forced a dry run.",
]
_EXTRA_TAG_OPTIONS = [
    "workflow",
    "insights",
    "roadmap",
    "ops",
    "strategy",
    "quality",
    "playbook",
    "enablement",
    "dispatch",
    "weekly",
    "practice",
]


def _discover_cover_images() -> list[str]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    try:
        here = Path(__file__).resolve()
    except Exception:
        return []
    for parent in here.parents:
        candidate = parent / "static"
        if candidate.is_dir():
            files = sorted(
                f.name for f in candidate.iterdir() if f.is_file() and f.suffix.lower() in exts
            )
            if files:
                return files
    return []


def _canon_tag(value: object) -> str:
    slug = re.sub(r"[^a-z0-9\s-]", "", str(value).lower())
    slug = slug.replace(" ", "-")
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "insights"


def _compose_node_content(
    *, topic: dict, frame: dict, callout: str, spotlight: str, highlights: list[str]
) -> str:
    sections: list[str] = []
    sections.append(
        f"<p><strong>{frame['label']}:</strong> {frame['lead'].format(topic=topic['title'].lower())}</p>"
    )
    sections.append(f"<p>{topic['summary']}</p>")
    if highlights:
        sections.append("<p>Key points we captured:</p>")
        sections.append("<ul>" + "".join(f"<li>{point}</li>" for point in highlights) + "</ul>")
    sections.append(f"<blockquote>{spotlight}</blockquote>")
    sections.append(f"<p>{callout}</p>")
    return "\n".join(sections)


def _build_embedding_payload(title: str, tags: Sequence[str], content_html: str) -> str:
    parts: list[str] = []
    if title:
        parts.append(title.strip())
    if tags:
        parts.append(" ".join(t.strip() for t in tags if t))
    if content_html:
        stripped = re.sub(r"<[^>]+>", " ", content_html)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        if stripped:
            parts.append(stripped)
    return "\n".join(part for part in parts if part).strip()


def _build_embedding_client() -> tuple[object | None, int]:
    try:
        from domains.product.nodes.application.embedding import EmbeddingClient
        from packages.core.config import load_settings
    except Exception:
        return None, 384
    try:
        settings = load_settings()
        dim = int(getattr(settings, "embedding_dim", None) or 384)
        base = settings.embedding_api_base
        base_url = str(base) if base else None
        if base_url and base_url.rstrip("/").endswith("/embeddings"):
            trimmed = base_url.rstrip("/")
            base_url = trimmed[: -len("/embeddings")]
        client = EmbeddingClient(
            base_url=base_url,
            model=str(settings.embedding_model) if settings.embedding_model else None,
            api_key=str(settings.embedding_api_key) if settings.embedding_api_key else None,
            provider=str(settings.embedding_provider) if settings.embedding_provider else None,
            timeout=float(getattr(settings, "embedding_timeout", 10.0)),
            connect_timeout=float(getattr(settings, "embedding_connect_timeout", 2.0)),
            retries=int(getattr(settings, "embedding_retries", 3)),
            enabled=bool(getattr(settings, "embedding_enabled", True)),
        )
        return client, dim
    except Exception:
        return None, 384


def _fallback_embedding(text: str, dim: int) -> list[float]:
    seed_source = text or "seed-demo"
    digest = hashlib.sha256(seed_source.encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest, "big"))
    vec = [rng.uniform(-1.0, 1.0) for _ in range(dim)]
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 1e-9:
        vec = [v / norm for v in vec]
    return vec


def _normalize_vector(vec: Sequence[float] | None) -> list[float] | None:
    if not vec:
        return None
    norm = math.sqrt(sum(float(v) * float(v) for v in vec))
    if norm <= 1e-9:
        return None
    return [float(v) / norm for v in vec]


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b, strict=False)))


async def _seed_tag_catalog(engine: AsyncEngine, tags: Sequence[str]) -> int:
    if not tags:
        return 0
    try:
        if not await _table_exists(engine, "tag"):
            return 0
    except Exception:
        return 0
    inserted = 0
    try:
        async with engine.begin() as conn:
            for slug in tags:
                name = slug.replace("-", " ").title()
                await conn.execute(
                    text(
                        "INSERT INTO tag (slug, name) VALUES (:slug, :name) "
                        "ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name"
                    ),
                    {"slug": slug, "name": name},
                )
                inserted += 1
    except Exception:
        return 0
    return inserted


async def _seed_tag_usage(engine: AsyncEngine, nodes: Sequence[CreatedNode]) -> int:
    if not nodes:
        return 0
    try:
        if not await _table_exists(engine, "tag_usage_counters"):
            return 0
    except Exception:
        return 0
    counters: dict[tuple[str, str], int] = {}
    for node in nodes:
        for tag in node.tags:
            key = (node.author_id, tag)
            counters[key] = counters.get(key, 0) + 1
    if not counters:
        return 0
    updated = 0
    try:
        async with engine.begin() as conn:
            for (author_id, tag), count in counters.items():
                await conn.execute(
                    text(
                        "INSERT INTO tag_usage_counters(author_id, content_type, slug, count) "
                        "VALUES (cast(:aid as uuid), 'node', :slug, :count) "
                        "ON CONFLICT (author_id, content_type, slug) DO UPDATE SET "
                        "count = tag_usage_counters.count + EXCLUDED.count"
                    ),
                    {"aid": author_id, "slug": tag, "count": count},
                )
                updated += 1
    except Exception:
        return 0
    return updated


async def _seed_node_assoc_cache(engine: AsyncEngine, nodes: Sequence[CreatedNode]) -> int:
    if not nodes:
        return 0
    try:
        if not await _table_exists(engine, "node_assoc_cache"):
            return 0
    except Exception:
        return 0
    normalized: dict[int, list[float]] = {}
    for node in nodes:
        norm = _normalize_vector(node.embedding)
        if norm is not None:
            normalized[node.id] = norm
    entries: dict[tuple[str, int, int], float] = {}
    if len(normalized) >= 2:
        for node in nodes:
            base = normalized.get(node.id)
            if base is None:
                continue
            scored: list[tuple[float, int]] = []
            for other_id, other_vec in normalized.items():
                if other_id == node.id:
                    continue
                score = _cosine_similarity(base, other_vec)
                if score <= 0:
                    continue
                scored.append((score, other_id))
            scored.sort(key=lambda item: item[0], reverse=True)
            for score, target_id in scored[:6]:
                entries[("embedding", node.id, target_id)] = max(
                    entries.get(("embedding", node.id, target_id), 0.0), float(score)
                )
    for node in nodes:
        tag_set = set(node.tags)
        if not tag_set:
            continue
        tag_scored: list[tuple[float, int]] = []
        for other in nodes:
            if other.id == node.id:
                continue
            other_tags = set(other.tags)
            if not other_tags:
                continue
            inter = len(tag_set & other_tags)
            if inter == 0:
                continue
            union = len(tag_set | other_tags)
            jaccard = inter / union if union else 0.0
            score = jaccard + (0.05 if other.is_public else 0.0)
            tag_scored.append((score, other.id))
        tag_scored.sort(key=lambda item: item[0], reverse=True)
        for score, target_id in tag_scored[:6]:
            entries[("tags", node.id, target_id)] = max(
                entries.get(("tags", node.id, target_id), 0.0), float(score)
            )
    if not entries:
        return 0
    source_ids = sorted({key[1] for key in entries.keys()})
    algos = sorted({key[0] for key in entries.keys()})
    rows = [
        {"algo": algo, "source_id": sid, "target_id": tid, "score": round(score, 6)}
        for (algo, sid, tid), score in entries.items()
    ]
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "DELETE FROM node_assoc_cache WHERE source_id = ANY(:ids) AND algo = ANY(:algos)"
                ),
                {"ids": source_ids, "algos": algos},
            )
            for row in rows:
                await conn.execute(
                    text(
                        "INSERT INTO node_assoc_cache(source_id, target_id, algo, score, updated_at) "
                        "VALUES (:source_id, :target_id, :algo, :score, now()) "
                        "ON CONFLICT (source_id, target_id, algo) DO UPDATE SET "
                        "score = EXCLUDED.score, updated_at = now()"
                    ),
                    row,
                )
    except Exception:
        return 0
    return len(rows)


async def _make_embedding_vector(
    client: object | None, text_value: str, dim: int
) -> tuple[list[float], str]:
    cleaned = (text_value or "").strip()
    if not cleaned:
        cleaned = "seed-demo node"
    try:
        enabled = bool(getattr(client, "enabled", False)) if client is not None else False
    except Exception:
        enabled = False
    if client is not None and enabled:
        try:
            vec = await client.embed(cleaned)  # type: ignore[attr-defined]
            if vec:
                return [float(v) for v in vec], "provider"
        except Exception as exc:
            logger.debug("embedding provider unavailable, falling back: %s", exc)
    return _fallback_embedding(cleaned, dim), "fallback"


async def seed_nodes(
    engine: AsyncEngine, authors: Iterable[CreatedUser], count: int = 50
) -> list[int]:
    author_ids = [a.id for a in authors]
    if not author_ids:
        raise RuntimeError("No authors available to create nodes")
    have_slug = await _column_exists(engine, "nodes", "slug")
    have_status = await _column_exists(engine, "nodes", "status")
    have_publish = await _column_exists(engine, "nodes", "publish_at")
    have_unpublish = await _column_exists(engine, "nodes", "unpublish_at")
    have_content = await _column_exists(engine, "nodes", "content_html")
    have_cover = await _column_exists(engine, "nodes", "cover_url")
    have_embedding = await _column_exists(engine, "nodes", "embedding")
    cover_choices = _discover_cover_images()
    cover_index = 0
    embedding_client: object | None
    embedding_dim: int
    if have_embedding:
        embedding_client, embedding_dim = _build_embedding_client()
    else:
        embedding_client, embedding_dim = None, 384
    embedding_stats = {"provider": 0, "fallback": 0, "skipped": 0}
    seeds: list[NodeSeedData] = []
    for _ in range(count):
        author_id = random.choice(author_ids)
        topic = random.choice(_CONTENT_TOPICS)
        frame = random.choice(_CONTENT_FRAMES)
        callout = random.choice(_CTA_LIBRARY)
        spotlight = random.choice(_SPOTLIGHT_QUOTES)
        highlight_pool = list(topic["insights"])
        extra_highlights = min(2, len(_GENERAL_INSIGHTS))
        if extra_highlights:
            highlight_pool.extend(random.sample(_GENERAL_INSIGHTS, k=extra_highlights))
        highlights = random.sample(highlight_pool, k=min(3, len(highlight_pool)))
        title_options = [
            f"{frame['label']}: {topic['title']}",
            f"{topic['title']} - {frame['label']}",
            f"{frame['label']} | {topic['title']}",
        ]
        title = random.choice(title_options)
        content_html = _compose_node_content(
            topic=topic,
            frame=frame,
            callout=callout,
            spotlight=spotlight,
            highlights=highlights,
        )
        tag_pool = {_canon_tag(t) for t in topic["tags"]}
        tag_pool.update(_canon_tag(t) for t in frame.get("tags", []))
        tag_pool.add(_canon_tag(frame["label"]))
        extra_tag_count = min(2, len(_EXTRA_TAG_OPTIONS))
        if extra_tag_count:
            tag_pool.update(
                _canon_tag(t) for t in random.sample(_EXTRA_TAG_OPTIONS, k=extra_tag_count)
            )
        tags = sorted(tag_pool)
        if len(tags) > 5:
            random.shuffle(tags)
            tags = sorted(tags[:5])
        is_public = random.random() < 0.72
        status = "published" if is_public else "draft"
        cover_url = None
        if cover_choices:
            cover_name = cover_choices[cover_index % len(cover_choices)]
            cover_url = f"/static/{cover_name}"
            cover_index += 1
        embedding_vec: list[float] | None = None
        if have_embedding:
            payload = _build_embedding_payload(title, tags, content_html)
            embedding_vec, source = await _make_embedding_vector(
                embedding_client, payload, embedding_dim
            )
            embedding_stats[source] = embedding_stats.get(source, 0) + 1
        else:
            embedding_stats["skipped"] += 1
        seeds.append(
            NodeSeedData(
                author_id=author_id,
                title=title,
                tags=tags,
                is_public=is_public,
                status=status,
                publish_at=None,
                unpublish_at=None,
                content_html=content_html,
                cover_url=cover_url,
                embedding=embedding_vec if have_embedding else None,
            )
        )
    all_tags = sorted({tag for seed in seeds for tag in seed.tags})
    tag_catalog_updates = await _seed_tag_catalog(engine, all_tags)
    created_ids: list[int] = []
    created_nodes: list[CreatedNode] = []
    async with engine.begin() as conn:
        for seed in seeds:
            cols = ["author_id", "title", "is_public"]
            vals = ["cast(:aid as uuid)", ":title", ":pub"]
            params: dict[str, object] = {
                "aid": seed.author_id,
                "title": seed.title,
                "pub": seed.is_public,
            }
            if have_slug:
                slug = secrets.token_hex(8)
                cols.append("slug")
                vals.append(":slug")
                params["slug"] = slug
            if have_status:
                cols.append("status")
                vals.append(":status")
                params["status"] = seed.status
            if have_publish:
                cols.append("publish_at")
                vals.append(":publish_at")
                params["publish_at"] = seed.publish_at
            if have_unpublish:
                cols.append("unpublish_at")
                vals.append(":unpublish_at")
                params["unpublish_at"] = seed.unpublish_at
            if have_content:
                cols.append("content_html")
                vals.append(":content")
                params["content"] = seed.content_html
            if have_cover:
                cols.append("cover_url")
                vals.append(":cover")
                params["cover"] = seed.cover_url
            if have_embedding:
                cols.append("embedding")
                vals.append(":embedding")
                params["embedding"] = list(seed.embedding) if seed.embedding is not None else None
            sql = text(
                f"INSERT INTO nodes({', '.join(cols)}) VALUES ({', '.join(vals)}) RETURNING id"
            )
            row = (await conn.execute(sql, params)).first()
            if row is None:
                continue
            nid = int(row[0])
            created_ids.append(nid)
            created_nodes.append(
                CreatedNode(
                    id=nid,
                    author_id=seed.author_id,
                    tags=seed.tags,
                    embedding=(
                        list(seed.embedding)
                        if (have_embedding and seed.embedding is not None)
                        else None
                    ),
                    is_public=seed.is_public,
                )
            )
            for tag in seed.tags:
                await conn.execute(
                    text(
                        "INSERT INTO product_node_tags(node_id, slug) VALUES (:id, :slug) ON CONFLICT DO NOTHING"
                    ),
                    {"id": nid, "slug": tag},
                )
    tag_usage_updates = await _seed_tag_usage(engine, created_nodes)
    assoc_updates = await _seed_node_assoc_cache(engine, created_nodes)
    if have_embedding:
        print(
            "Embedding coverage -> provider:{provider} fallback:{fallback} skipped:{skipped}".format(
                provider=embedding_stats.get("provider", 0),
                fallback=embedding_stats.get("fallback", 0),
                skipped=embedding_stats.get("skipped", 0),
            )
        )
    if tag_catalog_updates:
        print(f"Ensured {tag_catalog_updates} tag slugs in catalog")
    if tag_usage_updates:
        print(f"Updated {tag_usage_updates} tag usage counters")
    if assoc_updates:
        print(f"Cached {assoc_updates} node relations")
    if cover_choices:
        print(f"Cover pool size: {len(cover_choices)} images")
    return created_ids


async def main() -> None:
    ap = argparse.ArgumentParser(description="Seed demo users and nodes")
    ap.add_argument("--users", type=int, default=10, help="Users to create")
    ap.add_argument("--nodes", type=int, default=50, help="Nodes to create")
    ap.add_argument("--dburl", type=str, default=None, help="Override DB URL (postgresql://...)")
    ap.add_argument("--debug", action="store_true", help="Print debug info (show sanitized DSN)")
    args = ap.parse_args()

    _load_env_files_nearby()
    dsn = args.dburl or os.getenv("APP_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise SystemExit("Set APP_DATABASE_URL or DATABASE_URL")
    # Normalize DSN robustly; print for debug
    dsn_norm = _to_async_dsn(dsn)
    try:
        # Final strip if any sslmode sneaked in
        import re as _re

        dsn_norm = _re.sub(
            r"([?&])sslmode=[^&]*(&|$)",
            lambda m: m.group(1) if m.group(2) == "&" else "",
            dsn_norm,
            flags=_re.IGNORECASE,
        )
        dsn_norm = _re.sub(r"[?&]$", "", dsn_norm)
    except Exception:
        pass
    # Optional: unset PGSSLMODE to avoid interference (safety; asyncpg shouldn't read it)
    os.environ.pop("PGSSLMODE", None)

    # Build engine without query; pass ssl via connect_args explicitly
    from urllib.parse import parse_qsl as _pqsl
    from urllib.parse import urlsplit as _usplit
    from urllib.parse import urlunsplit as _uunsplit

    dsn_parts = _usplit(dsn_norm)
    qs = dict(_pqsl(dsn_parts.query, keep_blank_values=True))
    ssl_flag = None
    if "ssl" in {k.lower() for k in qs.keys()}:
        for k, v in list(qs.items()):
            if k.lower() == "ssl":
                ssl_flag = str(v).strip().lower() in {"1", "true", "yes"}
    # Also map sslmode (if present after all cleans)
    if ssl_flag is None:
        for k, v in list(qs.items()):
            if k.lower() == "sslmode":
                mode = str(v).strip().lower()
                if mode in {"require", "verify-full", "verify-ca"}:
                    ssl_flag = True
                elif mode in {"disable", "allow", "prefer", "0", "false"}:
                    ssl_flag = False
                break
    dsn_no_query = _uunsplit(
        (dsn_parts.scheme, dsn_parts.netloc, dsn_parts.path, "", dsn_parts.fragment)
    )
    connect_args = {}
    if ssl_flag is not None:
        connect_args = {"connect_args": {"ssl": ssl_flag}}
    if args.debug:

        def _sanitize(netloc: str) -> str:
            try:
                if "@" not in netloc:
                    return netloc
                creds, host = netloc.split("@", 1)
                if ":" in creds:
                    user, _pwd = creds.split(":", 1)
                    return f"{user}:***@{host}"
                return f"***@{host}"
            except Exception:
                return netloc

        print(
            "[seed] Using DSN:",
            _uunsplit(
                (
                    dsn_parts.scheme,
                    _sanitize(dsn_parts.netloc),
                    dsn_parts.path,
                    "",
                    dsn_parts.fragment,
                )
            ),
        )
        print("[seed] connect_args:", connect_args)
        print("[seed] PGSSLMODE present:", "PGSSLMODE" in os.environ)
    engine = create_async_engine(dsn_no_query, **connect_args)

    users = await seed_users(engine, args.users)
    print(f"Created/updated users: {len(users)}")
    nodes = await seed_nodes(engine, users, args.nodes)
    print(f"Created nodes: {len(nodes)}")
    print("Sample:")
    for u in users[:3]:
        print(f" - {u.username} <{u.email}> id={u.id}")
    for nid in nodes[:5]:
        print(f" - node {nid}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
