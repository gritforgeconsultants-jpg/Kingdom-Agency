import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.child import (
    ChildCreate,
    ChildResponse,
    ChildUpdate,
    ConsentRequest,
    ConsentResponse,
    KidModeEnter,
    KidModeExit,
    KidModeSession,
    PinSet,
    PrivacyNotice,
    XPAward,
    XPAwardResponse,
)
from app.services.child_service import (
    award_xp,
    create_child,
    create_kid_mode_token,
    delete_child_data,
    export_child_data,
    get_child,
    get_privacy_notice,
    grant_consent,
    list_children,
    update_child,
    verify_pin,
)

router = APIRouter(prefix="/children", tags=["children"])


@router.get("/privacy-notice", response_model=PrivacyNotice)
async def privacy_notice() -> dict[str, str]:
    return get_privacy_notice()


@router.post("/", response_model=ChildResponse, status_code=201)
async def create_child_profile(
    body: ChildCreate,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildResponse:
    if not user.kid_mode_pin:
        raise HTTPException(status_code=400, detail="Set a Kid Mode PIN before creating a child profile")

    child = await create_child(
        db, parent=user, codename=body.codename, age_band=body.age_band, avatar=body.avatar
    )
    await grant_consent(
        db, parent=user, child=child, ip_address=request.client.host if request.client else None
    )
    return ChildResponse.from_child(child)


@router.get("/", response_model=list[ChildResponse])
async def list_my_children(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChildResponse]:
    children = await list_children(db, parent=user)
    return [ChildResponse.from_child(c) for c in children]


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child_profile(
    child_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildResponse:
    child = await get_child(db, child_id, parent=user)
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")
    return ChildResponse.from_child(child)


@router.patch("/{child_id}", response_model=ChildResponse)
async def update_child_profile(
    child_id: uuid.UUID,
    body: ChildUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildResponse:
    child = await get_child(db, child_id, parent=user)
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")
    updated = await update_child(
        db, child, codename=body.codename, avatar=body.avatar, age_band=body.age_band
    )
    return ChildResponse.from_child(updated)


@router.get("/{child_id}/export")
async def export_data(
    child_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    child = await get_child(db, child_id, parent=user)
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")
    return await export_child_data(db, child)


@router.delete("/{child_id}", status_code=204)
async def delete_child_permanently(
    child_id: uuid.UUID,
    body: ConsentRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    if not verify_pin(user, body.pin):
        raise HTTPException(status_code=403, detail="Invalid PIN")
    child = await get_child(db, child_id, parent=user)
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")
    await delete_child_data(db, child)


# --- Kid Mode ---

@router.post("/pin", status_code=204)
async def set_kid_mode_pin(
    body: PinSet,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    user.kid_mode_pin = body.pin
    await db.flush()


@router.post("/{child_id}/xp", response_model=XPAwardResponse)
async def award_child_xp(
    child_id: uuid.UUID,
    body: XPAward,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> XPAwardResponse:
    child = await get_child(db, child_id, parent=user)
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")
    child, old_rank, new_rank = await award_xp(db, child, body.amount)
    return XPAwardResponse(
        child=ChildResponse.from_child(child),
        xp_awarded=body.amount,
        ranked_up=old_rank != new_rank,
        old_rank=old_rank.value if old_rank != new_rank else None,
        new_rank=new_rank.value if old_rank != new_rank else None,
    )


@router.post("/kid-mode/enter", response_model=KidModeSession)
async def enter_kid_mode(
    body: KidModeEnter,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> KidModeSession:
    child = await get_child(db, body.child_id, parent=user)
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")
    token = create_kid_mode_token(user, child)
    return KidModeSession(
        child=ChildResponse.from_child(child), token=token, token_type="bearer"
    )


@router.post("/kid-mode/exit", status_code=200)
async def exit_kid_mode(
    body: KidModeExit,
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    if not verify_pin(user, body.pin):
        raise HTTPException(status_code=403, detail="Invalid PIN")
    return {"status": "exited", "message": "Kid Mode deactivated"}
