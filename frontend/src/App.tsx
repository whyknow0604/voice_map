import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import LoginPage from "@/pages/LoginPage";
import ChatRoom from "@/pages/ChatRoom";
import VoicePage from "@/pages/VoicePage";
import ConversationList from "@/pages/ConversationList";
import ConversationDetail from "@/pages/ConversationDetail";
import { lazy, Suspense } from "react";
import DocumentList from "@/pages/DocumentList";
import DocumentDetail from "@/pages/DocumentDetail";
import SettingsPage from "@/pages/SettingsPage";
// KnowledgeGraph는 react-force-graph 번들이 크므로 lazy loading으로 초기 번들에서 분리
const KnowledgeGraph = lazy(() => import("@/pages/KnowledgeGraph"));

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/chat"
              element={
                <ProtectedRoute>
                  <ChatRoom />
                </ProtectedRoute>
              }
            />
            <Route
              path="/conversations"
              element={
                <ProtectedRoute>
                  <ConversationList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/voice"
              element={
                <ProtectedRoute>
                  <VoicePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/conversations/:id"
              element={
                <ProtectedRoute>
                  <ConversationDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/documents"
              element={
                <ProtectedRoute>
                  <DocumentList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/documents/:id"
              element={
                <ProtectedRoute>
                  <DocumentDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/graph"
              element={
                <ProtectedRoute>
                  <Suspense fallback={<div style={{ padding: "2rem", textAlign: "center" }}>그래프 로딩 중...</div>}>
                    <KnowledgeGraph />
                  </Suspense>
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
