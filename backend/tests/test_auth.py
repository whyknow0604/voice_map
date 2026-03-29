"""Google OAuth 인증 엔드포인트 테스트."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db
from app.main import app
from app.models.user import User  # noqa: F401 — Alembic autogenerate 감지
from tests.conftest import create_test_tables

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """각 테스트마다 인메모리 SQLite DB를 사용하는 세션 픽스처."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(create_test_tables)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession):
    """테스트용 FastAPI AsyncClient — DB를 테스트 세션으로 override한다."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


MOCK_GOOGLE_TOKEN_RESPONSE = {
    "access_token": "mock-google-access-token",
    "token_type": "Bearer",
}

MOCK_GOOGLE_USERINFO = {
    "sub": "google-user-id-123",
    "email": "test@example.com",
    "name": "Test User",
}


def _mock_google_responses():
    """Google OAuth API 호출을 모킹하는 컨텍스트 매니저 조합."""
    token_resp = MagicMock()
    token_resp.status_code = 200
    token_resp.json.return_value = MOCK_GOOGLE_TOKEN_RESPONSE

    userinfo_resp = MagicMock()
    userinfo_resp.status_code = 200
    userinfo_resp.json.return_value = MOCK_GOOGLE_USERINFO

    return token_resp, userinfo_resp


class TestGoogleLogin:
    async def test_new_user_gets_tokens(self, client: AsyncClient):
        """신규 유저: 유효한 코드로 요청 시 access/refresh token 발급."""
        token_resp, userinfo_resp = _mock_google_responses()

        with (
            patch(
                "app.services.auth_service.exchange_google_code",
                new=AsyncMock(return_value=MOCK_GOOGLE_TOKEN_RESPONSE),
            ),
            patch(
                "app.services.auth_service.get_google_user_info",
                new=AsyncMock(return_value={
                    "email": "test@example.com",
                    "name": "Test User",
                    "provider_id": "google-user-id-123",
                }),
            ),
        ):
            response = await client.post(
                "/api/v1/auth/google",
                json={"authorization_code": "valid-auth-code"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_existing_user_gets_tokens(self, client: AsyncClient, db_session: AsyncSession):
        """기존 유저: 동일 email로 재로그인 시 토큰 발급 및 last_login 갱신."""
        existing_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            name="Test User",
            provider="google",
            provider_id="google-user-id-123",
        )
        db_session.add(existing_user)
        await db_session.flush()

        with (
            patch(
                "app.services.auth_service.exchange_google_code",
                new=AsyncMock(return_value=MOCK_GOOGLE_TOKEN_RESPONSE),
            ),
            patch(
                "app.services.auth_service.get_google_user_info",
                new=AsyncMock(return_value={
                    "email": "test@example.com",
                    "name": "Test User",
                    "provider_id": "google-user-id-123",
                }),
            ),
        ):
            response = await client.post(
                "/api/v1/auth/google",
                json={"authorization_code": "valid-auth-code"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_invalid_code_returns_401(self, client: AsyncClient):
        """유효하지 않은 Authorization Code → 401 응답."""
        from fastapi import HTTPException

        with patch(
            "app.services.auth_service.exchange_google_code",
            new=AsyncMock(
                side_effect=HTTPException(
                    status_code=401,
                    detail={
                        "code": "GOOGLE_TOKEN_EXCHANGE_FAILED",
                        "message": "Google 인증 코드가 유효하지 않습니다.",
                    },
                )
            ),
        ):
            response = await client.post(
                "/api/v1/auth/google",
                json={"authorization_code": "invalid-code"},
            )

        assert response.status_code == 401

    async def test_missing_authorization_code_returns_422(self, client: AsyncClient):
        """authorization_code 필드 누락 → 422 Unprocessable Entity."""
        response = await client.post("/api/v1/auth/google", json={})
        assert response.status_code == 422


class TestGetMe:
    async def test_valid_access_token_returns_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """유효한 access token으로 /me 요청 → 사용자 정보 반환."""
        from app.core.security import create_access_token

        user = User(
            id=uuid.uuid4(),
            email="auth@example.com",
            name="Auth User",
            provider="google",
            provider_id="gid-auth",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_access_token(user.id)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "auth@example.com"
        assert data["name"] == "Auth User"

    async def test_no_token_returns_403(self, client: AsyncClient):
        """토큰 없이 /me 요청 → 403."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403

    async def test_invalid_token_returns_401(self, client: AsyncClient):
        """유효하지 않은 JWT로 /me 요청 → 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        assert response.status_code == 401

    async def test_refresh_token_cannot_access_me(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """refresh token으로 /me 접근 시 401 — access token 전용 엔드포인트."""
        from app.core.security import create_refresh_token

        user = User(
            id=uuid.uuid4(),
            email="refresh@example.com",
            name="Refresh User",
            provider="google",
            provider_id="gid-refresh",
        )
        db_session.add(user)
        await db_session.flush()

        refresh_token = create_refresh_token(user.id)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_TOKEN_TYPE"
