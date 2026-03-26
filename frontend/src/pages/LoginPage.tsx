import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import api from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import "./LoginPage.css";

interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleLogin = useGoogleLogin({
    flow: "auth-code",
    onSuccess: async ({ code }) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.post<TokenResponse>("/auth/google", {
          authorization_code: code,
        });
        login(response.data.access_token, response.data.refresh_token);
        navigate("/chat");
      } catch {
        setError("로그인에 실패했습니다. 다시 시도해주세요.");
      } finally {
        setIsLoading(false);
      }
    },
    onError: () => {
      setError("Google 로그인이 취소되었거나 오류가 발생했습니다.");
    },
  });

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-logo">
          <span className="login-logo-icon">🗺️</span>
          <h1 className="login-title">Voice Map</h1>
        </div>
        <p className="login-subtitle">아이디어를 말로, 지식을 지도로</p>

        {error && <p className="login-error">{error}</p>}

        <button
          className="google-login-btn"
          onClick={() => handleGoogleLogin()}
          disabled={isLoading}
        >
          <svg className="google-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          {isLoading ? "로그인 중..." : "Google로 계속하기"}
        </button>
      </div>
    </div>
  );
}
