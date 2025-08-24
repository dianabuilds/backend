import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, ready } = useAuth();

  // Пока не знаем состояние сессии — ничего не рендерим (без редиректа)
  if (!ready) return null;

  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
