import React, { useCallback, useEffect, useMemo, useState } from "react";

import { decodeJwt, getCsrfToken, setAuthLostHandler, setCsrfToken } from "../api";
import { AuthSession, AuthUser, fetchCurrentUser, login as loginRequest, logout as logoutRequest } from "../api/auth";
import { AuthContext, AuthContextUser, AuthContextValue, LoginArgs } from "./context";

type JwtClaims = {
  sub?: string | number;
  username?: string;
  email?: string;
  role?: string;
  roles?: Array<string | number>;
  [key: string]: unknown;
};

function makeEmptyTokens(): AuthContextValue['tokens'] {
  return {
    accessToken: null,
    refreshToken: null,
    csrfToken: getCsrfToken(),
    expiresAt: null,
    tokenType: null,
  };
}

function computeExpiresAt(expiresIn?: number | null): number | null {
  if (typeof expiresIn !== 'number' || !Number.isFinite(expiresIn)) {
    return null;
  }
  return Date.now() + expiresIn * 1000;
}

function deriveTokens(
  session?: AuthSession | null,
  previous?: AuthContextValue['tokens'],
): AuthContextValue['tokens'] {
  const base = previous ?? makeEmptyTokens();
  const expiresAt =
    session && session.expires_in != null ? computeExpiresAt(session.expires_in) : base.expiresAt;

  return {
    accessToken: session?.access_token ?? base.accessToken,
    refreshToken: session?.refresh_token ?? base.refreshToken,
    csrfToken: getCsrfToken(),
    expiresAt,
    tokenType: session?.token_type ?? base.tokenType,
  };
}

function normalizeAuthUser(
  rawUser: AuthUser | null | undefined,
  claims?: JwtClaims,
  authSource?: string | null,
): AuthContextUser | null {
  const id = rawUser?.id ?? (claims?.sub !== undefined ? String(claims.sub) : undefined);
  const username = rawUser?.username ?? (claims?.username ? String(claims.username) : undefined);
  const email = rawUser?.email ?? (claims?.email ? String(claims.email) : undefined);
  const role = rawUser?.role ?? (claims?.role ? String(claims.role) : undefined);

  const roleSet = new Set<string>();
  if (Array.isArray(rawUser?.roles)) {
    rawUser.roles.forEach((value) => {
      if (value != null && value !== '') roleSet.add(String(value));
    });
  }
  if (Array.isArray(claims?.roles)) {
    claims.roles.forEach((value) => {
      if (value != null && value !== '') roleSet.add(String(value));
    });
  }
  if (role) {
    roleSet.add(role);
  }

  const firstName = (rawUser as any)?.first_name ?? (rawUser as any)?.firstName;
  const lastName = (rawUser as any)?.last_name ?? (rawUser as any)?.lastName;
  const nameFromParts = [firstName, lastName]
    .filter((value) => typeof value === 'string' && value.trim())
    .map((value) => String(value).trim())
    .join(' ')
    .trim();
  const displayNameCandidate =
    (rawUser as any)?.display_name ??
    (rawUser as any)?.displayName ??
    (nameFromParts ? nameFromParts : undefined) ??
    (claims?.username ? String(claims.username) : undefined);

  const avatarUrl = (rawUser as any)?.avatar_url ?? (rawUser as any)?.avatarUrl ?? (rawUser as any)?.avatar ?? null;

  const candidate: AuthContextUser = {
    id,
    username,
    email,
    displayName: displayNameCandidate && displayNameCandidate.trim() ? displayNameCandidate.trim() : undefined,
    avatarUrl: typeof avatarUrl === 'string' && avatarUrl.trim() ? avatarUrl.trim() : undefined,
    role,
    roles: Array.from(roleSet),
    isActive:
      typeof rawUser?.is_active === 'boolean'
        ? rawUser.is_active
        : typeof (rawUser as any)?.isActive === 'boolean'
        ? (rawUser as any).isActive
        : undefined,
    authSource: rawUser?.authSource ?? authSource ?? undefined,
    metadata: (rawUser as any)?.meta ?? (rawUser as any)?.metadata ?? null,
  };

  if (!candidate.roles.length && role) {
    candidate.roles = [role];
  }

  const hasData = Boolean(
    candidate.id ||
      candidate.username ||
      candidate.email ||
      candidate.displayName ||
      candidate.roles.length,
  );

  return hasData ? candidate : null;
}

