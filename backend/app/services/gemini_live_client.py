"""Gemini Live API 클라이언트 — 양방향 음성 스트리밍."""

from __future__ import annotations

import base64
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Union

from google import genai
from google.genai import live as genai_live
from google.genai import types

from app.core.config import settings

# websockets 기본 ping_interval=20, ping_timeout=20이 Gemini Live 세션을
# 조기 종료시킴. SDK의 ws_connect를 래핑하여 keepalive를 비활성화.
_original_ws_connect = genai_live.ws_connect


class _NoPingConnect(_original_ws_connect):  # type: ignore[misc]
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("ping_interval", None)
        kwargs.setdefault("ping_timeout", None)
        super().__init__(*args, **kwargs)


genai_live.ws_connect = _NoPingConnect


@dataclass
class AudioChunk:
    """오디오 응답 청크 — base64 인코딩된 PCM 24kHz."""

    data: str  # base64 encoded PCM audio


@dataclass
class TranscriptChunk:
    """텍스트 트랜스크립트 청크."""

    content: str


@dataclass
class TurnComplete:
    """AI 응답 완료 신호."""


# GeminiLiveClient.stream() 의 yield 타입
LiveChunk = Union[AudioChunk, TranscriptChunk, TurnComplete]


class GeminiLiveClient:
    """Gemini Live API 비동기 클라이언트.

    오디오 청크를 Gemini Live API로 전송하고, 응답(오디오/트랜스크립트)을
    AsyncGenerator로 스트리밍한다.

    사용 예:
        client = GeminiLiveClient()
        async with client.connect() as session:
            await session.send_audio(pcm_bytes)
            await session.send_end_of_turn()
            async for chunk in session.receive():
                ...
    """

    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model = settings.GEMINI_LIVE_MODEL

    def _build_config(self) -> types.LiveConnectConfig:
        """Live API 연결 설정 빌드.

        오디오 + 텍스트 트랜스크립트를 모두 수신하도록 설정.
        """
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                )
            ),
            # TODO: SDK 업그레이드 후 AudioTranscriptionConfig 추가
            # output_audio_transcription, input_audio_transcription
            system_instruction=types.Content(
                parts=[
                    types.Part(
                        text=(
                            "당신은 Voice Map의 AI 도우미입니다. "
                            "사용자의 아이디어를 소크라테스식 질문으로 구조화해주세요. "
                            "한국어로 대화합니다."
                        )
                    )
                ],
                role="user",
            ),
        )

    async def stream(
        self,
        audio_chunks: list[bytes],
        *,
        send_end_of_turn: bool = True,
    ) -> AsyncGenerator[LiveChunk, None]:
        """오디오 청크 목록을 Gemini Live API로 전송하고 응답을 스트리밍한다.

        Args:
            audio_chunks: PCM 16kHz 16-bit 모노 오디오 청크 목록
            send_end_of_turn: True이면 전송 후 end_of_turn 신호 발송
        """
        config = self._build_config()
        async with self._client.aio.live.connect(model=self._model, config=config) as session:
            # 오디오 청크 전송
            for chunk in audio_chunks:
                await session.send_realtime_input(
                    audio=types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                )

            if send_end_of_turn:
                await session.send_client_content(turn_complete=True)

            # 응답 수신
            async for message in session.receive():
                server_content = message.server_content
                if server_content is None:
                    continue

                if server_content.model_turn:
                    for part in server_content.model_turn.parts:
                        # 오디오 응답 — inline_data.data는 bytes, base64로 변환
                        if part.inline_data and part.inline_data.data:
                            audio_b64 = base64.b64encode(
                                part.inline_data.data
                            ).decode("ascii")
                            yield AudioChunk(data=audio_b64)

                        # 텍스트 트랜스크립트 (있는 경우)
                        if part.text:
                            yield TranscriptChunk(content=part.text)

                if server_content.turn_complete:
                    yield TurnComplete()
                    break

    async def stream_with_session(
        self,
        session: genai.live.AsyncSession,
        audio_chunk: bytes,
    ) -> None:
        """기존 세션에 오디오 청크를 전송한다.

        세션을 외부에서 관리하는 경우(WebSocket 연결 유지 중) 사용.
        """
        await session.send_realtime_input(
            audio=types.Blob(data=audio_chunk, mime_type="audio/pcm;rate=16000")
        )

    async def send_end_of_turn(self, session: genai.live.AsyncSession) -> None:
        """발화 종료 신호를 전송한다."""
        await session.send_client_content(end_of_turn=True)

    def connect(self) -> genai.live.AsyncLive:
        """새 Live API 세션 컨텍스트 매니저를 반환한다.

        WebSocket 핸들러에서 세션 수명을 직접 관리할 때 사용.
        사용 예: async with client.connect() as session: ...
        """
        config = self._build_config()
        return self._client.aio.live.connect(model=self._model, config=config)
