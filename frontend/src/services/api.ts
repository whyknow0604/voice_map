import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor: 토큰 자동 첨부
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: 401 시 토큰 제거 + 로그인 페이지로 리디렉션
// window.location.href 사용으로 React Router 외부에서 강제 이동 → AuthProvider가
// 초기화 시 localStorage를 다시 읽으므로 isAuthenticated 상태도 false로 재시작됨
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
