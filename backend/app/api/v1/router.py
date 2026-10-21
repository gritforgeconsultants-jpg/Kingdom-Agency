from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.children import router as children_router
from app.api.v1.endpoints.organizations import router as org_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(org_router)
api_router.include_router(children_router)
