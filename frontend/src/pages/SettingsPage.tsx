import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";

interface UserProfile {
  id: string;
  name: string;
  email: string;
  picture?: string;
}

export default function SettingsPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<UserProfile>("/auth/me")
      .then((res) => setProfile(res.data))
      .catch(() => setError("사용자 정보를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

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
        <h1 style={styles.title}>설정</h1>
        <div style={styles.headerSpacer} />
      </header>

      <main style={styles.main}>
        {loading && <p style={styles.center}>불러오는 중...</p>}
        {error && (
          <p style={{ ...styles.center, color: "var(--color-error)" }}>{error}</p>
        )}

        {!loading && !error && profile && (
          <>
            <section style={styles.section}>
              <h2 style={styles.sectionTitle}>계정</h2>
              <div style={styles.profileCard}>
                {profile.picture && (
                  <img
                    src={profile.picture}
                    alt={profile.name}
                    style={styles.avatar}
                    referrerPolicy="no-referrer"
                  />
                )}
                {!profile.picture && (
                  <div style={styles.avatarFallback}>
                    {profile.name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div style={styles.profileInfo}>
                  <p style={styles.profileName}>{profile.name}</p>
                  <p style={styles.profileEmail}>{profile.email}</p>
                </div>
              </div>
            </section>

            <section style={styles.section}>
              <h2 style={styles.sectionTitle}>앱</h2>
              <div style={styles.menuList}>
                <button
                  style={styles.menuItem}
                  onClick={() => navigate("/documents")}
                >
                  <span>내 문서</span>
                  <span style={styles.menuArrow}>›</span>
                </button>
                <button
                  style={styles.menuItem}
                  onClick={() => navigate("/graph")}
                >
                  <span>Knowledge Graph</span>
                  <span style={styles.menuArrow}>›</span>
                </button>
              </div>
            </section>

            <section style={styles.section}>
              <button style={styles.logoutBtn} onClick={handleLogout}>
                로그아웃
              </button>
            </section>
          </>
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
  headerSpacer: {
    width: "var(--touch-target)",
  },
  main: {
    flex: 1,
    padding: "var(--space-6)",
    overflowY: "auto",
    maxWidth: "600px",
    width: "100%",
    margin: "0 auto",
  },
  center: {
    textAlign: "center",
    color: "var(--color-text-muted)",
    marginTop: "var(--space-10)",
  },
  section: {
    marginBottom: "var(--space-8)",
  },
  sectionTitle: {
    fontSize: "var(--text-sm)",
    fontWeight: "var(--font-semibold)",
    color: "var(--color-text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    margin: "0 0 var(--space-4) 0",
  },
  profileCard: {
    display: "flex",
    alignItems: "center",
    gap: "var(--space-6)",
    padding: "var(--space-6)",
    backgroundColor: "var(--color-surface-container-lowest)",
    border: "1px solid var(--color-outline-variant)",
    borderRadius: "var(--radius-xl)",
  },
  avatar: {
    width: "56px",
    height: "56px",
    borderRadius: "var(--radius-full)",
    objectFit: "cover",
    flexShrink: 0,
  },
  avatarFallback: {
    width: "56px",
    height: "56px",
    borderRadius: "var(--radius-full)",
    backgroundColor: "var(--color-primary)",
    color: "var(--color-on-primary)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "var(--text-2xl)",
    fontWeight: "var(--font-bold)",
    flexShrink: 0,
  },
  profileInfo: {
    flex: 1,
    overflow: "hidden",
  },
  profileName: {
    fontSize: "var(--text-xl)",
    fontWeight: "var(--font-semibold)",
    color: "var(--color-on-surface)",
    margin: "0 0 var(--space-1) 0",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  profileEmail: {
    fontSize: "var(--text-md)",
    color: "var(--color-text-muted)",
    margin: 0,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  menuList: {
    backgroundColor: "var(--color-surface-container-lowest)",
    border: "1px solid var(--color-outline-variant)",
    borderRadius: "var(--radius-xl)",
    overflow: "hidden",
  },
  menuItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    width: "100%",
    padding: "var(--space-5) var(--space-6)",
    background: "none",
    border: "none",
    borderBottom: "1px solid var(--color-outline-variant)",
    cursor: "pointer",
    fontSize: "var(--text-md)",
    color: "var(--color-on-surface)",
    minHeight: "var(--touch-target)",
    textAlign: "left",
  },
  menuArrow: {
    fontSize: "var(--text-xl)",
    color: "var(--color-text-muted)",
  },
  logoutBtn: {
    width: "100%",
    padding: "var(--space-5) var(--space-6)",
    backgroundColor: "var(--color-error-container)",
    color: "var(--color-on-error-container)",
    border: "none",
    borderRadius: "var(--radius-xl)",
    fontSize: "var(--text-md)",
    fontWeight: "var(--font-medium)",
    cursor: "pointer",
    minHeight: "var(--touch-target)",
  },
};
