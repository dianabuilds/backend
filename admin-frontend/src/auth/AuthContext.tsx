import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiFetch, setCsrfToken, syncCsrfFromResponse } from "../api/client";

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
  ready: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async () => {},
  logout: () => {},
  ready: false,
});

function isAllowed(role: string): boolean {
  return role === "admin" || role === "moderator";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState<boolean>(false);

  const logout = async () => {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } catch {
      // игнорируем — цель только локально очистить состояние
    }
    setCsrfToken(null);
    setUser(null);
  };

  const login = async (username: string, password: string) => {
    const resp = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password }),
    });

    const loginText = await resp.text();
    if (!resp.ok) {
      // пробуем вытащить detail/message из ответа
      try {
        const err = JSON.parse(loginText) as { detail?: string; message?: string };
        throw new Error(err.detail || err.message || loginText || "Неверный логин или пароль");
      } catch {
        throw new Error(loginText || "Неверный логин или пароль");
      }
    }

    // синхронизируем CSRF и разбираем access_token
    await syncCsrfFromResponse(new Response(loginText, { headers: { "Content-Type": "application/json" } }));
    let loginData: { ok: boolean; csrf_token?: string; access_token?: string };
    try {
      loginData = JSON.parse(loginText) as { ok: boolean; csrf_token?: string; access_token?: string };
    } catch {
      throw new Error("Некорректный ответ от сервера");
    }
    if (!loginData.ok) throw new Error("Неверный логин или пароль");
    if (loginData.csrf_token) setCsrfToken(loginData.csrf_token);

    // Делаем /users/me с Bearer из ответа, не полагаясь на моментальную установку cookie
    const meHeaders: Record<string, string> = {};
    if (loginData.access_token) {
      meHeaders["Authorization"] = `Bearer ${loginData.access_token}`;
    }
    const meResp = await apiFetch("/users/me", { headers: meHeaders });
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
        let resp = await apiFetch("/users/me");

        // Если не авторизованы по access — пробуем обновить сессию и повторить запрос
        if (resp.status === 401) {
          try {
            const refresh = await apiFetch("/auth/refresh", { method: "POST" });
            if (refresh.ok) {
              await syncCsrfFromResponse(refresh);
              resp = await apiFetch("/users/me");
            }
          } catch {
            // игнорируем — просто оставим пользователя неавторизованным
          }
        }

        if (!resp.ok) {
          return;
        }

        const me: User = await resp.json();
        if (isAllowed(me.role)) {
          setUser(me);
        } else {
          await logout();
        }
      } catch {
        // На старте не выполняем logout — не сбрасываем refresh/сессию
      } finally {
        setReady(true);
      }
    };
    init();
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, ready }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}

