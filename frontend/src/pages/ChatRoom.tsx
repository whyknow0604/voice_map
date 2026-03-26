import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useWebSocket } from "@/hooks/useWebSocket";
import MessageBubble, { Message } from "@/components/MessageBubble";
import "@/styles/ChatRoom.css";

let messageIdCounter = 0;
function nextId(): string {
  messageIdCounter += 1;
  return String(messageIdCounter);
}

export default function ChatRoom() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const streamingIdRef = useRef<string | null>(null);

  const wsToken = localStorage.getItem("access_token") ?? "";
  const wsUrl = `/ws/chat?token=${encodeURIComponent(wsToken)}`;

  const handleToken = useCallback((receivedToken: string) => {
    setIsTyping(false);
    setMessages((prev) => {
      if (streamingIdRef.current === null) {
        const id = nextId();
        streamingIdRef.current = id;
        return [
          ...prev,
          { id, role: "ai", content: receivedToken, timestamp: new Date(), isStreaming: true },
        ];
      }
      return prev.map((m) =>
        m.id === streamingIdRef.current
          ? { ...m, content: m.content + receivedToken }
          : m
      );
    });
  }, []);

  const handleDone = useCallback(() => {
    setIsSending(false);
    setIsTyping(false);
    if (streamingIdRef.current !== null) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === streamingIdRef.current ? { ...m, isStreaming: false } : m
        )
      );
      streamingIdRef.current = null;
    }
  }, []);

  const handleWsError = useCallback((msg: string) => {
    setIsSending(false);
    setIsTyping(false);
    streamingIdRef.current = null;
    setMessages((prev) => [
      ...prev,
      { id: nextId(), role: "ai", content: `오류: ${msg}`, timestamp: new Date() },
    ]);
  }, []);

  const { status, send } = useWebSocket(wsUrl, {
    onToken: handleToken,
    onDone: handleDone,
    onError: handleWsError,
  });

  // 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = useCallback(() => {
    const text = inputText.trim();
    if (!text || isSending || status !== "open") return;

    setMessages((prev) => [
      ...prev,
      { id: nextId(), role: "user", content: text, timestamp: new Date() },
    ]);
    setInputText("");
    setIsSending(true);
    setIsTyping(true);
    streamingIdRef.current = null;
    send(text);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [inputText, isSending, status, send]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="chatroom">
      <header className="chatroom-header">
        <h1 className="chatroom-title">Voice Map</h1>
        <span className={`chatroom-status chatroom-status--${status}`}>
          {status === "open"
            ? "연결됨"
            : status === "connecting"
            ? "연결 중"
            : "연결 끊김"}
        </span>
        <button className="logout-btn" onClick={handleLogout}>
          로그아웃
        </button>
      </header>

      <div className="message-list">
        {messages.length === 0 && (
          <div className="message-list--empty">
            <p>무슨 생각을 하고 계신가요?</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isTyping && (
          <div className="typing-indicator">
            <div className="typing-indicator__avatar">AI</div>
            <div className="typing-dots">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <textarea
          ref={textareaRef}
          className="chat-input"
          rows={1}
          placeholder="메시지를 입력하세요... (Enter로 전송, Shift+Enter 줄바꿈)"
          value={inputText}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          disabled={isSending}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={!inputText.trim() || isSending || status !== "open"}
          aria-label="전송"
        >
          <svg
            className="send-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
