"""WebSocket 음성 채널 — Gemini Live API 중계."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
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

logger = logging.getLogger("voice")

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
    """FE로부터 메시지를 수신하여 큐에 넣는다 (always-on 모드).

    - 바이너리: 오디오 청크 → audio_queue에 push
    - JSON {"type": "mode_switch"}: 모드 전환 → sentinel 넣고 종료
    - Gemini VAD가 발화 감지를 자동 처리하므로 end_of_turn은 무시
    """
    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"] is not None:
                await audio_queue.put(message["bytes"])
            elif "text" in message and message["text"] is not None:
                try:
                    parsed = json.loads(message["text"])
                    msg_type = parsed.get("type", "")
                except (json.JSONDecodeError, AttributeError):
                    continue

                if msg_type == "mode_switch":
                    await audio_queue.put(None)
                    break
                # end_of_turn은 무시 — VAD가 자동 처리
    except WebSocketDisconnect:
        await audio_queue.put(None)
    except Exception:
        await audio_queue.put(None)


async def _send_loop(
    session: genai.live.AsyncSession,
    audio_queue: asyncio.Queue[bytes | None],
) -> None:
    """audio_queue에서 오디오 청크를 꺼내 Gemini Live API 세션으로 전송한다.

    None(sentinel)을 받으면 루프를 종료한다.
    에러 발생 시 로깅 후 재시도 — 세션이 살아있는 한 전송 계속.
    """
    chunk_count = 0
    try:
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                logger.info("[send_loop] sentinel 수신, 종료 (전송 청크: %d)", chunk_count)
                break
            try:
                await session.send_realtime_input(
                    audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                )
                chunk_count += 1
                if chunk_count % 50 == 0:
                    logger.debug("[send_loop] %d 청크 전송됨", chunk_count)
            except Exception as e:
                logger.error("[send_loop] 청크 전송 실패 (청크 %d): %s", chunk_count, e)
                # 세션 에러는 치명적이므로 종료
                break
    except asyncio.CancelledError:
        logger.info("[send_loop] 취소됨 (전송 청크: %d)", chunk_count)
        raise
    except Exception as e:
        logger.error("[send_loop] 루프 에러: %s", e)


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
    try:
        async for message in session.receive():
            server_content = message.server_content
            if server_content is None:
                continue

            # 사용자 발화 감지 시 Gemini가 현재 응답을 중단 — FE에 알려 재생 중단
            if server_content.interrupted:
                logger.info("[recv_loop] interrupted — FE에 중단 신호 전달")
                await websocket.send_text(_make_message("interrupted"))

            if server_content.model_turn:
                for part in server_content.model_turn.parts:
                    if part.inline_data and part.inline_data.data:
                        audio_b64 = base64.b64encode(
                            part.inline_data.data
                        ).decode("ascii")
                        await websocket.send_text(
                            _make_message("audio", data=audio_b64)
                        )

                    if part.text:
                        transcript_parts.append(part.text)
                        await websocket.send_text(
                            _make_message("transcript", content=part.text)
                        )

            if server_content.turn_complete:
                logger.info("[recv_loop] turn_complete — 다음 턴 대기")
                await websocket.send_text(_make_message("turn_complete"))
                # 멀티턴: 종료하지 않고 다음 턴 대기
    except asyncio.CancelledError:
        logger.info("[recv_loop] 취소됨")
        raise
    except Exception as e:
        logger.error("[recv_loop] 에러: %s", e)


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

    # 트랜스크립트가 있을 때만 대화 저장 (빈 대화 방지)
    conversation_id: uuid.UUID | None = None
    transcript_parts: list[str] = []

    try:
        logger.info("[voice] Gemini 세션 연결 시작")
        async with client.connect() as session:
            logger.info("[voice] Gemini 세션 연결 성공, 태스크 시작")
            receive_task = asyncio.create_task(
                _receive_loop(websocket, session, audio_queue)
            )
            send_task = asyncio.create_task(_send_loop(session, audio_queue))
            recv_task = asyncio.create_task(
                _recv_loop(websocket, session, transcript_parts)
            )

            # receive_task가 FE WebSocket 생명주기를 관리 — 종료될 때까지 대기
            try:
                await receive_task
            finally:
                logger.info("[voice] receive_task 종료, 나머지 태스크 정리")
                send_task.cancel()
                recv_task.cancel()
                for task in [send_task, recv_task]:
                    try:
                        await task
                    except (asyncio.CancelledError, Exception):
                        pass

            # 트랜스크립트가 있으면 대화 생성 + AI 응답 DB 저장
            if transcript_parts:
                full_transcript = "".join(transcript_parts)
                async with async_session() as db:
                    conversation = Conversation(
                        user_id=user.id, mode=ConversationMode.voice
                    )
                    db.add(conversation)
                    await db.flush()
                    conversation_id = conversation.id
                    db.add(Message(
                        conversation_id=conversation_id,
                        role=MessageRole.ai,
                        content=full_transcript,
                    ))
                    await db.commit()

    except WebSocketDisconnect:
        logger.info("[voice] WebSocket 연결 종료 (클라이언트)")
    except Exception as e:
        logger.error("[voice] 핸들러 에러: %s", e)
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
