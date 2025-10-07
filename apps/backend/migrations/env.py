"""Alembic environment for the backend project.

Goals:
- Use DB URL from .env (APP_DATABASE_URL / DATABASE_URL) or -x dburl=...
- Import ONLY ORM model modules from platform/product domains (no app routes)
- Support explicit module/package list via ALEMBIC_MODELS or -x models=...
- Work with sync engine (convert asyncpg; map ssl=true → sslmode=require)
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
from collections.abc import Sequence
from logging.config import fileConfig
from pathlib import Path
from types import ModuleType
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from alembic import context
from sqlalchemy import MetaData, engine_from_config, pool

# Alembic config and logging
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")
DEBUG_IMPORTS = os.getenv("ALEMBIC_DEBUG_IMPORTS") in {"1", "true", "True"}


def _add_repo_root_to_path() -> None:
    here = Path(__file__).resolve()
    cur = here
    for _ in range(6):
        if (cur.parent / "apps").exists():
            repo_root = cur.parent
            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))
            return
        cur = cur.parent


_add_repo_root_to_path()


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
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


def _load_env_file() -> None:
    here = Path(__file__).resolve()
    cur = here
    for _ in range(6):
        env_path = cur.parent / ".env"
        if env_path.exists():
            _load_dotenv(env_path)
            break
        cur = cur.parent


_load_env_file()


def _choose_env_url() -> str | None:
    for key in ("DATABASE_URL", "APP_DATABASE_URL", "DB_URL"):
        val = os.getenv(key)
        if val:
            return val
    return None


def _normalize_url_for_alembic(url: str | None) -> str | None:
    if not url:
        return url
    if url.startswith("postgresql+asyncpg://"):
        driver = "postgresql"
        try:

            driver = "postgresql+psycopg"
        except Exception:
            try:

                driver = "postgresql+psycopg2"
            except Exception:
                driver = "postgresql"
        url = driver + url[len("postgresql+asyncpg") :]

    try:
        parts = urlsplit(url)
        if parts.scheme.startswith("postgresql"):
            q = dict(parse_qsl(parts.query, keep_blank_values=True))
            if q.get("ssl") == "true" and "sslmode" not in q:
                q.pop("ssl", None)
                q["sslmode"] = "require"
                url = urlunsplit(
                    (
                        parts.scheme,
                        parts.netloc,
                        parts.path,
                        urlencode(q),
                        parts.fragment,
                    )
                )
    except Exception:
        pass
    return url


def get_database_url() -> str:
    xargs = context.get_x_argument(as_dictionary=True)
    dburl = xargs.get("dburl") if isinstance(xargs, dict) else None
    env_url = dburl or _choose_env_url() or config.get_main_option("sqlalchemy.url")
    url = _normalize_url_for_alembic(env_url)
    if not url:
        raise RuntimeError("Database URL is not configured for Alembic")
    if not url:
        raise RuntimeError(
            "Database URL not configured. Set APP_DATABASE_URL/DATABASE_URL in .env or use -x dburl="
        )
    return url


def _explicit_models_from_args() -> list[str]:
    xargs = context.get_x_argument(as_dictionary=True)
    raw = None
    if isinstance(xargs, dict):
        raw = xargs.get("models") or xargs.get("model")
    raw = raw or os.getenv("ALEMBIC_MODELS")
    if not raw:
        return []
    parts = [
        p.strip()
        for p in raw.replace(";", ",").replace(" ", ",").split(",")
        if p.strip()
    ]
    return parts


def _import_model_files_under_package(pkg: ModuleType) -> None:
    # Import only typical ORM modules to avoid app-wide side effects
    try:
        # Packages can have multiple paths; take all
        pkg_paths = [Path(p) for p in getattr(pkg, "__path__", [])]
    except Exception:
        pkg_paths = []
    patterns = ("**/models.py", "**/tables.py", "**/entities.py", "**/orm.py")
    for root_dir in pkg_paths:
        for pattern in patterns:
            for fp in root_dir.glob(pattern):
                # Skip files in tests or alembic directories
                parts = fp.parts
                if any(p in {"tests", "__pycache__", "migrations"} for p in parts):
                    continue
                rel = fp.relative_to(root_dir).with_suffix("")
                mod_name = pkg.__name__ + "." + ".".join(rel.parts)
                try:
                    importlib.import_module(mod_name)
                    if DEBUG_IMPORTS:
                        logger.info("Imported model module: %s", mod_name)
                except Exception as e:
                    if DEBUG_IMPORTS:
                        logger.warning("Skip model module %s: %s", mod_name, e)


def _import_all_domain_modules() -> None:
    # 1) Explicit modules/packages via env/args
    explicit = _explicit_models_from_args()
    if explicit:
        for name in explicit:
            try:
                mod = importlib.import_module(name)
                if DEBUG_IMPORTS:
                    logger.info("Imported explicit: %s", name)
                if hasattr(mod, "__path__"):
                    _import_model_files_under_package(mod)
            except Exception as e:
                if DEBUG_IMPORTS:
                    logger.warning("Skip explicit %s: %s", name, e)
        return

    # 2) Default: import models from platform and product packages only
    for root in ("apps.backend.domains.platform", "apps.backend.domains.product"):
        try:
            pkg = importlib.import_module(root)
            if DEBUG_IMPORTS:
                logger.info("Root imported: %s", root)
            if hasattr(pkg, "__path__"):
                _import_model_files_under_package(pkg)
        except Exception as e:
            if DEBUG_IMPORTS:
                logger.warning("Skip root %s: %s", root, e)


def _collect_all_metadatas() -> MetaData | Sequence[MetaData] | None:
    metadatas: list[MetaData] = []
    seen = set()
    for mod_name, mod in list(sys.modules.items()):
        if not isinstance(mod_name, str):
            continue
        if not mod_name.startswith(
            "apps.backend.domains.platform"
        ) and not mod_name.startswith("apps.backend.domains.product"):
            continue
        for attr in dir(mod):
            try:
                obj = getattr(mod, attr)
            except Exception:
                continue
            md = getattr(obj, "metadata", None)
            if isinstance(md, MetaData):
                if id(md) not in seen:
                    seen.add(id(md))
                    metadatas.append(md)
    if metadatas:
        if DEBUG_IMPORTS:
            logger.info("Collected %d MetaData objects", len(metadatas))
        return metadatas
    try:
        from sqlmodel import SQLModel  # type: ignore

        if DEBUG_IMPORTS:
            logger.info("Falling back to SQLModel.metadata")
        return SQLModel.metadata  # type: ignore[attr-defined]
    except Exception:
        return None


# Import models and determine target metadata
_import_all_domain_modules()
_tm = _collect_all_metadatas()
if not _tm:
    logger.warning("Alembic: no MetaData discovered; autogenerate may be empty.")
    target_metadata: MetaData | Sequence[MetaData] = MetaData()
else:
    target_metadata = _tm


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    url = get_database_url()
    if url:
        configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
