Service Template (Application Layer)

Goals
- Consistent structure across domains
- Clear separation: API → Application Services → Ports → Infrastructure
- Testable services without HTTP or DB globals

Structure
- application/services: Stateless orchestration classes (business logic)
- application/ports: Protocol interfaces for dependencies (repos, cache, slug, etc.)
- infrastructure/repositories|adapters: Concrete implementations of ports
- schemas: Pydantic DTOs (input/output), handle backward compatibility via aliases/validators
- application/errors: Use app.common.errors (DomainError, NotFoundError, etc.)

Conventions
- Naming: <Subject>Service, I<Subject>Repository, I<Feature>Service
- Construction: explicit dependencies via constructor (Protocol types)
- Logging: use BaseService.logger; avoid print
- Errors: raise DomainError subclasses; map to HTTP in exception handlers; do not raise HTTPException in services
- I/O: accept DTOs, return DTOs or domain entities; do not read env directly in services
- Caching: add dedicated ports like INodeCacheInvalidation instead of calling adapters directly

Example
```
from app.common.service import BaseService
from .ports.repo_port import IThingRepository

class ThingService(BaseService):
    def __init__(self, repo: IThingRepository):
        super().__init__()
        self._repo = repo

    async def do(self, payload: ThingIn) -> ThingOut:
        item = await self._repo.create(payload)
        return ThingOut.model_validate(item)
```

Ports example
```
class IThingRepository(Protocol):
    async def create(self, payload: ThingIn) -> Thing: ...
```

Adapters example
```
class ThingRepository(IThingRepository):
    def __init__(self, db: AsyncSession): ...
```

Migration Guidance
- Introduce ports and minimal adapters beside existing code
- Update services to depend on ports; keep backwards-compat constructors
- Move compatibility field handling into Pydantic schemas
- Add unit tests for re-exports and service wiring

