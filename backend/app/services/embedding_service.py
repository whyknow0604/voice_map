"""
임베딩 서비스 — 텍스트를 768차원 벡터로 변환

Google Gemini text-embedding-004 모델을 사용하여 텍스트 임베딩을 생성한다.
생성된 벡터는 pgvector에 저장되어 Graph RAG 파이프라인에서 의미 기반 검색에 활용된다.

모델 선택 근거:
  - text-embedding-004: 768차원 출력, 다국어 지원(한국어 포함), Gemini API 기본 임베딩 모델
  - pgvector의 기본 벡터 차원과 일치하여 스키마 변경 없이 바로 활용 가능
"""

import asyncio

from google import genai

from app.core.config import settings


async def generate_embedding(text: str) -> list[float]:
    """텍스트를 768차원 부동소수점 벡터로 변환한다.

    google-genai SDK의 embed_content를 사용한다. SDK 호출은 동기이므로
    이벤트 루프 블로킹을 방지하기 위해 asyncio.to_thread로 감싼다.

    Args:
        text: 임베딩할 텍스트 문자열. 빈 문자열은 허용하지 않는다.

    Returns:
        768차원 float 리스트.

    Raises:
        ValueError: 빈 텍스트가 입력된 경우.
        RuntimeError: Gemini API 호출 실패 또는 응답이 비어 있는 경우.
    """
    if not text or not text.strip():
        raise ValueError("임베딩 대상 텍스트는 비어 있을 수 없습니다.")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # SDK embed_content는 동기 메서드 — to_thread로 비동기 컨텍스트에서 실행
    result = await asyncio.to_thread(
        client.models.embed_content,
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=text,
    )

    if result.embeddings is None or len(result.embeddings) == 0:
        raise RuntimeError("Gemini 임베딩 응답이 비어 있습니다.")

    values = result.embeddings[0].values
    if not values:
        raise RuntimeError("Gemini 임베딩 벡터 값이 없습니다.")

    return list(values)
