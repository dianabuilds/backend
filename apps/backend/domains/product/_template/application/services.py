from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .ports import (
    CreateProductInput,
    Flags,
    IamClient,
    Outbox,
    ProductDTO,
    Repo,
    UpdateProductInput,
)


@dataclass(slots=True)
class Service:
    repo: Repo
    outbox: Outbox
    iam: IamClient
    flags: Flags

    async def get(self, product_id: str) -> ProductDTO | None:
        return await self.repo.get(product_id)

    async def list_by_owner(
        self, owner_id: str, *, limit: int = 50, offset: int = 0
    ) -> Sequence[ProductDTO]:
        return await self.repo.list_by_owner(owner_id, limit=limit, offset=offset)

    async def create(self, data: CreateProductInput) -> ProductDTO:
        # Example gating: check IAM permission or premium level.
        if not self.flags.allow_create_without_premium:
            premium = await self.iam.get_premium_level(data.owner_id)
            if premium <= 0:
                raise PermissionError("premium required to create product")

        product = ProductDTO(
            id=self._gen_id(), owner_id=data.owner_id, name=data.name, is_active=True
        )
        await self.repo.upsert(product)
        self.outbox.publish(
            "product.created.v1",
            {"id": product.id, "owner_id": product.owner_id},
            key=product.id,
        )
        return product

    async def update(self, data: UpdateProductInput) -> ProductDTO:
        current = await self.repo.get(data.id)
        if current is None:
            raise LookupError("product not found")

        new_name = current.name if data.name is None else data.name
        new_active = current.is_active if data.is_active is None else data.is_active
        updated = ProductDTO(
            id=current.id,
            owner_id=current.owner_id,
            name=new_name,
            is_active=new_active,
        )
        await self.repo.upsert(updated)
        self.outbox.publish("product.updated.v1", {"id": updated.id}, key=updated.id)
        return updated

    async def delete(self, product_id: str) -> bool:
        deleted = await self.repo.delete(product_id)
        if deleted:
            self.outbox.publish("product.deleted.v1", {"id": product_id}, key=product_id)
        return deleted

    def _gen_id(self) -> str:
        # Keep simple for template; real impl may use ULIDs.
        import uuid

        return uuid.uuid4().hex
