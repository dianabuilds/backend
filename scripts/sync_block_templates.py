"""Sync block templates from canonical catalog into the database.

Usage:
    python scripts/sync_block_templates.py [--dsn <url>] [--dry-run]

If --dsn is not provided, the script will try APP_DATABASE_URL/DATABASE_URL from `.env`.
"""

from __future__ import annotations

import argparse
import json
import os
import uuid
from dataclasses import dataclass, asdict
from typing import Any, cast

from sqlalchemy import MetaData, Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


TEMPLATE_NAMESPACE = uuid.UUID("7d2c6f5c-5db3-4d0c-95f0-0af1fef82810")
DEFAULT_ACTOR = "seed:block-library"


OWNER_ALIAS_MAP: dict[str, str] = {
    "Маркетинг": "team_marketing",
    "Продукт": "team_product",
    "Продакт": "team_product",
    "Продакт Quests": "team_quests_product",
    "Продакт Nodes": "team_nodes_product",
    "DevRel": "team_devrel",
    "Контент": "team_content",
    "Редакция контента": "team_content",
    "Саппорт": "team_support",
    "Аналитика": "team_analytics",
    "Data/ML": "team_data_ml",
    "team_public_site": "team_public_site",
}


def _normalize_owner(owner: str) -> str:
    return OWNER_ALIAS_MAP.get(owner, owner)


@dataclass(slots=True)
class TemplateRecord:
    key: str
    title: str
    section: str
    status: str = "available"
    default_locale: str = "ru"
    available_locales: list[str] | None = None
    default_data: dict[str, Any] | None = None
    default_meta: dict[str, Any] | None = None
    description: str | None = None
    block_type: str | None = None
    category: str | None = None
    sources: list[str] | None = None
    surfaces: list[str] | None = None
    owners: list[str] | None = None
    catalog_locales: list[str] | None = None
    documentation_url: str | None = None
    keywords: list[str] | None = None
    preview_kind: str | None = None
    status_note: str | None = None
    requires_publisher: bool = False
    allow_shared_scope: bool = False
    allow_page_scope: bool = True
    shared_note: str | None = None
    key_prefix: str | None = None

    def __post_init__(self) -> None:
        if self.available_locales is None:
            computed_available = [self.default_locale]
        else:
            computed_available = list(self.available_locales)
        self.available_locales = computed_available
        if self.catalog_locales is None:
            self.catalog_locales = list(computed_available)
        if self.default_data is None:
            self.default_data = {}
        if self.default_meta is None:
            self.default_meta = {}

    @property
    def id(self) -> uuid.UUID:
        return uuid.uuid5(TEMPLATE_NAMESPACE, self.key)

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["id"] = str(self.id)
        available_locales = cast(list[str], self.available_locales)
        payload["available_locales"] = list(available_locales)
        catalog_locales = cast(list[str], self.catalog_locales)
        payload["catalog_locales"] = list(catalog_locales)
        default_data = cast(dict[str, Any], self.default_data)
        payload["default_data"] = default_data
        default_meta = cast(dict[str, Any], self.default_meta)
        payload["default_meta"] = default_meta
        payload["owners"] = list(payload["owners"]) if payload.get("owners") else None
        payload["description"] = self.description
        return payload