function extractAuthSource(session: AuthSession | null | undefined): string | null {
  const source = session?.auth?.source;
  if (source == null) {
    return null;
  }
  return String(source);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setAuthenticated] = useState(false);
  const [isReady, setReady] = useState(false);
  const [errorMessage, setError] = useState<string | null>(null);
  const [user, setUser] = useState<AuthContextUser | null>(null);
  const [tokens, setTokens] = useState<AuthContextValue['tokens']>(() => makeEmptyTokens());

  const authEndpoint = (import.meta as any).env.VITE_AUTH_ENDPOINT || '/v1/auth/login';
  const logoutEndpoint = (import.meta as any).env.VITE_AUTH_LOGOUT_ENDPOINT || '/v1/auth/logout';
  const currentUserEndpoint = (import.meta as any).env.VITE_AUTH_ME_ENDPOINT || '/v1/users/me';

  const login = useCallback(
    async ({ login: identifier, password, remember }: LoginArgs) => {
      setError(null);
      try {
        const session = await loginRequest({ login: identifier, password, remember }, { endpoint: authEndpoint });
        setCsrfToken(session?.csrf_token ?? null, { ttlSeconds: session?.csrf_expires_in ?? undefined });
        setTokens(() => deriveTokens(session));

        const accessToken = session?.access_token ?? undefined;
        if (!accessToken) {
          throw new Error('Login failed');
        }

        setAuthenticated(true);

        const claims = decodeJwt<JwtClaims>(accessToken) ?? {};
        const authSource = extractAuthSource(session);

        const primaryUser = normalizeAuthUser(session?.user ?? null, claims, authSource);
        setUser(primaryUser);

        try {
          const current = await fetchCurrentUser({ endpoint: currentUserEndpoint });
          if (current?.user) {
            const enriched = normalizeAuthUser(current.user, claims, authSource);
            if (enriched) {
              setUser(enriched);
            }
          }
        } catch {
          // ignore subsequent fetch errors
        } finally {
          setTokens((prev) => deriveTokens(null, prev));
        }

        setReady(true);
        return true;
      } catch (err: any) {
        setAuthenticated(false);
        setUser(null);
        setCsrfToken(null);
        setTokens(() => makeEmptyTokens());
        setError(err?.message || 'Login failed');
        setReady(true);
        return false;
      }
    },
    [authEndpoint, currentUserEndpoint],
  );

  const logout = useCallback(async () => {
    try {
      await logoutRequest({ endpoint: logoutEndpoint });
    } catch {
      // ignore logout errors
    }
    setAuthenticated(false);
    setUser(null);
    setCsrfToken(null);
    setTokens(() => makeEmptyTokens());
    setError(null);
    setReady(true);
  }, [logoutEndpoint]);

  useEffect(() => {
    setAuthLostHandler(() => {
      setAuthenticated(false);
      setUser(null);
      setCsrfToken(null);
      setTokens(() => makeEmptyTokens());
      setReady(true);
    });
    return () => setAuthLostHandler(undefined);
  }, []);

  const refresh = useCallback(async (): Promise<AuthContextUser | null> => {
    try {
      const current = await fetchCurrentUser({ endpoint: currentUserEndpoint });
      const normalized = normalizeAuthUser(current?.user ?? null);
      setUser(normalized);
      setAuthenticated(Boolean(normalized));
      setTokens((prev) => deriveTokens(null, prev));
      return normalized;
    } catch {
      setAuthenticated(false);
      setUser(null);
      setTokens(() => makeEmptyTokens());
      return null;
    }
  }, [currentUserEndpoint]);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    (async () => {
      try {
        const current = await fetchCurrentUser({
          endpoint: currentUserEndpoint,
          signal: controller.signal,
        });
        if (cancelled) {
          return;
        }
        const normalized = normalizeAuthUser(current?.user ?? null);
        setUser(normalized);
        setAuthenticated(Boolean(normalized));
      } catch {
        if (!cancelled) {
          setAuthenticated(false);
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setTokens((prev) => deriveTokens(null, prev));
          setReady(true);
        }
      }
    })();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [currentUserEndpoint]);

  const value = useMemo<AuthContextValue>(
    () => ({ isAuthenticated, isReady, errorMessage, user, tokens, login, logout, refresh }),
    [isAuthenticated, isReady, errorMessage, user, tokens, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}



