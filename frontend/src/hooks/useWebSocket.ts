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

export function useWebSocket(url: string, options: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<WsStatus>("closed");
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
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
      setStatus("error");
    };

    ws.onclose = () => {
      setStatus("closed");
      wsRef.current = null;
      // 3초 후 재연결
      reconnectTimer.current = setTimeout(() => {
        connect();
      }, 3000);
    };
  }, [url]);

  const send = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "message", content: text }));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { status, send };
}
