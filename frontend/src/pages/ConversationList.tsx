import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/services/api";
import "@/styles/ConversationList.css";

interface Conversation {
  id: string;
  mode: "text" | "voice";
  title: string | null;
  created_at: string;
  ended_at: string | null;
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ConversationList() {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<Conversation[]>("/conversations");
      setConversations(response.data);
    } catch {
      setError("대화 목록을 불러오는 데 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  const handleNewChat = () => {
    navigate("/chat");
  };

  const handleConversationClick = (id: string) => {
    navigate(`/conversations/${id}`);
  };

  return (
    <div className="conv-list-page">
      <header className="conv-list-header">
        <h1 className="conv-list-title">대화 목록</h1>
        <button className="conv-new-btn" onClick={handleNewChat}>
          새 대화
        </button>
      </header>

      <main className="conv-list-main">
        {isLoading && (
          <div className="conv-list-loading">
            <span>불러오는 중...</span>
          </div>
        )}

        {!isLoading && error && (
          <div className="conv-list-error">
            <p>{error}</p>
            <button className="conv-retry-btn" onClick={fetchConversations}>
              다시 시도
            </button>
          </div>
        )}

        {!isLoading && !error && conversations.length === 0 && (
          <div className="conv-list-empty">
            <p className="conv-list-empty__message">아직 대화가 없습니다.</p>
            <p className="conv-list-empty__sub">새 대화를 시작해보세요!</p>
            <button className="conv-start-btn" onClick={handleNewChat}>
              첫 대화 시작하기
            </button>
          </div>
        )}

        {!isLoading && !error && conversations.length > 0 && (
          <ul className="conv-list">
            {conversations.map((conv) => (
              <li
                key={conv.id}
                className="conv-item"
                onClick={() => handleConversationClick(conv.id)}
              >
                <div className="conv-item__info">
                  <span className="conv-item__title">
                    {conv.title ?? "제목 없는 대화"}
                  </span>
                  <span className="conv-item__date">{formatDate(conv.created_at)}</span>
                </div>
                <span className={`conv-item__mode conv-item__mode--${conv.mode}`}>
                  {conv.mode === "text" ? "텍스트" : "음성"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
