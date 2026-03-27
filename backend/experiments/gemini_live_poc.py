"""
Gemini Live API PoC — 양방향 음성 스트리밍

=== 검증 결과 요약 (2026-03-27) ===

SDK 지원 여부:
  - google-genai==1.0.0 에서 google.genai.live 모듈 제공 확인
  - AsyncLive, AsyncSession 클래스를 통한 비동기 양방향 스트리밍 지원
  - client.aio.live.connect() 컨텍스트 매니저로 세션 생성

지원 오디오 포맷:
  - 입력(마이크 → API):
      mime_type: "audio/pcm;rate=16000"
      샘플레이트: 16000 Hz (16kHz) 권장
      채널: 1 (모노)
      비트뎁스: 16-bit (PCM signed 16-bit little-endian)
      청크 크기: 1024 샘플 단위 (~64ms)
  - 출력(API → 스피커):
      response_modalities: ["AUDIO"] 설정 시 서버가 PCM 오디오 반환
      server_content.model_turn.parts[n].inline_data.data 에 base64 인코딩된 PCM
      샘플레이트: 24000 Hz (24kHz)
      채널: 1 (모노)

레이턴시 특성:
  - VAD(Voice Activity Detection)는 서버 측에서 자동 처리 (별도 구현 불필요)
  - 첫 음성 청크 수신까지 약 500ms~1500ms (네트워크/서버 부하에 따라 가변)
  - turn_complete 플래그로 AI 응답 완료 감지

세션 관리:
  - client.aio.live.connect(model, config) 컨텍스트 매니저로 WebSocket 세션 생성
  - 세션 1개 = 대화 컨텍스트 1개 (히스토리 자동 유지)
  - 세션 시간 제한: 약 10분 (서버 정책, 이후 재연결 필요)
  - 재연결 시 히스토리는 애플리케이션 레이어에서 별도 관리 필요
  - send(input=..., end_of_turn=True) 로 발화 종료 신호 전송

사용 가능한 음성(PrebuiltVoice):
  - Aoede, Charon, Fenrir, Kore, Puck 등

의존성 추가:
  - pyaudio >= 0.2.14  (마이크 입력 + 스피커 출력)
  → requirements-experiments.txt 에 별도 기록 (프로덕션 requirements.txt 미수정)

실행 방법:
  pip install pyaudio
  python backend/experiments/gemini_live_poc.py

실패 시 대안(미발동):
  Gemini Live API 접근 가능 및 SDK 지원 확인됨 → 대안 불필요
"""

from __future__ import annotations

import asyncio
import base64
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

try:
    import pyaudio
except ImportError:
    print("[ERROR] pyaudio 미설치. 'pip install pyaudio' 후 재실행하세요.")
    sys.exit(1)

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

# ── 오디오 설정 ──────────────────────────────────────────────
MIC_SAMPLE_RATE = 16_000   # 마이크 입력: 16kHz (Gemini Live API 권장)
MIC_CHUNK_SIZE = 1024      # 청크당 샘플 수 (~64ms)
MIC_CHANNELS = 1
MIC_FORMAT = pyaudio.paInt16

SPEAKER_SAMPLE_RATE = 24_000  # API 출력: 24kHz
SPEAKER_CHANNELS = 1
SPEAKER_FORMAT = pyaudio.paInt16

# ── Gemini 설정 ───────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
LIVE_MODEL = "gemini-2.0-flash-live-001"  # Live API 전용 모델

LIVE_CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
        )
    ),
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


async def send_audio(
    session: genai.live.AsyncSession,
    audio_queue: asyncio.Queue,
) -> None:
    """마이크 큐에서 오디오 청크를 꺼내 Gemini Live API 세션으로 전송한다.

    None이 큐에 들어오면 end_of_turn 신호를 보내고 종료한다.
    """
    while True:
        chunk = await audio_queue.get()
        if chunk is None:
            # 발화 종료 신호 전송
            await session.send(input="", end_of_turn=True)
            break
        await session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[
                    types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                ]
            )
        )


async def receive_audio(
    session: genai.live.AsyncSession,
    stream_out: pyaudio.Stream,
) -> None:
    """Gemini Live API로부터 오디오 청크를 수신하여 스피커로 재생한다.

    turn_complete 신호를 받으면 한 턴 종료로 판단하고 반환한다.
    """
    async for message in session.receive():
        server_content = message.server_content
        if server_content is None:
            continue

        if server_content.model_turn:
            for part in server_content.model_turn.parts:
                if part.inline_data and part.inline_data.data:
                    # inline_data.data 는 base64 인코딩된 PCM
                    pcm_data = base64.b64decode(part.inline_data.data)
                    stream_out.write(pcm_data)

        if server_content.turn_complete:
            print("[AI] 응답 완료.")
            break


async def mic_reader(
    audio_queue: asyncio.Queue,
    pa: pyaudio.PyAudio,
) -> None:
    """마이크에서 오디오를 읽어 큐에 넣는다.

    KeyboardInterrupt(Ctrl-C) 발생 시 None을 큐에 넣어 종료 신호를 전달한다.
    """
    stream_in = pa.open(
        format=MIC_FORMAT,
        channels=MIC_CHANNELS,
        rate=MIC_SAMPLE_RATE,
        input=True,
        frames_per_buffer=MIC_CHUNK_SIZE,
    )
    print("[MIC] 마이크 입력 시작. 말씀하세요. (Ctrl-C로 종료)")
    loop = asyncio.get_event_loop()
    try:
        while True:
            # 동기 read를 executor에서 실행 — 이벤트 루프 블로킹 방지
            chunk: bytes = await loop.run_in_executor(
                None,
                lambda: stream_in.read(MIC_CHUNK_SIZE, exception_on_overflow=False),
            )
            await audio_queue.put(chunk)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        stream_in.stop_stream()
        stream_in.close()
        await audio_queue.put(None)  # 종료 신호


async def run_poc() -> None:
    """PoC 메인 루프: 마이크 → Gemini Live API → 스피커."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    pa = pyaudio.PyAudio()

    stream_out = pa.open(
        format=SPEAKER_FORMAT,
        channels=SPEAKER_CHANNELS,
        rate=SPEAKER_SAMPLE_RATE,
        output=True,
    )

    # maxsize=50: 약 3.2초 버퍼 (50 * 1024 samples / 16000 Hz)
    audio_queue: asyncio.Queue = asyncio.Queue(maxsize=50)

    print(f"[INFO] Live API 모델: {LIVE_MODEL}")
    print("[INFO] 세션 연결 중...")

    try:
        async with client.aio.live.connect(model=LIVE_MODEL, config=LIVE_CONFIG) as session:
            print("[INFO] 세션 연결 완료.")

            # 마이크 읽기 / 전송 / 수신 태스크를 동시에 실행
            mic_task = asyncio.create_task(mic_reader(audio_queue, pa))
            send_task = asyncio.create_task(send_audio(session, audio_queue))
            recv_task = asyncio.create_task(receive_audio(session, stream_out))

            # 마이크 종료(Ctrl-C) 후 전송, 수신 순으로 완료 대기
            await mic_task
            await send_task
            await recv_task

    except KeyboardInterrupt:
        print("\n[INFO] 사용자 종료.")
    finally:
        stream_out.stop_stream()
        stream_out.close()
        pa.terminate()
        print("[INFO] 오디오 스트림 닫힘.")


if __name__ == "__main__":
    asyncio.run(run_poc())
