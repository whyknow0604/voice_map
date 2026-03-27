"""WebSocket 음성 채널 — Gemini Live API 중계."""

from __future__ import annotations

import asyncio
import base64
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from google import genai
from google.genai import types
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import async_session
from app.models.conversation import Conversation, ConversationMode, Message, MessageRole
from app.models.user import User
from app.services.gemini_live_client import GeminiLiveClient

router = APIRouter()

# GeminiLiveClient 지연 초기화 — 테스트 환경에서 API 키 없이 모듈 로드 가능
_gemini_live_client: GeminiLiveClient | None = None


def _get_gemini_live_client() -> GeminiLiveClient:
    global _gemini_live_client
    if _gemini_live_client is None:
        _gemini_live_client = GeminiLiveClient()
    return _gemini_live_client


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


def _make_message(msg_type: str, **kwargs: object) -> str:
    """JSON 메시지 직렬화."""
    return json.dumps({"type": msg_type, **kwargs}, ensure_ascii=False)


async def _receive_loop(
    websocket: WebSocket,
    session: genai.live.AsyncSession,
    audio_queue: asyncio.Queue[bytes | None],
) -> None:
    """FE로부터 메시지를 수신하여 큐에 넣거나 세션에 제어 신호를 전달한다.

    - 바이너리: 오디오 청크 → audio_queue에 push
    - JSON {"type": "end_of_turn"}: 발화 종료 → audio_queue에 None(sentinel) push
    - JSON {"type": "mode_switch"}: 모드 전환 → 현재는 연결 종료로 처리
    """
    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"] is not None:
                # 바이너리 — PCM 오디오 청크
                await audio_queue.put(message["bytes"])
            elif "text" in message and message["text"] is not None:
                try:
                    parsed = json.loads(message["text"])
                    msg_type = parsed.get("type", "")
                except (json.JSONDecodeError, AttributeError):
                    continue

                if msg_type == "end_of_turn":
                    # 발화 종료 신호 — sentinel으로 큐에 삽입
                    await audio_queue.put(None)
                elif msg_type == "mode_switch":
                    # 모드 전환 요청 — 정상 종료
                    await audio_queue.put(None)
                    break
    except WebSocketDisconnect:
        # 연결 종료 시 큐를 깨워 send_loop가 종료되도록 sentinel 삽입
        await audio_queue.put(None)
    except Exception:
        await audio_queue.put(None)


async def _send_loop(
    session: genai.live.AsyncSession,
    audio_queue: asyncio.Queue[bytes | None],
) -> None:
    """audio_queue에서 오디오 청크를 꺼내 Gemini Live API 세션으로 전송한다.

    None(sentinel)을 받으면 end_of_turn 신호를 전송하고 종료한다.
    """
    while True:
        chunk = await audio_queue.get()
        if chunk is None:
            # 발화 종료 신호
            await session.send(input="", end_of_turn=True)
            break
        await session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")]
            )
        )


async def _recv_loop(
    websocket: WebSocket,
    session: genai.live.AsyncSession,
    transcript_parts: list[str],
) -> None:
    """Gemini Live API로부터 응답을 수신하여 FE로 전달한다.

    - 오디오 응답 → {"type": "audio", "data": "<base64 PCM 24kHz>"}
    - 트랜스크립트 → {"type": "transcript", "content": "텍스트"}
    - 응답 완료 → {"type": "turn_complete"}

    transcript_parts에 텍스트를 수집하여 DB 저장에 활용한다.
    """
    async for message in session.receive():
        server_content = message.server_content
        if server_content is None:
            continue

        if server_content.model_turn:
            for part in server_content.model_turn.parts:
                # 오디오 응답 — inline_data.data 는 base64 인코딩된 PCM 24kHz
                if part.inline_data and part.inline_data.data:
                    audio_b64 = base64.b64encode(
                        part.inline_data.data
                    ).decode("ascii")
                    await websocket.send_text(
                        _make_message("audio", data=audio_b64)
                    )

                # 텍스트 트랜스크립트 (있는 경우)
                if part.text:
                    transcript_parts.append(part.text)
                    await websocket.send_text(
                        _make_message("transcript", content=part.text)
                    )

        if server_content.turn_complete:
            await websocket.send_text(_make_message("turn_complete"))
            break


@router.websocket("/voice")
async def websocket_voice(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    session_id: str = Query(
        default_factory=lambda: str(uuid.uuid4()),
        description="대화 세션 ID",
    ),
):
    """WebSocket 음성 채널 엔드포인트.

    연결 시 JWT 인증 → Gemini Live API 세션 생성 → FE 오디오 수신/전달 루프.

    메시지 포맷 (FE → BE):
    - 바이너리: PCM 16kHz 16-bit 모노 오디오 청크
    - JSON {"type": "end_of_turn"}: 발화 종료 신호
    - JSON {"type": "mode_switch", "mode": "text"}: 모드 전환

    메시지 포맷 (BE → FE):
    - {"type": "audio", "data": "<base64 PCM 24kHz>"}: 오디오 응답
    - {"type": "transcript", "content": "텍스트"}: 트랜스크립트
    - {"type": "turn_complete"}: AI 응답 완료
    - {"type": "error", "content": "에러 메시지"}: 에러
    """
    user = await _authenticate_ws(token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    client = _get_gemini_live_client()
    # maxsize=100: 약 6.4초 버퍼 (100 * 1024 samples / 16000 Hz)
    audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=100)

    # DB에 음성 대화 세션 생성
    conversation_id: uuid.UUID | None = None
    async with async_session() as db:
        conversation = Conversation(user_id=user.id, mode=ConversationMode.voice)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        conversation_id = conversation.id

    transcript_parts: list[str] = []

    try:
        async with client.connect() as session:
            # 수신, 전송, Gemini 응답 수신 태스크를 동시에 실행
            receive_task = asyncio.create_task(
                _receive_loop(websocket, session, audio_queue)
            )
            send_task = asyncio.create_task(_send_loop(session, audio_queue))
            recv_task = asyncio.create_task(
                _recv_loop(websocket, session, transcript_parts)
            )

            # send_task 완료 후(end_of_turn 전송 완료) recv_task 대기
            # receive_task는 WebSocketDisconnect 시 종료
            try:
                await asyncio.gather(send_task, recv_task)
            finally:
                receive_task.cancel()
                try:
                    await receive_task
                except asyncio.CancelledError:
                    pass

            # 트랜스크립트가 있으면 AI 응답으로 DB 저장
            if transcript_parts and conversation_id:
                full_transcript = "".join(transcript_parts)
                async with async_session() as db:
                    db.add(Message(
                        conversation_id=conversation_id,
                        role=MessageRole.ai,
                        content=full_transcript,
                    ))
                    await db.commit()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(_make_message("error", content=str(e)))
        except Exception:
            pass
    finally:
        # 대화 종료 시각 기록
        if conversation_id:
            try:
                async with async_session() as db:
                    result = await db.execute(
                        select(Conversation).where(
                            Conversation.id == conversation_id
                        )
                    )
                    conv = result.scalar_one_or_none()
                    if conv:
                        conv.ended_at = datetime.now(timezone.utc)
                        await db.commit()
            except Exception:
                pass
