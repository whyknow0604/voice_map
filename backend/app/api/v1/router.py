"""API v1 라우터 — 모든 v1 엔드포인트를 통합한다."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, conversations, documents

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# chat/voice WebSocket 라우터는 main.py에서 /ws prefix로 별도 등록
