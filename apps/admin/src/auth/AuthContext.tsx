import { createContext, type ReactNode, useContext, useEffect, useState } from 'react';

import { api, apiFetch, setCsrfToken, syncCsrfFromResponse } from '../api/client';

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
  hasRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async () => {},
  logout: () => {},
  ready: false,
  hasRole: () => false,
});

function isAllowed(role: string): boolean {
  return role === 'admin' || role === 'moderator' || role === 'support';
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState<boolean>(false);

  const logout = async () => {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } catch {
      // игнорируем — цель только локально очистить состояние
    }
    setCsrfToken(null);
    setUser(null);
  };

  const login = async (username: string, password: string) => {
    try {
      // 1) Логин: увеличенный тайм-аут (60с), чтобы исключить обрыв на медленных стендах.
      // Отправляем данные как form-data, чтобы избежать preflight-запроса CORS
      const form = new URLSearchParams();
      form.set('username', username);
      form.set('password', password);
      const resp = await apiFetch('/auth/login', {
        method: 'POST',
        body: form,
        timeoutMs: 60000,
      });

      const data = (await resp.json()) as {
        ok: boolean;
        csrf_token?: string;
      };
      if (!resp.ok || !data.ok) {
        throw new Error('Неверный логин или пароль');
      }

      // Сохраняем CSRF
      if (data.csrf_token) setCsrfToken(data.csrf_token);

      // 2) Профиль после успешного логина
      const meRes = await api.get<User>('/users/me', { timeoutMs: 60000 });
      const me = meRes.data as User;
      if (!me) throw new Error('Не удалось получить профиль');

      if (!isAllowed(me.role)) {
        throw new Error('Недостаточно прав');
      }
      setUser(me);
    } catch (e) {
      const err = e as Error;
      // Нормализуем тайм-аут
      const raw = String(err?.message || '');
      const msg =
        raw === 'RequestTimeout'
          ? 'Превышено время ожидания ответа сервера. Проверьте соединение и попробуйте ещё раз.'
          : raw || 'Ошибка авторизации';
      throw new Error(msg);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        let resp = await apiFetch('/users/me');

        // Если не авторизованы по access — пробуем обновить сессию и повторить запрос
        if (resp.status === 401) {
          try {
            const refresh = await apiFetch('/auth/refresh', { method: 'POST' });
            if (refresh.ok) {
              await syncCsrfFromResponse(refresh);
              resp = await apiFetch('/users/me');
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
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        ready,
        hasRole: (...roles) => (user ? roles.includes(user.role) : false),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}
