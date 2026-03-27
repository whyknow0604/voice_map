import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useVoiceWebSocket } from "@/hooks/useVoiceWebSocket";
import "@/styles/VoicePage.css";

// BE가 기대하는 오디오 포맷
const TARGET_SAMPLE_RATE = 16000;
const TARGET_CHANNELS = 1;
// AI 응답 오디오 포맷
const AI_RESPONSE_SAMPLE_RATE = 24000;

type ConversationState = "connecting" | "listening" | "ai_speaking" | "error";

function generateSessionId(): string {
  return crypto.randomUUID();
}

function float32ToPcm16(float32Array: Float32Array): ArrayBuffer {
  const buffer = new ArrayBuffer(float32Array.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < float32Array.length; i++) {
    const sample = float32Array[i] ?? 0;
    const clamped = Math.max(-1, Math.min(1, sample));
    view.setInt16(i * 2, clamped * 32767, true);
  }
  return buffer;
}

function buildWavFromPcm(pcmBuffer: ArrayBuffer, sampleRate: number): ArrayBuffer {
  const pcmBytes = pcmBuffer.byteLength;
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = (sampleRate * numChannels * bitsPerSample) / 8;
  const blockAlign = (numChannels * bitsPerSample) / 8;
  const wavHeader = new ArrayBuffer(44);
  const view = new DataView(wavHeader);

  view.setUint8(0, 0x52); view.setUint8(1, 0x49); view.setUint8(2, 0x46); view.setUint8(3, 0x46);
  view.setUint32(4, 36 + pcmBytes, true);
  view.setUint8(8, 0x57); view.setUint8(9, 0x41); view.setUint8(10, 0x56); view.setUint8(11, 0x45);
  view.setUint8(12, 0x66); view.setUint8(13, 0x6d); view.setUint8(14, 0x74); view.setUint8(15, 0x20);
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  view.setUint8(36, 0x64); view.setUint8(37, 0x61); view.setUint8(38, 0x74); view.setUint8(39, 0x61);
  view.setUint32(40, pcmBytes, true);

  const wavBuffer = new Uint8Array(44 + pcmBytes);
  wavBuffer.set(new Uint8Array(wavHeader), 0);
  wavBuffer.set(new Uint8Array(pcmBuffer), 44);
  return wavBuffer.buffer;
}

