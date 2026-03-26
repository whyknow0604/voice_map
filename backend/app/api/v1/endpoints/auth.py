"""인증 엔드포인트 — Google OAuth 2.0."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import GoogleAuthRequest, TokenResponse
from app.services import auth_service

router = APIRouter()


@router.post("/google", response_model=TokenResponse)
async def google_login(
    payload: GoogleAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Google Authorization Code를 받아 JWT access/refresh token을 발급한다.

    - 신규 유저: users 테이블에 생성 후 토큰 발급
    - 기존 유저: last_login 갱신 후 토큰 발급

    Raises:
        401: 유효하지 않은 Authorization Code 또는 Google API 오류.
    """
    return await auth_service.google_login(db, payload.authorization_code)
