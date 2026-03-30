import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useVoiceWebSocket } from "@/hooks/useVoiceWebSocket";
import Sidebar from "@/components/Sidebar";
import "@/styles/VoicePage.css";

// BE가 기대하는 오디오 포맷
const TARGET_SAMPLE_RATE = 16000;
const TARGET_CHANNELS = 1;
// AI 응답 오디오 포맷
const AI_RESPONSE_SAMPLE_RATE = 24000;

type ConversationState = "connecting" | "listening" | "ai_speaking" | "error";

interface ConversationTurn {
  id: string;
  role: "user" | "ai";
  text: string;
}

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
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [currentAiText, setCurrentAiText] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const conversationEndRef = useRef<HTMLDivElement>(null);

  const sessionIdRef = useRef<string>(generateSessionId());
  const wsToken = localStorage.getItem("access_token") ?? "";
  const wsUrl = `/ws/voice?token=${encodeURIComponent(wsToken)}&session_id=${encodeURIComponent(sessionIdRef.current)}`;

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const isStreamingRef = useRef(false);
  const playbackContextRef = useRef<AudioContext | null>(null);
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

      const now = ctx.currentTime;
      const startTime = Math.max(now, nextPlayTimeRef.current);
      source.start(startTime);
      nextPlayTimeRef.current = startTime + audioBuffer.duration;
    } catch (err) {
      console.error("오디오 재생 실패:", err);
    }
  }, []);

  const handleTranscript = useCallback((content: string) => {
    setCurrentAiText((prev) => prev + content);
  }, []);

  const handleTurnComplete = useCallback(() => {
    setConvState("listening");
    nextPlayTimeRef.current = 0;
    // 완성된 AI 응답을 turns에 추가
    setCurrentAiText((text) => {
      if (text) {
        setTurns((prev) => [
          ...prev,
          { id: crypto.randomUUID(), role: "ai", text },
        ]);
      }
      return "";
    });
  }, []);

  const handleWsError = useCallback((msg: string) => {
    setErrorMsg(msg);
    setConvState("error");
  }, []);

  const handleInterrupted = useCallback(() => {
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

  useEffect(() => {
    if (micPermission === "granted" && status === "open" && !isStreamingRef.current) {
      void startStreaming();
    }
  }, [micPermission, status, startStreaming]);

  // 새 turn이 추가되면 스크롤
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, currentAiText]);

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
    listening: "듣고 있어요...",
    ai_speaking: "AI가 응답하고 있어요...",
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
          <div className="voice-permission-error__icon" aria-hidden="true">🎤</div>
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

  const hasConversation = turns.length > 0 || currentAiText;

  return (
    <div className="voice-page">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Header */}
      <header className="voice-header">
        <button
          className="voice-mode-toggle-btn"
          onClick={() => setSidebarOpen(true)}
          aria-label="메뉴 열기"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="20" height="20" aria-hidden="true">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <h1 className="voice-header-title">Voice Map</h1>
        <button className="voice-mode-toggle-btn" onClick={handleModeSwitch}>
          텍스트
        </button>
      </header>

      {/* Main conversation area */}
      <main className="voice-main">
        {hasConversation ? (
          <div className="voice-conversation">
            {turns.map((turn) =>
              turn.role === "user" ? (
                <div key={turn.id} className="voice-turn-user">
                  <div className="voice-bubble-user">{turn.text}</div>
                </div>
              ) : (
                <div key={turn.id} className="voice-turn-ai">
                  <div className="voice-ai-label">
                    <div className="voice-ai-icon">
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5z"/>
                      </svg>
                    </div>
                    <span className="voice-ai-label-text">Voice Map Intelligence</span>
                  </div>
                  <p className="voice-bubble-ai">{turn.text}</p>
                </div>
              )
            )}

            {/* Streaming AI response */}
            {currentAiText && (
              <div className="voice-turn-ai">
                <div className="voice-ai-label">
                  <div className="voice-ai-icon">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5z"/>
                    </svg>
                  </div>
                  <span className="voice-ai-label-text">Voice Map Intelligence</span>
                </div>
                <p className="voice-bubble-ai">{currentAiText}</p>
              </div>
            )}

            <div ref={conversationEndRef} />
          </div>
        ) : (
          /* Center state view when no conversation yet */
          <div className="voice-state-center">
            <p className="voice-state-label">{stateLabel[convState]}</p>
          </div>
        )}
      </main>

      {/* Error banner */}
      {errorMsg && (
        <div className="voice-error-banner" role="alert" style={{ position: "fixed", top: 80, left: 16, right: 16, zIndex: 60 }}>
          오류: {errorMsg}
        </div>
      )}

      {/* Bottom interface */}
      <div className="voice-bottom">
        {/* Intelligence Orb */}
        <div className="voice-orb-container">
          <div className={`voice-orb-wrap voice-indicator--${convState}`}>
            <div className="voice-orb">
              {convState === "ai_speaking" ? (
                <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
                  <span className="voice-wave-icon" aria-hidden="true">
                    <span className="voice-wave-bar" />
                    <span className="voice-wave-bar" />
                    <span className="voice-wave-bar" />
                    <span className="voice-wave-bar" />
                    <span className="voice-wave-bar" />
                  </span>
                </div>
              ) : (
                <div className="voice-orb-inner" />
              )}
            </div>
          </div>
        </div>

        {/* Input control bar */}
        <div className="voice-control-bar">
          {/* Attach button */}
          <button className="voice-icon-btn voice-icon-btn--light" aria-label="문서 첨부">
            📄
          </button>

          {/* Text input */}
          <div className="voice-input-wrap">
            <input
              type="text"
              placeholder="아이디어를 말해보세요..."
              aria-label="텍스트 입력"
            />
            <button className="voice-input-mic-btn" aria-label="음성 입력 활성화">
              {/* mic filled */}
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
            </button>
          </div>

          {/* End / close button */}
          <button
            className="voice-icon-btn voice-icon-btn--dark"
            onClick={handleEndSession}
            aria-label="대화 종료"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16" aria-hidden="true">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
