import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useVoiceWebSocket } from "@/hooks/useVoiceWebSocket";
import "@/styles/VoicePage.css";

// BE가 기대하는 오디오 포맷
const TARGET_SAMPLE_RATE = 16000;
const TARGET_CHANNELS = 1;
// AI 응답 오디오 포맷
const AI_RESPONSE_SAMPLE_RATE = 24000;

type RecordingState = "idle" | "recording" | "ai_responding";

function generateSessionId(): string {
  return crypto.randomUUID();
}

/**
 * Float32 샘플을 PCM 16-bit little-endian ArrayBuffer로 변환
 */
function float32ToPcm16(float32Array: Float32Array): ArrayBuffer {
  const buffer = new ArrayBuffer(float32Array.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < float32Array.length; i++) {
    const sample = float32Array[i] ?? 0;
    const clamped = Math.max(-1, Math.min(1, sample));
    // -1..1 → -32768..32767
    view.setInt16(i * 2, clamped * 32767, true /* little-endian */);
  }
  return buffer;
}

/**
 * base64 인코딩된 PCM 24kHz 데이터를 디코딩하여 재생
 * AudioContext.decodeAudioData는 PCM raw 데이터를 직접 처리하지 않으므로
 * WAV 헤더를 붙여서 디코딩한다.
 */
function buildWavFromPcm(pcmBuffer: ArrayBuffer, sampleRate: number): ArrayBuffer {
  const pcmBytes = pcmBuffer.byteLength;
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = (sampleRate * numChannels * bitsPerSample) / 8;
  const blockAlign = (numChannels * bitsPerSample) / 8;
  const wavHeader = new ArrayBuffer(44);
  const view = new DataView(wavHeader);

  // RIFF chunk
  view.setUint8(0, 0x52); // 'R'
  view.setUint8(1, 0x49); // 'I'
  view.setUint8(2, 0x46); // 'F'
  view.setUint8(3, 0x46); // 'F'
  view.setUint32(4, 36 + pcmBytes, true);
  view.setUint8(8, 0x57);  // 'W'
  view.setUint8(9, 0x41);  // 'A'
  view.setUint8(10, 0x56); // 'V'
  view.setUint8(11, 0x45); // 'E'

  // fmt sub-chunk
  view.setUint8(12, 0x66); // 'f'
  view.setUint8(13, 0x6d); // 'm'
  view.setUint8(14, 0x74); // 't'
  view.setUint8(15, 0x20); // ' '
  view.setUint32(16, 16, true);          // Subchunk1Size (PCM)
  view.setUint16(20, 1, true);           // AudioFormat (1 = PCM)
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);

  // data sub-chunk
  view.setUint8(36, 0x64); // 'd'
  view.setUint8(37, 0x61); // 'a'
  view.setUint8(38, 0x74); // 't'
  view.setUint8(39, 0x61); // 'a'
  view.setUint32(40, pcmBytes, true);

  // WAV = header + PCM data
  const wavBuffer = new Uint8Array(44 + pcmBytes);
  wavBuffer.set(new Uint8Array(wavHeader), 0);
  wavBuffer.set(new Uint8Array(pcmBuffer), 44);
  return wavBuffer.buffer;
}

