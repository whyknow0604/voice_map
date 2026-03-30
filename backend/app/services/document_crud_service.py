"""Document CRUD 비즈니스 로직.

AI 요약/구조화는 document_service.py가 담당하며,
이 모듈은 Document 레코드의 생성/조회/삭제만 처리한다.
"""

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.schemas.document import SimilarDocumentResponse
from app.services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)


async def create_document(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    content: str,
    keywords: list[str] | None = None,
    conversation_id: uuid.UUID | None = None,
) -> Document:
    """새 문서 레코드를 생성하고 embedding을 저장한다.

    embedding 생성 실패 시 embedding은 None으로 저장하되 문서 생성은 성공으로 처리한다.
    """
    # title + content를 합쳐서 임베딩 — 제목 컨텍스트가 유사도 정확도를 높인다
    embedding: list[float] | None = None
    try:
        embedding_text = f"{title}\n\n{content}"
        embedding = await generate_embedding(embedding_text)
    except Exception as e:
        # embedding 실패는 문서 생성을 막지 않는다 — 나중에 배치로 채울 수 있음
        logger.warning("embedding 생성 실패, None으로 저장: %s", e)

    document = Document(
        user_id=user_id,
        conversation_id=conversation_id,
        title=title,
        content=content,
        keywords=keywords,
        embedding=embedding,
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


async def get_similar_documents(
    db: AsyncSession,
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 5,
) -> list[SimilarDocumentResponse]:
    """대상 문서와 cosine similarity가 높은 유사 문서를 반환한다.

    pgvector의 <=> 연산자(cosine distance)를 사용한다.
    자기 자신 및 embedding이 없는 문서는 제외하며, 같은 사용자의 문서만 검색한다.

    Args:
        db: 비동기 DB 세션.
        document_id: 기준 문서 ID.
        user_id: 현재 사용자 ID — 타 사용자 문서 노출 방지.
        limit: 반환할 최대 문서 수 (기본값 5).

    Returns:
        SimilarDocumentResponse 리스트 (similarity_score 내림차순).

    Raises:
        HTTPException 404: 문서를 찾을 수 없거나 embedding이 없는 경우.
    """
    # 기준 문서 조회 (소유권 검증 포함)
    document = await get_document(db=db, document_id=document_id, user_id=user_id)

    if document.embedding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "EMBEDDING_NOT_FOUND", "message": "해당 문서에 embedding이 없습니다."},
        )

    # cosine distance = 1 - cosine similarity, 오름차순 정렬 → 가장 유사한 문서가 먼저
    distance_col = Document.embedding.cosine_distance(document.embedding).label("distance")

    result = await db.execute(
        select(Document.id, Document.title, distance_col)
        .where(Document.user_id == user_id)
        .where(Document.id != document_id)
        .where(Document.embedding.is_not(None))
        .order_by(distance_col)
        .limit(limit)
    )

    rows = result.all()
    return [
        SimilarDocumentResponse(
            id=row.id,
            title=row.title,
            # cosine similarity = 1 - cosine distance
            similarity_score=round(1.0 - row.distance, 6),
        )
        for row in rows
    ]
