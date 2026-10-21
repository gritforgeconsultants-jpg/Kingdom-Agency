import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.child import AgeBand, AgentRank, AvatarChoice, RANK_THRESHOLDS, rank_for_xp


class ChildCreate(BaseModel):
    codename: str = Field(min_length=2, max_length=50)
    avatar: AvatarChoice = AvatarChoice.SHIELD
    age_band: AgeBand


class ChildUpdate(BaseModel):
    codename: str | None = Field(None, min_length=2, max_length=50)
    avatar: AvatarChoice | None = None
    age_band: AgeBand | None = None


class RankInfo(BaseModel):
    rank: AgentRank
    designation: str
    xp: int
    xp_to_next_rank: int | None
    next_rank: AgentRank | None


class ChildResponse(BaseModel):
    id: uuid.UUID
    codename: str
    avatar: AvatarChoice
    age_band: AgeBand
    xp: int = 0
    rank_info: RankInfo | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_child(cls, child) -> "ChildResponse":
        rank, designation, xp_to_next = rank_for_xp(child.xp)
        next_rank = None
        for i, (r, _thresh, _desig) in enumerate(RANK_THRESHOLDS):
            if r == rank and i + 1 < len(RANK_THRESHOLDS):
                next_rank = RANK_THRESHOLDS[i + 1][0]
                break
        return cls(
            id=child.id,
            codename=child.codename,
            avatar=child.avatar,
            age_band=child.age_band,
            xp=child.xp,
            rank_info=RankInfo(
                rank=rank,
                designation=designation,
                xp=child.xp,
                xp_to_next_rank=xp_to_next,
                next_rank=next_rank,
            ),
            is_active=child.is_active,
            created_at=child.created_at,
        )


class KidModeEnter(BaseModel):
    child_id: uuid.UUID


class KidModeExit(BaseModel):
    pin: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")


class PinSet(BaseModel):
    pin: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")


class KidModeSession(BaseModel):
    child: ChildResponse
    token: str
    token_type: str = "bearer"


class ConsentRequest(BaseModel):
    pin: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")


class ConsentResponse(BaseModel):
    id: uuid.UUID
    child_id: uuid.UUID
    consent_version: str
    granted_at: datetime

    model_config = {"from_attributes": True}


class DataExport(BaseModel):
    child: ChildResponse
    consents: list[ConsentResponse]


class XPAward(BaseModel):
    amount: int = Field(gt=0, le=500)


class XPAwardResponse(BaseModel):
    child: ChildResponse
    xp_awarded: int
    ranked_up: bool
    old_rank: str | None = None
    new_rank: str | None = None


class PrivacyNotice(BaseModel):
    version: str
    text: str
