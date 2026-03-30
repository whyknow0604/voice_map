"""Document CRUD 엔드포인트."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentResponse,
    SimilarDocumentResponse,
)
from app.services import document_crud_service

router = APIRouter()


@router.post("", response_model=DocumentResponse, status_code=201)
async def create_document(
    payload: DocumentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentResponse:
    """새 문서를 생성한다.

    Raises:
        401/403: 인증되지 않은 요청.
    """
    document = await document_crud_service.create_document(
        db=db,
        user_id=current_user.id,
        title=payload.title,
        content=payload.content,
        keywords=payload.keywords,
        conversation_id=payload.conversation_id,
    )
    return DocumentResponse.model_validate(document)


@router.get("", response_model=list[DocumentListResponse])
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DocumentListResponse]:
    """현재 사용자의 문서 목록을 반환한다 (최신순, embedding 제외).

    Raises:
        401/403: 인증되지 않은 요청.
    """
    documents = await document_crud_service.get_documents(db=db, user_id=current_user.id)
    return [DocumentListResponse.model_validate(d) for d in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentResponse:
    """문서 상세 정보를 반환한다.

    Raises:
        401/403: 인증되지 않은 요청.
        404: 문서를 찾을 수 없거나 다른 사용자의 문서.
    """
    document = await document_crud_service.get_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/similar", response_model=list[SimilarDocumentResponse])
async def get_similar_documents(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SimilarDocumentResponse]:
    """cosine similarity 기반으로 유사 문서 상위 5개를 반환한다.

    pgvector <=> 연산자를 사용하며, 같은 사용자 문서 내에서만 검색한다.

    Raises:
        401/403: 인증되지 않은 요청.
        404: 문서를 찾을 수 없거나 embedding이 없는 경우.
    """
    return await document_crud_service.get_similar_documents(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """문서를 삭제한다.

    Raises:
        401/403: 인증되지 않은 요청.
        404: 문서를 찾을 수 없거나 다른 사용자의 문서.
    """
    await document_crud_service.delete_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )
