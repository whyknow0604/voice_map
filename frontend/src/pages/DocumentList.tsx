import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/services/api";

interface Document {
  id: string;
  title: string;
  keywords: string[] | null;
  created_at: string;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function DocumentList() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Document[]>("/documents")
      .then((res) => setDocuments(res.data))
      .catch(() => setError("문서 목록을 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <button
          style={styles.backBtn}
          onClick={() => navigate(-1)}
          aria-label="뒤로 가기"
        >
          ←
        </button>
        <h1 style={styles.title}>내 문서</h1>
        <button
          style={styles.graphBtn}
          onClick={() => navigate("/graph")}
          aria-label="Knowledge Graph"
        >
          그래프
        </button>
      </header>

      <main style={styles.main}>
        {loading && <p style={styles.center}>불러오는 중...</p>}
        {error && <p style={{ ...styles.center, color: "var(--color-error)" }}>{error}</p>}
        {!loading && !error && documents.length === 0 && (
          <div style={styles.emptyState}>
            <p style={styles.emptyIcon}>📄</p>
            <p style={styles.emptyTitle}>아직 저장된 문서가 없습니다</p>
            <p style={styles.emptyDesc}>
              채팅을 통해 아이디어를 정리하면 문서가 생성됩니다.
            </p>
            <button
              style={styles.newChatBtn}
              onClick={() => navigate("/chat")}
            >
              새 채팅 시작
            </button>
          </div>
        )}
        {!loading && !error && documents.length > 0 && (
          <div style={styles.grid}>
            {documents.map((doc) => (
              <button
                key={doc.id}
                style={styles.card}
                onClick={() => navigate(`/documents/${doc.id}`)}
              >
                <h2 style={styles.cardTitle}>{doc.title}</h2>
                {doc.keywords && doc.keywords.length > 0 && (
                  <div style={styles.tagRow}>
                    {doc.keywords.slice(0, 4).map((kw) => (
                      <span key={kw} style={styles.tag}>
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
                <p style={styles.cardDate}>{formatDate(doc.created_at)}</p>
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: "100dvh",
    backgroundColor: "var(--color-background)",
    display: "flex",
    flexDirection: "column",
    paddingTop: "env(safe-area-inset-top)",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "var(--space-4) var(--space-6)",
    backgroundColor: "var(--color-surface-container-lowest)",
    borderBottom: "1px solid var(--color-outline-variant)",
    minHeight: "var(--touch-target)",
  },
  backBtn: {
    background: "none",
    border: "none",
    fontSize: "var(--text-xl)",
    cursor: "pointer",
    color: "var(--color-primary)",
    minWidth: "var(--touch-target)",
    minHeight: "var(--touch-target)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 0,
  },
  title: {
    fontSize: "var(--text-2xl)",
    fontWeight: "var(--font-semibold)",
    color: "var(--color-on-surface)",
    margin: 0,
  },
  graphBtn: {
    background: "none",
    border: "1px solid var(--color-outline-variant)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-4)",
    fontSize: "var(--text-sm)",
    color: "var(--color-primary)",
    cursor: "pointer",
    minHeight: "var(--touch-target)",
  },
  main: {
    flex: 1,
    padding: "var(--space-6)",
    overflowY: "auto",
  },
  center: {
    textAlign: "center",
    color: "var(--color-text-muted)",
    marginTop: "var(--space-10)",
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    paddingTop: "var(--space-11)",
    gap: "var(--space-4)",
  },
  emptyIcon: {
    fontSize: "48px",
    margin: 0,
  },
  emptyTitle: {
    fontSize: "var(--text-xl)",
    fontWeight: "var(--font-semibold)",
    color: "var(--color-on-surface)",
    margin: 0,
  },
  emptyDesc: {
    fontSize: "var(--text-md)",
    color: "var(--color-text-muted)",
    textAlign: "center",
    margin: 0,
  },
  newChatBtn: {
    marginTop: "var(--space-4)",
    padding: "var(--space-4) var(--space-8)",
    backgroundColor: "var(--color-primary)",
    color: "var(--color-on-primary)",
    border: "none",
    borderRadius: "var(--radius-xl)",
    fontSize: "var(--text-md)",
    fontWeight: "var(--font-medium)",
    cursor: "pointer",
    minHeight: "var(--touch-target)",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
    gap: "var(--space-6)",
  },
  card: {
    background: "var(--color-surface-container-lowest)",
    border: "1px solid var(--color-outline-variant)",
    borderRadius: "var(--radius-xl)",
    padding: "var(--space-6)",
    textAlign: "left",
    cursor: "pointer",
    transition: "box-shadow var(--transition-normal)",
    boxShadow: "var(--shadow-xs)",
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
    width: "100%",
  },
  cardTitle: {
    fontSize: "var(--text-xl)",
    fontWeight: "var(--font-semibold)",
    color: "var(--color-on-surface)",
    margin: 0,
    lineHeight: "var(--leading-tight)",
    overflow: "hidden",
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
  },
  tagRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: "var(--space-2)",
  },
  tag: {
    backgroundColor: "var(--color-primary-fixed)",
    color: "var(--color-on-primary-fixed-variant)",
    borderRadius: "var(--radius-full)",
    padding: "2px var(--space-3)",
    fontSize: "var(--text-xs)",
    fontWeight: "var(--font-medium)",
  },
  cardDate: {
    fontSize: "var(--text-sm)",
    color: "var(--color-text-muted)",
    margin: 0,
    marginTop: "auto",
  },
};
