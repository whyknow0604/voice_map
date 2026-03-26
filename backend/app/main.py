from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
# from app.api.v1.endpoints import auth, chat
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
