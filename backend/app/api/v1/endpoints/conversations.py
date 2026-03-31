"""Conversation CRUD 엔드포인트."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
)
from app.services import conversation_service

logger = logging.getLogger("conversations")

router = APIRouter()


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationResponse:
    """새 대화 세션을 생성한다.

    Raises:
        401/403: 인증되지 않은 요청.
    """
    conversation = await conversation_service.create_conversation(
        db=db,
        user_id=current_user.id,
        mode=payload.mode,
        title=payload.title,
    )
    return ConversationResponse.model_validate(conversation)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ConversationResponse]:
    """현재 사용자의 대화 목록을 반환한다 (최신순).

    Raises:
        401/403: 인증되지 않은 요청.
    """
    try:
        conversations = await conversation_service.get_conversations(
            db=db, user_id=current_user.id
        )
    except OperationalError as e:
        logger.warning("[conversations] DB 연결 실패, 재시도: %s", e)
        # connection pool cold start — rollback 후 재시도
        await db.rollback()
        conversations = await conversation_service.get_conversations(
            db=db, user_id=current_user.id
        )
    except Exception as e:
        logger.error("[conversations] 대화 목록 조회 실패: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "CONVERSATIONS_FETCH_ERROR",
                "message": "대화 목록을 불러올 수 없습니다.",
            },
        ) from e
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationDetailResponse:
    """대화 상세 정보(메시지 포함)를 반환한다.

    Raises:
        401/403: 인증되지 않은 요청.
        404: 대화를 찾을 수 없거나 다른 사용자의 대화.
    """
    conversation = await conversation_service.get_conversation_detail(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    return ConversationDetailResponse.model_validate(conversation)
