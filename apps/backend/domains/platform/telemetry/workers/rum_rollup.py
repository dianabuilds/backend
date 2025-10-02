from __future__ import annotations

import asyncio
import gzip
import io
import json
import time
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from domains.platform.telemetry.adapters.rum_repository import (
    RumAggregate,
    RumRedisRepository,
)
from domains.platform.telemetry.wires import build_container
from packages.core.config import Settings
from packages.worker import PeriodicWorker, PeriodicWorkerConfig
from packages.worker.registry import WorkerRuntimeContext, register_worker

_WORKER_NAME = "telemetry.rum_rollup"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _ensure_trailing_slash(prefix: str) -> str:
    return prefix if prefix.endswith("/") else f"{prefix}/"


class _S3RumExporter:
    def __init__(
        self,
        *,
        bucket: str,
        prefix: str,
        region: str | None,
        compress: bool,
    ) -> None:
        try:
            import boto3  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - optional dep
            raise RuntimeError("boto3 is required for RUM S3 export") from exc
        self._client = boto3.client("s3", region_name=region)
        self.bucket = bucket
        self._prefix = _ensure_trailing_slash(prefix)
        self._compress = compress

    async def export(self, records: Sequence[dict[str, Any]]) -> str:
        if not records:
            return ""
        key = self._build_key(records)
        body, encoding = self._serialize(records)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._put_object, key, body, encoding)
        return key

    def _serialize(self, records: Sequence[dict[str, Any]]) -> tuple[bytes, str | None]:
        lines = [
            json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
            for record in records
        ]
        if self._compress:
            buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=buffer, mode="wb") as gz:
                for line in lines:
                    gz.write(line)
                    gz.write(b"\n")
            return buffer.getvalue(), "gzip"
        return b"\n".join(lines) + b"\n", None

    def _build_key(self, records: Sequence[dict[str, Any]]) -> str:
        first_bucket = min(int(record.get("bucket_ms", 0)) for record in records)
        dt = datetime.fromtimestamp(first_bucket / 1000, tz=UTC)
        suffix = "jsonl.gz" if self._compress else "jsonl"
        return f"{self._prefix}{dt:%Y/%m/%d/%H}/rum-{first_bucket}-{uuid.uuid4().hex[:8]}.{suffix}"

    def _put_object(self, key: str, body: bytes, encoding: str | None) -> None:
        params: dict[str, Any] = {
            "Bucket": self.bucket,
            "Key": key,
            "Body": body,
            "ContentType": "application/json",
        }
        if encoding:
            params["ContentEncoding"] = encoding
        self._client.put_object(**params)


def _build_exporter(settings: Settings, logger) -> _S3RumExporter | None:
    bucket = getattr(settings, "rum_export_s3_bucket", None)
    if not bucket:
        return None
    prefix = getattr(settings, "rum_export_s3_prefix", "rum/rollup/") or "rum/rollup/"
    region = getattr(settings, "rum_export_s3_region", None)
    compress = bool(getattr(settings, "rum_export_compress", True))
    try:
        return _S3RumExporter(
            bucket=bucket,
            prefix=prefix,
            region=region,
            compress=compress,
        )
    except RuntimeError as exc:
        logger.warning("Disabling RUM S3 export: %s", exc)
        return None


class RumRollupWorker(PeriodicWorker):
    def __init__(
        self,
        *,
        context: WorkerRuntimeContext,
        interval: float,
        jitter: float,
        min_age_sec: float,
        batch_size: int,
    ) -> None:
        container = build_container(settings=context.settings)
        repo = getattr(container, "rum_repository", None)
        if not isinstance(repo, RumRedisRepository):
            raise RuntimeError(
                "telemetry.rum_rollup worker requires Redis-backed RUM storage"
            )
        self._repo = repo
        self._exporter = _build_exporter(context.settings, context.logger)
        self._min_age_ms = max(int(min_age_sec * 1000), 60_000)
        self._batch_limit = max(int(batch_size), 1)

        async def _tick() -> None:
            await self._run_once()

        config = PeriodicWorkerConfig(interval=interval, jitter=jitter)
        super().__init__(_WORKER_NAME, _tick, config=config, logger=context.logger)

    async def _run_once(self) -> None:
        ready_before_ms = _now_ms() - self._min_age_ms
        aggregates = await self._repo.fetch_pending_aggregates(
            ready_before_ms,
            limit=self._batch_limit,
        )
        if not aggregates:
            return

        records = [self._serialize(agg) for agg in aggregates if agg.count > 0]
        keys = [agg.key for agg in aggregates]
        if not records:
            await self._repo.ack_aggregates(keys)
            return

        exported: str | None = None
        if self._exporter is not None:
            try:
                exported = await self._exporter.export(records)
            except Exception as exc:  # pragma: no cover - defensive logging
                self.logger.exception("RUM rollup export failed", exc_info=exc)
                return

        await self._repo.ack_aggregates(keys)
        total_events = sum(agg.count for agg in aggregates)
        if exported and self._exporter is not None:
            self.logger.info(
                "Rolled up %s buckets (%s events) -> s3://%s/%s",
                len(records),
                total_events,
                self._exporter.bucket,
                exported,
            )
        else:
            self.logger.info(
                "Rolled up %s buckets (%s events)", len(records), total_events
            )

    async def shutdown(self) -> None:  # pragma: no cover - graceful shutdown
        redis_client = getattr(self._repo, "_redis", None)
        if redis_client is not None:
            try:
                await redis_client.close()
            except Exception:
                pass
            try:
                await redis_client.wait_closed()
            except Exception:
                pass
        await super().shutdown()

    def _serialize(self, agg: RumAggregate) -> dict[str, Any]:
        metrics: dict[str, Any] = {}
        for name, total in agg.sums.items():
            entry: dict[str, Any] = {"sum": total}
            sq = agg.sum_squares.get(name)
            if sq is not None:
                entry["sum_squares"] = sq
            if agg.count > 0:
                entry["avg"] = total / float(agg.count)
            metrics[name] = entry
        bucket_iso = datetime.fromtimestamp(agg.bucket_ms / 1000, tz=UTC).isoformat()
        return {
            "version": 1,
            "event": agg.event,
            "category": agg.category,
            "route": agg.route,
            "bucket_ms": agg.bucket_ms,
            "bucket_iso": bucket_iso,
            "count": agg.count,
            "last_ts_ms": agg.last_ts,
            "metrics": metrics,
        }


@register_worker(_WORKER_NAME)
async def build_rum_rollup_worker(context: WorkerRuntimeContext) -> RumRollupWorker:
    settings = context.settings
    interval = max(float(getattr(settings, "rum_rollup_interval_sec", 60.0)), 15.0)
    jitter = min(interval * 0.25, 30.0)
    min_age = max(float(getattr(settings, "rum_rollup_min_age_sec", 120.0)), interval)
    batch_size = max(int(getattr(settings, "rum_rollup_batch_size", 200)), 1)
    return RumRollupWorker(
        context=context,
        interval=interval,
        jitter=jitter,
        min_age_sec=min_age,
        batch_size=batch_size,
    )


__all__ = ["build_rum_rollup_worker"]
