import { useState } from "react";
import api from "@/services/api";

interface DeleteConfirmDialogProps {
  documentTitle: string;
  documentId: string;
  onCancel: () => void;
  onDeleted: () => void;
}

export default function DeleteConfirmDialog({
  documentTitle,
  documentId,
  onCancel,
  onDeleted,
}: DeleteConfirmDialogProps) {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    setDeleting(true);
    setError(null);
    try {
      await api.delete(`/documents/${documentId}`);
      onDeleted();
    } catch {
      setError("삭제 중 오류가 발생했습니다. 다시 시도해주세요.");
      setDeleting(false);
    }
  };

  return (
    // 오버레이 클릭 시 취소 (접근성: 배경 닫기)
    <div style={styles.overlay} onClick={onCancel} role="dialog" aria-modal="true">
      <div
        style={styles.dialog}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={styles.dialogTitle}>문서 삭제</h2>
        <p style={styles.dialogBody}>
          <strong style={styles.docName}>{documentTitle}</strong>를(을) 삭제하시겠습니까?
          <br />
          <span style={styles.warnText}>이 작업은 되돌릴 수 없습니다.</span>
        </p>

        {error && <p style={styles.error}>{error}</p>}

        <div style={styles.btnRow}>
          <button
            style={styles.cancelBtn}
            onClick={onCancel}
            disabled={deleting}
          >
            취소
          </button>
          <button
            style={styles.confirmBtn}
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? "삭제 중..." : "삭제"}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed",
    inset: 0,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
    padding: "var(--space-6)",
  },
  dialog: {
    backgroundColor: "var(--color-surface-container-lowest)",
    borderRadius: "var(--radius-2xl)",
    padding: "var(--space-8)",
    width: "100%",
    maxWidth: "400px",
    boxShadow: "var(--shadow-md)",
  },
  dialogTitle: {
    fontSize: "var(--text-2xl)",
    fontWeight: "var(--font-semibold)",
    color: "var(--color-on-surface)",
    margin: "0 0 var(--space-6) 0",
  },
  dialogBody: {
    fontSize: "var(--text-md)",
    color: "var(--color-text-secondary)",
    lineHeight: "var(--leading-relaxed)",
    margin: "0 0 var(--space-8) 0",
  },
  docName: {
    color: "var(--color-on-surface)",
    fontWeight: "var(--font-semibold)",
  },
  warnText: {
    color: "var(--color-error)",
    fontSize: "var(--text-sm)",
  },
  error: {
    color: "var(--color-error)",
    fontSize: "var(--text-sm)",
    margin: "0 0 var(--space-6) 0",
    padding: "var(--space-3) var(--space-4)",
    backgroundColor: "var(--color-error-container)",
    borderRadius: "var(--radius-md)",
  },
  btnRow: {
    display: "flex",
    gap: "var(--space-4)",
    justifyContent: "flex-end",
  },
  cancelBtn: {
    padding: "var(--space-4) var(--space-7)",
    backgroundColor: "var(--color-surface-container)",
    color: "var(--color-on-surface)",
    border: "none",
    borderRadius: "var(--radius-xl)",
    fontSize: "var(--text-md)",
    fontWeight: "var(--font-medium)",
    cursor: "pointer",
    minHeight: "var(--touch-target)",
  },
  confirmBtn: {
    padding: "var(--space-4) var(--space-7)",
    backgroundColor: "var(--color-error)",
    color: "var(--color-on-error)",
    border: "none",
    borderRadius: "var(--radius-xl)",
    fontSize: "var(--text-md)",
    fontWeight: "var(--font-medium)",
    cursor: "pointer",
    minHeight: "var(--touch-target)",
  },
};
