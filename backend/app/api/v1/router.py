"""API v1 라우터 — 모든 v1 엔드포인트를 통합한다."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
