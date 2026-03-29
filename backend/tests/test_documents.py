"""Documents CRUD 엔드포인트 테스트."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models.document import Document
from app.models.user import User  # noqa: F401 — Base.metadata 감지용
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
# POST /api/v1/documents
# ---------------------------------------------------------------------------


class TestCreateDocument:
    async def test_create_document_success(self, client: AsyncClient, auth_headers: dict):
        """인증된 사용자가 문서를 생성한다 (keywords 없이 — SQLite ARRAY 미지원)."""
        response = await client.post(
            "/api/v1/documents",
            json={"title": "테스트 문서", "content": "내용입니다."},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "테스트 문서"
        assert data["content"] == "내용입니다."
        assert data["conversation_id"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_document_minimal(self, client: AsyncClient, auth_headers: dict):
        """keywords, conversation_id 없이 최소 필드로 생성한다."""
        response = await client.post(
            "/api/v1/documents",
            json={"title": "최소 문서", "content": "내용"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "최소 문서"
        assert data["keywords"] is None
        assert data["conversation_id"] is None

    async def test_create_document_without_auth_returns_403(self, client: AsyncClient):
        """인증 없이 문서 생성 → 403."""
        response = await client.post(
            "/api/v1/documents",
            json={"title": "문서", "content": "내용"},
        )
        assert response.status_code == 403

    async def test_create_document_missing_fields_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ):
        """필수 필드 누락 → 422."""
        response = await client.post(
            "/api/v1/documents",
            json={"title": "제목만"},
            headers=auth_headers,
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/documents
# ---------------------------------------------------------------------------


class TestListDocuments:
    async def test_returns_only_own_documents(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
        other_user: User,
        auth_headers: dict,
    ):
        """자신의 문서만 목록에 포함된다."""
        own = Document(user_id=user.id, title="내 문서", content="내용")
        others = Document(user_id=other_user.id, title="남의 문서", content="내용")
        db_session.add_all([own, others])
        await db_session.flush()

        response = await client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(own.id)

    async def test_empty_list_when_no_documents(
        self, client: AsyncClient, auth_headers: dict
    ):
        """문서가 없을 때 빈 리스트 반환."""
        response = await client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_without_auth_returns_403(self, client: AsyncClient):
        """인증 없이 목록 조회 → 403."""
        response = await client.get("/api/v1/documents")
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
        d1 = Document(
            user_id=user.id, title="첫 번째", content="내용", created_at=now
        )
        d2 = Document(
            user_id=user.id,
            title="두 번째",
            content="내용",
            created_at=now + timedelta(seconds=1),
        )
        db_session.add_all([d1, d2])
        await db_session.flush()

        response = await client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # 두 번째로 생성된 d2가 먼저 나와야 한다
        assert data[0]["id"] == str(d2.id)

    async def test_list_response_excludes_content(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
        auth_headers: dict,
    ):
        """목록 응답에는 content 필드가 없다 (DocumentListResponse)."""
        db_session.add(Document(user_id=user.id, title="문서", content="내용"))
        await db_session.flush()

        response = await client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "content" not in data[0]


# ---------------------------------------------------------------------------
# GET /api/v1/documents/{id}
# ---------------------------------------------------------------------------


class TestGetDocument:
    async def test_returns_document_with_content(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
        auth_headers: dict,
    ):
        """문서 상세 조회 시 content가 포함된다 (keywords 없이 — SQLite ARRAY 미지원)."""
        doc = Document(
            user_id=user.id,
            title="상세 문서",
            content="상세 내용입니다.",
        )
        db_session.add(doc)
        await db_session.flush()

        response = await client.get(f"/api/v1/documents/{doc.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(doc.id)
        assert data["title"] == "상세 문서"
        assert data["content"] == "상세 내용입니다."

    async def test_other_users_document_returns_404(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        other_user: User,
        auth_headers: dict,
    ):
        """다른 사용자의 문서 조회 → 404 (존재 여부 미노출)."""
        doc = Document(user_id=other_user.id, title="남의 문서", content="내용")
        db_session.add(doc)
        await db_session.flush()

        response = await client.get(f"/api/v1/documents/{doc.id}", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "DOCUMENT_NOT_FOUND"

    async def test_nonexistent_document_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """존재하지 않는 UUID → 404."""
        random_id = uuid.uuid4()
        response = await client.get(f"/api/v1/documents/{random_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_detail_without_auth_returns_403(self, client: AsyncClient):
        """인증 없이 상세 조회 → 403."""
        random_id = uuid.uuid4()
        response = await client.get(f"/api/v1/documents/{random_id}")
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/v1/documents/{id}
# ---------------------------------------------------------------------------


class TestDeleteDocument:
    async def test_delete_own_document_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
        auth_headers: dict,
    ):
        """자신의 문서 삭제 → 204."""
        doc = Document(user_id=user.id, title="삭제할 문서", content="내용")
        db_session.add(doc)
        await db_session.flush()

        response = await client.delete(f"/api/v1/documents/{doc.id}", headers=auth_headers)
        assert response.status_code == 204

    async def test_deleted_document_not_found(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user: User,
        auth_headers: dict,
    ):
        """삭제 후 조회 시 404."""
        doc = Document(user_id=user.id, title="삭제할 문서", content="내용")
        db_session.add(doc)
        await db_session.flush()

        await client.delete(f"/api/v1/documents/{doc.id}", headers=auth_headers)
        response = await client.get(f"/api/v1/documents/{doc.id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_delete_other_users_document_returns_404(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        other_user: User,
        auth_headers: dict,
    ):
        """다른 사용자의 문서 삭제 시도 → 404."""
        doc = Document(user_id=other_user.id, title="남의 문서", content="내용")
        db_session.add(doc)
        await db_session.flush()

        response = await client.delete(f"/api/v1/documents/{doc.id}", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "DOCUMENT_NOT_FOUND"

    async def test_delete_nonexistent_document_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """존재하지 않는 문서 삭제 → 404."""
        random_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/documents/{random_id}", headers=auth_headers)
        assert response.status_code == 404

    async def test_delete_without_auth_returns_403(self, client: AsyncClient):
        """인증 없이 삭제 → 403."""
        random_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/documents/{random_id}")
        assert response.status_code == 403
