from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.chat import router as ws_chat_router
from app.api.v1.endpoints.voice import router as ws_voice_router
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Voice Map — 사고 외장 하드 API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}


# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

# WebSocket 라우터 — /ws/chat, /ws/voice
app.include_router(ws_chat_router, prefix="/ws", tags=["websocket"])
app.include_router(ws_voice_router, prefix="/ws", tags=["websocket"])
