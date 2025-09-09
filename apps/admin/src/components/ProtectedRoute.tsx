import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';

export default function ProtectedRoute({
  children,
  roles,
}: {
  children: ReactNode;
  roles?: string[];
}) {
  const { user, ready, hasRole } = useAuth();

  if (!ready) return null;
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (roles && !hasRole(...roles)) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
