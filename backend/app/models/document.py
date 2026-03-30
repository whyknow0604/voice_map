import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Document(Base):
    """문서 모델 — 대화에서 AI가 구조화한 문서를 저장한다.

    대화(conversation)가 종료된 후 AI가 요약/구조화한 결과물이며,
    embedding 컬럼은 Graph RAG 실험을 위한 pgvector 768차원 벡터다.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # users 테이블에 대한 FK — 사용자 삭제 시 문서도 함께 삭제
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # conversations 테이블에 대한 FK — 대화 삭제 시 문서는 유지 (SET NULL)
    # 직접 생성한 문서는 대화와 무관할 수 있으므로 nullable
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # AI가 추출한 문서 제목
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # AI가 구조화한 본문 내용 (Markdown 형식)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # AI가 추출한 키워드 목록 — 검색 및 Graph RAG 노드 레이블로 활용
    keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
    )

    # pgvector 768차원 임베딩 — Gemini text-embedding-004 모델 기준
    # Graph RAG 유사도 검색에 사용
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
