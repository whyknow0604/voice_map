import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useWebSocket } from "@/hooks/useWebSocket";
import MessageBubble, { Message } from "@/components/MessageBubble";
import Sidebar from "@/components/Sidebar";
import "@/styles/ChatRoom.css";

let messageIdCounter = 0;
function nextId(): string {
  messageIdCounter += 1;
  return String(messageIdCounter);
}

function generateSessionId(): string {
  return crypto.randomUUID();
}

const SUGGESTIONS = [
  "새 사업 아이디어 정리",
  "논문 주제 브레인스토밍",
  "프로젝트 기획 구체화",
  "회의 안건 정리",
];

export default function ChatRoom() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const streamingIdRef = useRef<string | null>(null);
  const sessionIdRef = useRef<string>(generateSessionId());

  const wsToken = localStorage.getItem("access_token") ?? "";
  const wsUrl = `/ws/chat?token=${encodeURIComponent(wsToken)}&session_id=${encodeURIComponent(sessionIdRef.current)}`;

  const handleToken = useCallback((receivedToken: string) => {
    setIsTyping(false);
    if (streamingIdRef.current === null) {
      const id = nextId();
      streamingIdRef.current = id;
      setMessages((prev) => [
        ...prev,
        { id, role: "ai" as const, content: receivedToken, timestamp: new Date(), isStreaming: true },
      ]);
    } else {
      const currentId = streamingIdRef.current;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === currentId
            ? { ...m, content: m.content + receivedToken }
            : m
        )
      );
    }
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

  const handleSuggestion = useCallback((text: string) => {
    setInputText(text);
    textareaRef.current?.focus();
  }, []);

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

  return (
    <div className="chatroom">
      {/* Background decoration */}
      <div className="chatroom-bg-decor" aria-hidden="true" />

      {/* Header */}
      <header className="chatroom-header">
        <button
          className="chatroom-history-btn"
          onClick={() => setSidebarOpen(true)}
          aria-label="메뉴 열기"
        >
          {/* menu icon */}
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        <h1 className="chatroom-title">Voice Map</h1>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span className={`chatroom-status chatroom-status--${status}`}>
            {status === "open"
              ? "연결됨"
              : status === "connecting"
              ? "연결 중"
              : "연결 끊김"}
          </span>
          <button
            className="chatroom-voice-btn"
            onClick={() => navigate("/voice")}
            aria-label="음성 모드로 전환"
            title="음성 모드"
          >
            {/* graphic_eq icon */}
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20" aria-hidden="true">
              <path d="M7 18H5V6h2v12zm4 2H9V4h2v16zm4-4h-2V8h2v8zm4 4h-2V6h2v12z"/>
            </svg>
          </button>
        </div>
      </header>

      {/* Message list */}
      <div className="message-list">
        {messages.length === 0 && (
          <div className="message-list--empty">
            {/* AI orb */}
            <div className="empty-state-orb">
              <div className="empty-state-orb-inner">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25L19 15z"/>
                </svg>
              </div>
              <div className="empty-state-orb-glow" aria-hidden="true" />
            </div>

            <p className="empty-state-title">무엇에 대해 생각하고 계신가요?</p>

            <div className="suggestion-grid">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className="suggestion-chip"
                  onClick={() => handleSuggestion(s)}
                >
                  {s}
                </button>
              ))}
            </div>
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

      {/* Input area */}
      <div className="chat-input-area">
        <div className="chat-input-inner">
          {/* Document attach button */}
          <button className="chat-attach-btn" aria-label="문서 첨부">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </button>

          {/* Input field */}
          <div className="chat-input-field-wrap">
            <textarea
              ref={textareaRef}
              className="chat-input"
              rows={1}
              placeholder="아이디어를 말해보세요..."
              value={inputText}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              disabled={isSending}
            />
            <button className="chat-mic-btn" aria-label="음성 입력">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>
          </div>

          {/* Voice mode / Send button */}
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!inputText.trim() || isSending || status !== "open"}
            aria-label="전송"
          >
            {inputText.trim() ? (
              <svg
                className="send-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5 12 12 5 19 12" />
              </svg>
            ) : (
              /* graphic_eq */
              <svg viewBox="0 0 24 24" fill="currentColor" className="send-icon" aria-hidden="true">
                <path d="M7 18H5V6h2v12zm4 2H9V4h2v16zm4-4h-2V8h2v8zm4 4h-2V6h2v12z"/>
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Sidebar drawer */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
    </div>
  );
}
