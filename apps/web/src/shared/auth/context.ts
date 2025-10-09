import { createContext, useContext } from 'react';

export type LoginArgs = { login: string; password: string; remember?: boolean };

export type AuthContextUser = {
  id?: string;
  username?: string;
  displayName?: string;
  avatarUrl?: string | null;
  email?: string;
  role?: string;
  roles: string[];
  isActive?: boolean;
  authSource?: string;
  metadata?: Record<string, unknown> | null;
};

export type AuthTokens = {
  accessToken: string | null;
  refreshToken: string | null;
  csrfToken: string | null;
  expiresAt: number | null;
  tokenType: string | null;
};

export type AuthContextValue = {
  isAuthenticated: boolean;
  isReady: boolean;
  errorMessage: string | null;
  user: AuthContextUser | null;
  tokens: AuthTokens;
  login: (args: LoginArgs) => Promise<boolean>;
  logout: () => Promise<void>;
  refresh: () => Promise<AuthContextUser | null>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}

export { AuthContext, useAuthContext as useAuth };
