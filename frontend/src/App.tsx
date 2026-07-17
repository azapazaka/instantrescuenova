import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { AppLayout } from "./layout/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { HeartRatePage } from "./pages/HeartRatePage";
import { ProfilePage } from "./pages/ProfilePage";
import { RecommendationsPage } from "./pages/RecommendationsPage";
import { SafetyPage } from "./pages/SafetyPage";
import { SignInPage } from "./pages/SignInPage";
import { SignUpPage } from "./pages/SignUpPage";

function RequireAuth({ children }: { children: ReactNode }) {
  const { session, loading } = useAuth();

  // Wait for the session check before deciding. Redirecting during the initial
  // load would bounce an already-signed-in user to the login screen on refresh.
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-lg font-extrabold text-muted">Загрузка…</p>
      </div>
    );
  }
  if (!session) return <Navigate to="/signin" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/signin" element={<SignInPage />} />
        <Route path="/signup" element={<SignUpPage />} />

        <Route
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/heart-rate" element={<HeartRatePage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
          <Route path="/safety" element={<SafetyPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