export default function VoicePage() {
  const navigate = useNavigate();
  const [convState, setConvState] = useState<ConversationState>("connecting");
  const [micPermission, setMicPermission] = useState<"unknown" | "granted" | "denied">("unknown");
  const [transcript, setTranscript] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const sessionIdRef = useRef<string>(generateSessionId());
  const wsToken = localStorage.getItem("access_token") ?? "";
  const wsUrl = `/ws/voice?token=${encodeURIComponent(wsToken)}&session_id=${encodeURIComponent(sessionIdRef.current)}`;

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const isStreamingRef = useRef(false);
  const playbackContextRef = useRef<AudioContext | null>(null);
  // 오디오 청크 순차 재생을 위한 스케줄링 시간
  const nextPlayTimeRef = useRef(0);

  const handleAudio = useCallback(async (base64Pcm: string) => {
    try {
      setConvState("ai_speaking");
      const binaryString = atob(base64Pcm);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const wavBuffer = buildWavFromPcm(bytes.buffer, AI_RESPONSE_SAMPLE_RATE);
      if (!playbackContextRef.current || playbackContextRef.current.state === "closed") {
        playbackContextRef.current = new AudioContext();
        nextPlayTimeRef.current = 0;
      }
      const ctx = playbackContextRef.current;
      const audioBuffer = await ctx.decodeAudioData(wavBuffer);
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);

      // 이전 청크 재생이 끝난 후에 시작하도록 스케줄링
      const now = ctx.currentTime;
      const startTime = Math.max(now, nextPlayTimeRef.current);
      source.start(startTime);
      nextPlayTimeRef.current = startTime + audioBuffer.duration;
    } catch (err) {
      console.error("오디오 재생 실패:", err);
    }
  }, []);

  const handleTranscript = useCallback((content: string) => {
    setTranscript((prev) => prev + content);
  }, []);

  const handleTurnComplete = useCallback(() => {
    setConvState("listening");
    nextPlayTimeRef.current = 0;
  }, []);

  const handleWsError = useCallback((msg: string) => {
    setErrorMsg(msg);
    setConvState("error");
  }, []);

  const handleInterrupted = useCallback(() => {
    // 사용자 발화 감지 시 현재 재생 중인 AI 오디오를 즉시 중단
    if (playbackContextRef.current && playbackContextRef.current.state !== "closed") {
      void playbackContextRef.current.close();
      playbackContextRef.current = null;
    }
    nextPlayTimeRef.current = 0;
    setConvState("listening");
  }, []);

  const { status, sendAudioChunk, sendModeSwitch, disconnect } = useVoiceWebSocket(wsUrl, {
    onAudio: handleAudio,
    onTranscript: handleTranscript,
    onTurnComplete: handleTurnComplete,
    onError: handleWsError,
    onInterrupted: handleInterrupted,
  });

  // 마이크 오디오 스트리밍 시작
  const startStreaming = useCallback(async () => {
    if (isStreamingRef.current) return;
    if (!mediaStreamRef.current) return;

    try {
      if (audioContextRef.current) {
        await audioContextRef.current.close();
      }
      const ctx = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE });
      audioContextRef.current = ctx;

      const source = ctx.createMediaStreamSource(mediaStreamRef.current);
      sourceNodeRef.current = source;

      // eslint-disable-next-line @typescript-eslint/no-deprecated
      const processor = ctx.createScriptProcessor(4096, TARGET_CHANNELS, TARGET_CHANNELS);
      scriptProcessorRef.current = processor;

      processor.onaudioprocess = (event: AudioProcessingEvent) => {
        if (!isStreamingRef.current) return;
        const channelData = event.inputBuffer.getChannelData(0);
        const pcm16 = float32ToPcm16(channelData);
        sendAudioChunk(pcm16);
      };

      source.connect(processor);
      processor.connect(ctx.destination);

      isStreamingRef.current = true;
      setConvState("listening");
      setErrorMsg("");
    } catch (err) {
      console.error("오디오 스트리밍 시작 실패:", err);
      setErrorMsg("마이크 연결에 실패했습니다.");
      setConvState("error");
    }
  }, [sendAudioChunk]);

  // 마이크 권한 요청
  const requestMicPermission = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: TARGET_CHANNELS,
          sampleRate: TARGET_SAMPLE_RATE,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      mediaStreamRef.current = stream;
      setMicPermission("granted");
      setErrorMsg("");
    } catch (err) {
      console.error("마이크 권한 거부:", err);
      setMicPermission("denied");
    }
  }, []);

  // 마이크 권한 획득 시 자동 요청
  useEffect(() => {
    void requestMicPermission();
    return () => {
      isStreamingRef.current = false;
      if (scriptProcessorRef.current) {
        scriptProcessorRef.current.disconnect();
        scriptProcessorRef.current = null;
      }
      if (sourceNodeRef.current) {
        sourceNodeRef.current.disconnect();
        sourceNodeRef.current = null;
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop());
        mediaStreamRef.current = null;
      }
      if (audioContextRef.current) {
        void audioContextRef.current.close();
        audioContextRef.current = null;
      }
      if (playbackContextRef.current) {
        void playbackContextRef.current.close();
        playbackContextRef.current = null;
      }
    };
  }, [requestMicPermission]);

  // 마이크 + WebSocket 모두 준비되면 자동으로 스트리밍 시작
  useEffect(() => {
    if (micPermission === "granted" && status === "open" && !isStreamingRef.current) {
      void startStreaming();
    }
  }, [micPermission, status, startStreaming]);

  const handleModeSwitch = useCallback(() => {
    isStreamingRef.current = false;
    sendModeSwitch("text");
    navigate("/chat");
  }, [sendModeSwitch, navigate]);

  const handleEndSession = useCallback(() => {
    isStreamingRef.current = false;
    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current = null;
    }
    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }
    if (audioContextRef.current) {
      void audioContextRef.current.close();
      audioContextRef.current = null;
    }
    disconnect();
    setConvState("connecting");
    navigate("/conversations");
  }, [disconnect, navigate]);

  const stateLabel: Record<ConversationState, string> = {
    connecting: "연결 중...",
    listening: "듣고 있습니다...",
    ai_speaking: "AI가 말하고 있습니다...",
    error: "오류가 발생했습니다",
  };

  if (micPermission === "denied") {
    return (
      <div className="voice-page">
        <header className="voice-header">
          <button className="voice-mode-toggle-btn" onClick={() => navigate("/chat")}>
            텍스트
          </button>
          <h1 className="voice-header-title">Voice Map</h1>
          <div style={{ width: 60 }} />
        </header>
        <div className="voice-permission-error">
          <div className="voice-permission-error__icon" aria-hidden="true">
            🎤
          </div>
          <p className="voice-permission-error__title">마이크 접근 권한이 필요합니다</p>
          <p className="voice-permission-error__desc">
            음성 기능을 사용하려면 마이크 권한을 허용해주세요.
          </p>
          <button
            className="voice-permission-error__retry-btn"
            onClick={() => void requestMicPermission()}
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="voice-page">
      <header className="voice-header">
        <button className="voice-mode-toggle-btn" onClick={handleModeSwitch}>
          텍스트
        </button>
        <h1 className="voice-header-title">Voice Map</h1>
        <span className={`voice-status-badge voice-status-badge--${status}`}>
          {status === "open" ? "연결됨" : status === "connecting" ? "연결 중" : "연결 끊김"}
        </span>
      </header>

      <main className="voice-main">
        <p className="voice-state-label">{stateLabel[convState]}</p>

        <div
          className={[
            "voice-indicator",
            convState === "listening" && "voice-indicator--listening",
            convState === "ai_speaking" && "voice-indicator--ai-speaking",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {convState === "ai_speaking" ? (
            <span className="voice-wave-icon" aria-hidden="true">
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
            </span>
          ) : (
            <svg
              className="voice-record-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          )}
        </div>

        <p className="voice-hint">
          {convState === "listening"
            ? "자유롭게 말씀하세요"
            : convState === "ai_speaking"
            ? "잠시 기다려주세요"
            : convState === "connecting"
            ? "마이크와 서버에 연결하고 있습니다"
            : ""}
        </p>

        {transcript && (
          <div className="voice-transcript">
            <p className="voice-transcript__label">트랜스크립트</p>
            <p className="voice-transcript__text">{transcript}</p>
          </div>
        )}

        {errorMsg && (
          <div className="voice-error-banner" role="alert">
            오류: {errorMsg}
          </div>
        )}

        <button className="voice-end-session-btn" onClick={handleEndSession}>
          대화 종료
        </button>
      </main>
    </div>
  );
}
