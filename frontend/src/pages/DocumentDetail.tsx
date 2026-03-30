import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import api from "@/services/api";
import DeleteConfirmDialog from "@/components/DeleteConfirmDialog";

interface DocumentDetailData {
  id: string;
  title: string;
  content: string;
  keywords: string[];
  created_at: string;
  updated_at: string;
}

interface SimilarDocument {
  id: string;
  title: string;
  similarity_score: number;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [doc, setDoc] = useState<DocumentDetailData | null>(null);
  const [similar, setSimilar] = useState<SimilarDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      api.get<DocumentDetailData>(`/documents/${id}`),
      api.get<SimilarDocument[]>(`/documents/${id}/similar`),
    ])
      .then(([docRes, simRes]) => {
        setDoc(docRes.data);
        setSimilar(simRes.data);
      })
      .catch(() => setError("문서를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div style={styles.container}>
        <p style={styles.center}>불러오는 중...</p>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div style={styles.container}>
        <p style={{ ...styles.center, color: "var(--color-error)" }}>
          {error ?? "문서를 찾을 수 없습니다."}
        </p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <button
          style={styles.backBtn}
          onClick={() => navigate("/documents")}
          aria-label="문서 목록으로"
        >
          ←
        </button>
        <span style={styles.headerDate}>{formatDate(doc.created_at)}</span>
        <button
          style={styles.deleteBtn}
          onClick={() => setShowDeleteDialog(true)}
          aria-label="문서 삭제"
        >
          삭제
        </button>
      </header>

      <main style={styles.main}>
        <h1 style={styles.title}>{doc.title}</h1>

        {doc.keywords && doc.keywords.length > 0 && (
          <div style={styles.tagRow}>
            {doc.keywords.map((kw) => (
              <span key={kw} style={styles.tag}>
                {kw}
              </span>
            ))}
          </div>
        )}

        <div style={styles.divider} />

        <div style={styles.markdownWrapper}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{doc.content}</ReactMarkdown>
        </div>

        {similar.length > 0 && (
          <section style={styles.similarSection}>
            <h2 style={styles.similarTitle}>유사 문서</h2>
            <div style={styles.similarList}>
              {similar.map((s) => (
                <button
                  key={s.id}
                  style={styles.similarCard}
                  onClick={() => navigate(`/documents/${s.id}`)}
                >
                  <span style={styles.similarDocTitle}>{s.title}</span>
                  <span style={styles.similarScore}>
                    {Math.round(s.similarity_score * 100)}% 유사
                  </span>
                </button>
              ))}
            </div>
          </section>
        )}
      </main>

      {showDeleteDialog && (
        <DeleteConfirmDialog
          documentTitle={doc.title}
          documentId={doc.id}
          onCancel={() => setShowDeleteDialog(false)}
          onDeleted={() => navigate("/documents")}
        />
      )}
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
  headerDate: {
    fontSize: "var(--text-sm)",
    color: "var(--color-text-muted)",
  },
  deleteBtn: {
    background: "none",
    border: "1px solid var(--color-error)",
    borderRadius: "var(--radius-sm)",
    padding: "var(--space-2) var(--space-4)",
    fontSize: "var(--text-sm)",
    color: "var(--color-error)",
    cursor: "pointer",
    minHeight: "var(--touch-target)",
  },
  main: {
    flex: 1,
    padding: "var(--space-8) var(--space-6)",
    overflowY: "auto",
    maxWidth: "720px",
    width: "100%",
    margin: "0 auto",
  },
  title: {
    fontSize: "var(--text-4xl)",
    fontWeight: "var(--font-bold)",
    color: "var(--color-on-surface)",
    margin: "0 0 var(--space-6) 0",
    lineHeight: "var(--leading-tight)",
  },
  tagRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: "var(--space-2)",
    marginBottom: "var(--space-6)",
  },
  tag: {
    backgroundColor: "var(--color-primary-fixed)",
    color: "var(--color-on-primary-fixed-variant)",
    borderRadius: "var(--radius-full)",
    padding: "var(--space-1) var(--space-4)",
    fontSize: "var(--text-sm)",
    fontWeight: "var(--font-medium)",
  },
  divider: {
    borderTop: "1px solid var(--color-outline-variant)",
    marginBottom: "var(--space-8)",
  },
  markdownWrapper: {
    fontSize: "var(--text-md)",
    lineHeight: "var(--leading-relaxed)",
    color: "var(--color-on-surface)",
  },
  center: {
    textAlign: "center",
    color: "var(--color-text-muted)",
    marginTop: "var(--space-10)",
  },
  similarSection: {
    marginTop: "var(--space-10)",
    paddingTop: "var(--space-8)",
    borderTop: "1px solid var(--color-outline-variant)",
  },
  similarTitle: {
    fontSize: "var(--text-xl)",
    fontWeight: "var(--font-semibold)",
    color: "var(--color-on-surface)",
    marginBottom: "var(--space-6)",
  },
  similarList: {
    display: "flex",
    flexDirection: "column",
    gap: "var(--space-3)",
  },
  similarCard: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "var(--space-5) var(--space-6)",
    backgroundColor: "var(--color-surface-container-low)",
    border: "1px solid var(--color-outline-variant)",
    borderRadius: "var(--radius-lg)",
    cursor: "pointer",
    textAlign: "left",
    transition: "background-color var(--transition-normal)",
    minHeight: "var(--touch-target)",
    width: "100%",
  },
  similarDocTitle: {
    fontSize: "var(--text-md)",
    color: "var(--color-on-surface)",
    fontWeight: "var(--font-medium)",
    flex: 1,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    marginRight: "var(--space-4)",
  },
  similarScore: {
    fontSize: "var(--text-sm)",
    color: "var(--color-primary)",
    fontWeight: "var(--font-medium)",
    whiteSpace: "nowrap",
  },
};
