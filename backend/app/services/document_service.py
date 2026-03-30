"""
문서 생성 서비스 — 대화 히스토리를 구조화된 문서로 변환

대화 세션이 완료되면 Gemini에게 summarize_v1 프롬프트를 사용하여
title/content/keywords JSON을 추출한다.
"""

import json
import logging
import re
from typing import Any

from app.models.conversation import Message, MessageRole
from app.prompts.summarize_v1 import SUMMARIZE_PROMPT_V1, SUMMARIZE_USER_TEMPLATE
from app.services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# 역할 레이블 매핑 — 프롬프트의 입력 형식과 일치
_ROLE_LABEL: dict[MessageRole, str] = {
    MessageRole.user: "User",
    MessageRole.ai: "AI",
}


async def generate_document(messages: list[Message]) -> dict[str, Any]:
    """대화 히스토리를 분석하여 구조화된 문서를 생성한다.

    GeminiClient를 통해 summarize_v1 프롬프트를 호출하고,
    반환된 JSON을 파싱하여 title/content/keywords 딕셔너리로 반환한다.

    Args:
        messages: 문서화할 대화의 Message 모델 목록. created_at 기준 정렬 가정.

    Returns:
        {"title": str, "content": str, "keywords": list[str]} 형식의 딕셔너리.

    Raises:
        ValueError: Gemini 응답이 유효한 JSON이 아니거나 필수 필드가 없는 경우.
    """
    conversation_history = _format_conversation_history(messages)
    user_message = SUMMARIZE_USER_TEMPLATE.format(conversation_history=conversation_history)

    client = GeminiClient()

    # 단일 사용자 메시지로 구성 — summarize 프롬프트는 대화형이 아닌 단발성 요청
    chat_messages = [{"role": "user", "text": user_message}]

    # 스트리밍으로 전체 응답 수집
    raw_chunks: list[str] = []
    async for chunk in client.generate_stream(chat_messages, SUMMARIZE_PROMPT_V1):
        raw_chunks.append(chunk)

    raw_response = "".join(raw_chunks).strip()
    logger.debug("Gemini summarize 원본 응답: %s", raw_response[:200])

    return _parse_document_json(raw_response)


def _format_conversation_history(messages: list[Message]) -> str:
    """Message 목록을 프롬프트 입력 형식의 문자열로 변환한다.

    프롬프트 입력 형식:
        [User]: 사용자 발화
        [AI]: AI 응답

    Args:
        messages: 대화 메시지 목록.

    Returns:
        포맷된 대화 히스토리 문자열.
    """
    lines: list[str] = []
    for msg in messages:
        label = _ROLE_LABEL.get(msg.role, "Unknown")
        lines.append(f"[{label}]: {msg.content}")
    return "\n".join(lines)


def _parse_document_json(raw: str) -> dict[str, Any]:
    """Gemini 응답 문자열에서 JSON을 추출하고 유효성을 검증한다.

    Gemini가 지시를 무시하고 마크다운 코드 블록으로 감쌀 수 있으므로
    ```json ... ``` 패턴을 먼저 제거한 뒤 파싱한다.

    Args:
        raw: Gemini 원본 응답 문자열.

    Returns:
        {"title": str, "content": str, "keywords": list[str]} 딕셔너리.

    Raises:
        ValueError: JSON 파싱 실패 또는 필수 필드 누락 시.
    """
    # 마크다운 코드 블록 제거: ```json ... ``` 또는 ``` ... ```
    cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        preview = raw[:300]
        raise ValueError(f"Gemini 응답을 JSON으로 파싱할 수 없습니다: {e}\n원본: {preview}") from e

    # 필수 필드 검증
    required_fields = ("title", "content", "keywords")
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f"Gemini 응답에 필수 필드가 없습니다: {missing}")

    if not isinstance(data["keywords"], list):
        raise ValueError("keywords 필드는 리스트여야 합니다.")

    return {
        "title": str(data["title"]),
        "content": str(data["content"]),
        "keywords": [str(k) for k in data["keywords"]],
    }