export default function VoicePage() {
  const navigate = useNavigate();
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [micPermission, setMicPermission] = useState<"unknown" | "granted" | "denied">("unknown");
  const [transcript, setTranscript] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const sessionIdRef = useRef<string>(generateSessionId());
  const wsToken = localStorage.getItem("access_token") ?? "";
  const wsUrl = `/ws/voice?token=${encodeURIComponent(wsToken)}&session_id=${encodeURIComponent(sessionIdRef.current)}`;

  // 오디오 녹음 관련 refs
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  // 미디어 스트림은 마이크 권한 획득 후 재사용
  const isRecordingRef = useRef(false);

  // AI 오디오 재생용 AudioContext (녹음과 분리)
  const playbackContextRef = useRef<AudioContext | null>(null);

  const handleAudio = useCallback(async (base64Pcm: string) => {
    try {
      // base64 → binary
      const binaryString = atob(base64Pcm);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      // WAV 헤더 추가 후 디코딩
      const wavBuffer = buildWavFromPcm(bytes.buffer, AI_RESPONSE_SAMPLE_RATE);

      if (!playbackContextRef.current || playbackContextRef.current.state === "closed") {
        playbackContextRef.current = new AudioContext();
      }
      const ctx = playbackContextRef.current;
      const audioBuffer = await ctx.decodeAudioData(wavBuffer);
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);
      source.start();
    } catch (err) {
      console.error("오디오 재생 실패:", err);
    }
  }, []);

  const handleTranscript = useCallback((content: string) => {
    setTranscript((prev) => prev + content);
  }, []);

  const handleTurnComplete = useCallback(() => {
    setRecordingState("idle");
  }, []);

  const handleWsError = useCallback((msg: string) => {
    setErrorMsg(msg);
    setRecordingState("idle");
  }, []);

  const { status, sendAudioChunk, sendEndOfTurn, sendModeSwitch } = useVoiceWebSocket(wsUrl, {
    onAudio: handleAudio,
    onTranscript: handleTranscript,
    onTurnComplete: handleTurnComplete,
    onError: handleWsError,
  });

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

  // 컴포넌트 마운트 시 마이크 권한 요청
  useEffect(() => {
    void requestMicPermission();
    return () => {
      // 페이지 언마운트 시 미디어 스트림 해제
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

  const startRecording = useCallback(async () => {
    if (!mediaStreamRef.current) {
      // 권한이 없으면 재요청
      await requestMicPermission();
      if (!mediaStreamRef.current) return;
    }
    if (isRecordingRef.current) return;

    try {
      // 기존 AudioContext 정리
      if (audioContextRef.current) {
        await audioContextRef.current.close();
      }
      const ctx = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE });
      audioContextRef.current = ctx;

      const source = ctx.createMediaStreamSource(mediaStreamRef.current);
      sourceNodeRef.current = source;

      // bufferSize 4096: 지연 vs CPU 트레이드오프 (모바일 고려)
      // eslint-disable-next-line @typescript-eslint/no-deprecated
      const processor = ctx.createScriptProcessor(4096, TARGET_CHANNELS, TARGET_CHANNELS);
      scriptProcessorRef.current = processor;

      processor.onaudioprocess = (event: AudioProcessingEvent) => {
        if (!isRecordingRef.current) return;
        const channelData = event.inputBuffer.getChannelData(0);
        const pcm16 = float32ToPcm16(channelData);
        sendAudioChunk(pcm16);
      };

      source.connect(processor);
      processor.connect(ctx.destination);

      isRecordingRef.current = true;
      setRecordingState("recording");
      setTranscript("");
      setErrorMsg("");
    } catch (err) {
      console.error("녹음 시작 실패:", err);
      setErrorMsg("녹음을 시작할 수 없습니다.");
    }
  }, [requestMicPermission, sendAudioChunk]);

  const stopRecording = useCallback(() => {
    if (!isRecordingRef.current) return;
    isRecordingRef.current = false;

    // ScriptProcessorNode 연결 해제
    if (scriptProcessorRef.current) {
      scriptProcessorRef.current.disconnect();
      scriptProcessorRef.current.onaudioprocess = null;
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

    // 발화 종료를 BE에 알림
    sendEndOfTurn();
    setRecordingState("ai_responding");
  }, [sendEndOfTurn]);

  const handleRecordButtonPress = useCallback(() => {
    if (recordingState === "idle") {
      void startRecording();
    } else if (recordingState === "recording") {
      stopRecording();
    }
    // ai_responding 중에는 버튼 비활성화
  }, [recordingState, startRecording, stopRecording]);

  const handleModeSwitch = useCallback(() => {
    // 녹음 중이면 먼저 중단
    if (isRecordingRef.current) {
      stopRecording();
    }
    sendModeSwitch("text");
    navigate("/chat");
  }, [stopRecording, sendModeSwitch, navigate]);

  const isButtonDisabled =
    micPermission !== "granted" || status !== "open" || recordingState === "ai_responding";

  const stateLabel: Record<RecordingState, string> = {
    idle: status === "open" ? "버튼을 눌러 말씀하세요" : "연결 중...",
    recording: "듣고 있습니다...",
    ai_responding: "AI가 응답 중입니다...",
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
            브라우저 주소창의 자물쇠 아이콘을 클릭하거나 브라우저 설정에서 마이크 권한을 허용하세요.
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
          {status === "open"
            ? "연결됨"
            : status === "connecting"
            ? "연결 중"
            : "연결 끊김"}
        </span>
      </header>

      <main className="voice-main">
        <p className="voice-state-label">{stateLabel[recordingState]}</p>

        <button
          className={[
            "voice-record-btn",
            recordingState === "recording" && "voice-record-btn--recording",
            recordingState === "ai_responding" && "voice-record-btn--ai-responding",
          ]
            .filter(Boolean)
            .join(" ")}
          onClick={handleRecordButtonPress}
          disabled={isButtonDisabled}
          aria-label={
            recordingState === "recording"
              ? "녹음 중지"
              : recordingState === "ai_responding"
              ? "AI 응답 중"
              : "녹음 시작"
          }
          aria-pressed={recordingState === "recording"}
        >
          {recordingState === "recording" && <span className="voice-stop-icon" aria-hidden="true" />}
          {recordingState === "ai_responding" && (
            <span className="voice-wave-icon" aria-hidden="true">
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
            </span>
          )}
          {recordingState === "idle" && (
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
        </button>

        <p className="voice-hint">
          {recordingState === "recording"
            ? "말씀이 끝나면 버튼을 다시 누르세요"
            : recordingState === "ai_responding"
            ? "잠시 기다려주세요"
            : "버튼을 누르고 말씀하세요"}
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
      </main>
    </div>
  );
}
