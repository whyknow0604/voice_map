import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/services/api";
import MessageBubble, { Message } from "@/components/MessageBubble";
import "@/styles/ConversationList.css";

interface ApiMessage {
  id: string;
  role: "user" | "ai";
  content: string;
  audio_url: string | null;
  created_at: string;
}

interface ConversationDetailData {
  id: string;
  mode: "text" | "voice";
  title: string | null;
  created_at: string;
  ended_at: string | null;
  messages: ApiMessage[];
}

function toMessage(apiMsg: ApiMessage): Message {
  return {
    id: apiMsg.id,
    role: apiMsg.role,
    content: apiMsg.content,
    timestamp: new Date(apiMsg.created_at),
  };
}

export default function ConversationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [conversation, setConversation] = useState<ConversationDetailData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const fetchConversation = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<ConversationDetailData>(`/conversations/${id}`);
      setConversation(response.data);
    } catch {
      setError("대화를 불러오는 데 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchConversation();
  }, [fetchConversation]);

  // 메시지 로드 후 맨 아래로 스크롤
  useEffect(() => {
    if (conversation) {
      messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
    }
  }, [conversation]);

  const handleBack = () => {
    navigate("/conversations");
  };

  return (
    <div className="conv-detail-page">
      <header className="conv-detail-header">
        <button className="conv-back-btn" onClick={handleBack} aria-label="뒤로가기">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="back-icon">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <h1 className="conv-detail-title">
          {conversation?.title ?? "대화 상세"}
        </h1>
      </header>

      <main className="conv-detail-main">
        {isLoading && (
          <div className="conv-list-loading">
            <span>불러오는 중...</span>
          </div>
        )}

        {!isLoading && error && (
          <div className="conv-list-error">
            <p>{error}</p>
            <button className="conv-retry-btn" onClick={fetchConversation}>
              다시 시도
            </button>
          </div>
        )}

        {!isLoading && !error && conversation && (
          <div className="conv-detail-messages">
            {conversation.messages.length === 0 ? (
              <div className="conv-list-empty">
                <p className="conv-list-empty__message">메시지가 없습니다.</p>
              </div>
            ) : (
              conversation.messages.map((msg) => (
                <MessageBubble key={msg.id} message={toMessage(msg)} />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>
    </div>
  );
}
