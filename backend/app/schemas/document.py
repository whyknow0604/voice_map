"""Document 관련 Pydantic v2 스키마."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    """문서 생성 요청 스키마."""

    title: str
    content: str
    keywords: list[str] | None = None
    conversation_id: uuid.UUID | None = None


class DocumentResponse(BaseModel):
    """문서 상세 응답 스키마 — embedding 포함."""

    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None
    title: str
    content: str
    keywords: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """문서 목록 응답 스키마 — embedding 제외 (대역폭 절약)."""

    id: uuid.UUID
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None
    title: str
    keywords: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
