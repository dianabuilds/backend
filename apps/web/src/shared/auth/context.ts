import { createContext, useContext } from 'react';

type LoginArgs = { login: string; password: string; remember?: boolean };

type AuthContextValue = {
  isAuthenticated: boolean;
  isReady: boolean;
  errorMessage: string | null;
  user: { id?: string; username?: string; email?: string; role?: string; roles?: string[]; is_active?: boolean; authSource?: string } | null;
  login: (args: LoginArgs) => Promise<boolean>;
  logout: () => void;
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
export type { AuthContextValue, LoginArgs };
