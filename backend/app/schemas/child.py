import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.child import AgeBand, AvatarChoice


class ChildCreate(BaseModel):
    codename: str = Field(min_length=2, max_length=50)
    avatar: AvatarChoice = AvatarChoice.SHIELD
    age_band: AgeBand


class ChildUpdate(BaseModel):
    codename: str | None = Field(None, min_length=2, max_length=50)
    avatar: AvatarChoice | None = None
    age_band: AgeBand | None = None


class ChildResponse(BaseModel):
    id: uuid.UUID
    codename: str
    avatar: AvatarChoice
    age_band: AgeBand
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


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


class PrivacyNotice(BaseModel):
    version: str
    text: str
