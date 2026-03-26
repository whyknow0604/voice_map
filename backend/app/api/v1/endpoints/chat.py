"""WebSocket 채팅 엔드포인트 — Gemini API 스트리밍 연동."""

import json
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import async_session
from app.models.user import User
from app.services.ai_service import get_system_prompt
from app.services.gemini_client import GeminiClient

router = APIRouter()

# 세션 단위 대화 히스토리 저장소 (메모리 기반, Sprint 2에서 DB로 이전)
# key: session_id (str), value: list of {"role": "user"|"model", "text": "..."}
_session_histories: dict[str, list[dict[str, str]]] = {}

# GeminiClient 지연 초기화 — 테스트 환경에서 API 키 없이 모듈 로드 가능
_gemini_client: GeminiClient | None = None


def _get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


async def _authenticate_ws(token: str) -> User | None:
    """WebSocket JWT 인증 — 유효한 토큰이면 User 반환, 아니면 None."""
    try:
        payload = decode_token(token)
    except Exception:
        return None

    if payload.get("type") != "access":
        return None

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return None

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


def _make_message(msg_type: str, data: str) -> str:
    """JSON 메시지 직렬화."""
    return json.dumps({"type": msg_type, "data": data}, ensure_ascii=False)


@router.websocket("/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    session_id: str = Query(default_factory=lambda: str(uuid.uuid4()), description="대화 세션 ID"),
):
    """WebSocket 채팅 엔드포인트.

    연결 시 JWT 인증 → 클라이언트 메시지 수신 → Gemini 스트리밍 응답 전송.

    메시지 포맷 (서버 → 클라이언트):
    - {"type": "chunk", "data": "텍스트 청크"}
    - {"type": "done", "data": ""}
    - {"type": "error", "data": "에러 메시지"}

    메시지 포맷 (클라이언트 → 서버):
    - 단순 문자열 텍스트
    """
    user = await _authenticate_ws(token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    # 세션 히스토리 초기화 (새 세션이면 빈 리스트 생성)
    if session_id not in _session_histories:
        _session_histories[session_id] = []

    history = _session_histories[session_id]
    system_prompt = get_system_prompt()

    try:
        while True:
            user_text = await websocket.receive_text()
            user_text = user_text.strip()
            if not user_text:
                continue

            # 히스토리에 사용자 메시지 추가
            history.append({"role": "user", "text": user_text})

            # Gemini 스트리밍 응답 전송
            full_response = ""
            async for chunk in _get_gemini_client().generate_stream(history, system_prompt):
                full_response += chunk
                await websocket.send_text(_make_message("chunk", chunk))

            # 히스토리에 모델 응답 추가
            if full_response:
                history.append({"role": "model", "text": full_response})

            await websocket.send_text(_make_message("done", ""))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(_make_message("error", str(e)))
        except Exception:
            pass