def build_catalog() -> list[TemplateRecord]:
    """Canonical catalog derived from legacy `blockLibraryData.ts`."""

    doc_url = "/docs/site-editor-block-library"

    entries: list[dict[str, Any]] = [
        {
            "key": "hero",
            "title": "Hero",
            "description": "Большой первый экран с заголовком и CTA.",
            "section": "hero",
            "status": "available",
            "block_type": "hero",
            "category": "hero",
            "sources": ["manual"],
            "surfaces": ["home", "landing", "promo"],
            "owners": ["Маркетинг"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#hero",
            "keywords": ["первый экран", "cta", "hero"],
            "preview_kind": "hero",
        },
        {
            "key": "dev_blog_list",
            "title": "Dev Blog",
            "description": "Список последних постов дев-блога.",
            "section": "content",
            "status": "available",
            "block_type": "dev_blog_list",
            "category": "content",
            "sources": ["auto"],
            "surfaces": ["home", "dev-blog"],
            "owners": ["DevRel", "Контент"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#dev_blog_list",
            "keywords": ["контент", "dev blog"],
            "preview_kind": "list",
        },
        {
            "key": "quests_carousel",
            "title": "Квесты",
            "description": "Карусель избранных квестов.",
            "section": "content",
            "status": "available",
            "block_type": "quests_carousel",
            "category": "catalog",
            "sources": ["auto"],
            "surfaces": ["home", "landing", "promo"],
            "owners": ["Продакт Quests"],
            "locales": ["ru"],
            "documentation_url": f"{doc_url}#quests_carousel",
            "keywords": ["квесты", "каталог"],
            "preview_kind": "carousel",
        },
        {
            "key": "nodes_carousel",
            "title": "Ноды",
            "description": "Подборка рекомендованных нод.",
            "section": "content",
            "status": "available",
            "block_type": "nodes_carousel",
            "category": "catalog",
            "sources": ["auto"],
            "surfaces": ["home", "landing", "promo", "collection"],
            "owners": ["Продакт Nodes"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#nodes_carousel",
            "keywords": ["ноды", "каталог"],
            "preview_kind": "carousel",
        },
        {
            "key": "popular_carousel",
            "title": "Популярное",
            "description": "Самые просматриваемые квесты и ноды.",
            "section": "content",
            "status": "available",
            "block_type": "popular_carousel",
            "category": "catalog",
            "sources": ["auto"],
            "surfaces": ["home", "landing"],
            "owners": ["Маркетинг"],
            "locales": ["ru"],
            "documentation_url": f"{doc_url}#popular_carousel",
            "keywords": ["просмотры", "каталог"],
            "preview_kind": "carousel",
        },
        {
            "key": "editorial_picks",
            "title": "Выбор редакции",
            "description": "Ручной список материалов от редакции.",
            "section": "content",
            "status": "available",
            "block_type": "editorial_picks",
            "category": "content",
            "sources": ["manual"],
            "surfaces": ["home", "landing", "promo"],
            "owners": ["Редакция контента"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#editorial_picks",
            "keywords": ["подборка", "контент"],
            "preview_kind": "list",
        },
        {
            "key": "recommendations",
            "title": "Персональные рекомендации",
            "description": "Автоматические рекомендации по интересам.",
            "section": "content",
            "status": "available",
            "block_type": "recommendations",
            "category": "personalization",
            "sources": ["auto"],
            "surfaces": ["home", "landing", "promo"],
            "owners": ["Data/ML"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#recommendations",
            "keywords": ["персонализация", "рекомендации"],
            "preview_kind": "personalized",
            "status_note": "Требует адаптера рекомендаций",
        },
        {
            "key": "custom_carousel",
            "title": "Кастомная карусель",
            "description": "Ручной список карточек с произвольным контентом.",
            "section": "promo",
            "status": "available",
            "block_type": "custom_carousel",
            "category": "promo",
            "sources": ["manual"],
            "surfaces": ["landing", "promo"],
            "owners": ["Маркетинг"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#custom_carousel",
            "keywords": ["промо", "ручной"],
            "preview_kind": "custom",
        },
        {
            "key": "header",
            "title": "Хедер",
            "description": "Единая навигация по публичному сайту с локализованными ссылками и CTA.",
            "section": "header",
            "status": "available",
            "block_type": "header",
            "category": "shared",
            "sources": ["manual"],
            "surfaces": ["shared"],
            "owners": ["team_public_site"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#header",
            "keywords": ["навигация", "header"],
            "preview_kind": "header",
            "requires_publisher": True,
            "allow_shared_scope": True,
            "allow_page_scope": False,
            "key_prefix": "header",
            "default_data": {
                "branding": {
                    "title": "Caves World",
                    "subtitle": "Играй и создавай",
                    "href": "/",
                    "logo": {
                        "light": "/assets/branding/logo-light.svg",
                        "dark": "/assets/branding/logo-dark.svg",
                        "alt": "Caves World",
                    },
                },
                "navigation": {
                    "primary": [
                        {"label": "Главная", "href": "/"},
                        {"label": "Квесты", "href": "/quests"},
                        {"label": "Dev Blog", "href": "/dev-blog"},
                        {"label": "Тарифы", "href": "/pricing"},
                    ],
                    "utility": [
                        {"label": "Помощь", "href": "/help"},
                        {"label": "Блог", "href": "/dev-blog"},
                    ],
                    "cta": {
                        "label": "Присоединиться",
                        "href": "/auth/signup",
                        "style": "primary",
                    },
                    "mobile": {
                        "menu": [
                            {"label": "Главная", "href": "/"},
                            {"label": "Квесты", "href": "/quests"},
                            {"label": "Dev Blog", "href": "/dev-blog"},
                            {"label": "Тарифы", "href": "/pricing"},
                            {"label": "Помощь", "href": "/help"},
                        ],
                        "cta": {
                            "label": "Присоединиться",
                            "href": "/auth/signup",
                            "style": "primary",
                        },
                    },
                },
                "layout": {"variant": "default", "sticky": True},
                "features": {"language_switcher": True},
                "localization": {"fallbackLocale": "ru", "available": ["ru", "en"]},
            },
            "default_meta": {
                "owners": ["team_public_site"],
                "documentation_url": f"{doc_url}#header",
            },
            "shared_note": "Проверьте локализацию ссылок и договоритесь с владельцем перед публикацией.",
        },
        {
            "key": "footer",
            "title": "Футер",
            "description": "Контакты, юридическая информация и ссылки на разделы для всех страниц.",
            "section": "footer",
            "status": "design",
            "block_type": "footer",
            "category": "shared",
            "sources": ["manual"],
            "surfaces": ["shared"],
            "owners": ["Маркетинг"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#footer",
            "keywords": ["footer"],
            "preview_kind": "footer",
            "status_note": "Дизайн и контент в работе",
            "requires_publisher": True,
            "allow_shared_scope": True,
            "allow_page_scope": False,
        },
        {
            "key": "faq_list",
            "title": "FAQ / Справка",
            "description": "Список вопросов и ответов для справки и лендингов поддержки.",
            "section": "content",
            "status": "research",
            "block_type": "faq_list",
            "category": "content",
            "sources": ["manual", "auto"],
            "surfaces": ["help", "landing"],
            "owners": ["Саппорт", "Контент"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#faq_list",
            "keywords": ["faq", "справка"],
            "preview_kind": "faq",
            "status_note": "Уточняем структуру данных",
        },
        {
            "key": "promo_banner",
            "title": "Промо-баннер",
            "description": "Одноэкранный баннер с медиа, описанием и расписанием показа.",
            "section": "promo",
            "status": "research",
            "block_type": "promo_banner",
            "category": "promo",
            "sources": ["manual"],
            "surfaces": ["landing", "promo"],
            "owners": ["Маркетинг"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#promo_banner",
            "keywords": ["баннер", "промо"],
            "preview_kind": "promo",
            "status_note": "Требуется проработка расписания и таргетинга",
        },
        {
            "key": "related_posts",
            "title": "Связанные материалы",
            "description": "Блок «Читайте также» для статей и блога с авто и ручной подборкой.",
            "section": "content",
            "status": "research",
            "block_type": "related_posts",
            "category": "content",
            "sources": ["auto", "manual"],
            "surfaces": ["article", "dev-blog"],
            "owners": ["DevRel", "Контент"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#related_posts",
            "keywords": ["related", "контент"],
            "preview_kind": "list",
            "status_note": "Зависит от API нод и тегов",
        },
        {
            "key": "metrics_highlight",
            "title": "Метрические карточки",
            "description": "Плашка KPI или статистики для главной и кампанийных лендингов.",
            "section": "metrics",
            "status": "research",
            "block_type": "metrics_highlight",
            "category": "metrics",
            "sources": ["manual", "auto"],
            "surfaces": ["home", "landing", "promo"],
            "owners": ["Продакт", "Аналитика"],
            "locales": ["ru", "en"],
            "documentation_url": f"{doc_url}#metrics_highlight",
            "keywords": ["метрики", "статистика"],
            "preview_kind": "metrics",
            "status_note": "Определяем источники данных",
        },
    ]

    records: list[TemplateRecord] = []
    for entry in entries:
        record = TemplateRecord(
            key=entry["key"],
            title=entry["title"],
            section=entry["section"],
            status=entry.get("status", "available"),
            description=entry.get("description"),
            block_type=entry.get("block_type"),
            category=entry.get("category"),
            sources=entry.get("sources"),
            surfaces=entry.get("surfaces"),
            owners=entry.get("owners"),
            default_locale=entry.get("default_locale", "ru"),
            available_locales=entry.get("locales"),
            catalog_locales=entry.get("catalog_locales"),
            default_data=entry.get("default_data"),
            default_meta=entry.get("default_meta"),
            documentation_url=entry.get("documentation_url"),
            keywords=entry.get("keywords"),
            preview_kind=entry.get("preview_kind"),
            status_note=entry.get("status_note"),
            requires_publisher=entry.get("requires_publisher", False),
            allow_shared_scope=entry.get("allow_shared_scope", False),
            allow_page_scope=entry.get("allow_page_scope", True),
            shared_note=entry.get("shared_note"),
            key_prefix=entry.get("key_prefix"),
        )
        records.append(record)

    for record in records:
        default_meta = cast(dict[str, Any], record.default_meta)
        if record.documentation_url:
            default_meta.setdefault("documentation_url", record.documentation_url)
        if record.owners:
            normalized = [_normalize_owner(owner) for owner in record.owners]
            record.owners = normalized
            default_meta.pop("owner", None)
            default_meta.setdefault("owners", normalized)
        owners_meta = default_meta.get("owners")
        if isinstance(owners_meta, list):
            default_meta["owners"] = [_normalize_owner(owner) for owner in owners_meta]

    return records


def sync_templates(
    engine: Engine, templates: list[TemplateRecord], dry_run: bool = False
) -> None:
    metadata = MetaData()
    table = Table("site_block_templates", metadata, autoload_with=engine)

    with engine.begin() as conn:
        for template in templates:
            payload = template.to_payload()
            payload["created_by"] = DEFAULT_ACTOR
            payload["updated_by"] = DEFAULT_ACTOR

            stmt = pg_insert(table).values(**payload)
            update_columns = {
                "title": stmt.excluded.title,
                "section": stmt.excluded.section,
                "status": stmt.excluded.status,
                "description": stmt.excluded.description,
                "default_locale": stmt.excluded.default_locale,
                "available_locales": stmt.excluded.available_locales,
                "default_data": stmt.excluded.default_data,
                "default_meta": stmt.excluded.default_meta,
                "block_type": stmt.excluded.block_type,
                "category": stmt.excluded.category,
                "sources": stmt.excluded.sources,
                "surfaces": stmt.excluded.surfaces,
                "owners": stmt.excluded.owners,
                "catalog_locales": stmt.excluded.catalog_locales,
                "documentation_url": stmt.excluded.documentation_url,
                "keywords": stmt.excluded.keywords,
                "preview_kind": stmt.excluded.preview_kind,
                "status_note": stmt.excluded.status_note,
                "requires_publisher": stmt.excluded.requires_publisher,
                "allow_shared_scope": stmt.excluded.allow_shared_scope,
                "allow_page_scope": stmt.excluded.allow_page_scope,
                "shared_note": stmt.excluded.shared_note,
                "key_prefix": stmt.excluded.key_prefix,
                "updated_at": text("timezone('utc', now())"),
                "updated_by": text(":actor"),
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=["key"], set_=update_columns
            )

            if dry_run:
                print(
                    f"[dry-run] would upsert template {template.key} -> {json.dumps(payload, ensure_ascii=False)}"
                )
            else:
                conn.execute(stmt, {"actor": DEFAULT_ACTOR})
    if dry_run:
        print("Dry-run completed – no changes committed.")
    else:
        print(f"Synced {len(templates)} templates.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync site block templates into the database."
    )
    parser.add_argument(
        "--dsn",
        help="SQLAlchemy connection string. Defaults to APP_DATABASE_URL/DATABASE_URL from .env.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print statements instead of applying changes.",
    )
    return parser.parse_args()


def resolve_dsn(args: argparse.Namespace) -> str:
    if args.dsn:
        return args.dsn
    if load_dotenv:
        load_dotenv(".env")
    dsn = os.getenv("APP_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not dsn:
        raise SystemExit(
            "Database DSN not provided. Use --dsn or define APP_DATABASE_URL/DATABASE_URL in environment/.env."
        )
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return dsn


def main() -> None:
    args = parse_args()
    dsn = resolve_dsn(args)
    engine = create_engine(dsn)
    templates = build_catalog()

    try:
        sync_templates(engine, templates, dry_run=args.dry_run)
    except SQLAlchemyError as exc:  # pragma: no cover - CLI handling
        raise SystemExit(f"Failed to sync templates: {exc}") from exc


if __name__ == "__main__":  # pragma: no cover
    main()
