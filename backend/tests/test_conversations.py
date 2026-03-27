"""Conversations CRUD 엔드포인트 테스트."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.conversation import Conversation, ConversationMode, Message, MessageRole
from app.models.user import User  # noqa: F401 — Base.metadata 감지용

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """각 테스트마다 인메모리 SQLite DB를 사용하는 세션 픽스처."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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


@pytest.fixture
async def user(db_session: AsyncSession) -> User:
    """테스트용 사용자 생성 픽스처."""
    u = User(
        id=uuid.uuid4(),
        email="user@example.com",
        name="Test User",
        provider="google",
        provider_id="google-uid-001",
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
async def other_user(db_session: AsyncSession) -> User:
    """다른 사용자 픽스처 — 권한 테스트용."""
    u = User(
        id=uuid.uuid4(),
        email="other@example.com",
        name="Other User",
        provider="google",
        provider_id="google-uid-002",
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
def auth_headers(user: User) -> dict:
    """user의 Bearer 토큰 헤더."""
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_auth_headers(other_user: User) -> dict:
    """other_user의 Bearer 토큰 헤더."""
    token = create_access_token(other_user.id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /api/v1/conversations
# ---------------------------------------------------------------------------


class TestCreateConversation:
    async def test_create_text_conversation(self, client: AsyncClient, auth_headers: dict):
        """인증된 사용자가 텍스트 대화를 생성한다."""
        response = await client.post(
            "/api/v1/conversations",
            json={"mode": "text"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["mode"] == "text"
        assert data["title"] is None
        assert "id" in data
        assert "created_at" in data

    async def test_create_voice_conversation_with_title(
        self, client: AsyncClient, auth_headers: dict
    ):
        """mode=voice, title 포함 대화 생성."""
        response = await client.post(
            "/api/v1/conversations",
            json={"mode": "voice", "title": "음성 테스트"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["mode"] == "voice"
        assert data["title"] == "음성 테스트"

    async def test_create_without_auth_returns_403(self, client: AsyncClient):
        """인증 없이 대화 생성 요청 → 403."""
        response = await client.post("/api/v1/conversations", json={"mode": "text"})
        assert response.status_code == 403

    async def test_invalid_mode_returns_422(self, client: AsyncClient, auth_headers: dict):
        """유효하지 않은 mode 값 → 422."""
        response = await client.post(
            "/api/v1/conversations",
            json={"mode": "invalid_mode"},
            headers=auth_headers,
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/conversations
# ---------------------------------------------------------------------------


class TestListConversations:
    async def test_returns_only_own_conversations(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
        other_user: User,
        auth_headers: dict,
    ):
        """자신의 대화만 목록에 포함된다."""
        own = Conversation(user_id=user.id, mode=ConversationMode.text)
        others = Conversation(user_id=other_user.id, mode=ConversationMode.text)
        db_session.add_all([own, others])
        await db_session.flush()

        response = await client.get("/api/v1/conversations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(own.id)

    async def test_empty_list_when_no_conversations(
        self, client: AsyncClient, auth_headers: dict
    ):
        """대화가 없을 때 빈 리스트 반환."""
        response = await client.get("/api/v1/conversations", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_without_auth_returns_403(self, client: AsyncClient):
        """인증 없이 목록 조회 → 403."""
        response = await client.get("/api/v1/conversations")
        assert response.status_code == 403

    async def test_list_sorted_newest_first(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
        auth_headers: dict,
    ):
        """목록은 최신순(내림차순)으로 정렬된다."""
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        # created_at 명시적 설정 — server_default가 동일 타임스탬프를 반환하는 문제 회피
        c1 = Conversation(
            user_id=user.id, mode=ConversationMode.text, title="첫 번째", created_at=now
        )
        c2 = Conversation(
            user_id=user.id,
            mode=ConversationMode.text,
            title="두 번째",
            created_at=now + timedelta(seconds=1),
        )
        db_session.add_all([c1, c2])
        await db_session.flush()

        response = await client.get("/api/v1/conversations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # 두 번째로 생성된 c2가 먼저 나와야 한다
        assert data[0]["id"] == str(c2.id)


# ---------------------------------------------------------------------------
# GET /api/v1/conversations/{id}
# ---------------------------------------------------------------------------


class TestGetConversationDetail:
    async def test_returns_conversation_with_messages(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
        auth_headers: dict,
    ):
        """대화 상세 조회 시 메시지가 포함된다."""
        conv = Conversation(user_id=user.id, mode=ConversationMode.text, title="상세 테스트")
        db_session.add(conv)
        await db_session.flush()

        msg1 = Message(
            conversation_id=conv.id,
            role=MessageRole.user,
            content="안녕하세요",
        )
        msg2 = Message(
            conversation_id=conv.id,
            role=MessageRole.ai,
            content="안녕하세요! 무엇을 도와드릴까요?",
        )
        db_session.add_all([msg1, msg2])
        await db_session.flush()

        response = await client.get(f"/api/v1/conversations/{conv.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(conv.id)
        assert data["title"] == "상세 테스트"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "ai"

    async def test_other_users_conversation_returns_404(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        other_user: User,
        auth_headers: dict,
    ):
        """다른 사용자의 대화 조회 → 404 (존재 여부 미노출)."""
        conv = Conversation(user_id=other_user.id, mode=ConversationMode.text)
        db_session.add(conv)
        await db_session.flush()

        response = await client.get(f"/api/v1/conversations/{conv.id}", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "CONVERSATION_NOT_FOUND"

    async def test_nonexistent_conversation_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """존재하지 않는 UUID → 404."""
        random_id = uuid.uuid4()
        response = await client.get(f"/api/v1/conversations/{random_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_detail_without_auth_returns_403(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
    ):
        """인증 없이 상세 조회 → 403."""
        conv = Conversation(user_id=user.id, mode=ConversationMode.text)
        db_session.add(conv)
        await db_session.flush()

        response = await client.get(f"/api/v1/conversations/{conv.id}")
        assert response.status_code == 403

    async def test_invalid_token_returns_401(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
    ):
        """유효하지 않은 JWT → 401."""
        conv = Conversation(user_id=user.id, mode=ConversationMode.text)
        db_session.add(conv)
        await db_session.flush()

        response = await client.get(
            f"/api/v1/conversations/{conv.id}",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
