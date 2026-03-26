"""Google OAuth 2.0 인증 서비스 — 코드 교환, 유저 upsert, JWT 발급."""

from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.schemas.auth import TokenResponse

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


async def exchange_google_code(authorization_code: str) -> dict:
    """Authorization Code를 Google access token으로 교환한다.

    Raises:
        HTTPException 401: 코드가 유효하지 않거나 Google 요청 실패 시.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": authorization_code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "GOOGLE_TOKEN_EXCHANGE_FAILED",
                "message": "Google 인증 코드가 유효하지 않습니다.",
            },
        )

    return response.json()


async def get_google_user_info(access_token: str) -> dict:
    """Google access token으로 사용자 정보를 가져온다.

    Raises:
        HTTPException 401: 사용자 정보 조회 실패 시.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "GOOGLE_USERINFO_FAILED",
                "message": "Google 사용자 정보를 가져올 수 없습니다.",
            },
        )

    data = response.json()
    email: str | None = data.get("email")
    name: str | None = data.get("name")
    sub: str | None = data.get("sub")  # Google's unique user ID

    if not email or not name or not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "GOOGLE_USERINFO_INCOMPLETE",
                "message": "Google 계정에서 필수 정보를 가져올 수 없습니다.",
            },
        )

    return {"email": email, "name": name, "provider_id": sub}


async def get_or_create_user(db: AsyncSession, email: str, name: str, provider_id: str) -> User:
    """email 기준으로 기존 유저를 반환하거나 신규 유저를 생성한다."""
    result = await db.execute(select(User).where(User.email == email))
    user: User | None = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if user is None:
        user = User(
            email=email,
            name=name,
            provider="google",
            provider_id=provider_id,
            last_login=now,
        )
        db.add(user)
        await db.flush()  # id 생성을 위해 flush (commit은 get_db에서)
    else:
        user.last_login = now
        # provider_id가 없던 기존 유저라면 채움
        if user.provider_id is None:
            user.provider_id = provider_id

    return user


async def google_login(db: AsyncSession, authorization_code: str) -> TokenResponse:
    """Google OAuth 전체 플로우: 코드 교환 → 유저 upsert → JWT 발급."""
    token_data = await exchange_google_code(authorization_code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "GOOGLE_TOKEN_EXCHANGE_FAILED",
                "message": "Google 인증에 실패했습니다.",
            },
        )

    user_info = await get_google_user_info(access_token)
    user = await get_or_create_user(
        db,
        email=user_info["email"],
        name=user_info["name"],
        provider_id=user_info["provider_id"],
    )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
