import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/services/api";
import "@/styles/Sidebar.css";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeConversationId?: string;
}

interface Conversation {
  id: string;
  title: string;
}

export default function Sidebar({ isOpen, onClose, activeConversationId }: SidebarProps) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userName, setUserName] = useState("사용자");

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    setError(null);
    api
      .get<Conversation[]>("/conversations", { params: { limit: 5 } })
      .then((res) => setConversations(res.data))
      .catch(() => setError("대화 목록을 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [isOpen]);

  useEffect(() => {
    api
      .get<{ name: string }>("/auth/me")
      .then((res) => setUserName(res.data.name || "사용자"))
      .catch(() => {/* 실패 시 기본값 유지 */});
  }, []);

  const handleNewChat = () => {
    navigate("/chat");
    onClose();
  };

  const handleConversationClick = (id: string) => {
    navigate(`/conversations/${id}`);
    onClose();
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Scrim backdrop */}
      <div
        className="sidebar-scrim"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside
        className="sidebar"
        role="dialog"
        aria-modal="true"
        aria-label="내비게이션 메뉴"
      >
        {/* Header */}
        <div className="sidebar-header">
          <span className="sidebar-brand">Voice Map</span>
          <button
            className="sidebar-close-btn"
            onClick={onClose}
            aria-label="메뉴 닫기"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* New Chat button */}
        <div className="sidebar-new-chat-wrap">
          <button className="sidebar-new-chat-btn" onClick={handleNewChat}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            새 대화
          </button>
        </div>

        {/* Scrollable nav + history */}
        <nav className="sidebar-nav">
          {/* Primary links */}
          <div className="sidebar-nav-section">
            <button
              className="sidebar-nav-item"
              onClick={() => { onClose(); navigate("/documents"); }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              내 문서
            </button>
            <button
              className="sidebar-nav-item"
              onClick={() => { onClose(); navigate("/graph"); }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2L12 5" />
                <path d="M12 19L12 22" />
                <path d="M4.22 4.22L6.34 6.34" />
                <path d="M17.66 17.66L19.78 19.78" />
                <path d="M2 12L5 12" />
                <path d="M19 12L22 12" />
                <path d="M4.22 19.78L6.34 17.66" />
                <path d="M17.66 6.34L19.78 4.22" />
              </svg>
              Knowledge Graph
            </button>
          </div>

          {/* Recent conversations */}
          <div className="sidebar-history-section">
            <p className="sidebar-section-label">최근 대화</p>
            <div className="sidebar-history-list">
              {loading && <p className="sidebar-history-loading">불러오는 중...</p>}
              {error && <p className="sidebar-history-error">{error}</p>}
              {!loading && !error && conversations.length === 0 && (
                <p className="sidebar-history-empty">최근 대화가 없습니다.</p>
              )}
              {!loading && !error && conversations.map((conv) => (
                <button
                  key={conv.id}
                  className={`sidebar-history-item${activeConversationId === conv.id ? " sidebar-history-item--active" : ""}`}
                  onClick={() => handleConversationClick(conv.id)}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                  <span className="sidebar-history-title">{conv.title}</span>
                </button>
              ))}
            </div>
          </div>
        </nav>

        {/* User profile footer */}
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">
              {userName.charAt(0).toUpperCase()}
            </div>
            <div className="sidebar-user-info">
              <p className="sidebar-user-name">{userName}</p>
              <p className="sidebar-user-plan">프리미엄 플랜</p>
            </div>
            <button
              className="sidebar-settings-btn"
              aria-label="설정"
              onClick={() => { onClose(); navigate("/settings"); }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>
            <button
              className="sidebar-logout-btn"
              aria-label="로그아웃"
              onClick={handleLogout}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
