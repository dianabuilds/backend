from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func

from . import Base
from .adapters import JSONB, UUID


class QuestStep(Base):
    __tablename__ = "quest_steps"
    __table_args__ = (
        UniqueConstraint("quest_id", "step_key", name="uq_quest_step_key"),
    )

    id = Column(UUID(), primary_key=True, default=uuid4)
    quest_id = Column(
        UUID(),
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key = Column("step_key", String, nullable=False)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False, default="normal")
    content = Column(JSONB, nullable=True)
    rewards = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    quest = relationship(
        "Quest",
        backref=backref("steps", cascade="all, delete-orphan"),
        passive_deletes=True,
    )
    outgoing_transitions = relationship(
        "QuestStepTransition",
        foreign_keys="QuestStepTransition.from_step_id",
        cascade="all, delete-orphan",
        back_populates="from_step",
    )
    incoming_transitions = relationship(
        "QuestStepTransition",
        foreign_keys="QuestStepTransition.to_step_id",
        cascade="all, delete-orphan",
        back_populates="to_step",
    )


class QuestStepTransition(Base):
    __tablename__ = "quest_step_transitions"
    __table_args__ = (
        UniqueConstraint(
            "quest_id", "from_step_id", "to_step_id", name="uq_quest_step_transition"
        ),
    )

    id = Column(UUID(), primary_key=True, default=uuid4)
    quest_id = Column(
        UUID(),
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_step_id = Column(
        UUID(), ForeignKey("quest_steps.id", ondelete="CASCADE"), nullable=False
    )
    to_step_id = Column(
        UUID(), ForeignKey("quest_steps.id", ondelete="CASCADE"), nullable=False
    )
    label = Column(String, nullable=True)
    condition = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    quest = relationship(
        "Quest",
        backref=backref("step_transitions", cascade="all, delete-orphan"),
        passive_deletes=True,
    )
    from_step = relationship(
        "QuestStep", foreign_keys=[from_step_id], back_populates="outgoing_transitions"
    )
    to_step = relationship(
        "QuestStep", foreign_keys=[to_step_id], back_populates="incoming_transitions"
    )
