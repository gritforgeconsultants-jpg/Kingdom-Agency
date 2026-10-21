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
