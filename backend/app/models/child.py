import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AgeBand(str, enum.Enum):
    YOUNG = "7-8"
    OLDER = "9-11"


class AvatarChoice(str, enum.Enum):
    SHIELD = "shield"
    SWORD = "sword"
    SCROLL = "scroll"
    DOVE = "dove"
    LION = "lion"
    EAGLE = "eagle"
    FLAME = "flame"
    STAR = "star"


class AgentRank(str, enum.Enum):
    TRAINEE = "trainee"
    SCOUT = "scout"
    OPERATIVE = "operative"
    SPECIALIST = "specialist"
    DOUBLE_0 = "double_0"
    COMMANDER = "commander"


RANK_THRESHOLDS: list[tuple[AgentRank, int, str]] = [
    (AgentRank.TRAINEE, 0, "Agent 0"),
    (AgentRank.SCOUT, 250, "Agent 1"),
    (AgentRank.OPERATIVE, 750, "Agent 7"),
    (AgentRank.SPECIALIST, 1500, "Agent 07"),
    (AgentRank.DOUBLE_0, 3000, "Agent 00"),
    (AgentRank.COMMANDER, 6000, "Agent 001"),
]


def rank_for_xp(xp: int) -> tuple[AgentRank, str, int | None]:
    """Return (rank, designation, xp_to_next_rank) for a given XP total."""
    current = RANK_THRESHOLDS[0]
    for i, entry in enumerate(RANK_THRESHOLDS):
        if xp >= entry[1]:
            current = entry
        else:
            return current[0], current[2], entry[1] - xp
    return current[0], current[2], None


class ChildProfile(Base):
    __tablename__ = "child_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    codename: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar: Mapped[AvatarChoice] = mapped_column(
        Enum(AvatarChoice), nullable=False, default=AvatarChoice.SHIELD
    )
    age_band: Mapped[AgeBand] = mapped_column(Enum(AgeBand), nullable=False)
    xp: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    parent: Mapped["User"] = relationship(back_populates="children")  # type: ignore[name-defined]  # noqa: F821

    @property
    def rank(self) -> AgentRank:
        return rank_for_xp(self.xp)[0]

    @property
    def designation(self) -> str:
        return rank_for_xp(self.xp)[1]

    @property
    def xp_to_next_rank(self) -> int | None:
        return rank_for_xp(self.xp)[2]
