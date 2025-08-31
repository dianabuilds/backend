from __future__ import annotations
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from . import Base
from .adapters import JSONB, UUID


class QuestStep(Base):
    __tablename__ = "quest_steps"
    __table_args__ = (
        UniqueConstraint("version_id", "key", name="uq_quest_step_key"),
    )

    id = Column(UUID(), primary_key=True, default=uuid4)
    version_id = Column(
        UUID(),
        ForeignKey("quest_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key = Column(String, nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False, default="normal")
    content = Column(JSONB, nullable=True)
    rewards = Column(JSONB, nullable=True)

    content_refs = relationship(
        "QuestStepContentRef",
        cascade="all, delete-orphan",
        back_populates="step",
    )


class QuestTransition(Base):
    __tablename__ = "quest_transitions"

    id = Column(UUID(), primary_key=True, default=uuid4)
    version_id = Column(
        UUID(),
        ForeignKey("quest_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_step_key = Column(String, nullable=False)
    to_step_key = Column(String, nullable=False)
    label = Column(String, nullable=True)
    condition = Column(JSONB, nullable=True)


class QuestStepContentRef(Base):
    __tablename__ = "quest_step_content_refs"
    __table_args__ = (
        UniqueConstraint("step_id", "content_id", name="uq_step_content_ref"),
    )

    id = Column(UUID(), primary_key=True, default=uuid4)
    step_id = Column(
        UUID(),
        ForeignKey("quest_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_id = Column(
        UUID(),
        ForeignKey("nodes.alt_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position = Column(Integer, nullable=False, default=0)

    step = relationship("QuestStep", back_populates="content_refs")
