from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection

from domains.product.site.domain import (
    GlobalBlockMetrics,
    MetricAlert,
    MetricSeverity,
    MetricValue,
    PageMetrics,
    SiteRepositoryError,
)

from ..tables import (
    SITE_GLOBAL_BLOCK_METRICS_TABLE,
    SITE_PAGE_METRICS_TABLE,
)
from . import helpers

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class MetricsRepositoryMixin:
    if TYPE_CHECKING:

        async def _require_engine(self) -> AsyncEngine: ...

    async def get_page_metrics(
        self,
        page_id: UUID,
        *,
        period: str = "7d",
        locale: str = helpers._DEFAULT_METRIC_LOCALE,
    ) -> PageMetrics | None:
        if period not in helpers._SUPPORTED_METRIC_PERIODS:
            raise SiteRepositoryError("site_metrics_unsupported_period")
        engine = await self._require_engine()
        async with engine.connect() as conn:
            rows = await self._load_page_metric_rows(
                conn, page_id, period, locale, helpers._MAX_METRIC_ROWS
            )
        if not rows:
            return None
        current = rows[0]
        previous = rows[1] if len(rows) > 1 else None
        trend_rows = list(reversed(rows[: min(len(rows), helpers._TREND_POINTS)]))

        views_value = helpers.normalize_numeric(current.get("views"))
        prev_views = helpers.normalize_numeric(previous.get("views")) if previous else None
        unique_value = helpers.normalize_numeric(current.get("unique_users"))
        prev_unique = helpers.normalize_numeric(previous.get("unique_users")) if previous else None
        clicks_value = helpers.normalize_numeric(current.get("cta_clicks"))
        prev_clicks = helpers.normalize_numeric(previous.get("cta_clicks")) if previous else None
        conversions_value = helpers.normalize_numeric(current.get("conversions"))
        prev_conversions = (
            helpers.normalize_numeric(previous.get("conversions")) if previous else None
        )

        trend_views = helpers.extract_trend(trend_rows, "views")
        metrics: dict[str, MetricValue] = {
            "views": MetricValue(
                value=views_value,
                delta=helpers.calc_delta(views_value, prev_views),
                trend=trend_views,
            ),
            "unique_users": MetricValue(
                value=unique_value,
                delta=helpers.calc_delta(unique_value, prev_unique),
            ),
            "cta_clicks": MetricValue(
                value=clicks_value,
                delta=helpers.calc_delta(clicks_value, prev_clicks),
            ),
            "conversions": MetricValue(
                value=conversions_value,
                delta=helpers.calc_delta(conversions_value, prev_conversions),
            ),
        }

        ctr_value = helpers.compute_ratio(current.get("cta_clicks"), current.get("views"))
        ctr_prev = (
            helpers.compute_ratio(previous.get("cta_clicks"), previous.get("views"))
            if previous
            else None
        )
        metrics["ctr"] = MetricValue(
            value=ctr_value,
            delta=helpers.calc_delta(ctr_value, ctr_prev),
            unit="ratio",
        )

        avg_time = helpers.normalize_numeric(current.get("avg_time_on_page"))
        prev_avg_time = (
            helpers.normalize_numeric(previous.get("avg_time_on_page")) if previous else None
        )
        metrics["avg_time_on_page"] = MetricValue(
            value=avg_time,
            delta=helpers.calc_delta(avg_time, prev_avg_time),
            unit="seconds",
        )

        status = str(current.get("status") or "ok")
        lag_raw = helpers.normalize_numeric(current.get("source_lag_ms"))
        source_lag_ms = int(lag_raw) if lag_raw is not None else None
        alerts: list[MetricAlert] = []

        if status != "ok":
            severity = MetricSeverity.WARNING if status == "stale" else MetricSeverity.CRITICAL
            alerts.append(
                MetricAlert(
                    code=f"status_{status}",
                    message=(
                        "Аналитика недоступна"
                        if severity == MetricSeverity.CRITICAL
                        else "Данные аналитики обновляются с задержкой"
                    ),
                    severity=severity,
                )
            )

        if source_lag_ms is not None and source_lag_ms > helpers._SLA_WARNING_LAG_MS:
            alerts.append(
                MetricAlert(
                    code="data_lag",
                    message="Данные по странице устарели: превышен SLA",
                    severity=MetricSeverity.WARNING,
                )
            )

        views_delta = metrics["views"].delta
        if views_delta is not None and views_delta <= helpers._VIEWS_DROP_THRESHOLD:
            alerts.append(
                MetricAlert(
                    code="views_drop",
                    message=f"Просмотры упали на {helpers.format_delta_percentage(views_delta)}",
                    severity=MetricSeverity.WARNING,
                )
            )

        ctr_delta = metrics["ctr"].delta
        if ctr_delta is not None and ctr_delta <= helpers._CTR_DROP_THRESHOLD:
            alerts.append(
                MetricAlert(
                    code="ctr_drop",
                    message=f"CTR упал на {helpers.format_delta_percentage(ctr_delta)}",
                    severity=MetricSeverity.WARNING,
                )
            )

        previous_range_start = previous.get("range_start") if previous else None
        previous_range_end = previous.get("range_end") if previous else None

        return PageMetrics(
            page_id=page_id,
            period=period,
            range_start=current["range_start"],
            range_end=current["range_end"],
            status=status,
            source_lag_ms=source_lag_ms,
            metrics=metrics,
            alerts=alerts,
            previous_range_start=previous_range_start,
            previous_range_end=previous_range_end,
        )

    async def get_global_block_metrics(
        self,
        block_id: UUID,
        *,
        period: str = "7d",
        locale: str = helpers._DEFAULT_METRIC_LOCALE,
    ) -> GlobalBlockMetrics | None:
        if period not in helpers._SUPPORTED_METRIC_PERIODS:
            raise SiteRepositoryError("site_metrics_unsupported_period")
        engine = await self._require_engine()
        async with engine.connect() as conn:
            rows = await self._load_global_block_metric_rows(
                conn, block_id, period, locale, helpers._MAX_METRIC_ROWS
            )
        if not rows:
            return None
        current = rows[0]
        previous = rows[1] if len(rows) > 1 else None
        trend_rows = list(reversed(rows[: min(len(rows), helpers._TREND_POINTS)]))

        impressions_value = helpers.normalize_numeric(current.get("impressions"))
        prev_impressions = (
            helpers.normalize_numeric(previous.get("impressions")) if previous else None
        )
        clicks_value = helpers.normalize_numeric(current.get("clicks"))
        prev_clicks = helpers.normalize_numeric(previous.get("clicks")) if previous else None
        conversions_value = helpers.normalize_numeric(current.get("conversions"))
        prev_conversions = (
            helpers.normalize_numeric(previous.get("conversions")) if previous else None
        )
        revenue_value = helpers.normalize_numeric(current.get("revenue"))
        prev_revenue = helpers.normalize_numeric(previous.get("revenue")) if previous else None

        impressions_trend = helpers.extract_trend(trend_rows, "impressions")
        metrics: dict[str, MetricValue] = {
            "impressions": MetricValue(
                value=impressions_value,
                delta=helpers.calc_delta(impressions_value, prev_impressions),
                trend=impressions_trend,
            ),
            "clicks": MetricValue(
                value=clicks_value,
                delta=helpers.calc_delta(clicks_value, prev_clicks),
            ),
            "conversions": MetricValue(
                value=conversions_value,
                delta=helpers.calc_delta(conversions_value, prev_conversions),
            ),
            "revenue": MetricValue(
                value=revenue_value,
                delta=helpers.calc_delta(revenue_value, prev_revenue),
                unit="currency",
            ),
        }

        ctr_value = helpers.compute_ratio(current.get("clicks"), current.get("impressions"))
        ctr_prev = (
            helpers.compute_ratio(previous.get("clicks"), previous.get("impressions"))
            if previous
            else None
        )
        ctr_trend = (
            tuple(
                value
                for value in (
                    helpers.compute_ratio(row.get("clicks"), row.get("impressions"))
                    for row in trend_rows
                )
                if value is not None
            )
            or None
        )
        metrics["ctr"] = MetricValue(
            value=ctr_value,
            delta=helpers.calc_delta(ctr_value, ctr_prev),
            unit="ratio",
            trend=ctr_trend,
        )

        status = str(current.get("status") or "ok")
        lag_raw = helpers.normalize_numeric(current.get("source_lag_ms"))
        source_lag_ms = int(lag_raw) if lag_raw is not None else None
        alerts: list[MetricAlert] = []

        if status != "ok":
            severity = MetricSeverity.WARNING if status == "stale" else MetricSeverity.CRITICAL
            alerts.append(
                MetricAlert(
                    code=f"status_{status}",
                    message=(
                        "Статистика по блоку недоступна"
                        if severity == MetricSeverity.CRITICAL
                        else "Статистика по блоку обновляется с задержкой"
                    ),
                    severity=severity,
                )
            )

        if source_lag_ms is not None and source_lag_ms > helpers._SLA_WARNING_LAG_MS:
            alerts.append(
                MetricAlert(
                    code="data_lag",
                    message="Данные по блоку устарели: превышен SLA",
                    severity=MetricSeverity.WARNING,
                )
            )

        impressions_delta = metrics["impressions"].delta
        if impressions_delta is not None and impressions_delta <= helpers._VIEWS_DROP_THRESHOLD:
            alerts.append(
                MetricAlert(
                    code="impressions_drop",
                    message=f"Показы блока упали на {helpers.format_delta_percentage(impressions_delta)}",
                    severity=MetricSeverity.WARNING,
                )
            )

        ctr_delta = metrics["ctr"].delta
        if ctr_delta is not None and ctr_delta <= helpers._CTR_DROP_THRESHOLD:
            alerts.append(
                MetricAlert(
                    code="block_ctr_drop",
                    message=f"CTR блока упал на {helpers.format_delta_percentage(ctr_delta)}",
                    severity=MetricSeverity.WARNING,
                )
            )

        previous_range_start = previous.get("range_start") if previous else None
        previous_range_end = previous.get("range_end") if previous else None

        top_pages = helpers.parse_top_pages(current.get("top_pages"))

        return GlobalBlockMetrics(
            block_id=block_id,
            period=period,
            range_start=current["range_start"],
            range_end=current["range_end"],
            status=status,
            source_lag_ms=source_lag_ms,
            metrics=metrics,
            top_pages=top_pages,
            alerts=alerts,
            previous_range_start=previous_range_start,
            previous_range_end=previous_range_end,
        )

    async def _load_page_metric_rows(
        self,
        conn: AsyncConnection,
        page_id: UUID,
        period: str,
        locale: str | None,
        limit: int,
    ) -> list[Mapping[str, Any]]:
        stmt = (
            sa.select(SITE_PAGE_METRICS_TABLE)
            .where(SITE_PAGE_METRICS_TABLE.c.page_id == page_id)
            .where(SITE_PAGE_METRICS_TABLE.c.period == period)
        )
        if locale is not None:
            stmt = stmt.where(SITE_PAGE_METRICS_TABLE.c.locale == locale)
        stmt = stmt.order_by(SITE_PAGE_METRICS_TABLE.c.range_end.desc()).limit(limit)
        rows = (await conn.execute(stmt)).mappings().all()
        if not rows and locale is not None:
            stmt = (
                sa.select(SITE_PAGE_METRICS_TABLE)
                .where(SITE_PAGE_METRICS_TABLE.c.page_id == page_id)
                .where(SITE_PAGE_METRICS_TABLE.c.period == period)
                .order_by(SITE_PAGE_METRICS_TABLE.c.range_end.desc())
                .limit(limit)
            )
            rows = (await conn.execute(stmt)).mappings().all()
        return rows

    async def _load_global_block_metric_rows(
        self,
        conn: AsyncConnection,
        block_id: UUID,
        period: str,
        locale: str | None,
        limit: int,
    ) -> list[Mapping[str, Any]]:
        stmt = (
            sa.select(SITE_GLOBAL_BLOCK_METRICS_TABLE)
            .where(SITE_GLOBAL_BLOCK_METRICS_TABLE.c.block_id == block_id)
            .where(SITE_GLOBAL_BLOCK_METRICS_TABLE.c.period == period)
        )
        if locale is not None:
            stmt = stmt.where(SITE_GLOBAL_BLOCK_METRICS_TABLE.c.locale == locale)
        stmt = stmt.order_by(SITE_GLOBAL_BLOCK_METRICS_TABLE.c.range_end.desc()).limit(limit)
        rows = (await conn.execute(stmt)).mappings().all()
        if not rows and locale is not None:
            stmt = (
                sa.select(SITE_GLOBAL_BLOCK_METRICS_TABLE)
                .where(SITE_GLOBAL_BLOCK_METRICS_TABLE.c.block_id == block_id)
                .where(SITE_GLOBAL_BLOCK_METRICS_TABLE.c.period == period)
                .order_by(SITE_GLOBAL_BLOCK_METRICS_TABLE.c.range_end.desc())
                .limit(limit)
            )
            rows = (await conn.execute(stmt)).mappings().all()
        return rows


__all__ = ["MetricsRepositoryMixin"]
