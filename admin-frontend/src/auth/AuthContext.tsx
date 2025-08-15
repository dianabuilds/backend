import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiFetch, setCsrfToken, syncCsrfFromResponse, setAccessToken, api } from "../api/client";

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
    setAccessToken(null);
    setUser(null);
  };

  const login = async (username: string, password: string) => {
    try {
      // Единый клиент: выставит Accept: application/json и credentials: include
      const res = await api.post<{ ok: boolean; csrf_token?: string; access_token?: string }>("/auth/login", {
        username,
        password,
      });

      const data = res.data!;
      if (!data.ok) {
        throw new Error("Неверный логин или пароль");
      }

      // Сохраняем CSRF и access_token (для Bearer)
      if (data.csrf_token) setCsrfToken(data.csrf_token);
      if (data.access_token) setAccessToken(data.access_token);

      // Запрашиваем профиль с Bearer из ответа, не полагаясь на моментальную установку cookie
      const meHeaders: Record<string, string> = {};
      if (data.access_token) {
        meHeaders["Authorization"] = `Bearer ${data.access_token}`;
      }
      const meRes = await api.get<User>("/users/me", { headers: meHeaders });
      const me = meRes.data as User;

      if (!isAllowed(me.role)) {
        throw new Error("Недостаточно прав");
      }
      setUser(me);
    } catch (e) {
      const err = e as Error;
      // Пробуем отобразить понятное сообщение
      const msg = err.message || "Ошибка авторизации";
      throw new Error(msg);
    }
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

