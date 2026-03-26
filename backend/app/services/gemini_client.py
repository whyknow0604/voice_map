"""
Gemini API 클라이언트

스트리밍 텍스트 대화를 위한 래퍼. Sprint 1에서는 텍스트 채팅만 지원하며,
Sprint 2에서 Gemini Live API(양방향 음성)로 확장 예정.

사용 예시:
    client = GeminiClient()
    async for chunk in client.generate_stream(messages, system_prompt):
        print(chunk, end="", flush=True)
"""

from collections.abc import AsyncGenerator

from google import genai
from google.genai import types

from app.core.config import settings


class GeminiClient:
    """Gemini API와의 통신을 담당하는 클라이언트."""

    def __init__(self) -> None:
        # google-genai 1.x: Client 생성 시 API 키 전달
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_MODEL

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> AsyncGenerator[str, None]:
        """대화 히스토리를 기반으로 스트리밍 응답을 생성한다.

        Args:
            messages: 대화 히스토리. 각 항목은 {"role": "user"|"model", "text": "..."}
                      형식. 마지막 항목이 현재 사용자 메시지여야 한다.
            system_prompt: Gemini에 전달할 시스템 프롬프트 문자열.

        Yields:
            응답 텍스트 청크. 빈 청크는 건너뜀.
        """
        contents = _build_contents(messages)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
        )

        # generate_content_stream은 동기 이터레이터를 반환하므로 async generator로 래핑
        response_iter = self._client.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=config,
        )

        for chunk in response_iter:
            if chunk.text:
                yield chunk.text


def _build_contents(messages: list[dict[str, str]]) -> list[types.Content]:
    """내부 메시지 리스트를 Gemini SDK의 Content 리스트로 변환한다.

    Args:
        messages: {"role": "user"|"model", "text": "..."} 형식의 메시지 목록.

    Returns:
        Gemini SDK가 요구하는 Content 객체 리스트.
    """
    contents: list[types.Content] = []
    for msg in messages:
        role = msg["role"]  # "user" 또는 "model"
        text = msg["text"]
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part(text=text)],
            )
        )
    return contents
