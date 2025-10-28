import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@shared/auth';

type GuardProps = {
  requireAdmin?: boolean;
  allowedRoles?: string[];
  children: React.ReactNode;
};

const ADMIN_ROLES = ['admin'];
const DEFAULT_SUPER_ROLES = new Set<string>(['admin']);

function normalizeRoles(user: any): Set<string> {
  const roles = new Set<string>();
  const append = (value: unknown) => {
    if (!value) return;
    const text = String(value).trim().toLowerCase();
    if (text) {
      roles.add(text);
    }
  };
  const collection = Array.isArray(user?.roles) ? user.roles : [];
  for (const role of collection) {
    append(role);
  }
  append(user?.role);
  return roles;
}

function isAuthorized(userRoles: Set<string>, allowed: Set<string>): boolean {
  if (allowed.size === 0) {
    return true;
  }
  if (userRoles.size === 0) {
    return false;
  }
  for (const role of userRoles) {
    if (DEFAULT_SUPER_ROLES.has(role) || allowed.has(role)) {
      return true;
    }
  }
  return false;
}

export function Guard({
  requireAdmin = false,
  allowedRoles,
  children,
}: GuardProps): React.ReactElement | null {
  const { isAuthenticated, isReady, user } = useAuth();
  if (!isReady) return null;
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const requiredRoles = new Set<string>();
  if (requireAdmin) {
    ADMIN_ROLES.forEach((role) => requiredRoles.add(role));
  }
  if (Array.isArray(allowedRoles)) {
    for (const role of allowedRoles) {
      if (typeof role === 'string' && role.trim()) {
        requiredRoles.add(role.trim().toLowerCase());
      }
    }
  }

  if (requiredRoles.size > 0) {
    const roles = normalizeRoles(user);
    if (!isAuthorized(roles, requiredRoles)) {
      return <Navigate to="/billing" replace />;
    }
  }
  return <>{children}</>;
}
