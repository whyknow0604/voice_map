"""Conversation 비즈니스 로직."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationMode


async def create_conversation(
    db: AsyncSession,
    user_id: uuid.UUID,
    mode: ConversationMode = ConversationMode.text,
    title: str | None = None,
) -> Conversation:
    """새 대화 세션을 생성한다."""
    conversation = Conversation(
        user_id=user_id,
        mode=mode,
        title=title,
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    return conversation


async def get_conversations(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[Conversation]:
    """해당 사용자의 대화 세션 목록을 반환한다 (최신순)."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation_detail(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Conversation:
    """대화 세션 상세 정보(메시지 포함)를 반환한다.

    다른 사용자의 대화 조회 시 404를 반환한다 — 존재 여부 자체를 노출하지 않기 위해
    403이 아닌 404 사용.
    """
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CONVERSATION_NOT_FOUND", "message": "대화를 찾을 수 없습니다."},
        )

    # 다른 사용자의 대화 — 존재 여부를 노출하지 않도록 404 반환
    if conversation.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CONVERSATION_NOT_FOUND", "message": "대화를 찾을 수 없습니다."},
        )

    return conversation
