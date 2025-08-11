import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

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

  const logout = () => {
    localStorage.removeItem("token");
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
    let access_token: string;
    try {
      ({ access_token } = JSON.parse(loginText));
    } catch {
      throw new Error("Некорректный ответ от сервера");
    }
    const meResp = await fetch("/users/me", {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    const meText = await meResp.text();
    if (!meResp.ok) {
      throw new Error(meText || "Не удалось получить пользователя");
    }
    let me: User;
    try {
      me = JSON.parse(meText) as User;
    } catch {
      throw new Error("Некорректный ответ пользователя");
    }
    if (!isAllowed(me.role)) {
      throw new Error("Недостаточно прав");
    }
    localStorage.setItem("token", access_token);
    setUser(me);
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    const init = async () => {
      try {
        const resp = await fetch("/users/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const text = await resp.text();
        if (!resp.ok) throw new Error();
        const me: User = JSON.parse(text);
        if (isAllowed(me.role)) {
          setUser(me);
        } else {
          logout();
        }
      } catch {
        logout();
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

