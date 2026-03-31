"""WebSocket 채팅 엔드포인트 — Gemini API 스트리밍 연동."""

import json
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import async_session
from app.models.conversation import Conversation, ConversationMode, Message, MessageRole
from app.models.user import User
from app.services.ai_service import get_system_prompt
from app.services.gemini_client import GeminiClient

router = APIRouter()

# 세션 단위 대화 히스토리 (Gemini API 컨텍스트 전달용, DB와 병행 사용)
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


def _make_message(msg_type: str, content: str) -> str:
    """JSON 메시지 직렬화."""
    return json.dumps({"type": msg_type, "content": content}, ensure_ascii=False)


@router.websocket("/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    session_id: str = Query(default_factory=lambda: str(uuid.uuid4()), description="대화 세션 ID"),
):
    """WebSocket 채팅 엔드포인트.

    연결 시 JWT 인증 → 클라이언트 메시지 수신 → Gemini 스트리밍 응답 전송.

    메시지 포맷 (서버 → 클라이언트):
    - {"type": "token", "content": "텍스트 청크"}
    - {"type": "done", "content": ""}
    - {"type": "error", "content": "에러 메시지"}

    메시지 포맷 (클라이언트 → 서버):
    - {"type": "message", "content": "텍스트"} 또는 단순 문자열
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

    # 첫 메시지 수신 시에만 Conversation 생성 (빈 대화 방지)
    conversation_id: uuid.UUID | None = None
    first_user_message: str | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            # FE는 JSON {type: "message", content: "..."} 형태로 전송, 단순 문자열도 지원
            try:
                parsed = json.loads(raw)
                user_text = parsed.get("content", "").strip()
            except (json.JSONDecodeError, AttributeError):
                user_text = raw.strip()
            if not user_text:
                continue

            # 첫 메시지 시 대화 세션 생성 (lazy)
            if conversation_id is None:
                first_user_message = user_text
                async with async_session() as db:
                    conversation = Conversation(
                        user_id=user.id, mode=ConversationMode.text
                    )
                    db.add(conversation)
                    await db.commit()
                    await db.refresh(conversation)
                    conversation_id = conversation.id

            # 히스토리에 사용자 메시지 추가
            history.append({"role": "user", "text": user_text})

            # 사용자 메시지 DB 저장
            async with async_session() as db:
                db.add(Message(
                    conversation_id=conversation_id,
                    role=MessageRole.user,
                    content=user_text,
                ))
                await db.commit()

            # Gemini 스트리밍 응답 전송
            full_response = ""
            try:
                async for chunk in _get_gemini_client().generate_stream(
                    history, system_prompt
                ):
                    full_response += chunk
                    await websocket.send_text(_make_message("token", chunk))

                # 히스토리에 모델 응답 추가
                if full_response:
                    history.append({"role": "model", "text": full_response})
                    # AI 응답 DB 저장
                    async with async_session() as db:
                        db.add(Message(
                            conversation_id=conversation_id,
                            role=MessageRole.ai,
                            content=full_response,
                        ))
                        await db.commit()
            except Exception as e:
                # 스트리밍 도중 에러 발생 — 클라이언트에 알리고 done으로 마무리
                try:
                    await websocket.send_text(_make_message("error", str(e)))
                except Exception:
                    pass

            # 성공/실패 무관하게 항상 done 전송 — 클라이언트가 무한 로딩에 빠지지 않도록
            await websocket.send_text(_make_message("done", ""))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(_make_message("error", str(e)))
            await websocket.send_text(_make_message("done", ""))
        except Exception:
            pass
    finally:
        # 대화 종료 시각 기록 + 제목 자동 생성 + 문서 생성 트리거
        if conversation_id:
            try:
                async with async_session() as db:
                    result = await db.execute(
                        select(Conversation).where(Conversation.id == conversation_id)
                    )
                    conv = result.scalar_one_or_none()
                    if conv:
                        from datetime import datetime, timezone
                        import logging

                        conv.ended_at = datetime.now(timezone.utc)
                        # 대화 제목 자동 생성: 첫 사용자 메시지의 앞 50자
                        if not conv.title and first_user_message:
                            conv.title = first_user_message[:50]
                        logging.getLogger("chat").warning(
                            "[chat] title 설정: %r (first_msg=%r)",
                            conv.title, first_user_message,
                        )
                        await db.commit()
            except Exception as e:
                import logging
                logging.getLogger("chat").error("[chat] finally 에러: %s", e)

            # 메시지가 있으면 문서 생성 트리거 — 실패 시 대화 종료를 블로킹하지 않음
            if history:
                try:
                    from app.models.conversation import Message as ConvMessage
                    from app.services import document_crud_service, document_service

                    async with async_session() as db:
                        # DB에서 해당 대화의 메시지 조회
                        msg_result = await db.execute(
                            select(ConvMessage).where(
                                ConvMessage.conversation_id == conversation_id
                            )
                        )
                        messages = list(msg_result.scalars().all())
                        if messages:
                            doc_data = await document_service.generate_document(messages)
                            await document_crud_service.create_document(
                                db=db,
                                user_id=user.id,
                                conversation_id=conversation_id,
                                title=doc_data["title"],
                                content=doc_data["content"],
                                keywords=doc_data.get("keywords"),
                            )
                            # 문서 제목을 대화 제목에도 반영 (AI 생성 제목이 더 나음)
                            conv_result = await db.execute(
                                select(Conversation).where(
                                    Conversation.id == conversation_id
                                )
                            )
                            conv = conv_result.scalar_one_or_none()
                            if conv and doc_data.get("title"):
                                conv.title = doc_data["title"]
                            await db.commit()
                except Exception as e:
                    # 문서 생성 실패는 대화 종료를 블로킹하지 않음 — 로깅만
                    import logging
                    logging.getLogger("chat").warning(
                        "[chat] 문서 생성 트리거 실패 (conversation_id=%s): %s",
                        conversation_id,
                        e,
                    )
