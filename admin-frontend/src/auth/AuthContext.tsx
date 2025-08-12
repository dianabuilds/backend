import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiFetch } from "../api/client";

interface User {
  id: string;
  email?: string | null;
  username?: string | null;
  role: string;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async () => {},
  logout: () => {},
});

function isAllowed(role: string): boolean {
  return role === "admin" || role === "moderator";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const logout = async () => {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } catch {}
    setUser(null);
  };

  const login = async (username: string, password: string) => {
    const resp = await fetch("/auth/login-json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const loginText = await resp.text();
    if (!resp.ok) {
      throw new Error(loginText || "Неверный логин или пароль");
    }
    let loginData: { ok: boolean };
    try {
      loginData = JSON.parse(loginText) as { ok: boolean };
    } catch {
      throw new Error("Некорректный ответ от сервера");
    }
    if (!loginData.ok) throw new Error("Неверный логин или пароль");
    const meResp = await apiFetch("/users/me");
    if (!meResp.ok) {
      throw new Error((await meResp.text()) || "Не удалось получить пользователя");
    }
    const me: User = await meResp.json();
    if (!isAllowed(me.role)) {
      throw new Error("Недостаточно прав");
    }
    setUser(me);
  };

  useEffect(() => {
    const init = async () => {
      try {
        const resp = await apiFetch("/users/me");
        if (!resp.ok) throw new Error();
        const me: User = await resp.json();
        if (isAllowed(me.role)) {
          setUser(me);
        } else {
          await logout();
        }
      } catch {
        await logout();
      }
    };
    init();
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}

