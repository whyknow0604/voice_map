import { useEffect, useRef, useCallback, useState } from "react";

export type WsStatus = "connecting" | "open" | "closed" | "error";

export interface WsMessage {
  type: "token" | "done" | "error";
  content: string;
}

interface UseWebSocketOptions {
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (msg: string) => void;
}

const BACKOFF_BASE_MS = 1000;
const BACKOFF_MAX_MS = 30000;

export function useWebSocket(url: string, options: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<WsStatus>("closed");
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const optionsRef = useRef(options);
  const reconnectAttemptRef = useRef(0);
  const isMountedRef = useRef(true);
  optionsRef.current = options;

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMountedRef.current) return;
      reconnectAttemptRef.current = 0;
      setStatus("open");
    };

    ws.onmessage = (event: MessageEvent<string>) => {
      let parsed: WsMessage;
      try {
        parsed = JSON.parse(event.data) as WsMessage;
      } catch {
        return;
      }
      if (parsed.type === "token") {
        optionsRef.current.onToken(parsed.content);
      } else if (parsed.type === "done") {
        optionsRef.current.onDone();
      } else if (parsed.type === "error") {
        optionsRef.current.onError(parsed.content);
      }
    };

    ws.onerror = () => {
      if (!isMountedRef.current) return;
      setStatus("error");
    };

    ws.onclose = () => {
      if (!isMountedRef.current) return;
      setStatus("closed");
      wsRef.current = null;
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

  const send = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "message", content: text }));
    }
  }, []);

  const disconnect = useCallback(() => {
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
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { status, send };
}
