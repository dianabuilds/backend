from __future__ import annotations

from app.domains.navigation.application.navigation_cache_service import NavigationCacheService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter

# Глобальный singleton, используемый в коде/тестах
navcache = NavigationCacheService(CoreCacheAdapter())

__all__ = ["navcache"]
