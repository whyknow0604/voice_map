"""WebSocket 채팅 엔드포인트 테스트."""

import json
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token, create_refresh_token
from app.main import app


def _make_fake_user() -> SimpleNamespace:
    """DB 없이 인증 mock용으로만 사용하는 유저 객체."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        email="ws@example.com",
        name="WS User",
        provider="google",
        provider_id="ws-gid-123",
    )


async def _mock_stream(chunks: list[str]) -> AsyncGenerator[str, None]:
    """테스트용 Gemini 스트리밍 응답 생성기."""
    for chunk in chunks:
        yield chunk


def _make_mock_client(stream_fn) -> MagicMock:
    """generate_stream이 stream_fn을 반환하는 mock GeminiClient."""
    mock = MagicMock()
    mock.generate_stream = stream_fn
    return mock


def _make_mock_async_session():
    """DB 없이 async_session을 mock하는 context manager.

    Conversation 생성 시 fake id를 부여하고 commit/refresh를 no-op 처리.
    """
    @asynccontextmanager
    async def mock_session():
        session = AsyncMock()

        async def fake_refresh(obj):
            if hasattr(obj, "id") and obj.id is None:
                obj.id = uuid.uuid4()

        session.refresh = fake_refresh
        session.commit = AsyncMock()
        session.add = MagicMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        yield session

    return mock_session


@pytest.mark.asyncio(loop_scope="function")
class TestWebSocketChat:
    async def test_unauthenticated_connection_is_rejected(self):
        """유효하지 않은 토큰으로 연결 시 거부 (1008)."""
        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect) as exc_info:
                with client.websocket_connect("/ws/chat?token=invalid-token"):
                    pass
        assert exc_info.value.code == 1008

    async def test_authenticated_connection_receives_streaming_response(self):
        """인증된 사용자가 메시지 전송 시 스트리밍 응답 수신."""
        from app.api.v1.endpoints import chat as chat_module

        user = _make_fake_user()
        token = create_access_token(user.id)
        chunks = ["안녕하세요, ", "무엇을 ", "도와드릴까요?"]

        async def mock_authenticate(t: str):
            return user

        def stream_fn(messages, system_prompt):
            return _mock_stream(chunks)

        with (
            patch.object(chat_module, "_authenticate_ws", side_effect=mock_authenticate),
            patch.object(
                chat_module, "_get_gemini_client", return_value=_make_mock_client(stream_fn)
            ),
            patch("app.api.v1.endpoints.chat.async_session", _make_mock_async_session()),
        ):
            with TestClient(app) as client:
                with client.websocket_connect(f"/ws/chat?token={token}") as ws:
                    ws.send_text("안녕하세요")

                    received_chunks = []
                    done = False
                    while not done:
                        msg = json.loads(ws.receive_text())
                        if msg["type"] == "token":
                            received_chunks.append(msg["content"])
                        elif msg["type"] == "done":
                            done = True

        assert received_chunks == chunks

    async def test_session_history_is_maintained(self):
        """세션 ID가 같으면 대화 히스토리가 유지된다."""
        from app.api.v1.endpoints import chat as chat_module

        user = _make_fake_user()
        session_id = str(uuid.uuid4())
        chat_module._session_histories[session_id] = []

        token = create_access_token(user.id)
        call_count = 0

        async def mock_authenticate(t: str):
            return user

        async def mock_stream_with_history(messages, system_prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                assert len(messages) >= 2
            yield f"응답{call_count}"

        with (
            patch.object(chat_module, "_authenticate_ws", side_effect=mock_authenticate),
            patch.object(
                chat_module,
                "_get_gemini_client",
                return_value=_make_mock_client(mock_stream_with_history),
            ),
            patch("app.api.v1.endpoints.chat.async_session", _make_mock_async_session()),
        ):
            with TestClient(app) as client:
                with client.websocket_connect(
                    f"/ws/chat?token={token}&session_id={session_id}"
                ) as ws:
                    ws.send_text("첫 번째 메시지")
                    while True:
                        if json.loads(ws.receive_text())["type"] == "done":
                            break

                    ws.send_text("두 번째 메시지")
                    while True:
                        if json.loads(ws.receive_text())["type"] == "done":
                            break

        assert call_count == 2
        chat_module._session_histories.pop(session_id, None)

    async def test_gemini_error_sends_error_then_done(self):
        """Gemini 스트리밍 도중 예외 발생 시 error 후 done을 전송한다 (무한 로딩 방지)."""
        from app.api.v1.endpoints import chat as chat_module

        user = _make_fake_user()
        token = create_access_token(user.id)

        async def mock_authenticate(t: str):
            return user

        async def failing_stream(messages, system_prompt):
            yield "일부 응답"
            raise RuntimeError("Gemini API 오류")

        with (
            patch.object(chat_module, "_authenticate_ws", side_effect=mock_authenticate),
            patch.object(
                chat_module,
                "_get_gemini_client",
                return_value=_make_mock_client(failing_stream),
            ),
            patch("app.api.v1.endpoints.chat.async_session", _make_mock_async_session()),
        ):
            with TestClient(app) as client:
                with client.websocket_connect(f"/ws/chat?token={token}") as ws:
                    ws.send_text("테스트 메시지")

                    received_types = []
                    # error + done 두 메시지를 수신
                    for _ in range(10):
                        msg = json.loads(ws.receive_text())
                        received_types.append(msg["type"])
                        if msg["type"] == "done":
                            break

        assert "error" in received_types
        assert received_types[-1] == "done"


@pytest.mark.asyncio(loop_scope="function")
class TestJWTAuthForWebSocket:
    async def test_refresh_token_is_rejected(self):
        """refresh token으로 WebSocket 연결 시 거부 (1008)."""
        user = _make_fake_user()
        refresh_token = create_refresh_token(user.id)
        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect) as exc_info:
                with client.websocket_connect(f"/ws/chat?token={refresh_token}"):
                    pass
        assert exc_info.value.code == 1008
