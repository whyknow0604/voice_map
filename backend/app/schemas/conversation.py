"""Conversation 관련 Pydantic v2 스키마."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.conversation import ConversationMode, MessageRole


class ConversationCreate(BaseModel):
    """대화 세션 생성 요청 스키마."""

    mode: ConversationMode = ConversationMode.text
    title: str | None = None


class MessageResponse(BaseModel):
    """메시지 응답 스키마."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    audio_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """대화 세션 목록 응답 스키마 — 메시지 미포함."""

    id: uuid.UUID
    user_id: uuid.UUID
    mode: ConversationMode
    title: str | None
    created_at: datetime
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    """대화 세션 상세 응답 스키마 — 메시지 포함."""

    messages: list[MessageResponse]
