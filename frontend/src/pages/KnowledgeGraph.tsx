import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import ForceGraph2D from "react-force-graph-2d";
import api from "@/services/api";

interface DocumentSummary {
  id: string;
  title: string;
  keywords: string[];
}

interface SimilarDocument {
  id: string;
  title: string;
  similarity_score: number;
}

interface GraphNode {
  id: string;
  label: string;
}

interface GraphLink {
  source: string;
  target: string;
  value: number;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// 유사도 임계값: 너무 낮으면 엣지가 너무 많아 가독성이 떨어짐
const SIMILARITY_THRESHOLD = 0.5;

export default function KnowledgeGraph() {
  const navigate = useNavigate();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>();

  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  // 컨테이너 크기 계측
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    observer.observe(el);
    setContainerSize({ width: el.clientWidth, height: el.clientHeight });
    return () => observer.disconnect();
  }, []);

  // 그래프 데이터 빌드
  useEffect(() => {
    let cancelled = false;

    async function buildGraph() {
      try {
        const docsRes = await api.get<DocumentSummary[]>("/documents");
        const docs = docsRes.data;

        if (docs.length === 0) {
          setGraphData({ nodes: [], links: [] });
          return;
        }

        const nodes: GraphNode[] = docs.map((d) => ({ id: d.id, label: d.title }));

        // 각 문서의 유사 문서를 병렬로 조회
        const simResults = await Promise.allSettled(
          docs.map((d) =>
            api.get<SimilarDocument[]>(`/documents/${d.id}/similar`)
          )
        );

        // 중복 엣지 방지를 위해 정렬된 쌍을 키로 사용
        const seen = new Set<string>();
        const links: GraphLink[] = [];

        simResults.forEach((result, i) => {
          if (result.status !== "fulfilled") return;
          const sourceId = docs[i]?.id;
          if (!sourceId) return;

          result.value.data.forEach((sim) => {
            if (sim.similarity_score < SIMILARITY_THRESHOLD) return;
            const key = [sourceId, sim.id].sort().join("--");
            if (seen.has(key)) return;
            seen.add(key);
            links.push({ source: sourceId, target: sim.id, value: sim.similarity_score });
          });
        });

        if (!cancelled) setGraphData({ nodes, links });
      } catch {
        if (!cancelled) setError("그래프 데이터를 불러오지 못했습니다.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    buildGraph();
    return () => { cancelled = true; };
  }, []);

  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      navigate(`/documents/${node.id}`);
    },
    [navigate]
  );

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
        <h1 style={styles.title}>Knowledge Graph</h1>
        <div style={styles.headerSpacer} />
      </header>

      <div ref={containerRef} style={styles.graphContainer}>
        {loading && <p style={styles.center}>그래프 구축 중...</p>}
        {error && (
          <p style={{ ...styles.center, color: "var(--color-error)" }}>{error}</p>
        )}
        {!loading && !error && graphData.nodes.length === 0 && (
          <div style={styles.emptyState}>
            <p style={styles.emptyIcon}>🕸️</p>
            <p style={styles.emptyTitle}>아직 문서가 없습니다</p>
            <p style={styles.emptyDesc}>
              문서가 생성되면 연결 관계가 그래프로 표시됩니다.
            </p>
          </div>
        )}
        {!loading && !error && graphData.nodes.length > 0 && containerSize.width > 0 && (
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            width={containerSize.width}
            height={containerSize.height}
            nodeLabel="label"
            nodeColor={() => "#3525CD"}
            nodeRelSize={6}
            linkColor={() => "#C7C4D8"}
            linkWidth={(link) => (link as GraphLink).value * 3}
            onNodeClick={handleNodeClick}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const n = node as GraphNode & { x?: number; y?: number };
              const x = n.x ?? 0;
              const y = n.y ?? 0;
              const label = n.label ?? "";
              const fontSize = Math.max(10, 14 / globalScale);

              // 노드 원
              ctx.beginPath();
              ctx.arc(x, y, 6, 0, 2 * Math.PI);
              ctx.fillStyle = "#3525CD";
              ctx.fill();

              // 레이블 (줌이 충분할 때만 표시)
              if (globalScale >= 0.6) {
                ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
                ctx.fillStyle = "#1A1C1D";
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                // 긴 제목 자르기
                const maxLen = 20;
                const text = label.length > maxLen ? label.slice(0, maxLen) + "…" : label;
                ctx.fillText(text, x, y + 8);
              }
            }}
            cooldownTicks={100}
          />
        )}
      </div>

      {!loading && !error && graphData.nodes.length > 0 && (
        <div style={styles.legend}>
          <span style={styles.legendNode} />
          <span style={styles.legendText}>문서 노드 (클릭하면 상세 이동)</span>
          <span style={styles.legendLine} />
          <span style={styles.legendText}>유사도 연결 (선 굵기 = 유사도)</span>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    height: "100dvh",
    backgroundColor: "var(--color-background)",
    display: "flex",
    flexDirection: "column",
    paddingTop: "env(safe-area-inset-top)",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "var(--space-4) var(--space-6)",
    backgroundColor: "var(--color-surface-container-lowest)",
    borderBottom: "1px solid var(--color-outline-variant)",
    minHeight: "var(--touch-target)",
    flexShrink: 0,
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
  headerSpacer: {
    width: "var(--touch-target)",
  },
  graphContainer: {
    flex: 1,
    position: "relative",
    overflow: "hidden",
  },
  center: {
    textAlign: "center",
    color: "var(--color-text-muted)",
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    gap: "var(--space-4)",
    padding: "var(--space-6)",
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
  legend: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-4)",
    padding: "var(--space-3) var(--space-6)",
    backgroundColor: "var(--color-surface-container-lowest)",
    borderTop: "1px solid var(--color-outline-variant)",
    flexShrink: 0,
    flexWrap: "wrap",
  },
  legendNode: {
    display: "inline-block",
    width: "12px",
    height: "12px",
    borderRadius: "50%",
    backgroundColor: "#3525CD",
    flexShrink: 0,
  },
  legendLine: {
    display: "inline-block",
    width: "24px",
    height: "2px",
    backgroundColor: "#C7C4D8",
    flexShrink: 0,
  },
  legendText: {
    fontSize: "var(--text-sm)",
    color: "var(--color-text-muted)",
  },
};
