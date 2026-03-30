import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import "@/styles/Sidebar.css";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeConversationId?: string;
}

const RECENT_CONVERSATIONS = [
  { id: "1", title: "AI 스타트업 수익 모델 정리" },
  { id: "2", title: "GraphRAG 기술 검토" },
  { id: "3", title: "Q2 마케팅 전략..." },
  { id: "4", title: "사용자 인터뷰..." },
  { id: "5", title: "프로덕트 로드맵..." },
];

export default function Sidebar({ isOpen, onClose, activeConversationId }: SidebarProps) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleNewChat = () => {
    navigate("/chat");
    onClose();
  };

  const handleConversations = () => {
    navigate("/conversations");
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
              onClick={handleConversations}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              내 문서
            </button>
            <button className="sidebar-nav-item" onClick={onClose}>
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
              {RECENT_CONVERSATIONS.map((conv) => (
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
              U
            </div>
            <div className="sidebar-user-info">
              <p className="sidebar-user-name">사용자</p>
              <p className="sidebar-user-plan">프리미엄 플랜</p>
            </div>
            <button
              className="sidebar-settings-btn"
              aria-label="설정"
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
