import React, { useCallback, useEffect, useMemo, useState } from 'react';

import { apiGet, apiPost, decodeJwt, setAuthLostHandler, setCsrfToken } from '../api/client';
import { AuthContext, AuthContextValue, LoginArgs } from './context';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setAuthenticated] = useState(false);
  const [isReady, setReady] = useState(false);
  const [errorMessage, setError] = useState<string | null>(null);
  const [user, setUser] = useState<AuthContextValue['user']>(null);

  const base = (import.meta as any).env.VITE_API_BASE as string | undefined;
  const endpoint = (import.meta as any).env.VITE_AUTH_ENDPOINT || '/v1/auth/login';

  const login = useCallback(async ({ login: identifier, password, remember }: LoginArgs) => {
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        login: identifier,
        password,
      };
      if (typeof remember === 'boolean') {
        payload.remember = remember;
      }
      const res = await apiPost(((import.meta as any).env.DEV ? '' : base || '') + endpoint, payload);
      setCsrfToken((res as any)?.csrf_token as string | undefined);
      const access = res?.access_token as string | undefined;
      const userData = res?.user as any;
      const authSource = (res as any)?.auth?.source as string | undefined;
      if (!access) throw new Error('Login failed');
      setAuthenticated(true);
      const claims = decodeJwt<any>(access) || {};
      let nextUser = userData ?? null;
      if (!nextUser) {
        nextUser = {
          id: claims.sub ? String(claims.sub) : undefined,
          username: claims.username,
          email: claims.email || (claims.sub ? String(claims.sub) : undefined),
        };
      }
      if (nextUser) {
        if (claims.role && !nextUser.role) nextUser.role = claims.role;
        if (!nextUser.roles && nextUser.role) nextUser.roles = [nextUser.role];
        if (authSource) nextUser.authSource = authSource;
      }
      setUser(nextUser);
      try {
        const me = await apiGet('/v1/users/me');
        if (me?.user) setUser(me.user);
      } catch {
        // ignore
      }
      setReady(true);
      return true;
    } catch (e: any) {
      setAuthenticated(false);
      setUser(null);
      setCsrfToken(null);
      setError(e?.message || 'Login failed');
      setReady(true);
      return false;
    }
  }, [base, endpoint]);

  const logout = useCallback(async () => {
    try {
      await apiPost('/v1/auth/logout', {});
    } catch {
      // ignore logout errors
    }
    setAuthenticated(false);
    setUser(null);
    setCsrfToken(null);
    setReady(true);
  }, []);

  useEffect(() => {
    setAuthLostHandler(() => {
      setAuthenticated(false);
      setUser(null);
      setCsrfToken(null);
      setReady(true);
    });
    return () => setAuthLostHandler(undefined);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const me = await apiGet('/v1/users/me');
        if (me?.user) {
          setUser(me.user);
          setAuthenticated(true);
          setReady(true);
          return;
        }
      } catch {
        // ignore
      }
      setReady(true);
    })();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ isAuthenticated, isReady, errorMessage, user, login, logout }),
    [isAuthenticated, isReady, errorMessage, user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

