import { useEffect, useRef, useCallback, useState } from "react";

export type VoiceWsStatus = "connecting" | "open" | "closed" | "error";

export interface VoiceTranscriptMessage {
  type: "transcript";
  content: string;
}

export interface VoiceAudioMessage {
  type: "audio";
  data: string; // base64 PCM 24kHz
}

export interface VoiceTurnCompleteMessage {
  type: "turn_complete";
}

export interface VoiceErrorMessage {
  type: "error";
  content: string;
}

export interface VoiceInterruptedMessage {
  type: "interrupted";
}

export type VoiceWsMessage =
  | VoiceTranscriptMessage
  | VoiceAudioMessage
  | VoiceTurnCompleteMessage
  | VoiceErrorMessage
  | VoiceInterruptedMessage;

interface UseVoiceWebSocketOptions {
  onAudio: (base64Pcm: string) => void;
  onTranscript: (content: string) => void;
  onTurnComplete: () => void;
  onError: (msg: string) => void;
  onInterrupted?: () => void;
}

const BACKOFF_BASE_MS = 1000;
const BACKOFF_MAX_MS = 30000;

export function useVoiceWebSocket(url: string, options: UseVoiceWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<VoiceWsStatus>("closed");
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const optionsRef = useRef(options);
  const reconnectAttemptRef = useRef(0);
  const isMountedRef = useRef(true);
  // 수동으로 disconnect 호출 시 재연결을 막기 위한 플래그
  const manualDisconnectRef = useRef(false);
  optionsRef.current = options;

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;
    if (manualDisconnectRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    // 기존 연결이 CONNECTING 상태로 남아있으면 정리
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus("connecting");
    const ws = new WebSocket(url);
    // 오디오 바이너리를 ArrayBuffer로 수신
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMountedRef.current) return;
      reconnectAttemptRef.current = 0;
      setStatus("open");
    };

    ws.onmessage = (event: MessageEvent) => {
      // 바이너리 메시지는 현재 스펙에 없으나 확장성을 위해 무시
      if (event.data instanceof ArrayBuffer) return;

      let parsed: VoiceWsMessage;
      try {
        parsed = JSON.parse(event.data as string) as VoiceWsMessage;
      } catch {
        return;
      }

      switch (parsed.type) {
        case "audio":
          optionsRef.current.onAudio(parsed.data);
          break;
        case "transcript":
          optionsRef.current.onTranscript(parsed.content);
          break;
        case "turn_complete":
          optionsRef.current.onTurnComplete();
          break;
        case "error":
          optionsRef.current.onError(parsed.content);
          break;
        case "interrupted":
          optionsRef.current.onInterrupted?.();
          break;
      }
    };

    ws.onerror = () => {
      if (!isMountedRef.current) return;
      if (wsRef.current !== ws) return;
      setStatus("error");
    };

    ws.onclose = () => {
      if (!isMountedRef.current) return;
      // 이미 다른 WebSocket이 wsRef를 대체했다면 무시 (StrictMode 대응)
      if (wsRef.current !== ws) return;
      setStatus("closed");
      wsRef.current = null;

      if (manualDisconnectRef.current) return;

      // Exponential backoff: 1s, 2s, 4s, ..., max 30s
      const delay = Math.min(
        BACKOFF_BASE_MS * Math.pow(2, reconnectAttemptRef.current),
        BACKOFF_MAX_MS
      );
      reconnectAttemptRef.current += 1;
      reconnectTimer.current = setTimeout(() => {
        connect();
      }, delay);
    };
  }, [url]);

  // 오디오 청크(PCM) 바이너리 전송
  const sendAudioChunk = useCallback((pcmData: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(pcmData);
    }
  }, []);

  // 발화 종료 신호 전송
  const sendEndOfTurn = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_of_turn" }));
    }
  }, []);

  // 모드 전환 신호 전송
  const sendModeSwitch = useCallback((mode: "text" | "voice") => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "mode_switch", mode }));
    }
  }, []);

  const disconnect = useCallback(() => {
    manualDisconnectRef.current = true;
    isMountedRef.current = false;
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    manualDisconnectRef.current = false;
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { status, sendAudioChunk, sendEndOfTurn, sendModeSwitch, disconnect };
}
