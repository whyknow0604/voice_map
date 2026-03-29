"""Document CRUD 비즈니스 로직.

AI 요약/구조화는 document_service.py가 담당하며,
이 모듈은 Document 레코드의 생성/조회/삭제만 처리한다.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


async def create_document(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    content: str,
    keywords: list[str] | None = None,
    conversation_id: uuid.UUID | None = None,
) -> Document:
    """새 문서 레코드를 생성한다."""
    document = Document(
        user_id=user_id,
        conversation_id=conversation_id,
        title=title,
        content=content,
        keywords=keywords,
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return document


async def get_documents(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[Document]:
    """해당 사용자의 문서 목록을 반환한다 (최신순)."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def get_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Document:
    """문서 상세 정보를 반환한다.

    다른 사용자의 문서 조회 시 404를 반환한다 — 존재 여부 자체를 노출하지 않기 위해
    403이 아닌 404 사용.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "문서를 찾을 수 없습니다."},
        )

    # 다른 사용자의 문서 — 존재 여부를 노출하지 않도록 404 반환
    if document.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "문서를 찾을 수 없습니다."},
        )

    return document


async def delete_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """문서를 삭제한다.

    다른 사용자의 문서 삭제 시도 시 404를 반환한다.
    """
    document = await get_document(db=db, document_id=document_id, user_id=user_id)
    await db.delete(document)
    await db.flush()
