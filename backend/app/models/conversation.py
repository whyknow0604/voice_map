import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConversationMode(str, Enum):
    """대화 모드 — 텍스트 기반 소크라테스 대화 또는 음성 기반 실시간 대화."""

    text = "text"
    voice = "voice"


class MessageRole(str, Enum):
    """메시지 발신자 역할 — 사용자 또는 AI."""

    user = "user"
    ai = "ai"


class Conversation(Base):
    """대화 세션 모델 — 하나의 대화 세션(텍스트 또는 음성)을 나타낸다."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # users 테이블에 대한 FK — 사용자 삭제 시 대화도 함께 삭제
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[ConversationMode] = mapped_column(
        String(10),
        nullable=False,
        default=ConversationMode.text,
    )
    # 대화 제목은 AI가 나중에 요약하여 채워줄 수 있으므로 nullable
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # ended_at이 None이면 대화가 진행 중임을 의미
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 관계 정의 — cascade delete로 대화 삭제 시 메시지도 함께 삭제
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    """메시지 모델 — 대화 세션 내의 개별 발화(사용자 또는 AI)를 나타낸다."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # conversations 테이블에 대한 FK — 대화 삭제 시 메시지도 함께 삭제
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        String(10),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 음성 모드에서 원본 오디오 파일 URL (텍스트 모드에서는 null)
    audio_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # 역방향 관계
    conversation: Mapped[Conversation] = relationship(
        "Conversation",
        back_populates="messages",
    )
