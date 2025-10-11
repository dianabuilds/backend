import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@shared/auth';

const ADMIN_ROLES = ['admin'];

type GuardProps = {
  requireAdmin?: boolean;
  children: React.ReactNode;
};

export function Guard({ requireAdmin = false, children }: GuardProps): React.ReactElement | null {
  const { isAuthenticated, isReady, user } = useAuth();
  if (!isReady) return null;
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (requireAdmin) {
    const roles: string[] = [];
    if (Array.isArray(user?.roles)) {
      roles.push(...user.roles.map((role) => String(role).toLowerCase()));
    }
    if (user?.role) {
      roles.push(String(user.role).toLowerCase());
    }
    if (!roles.some((role) => ADMIN_ROLES.includes(role))) {
      return <Navigate to="/billing" replace />;
    }
  }
  return <>{children}</>;
}
