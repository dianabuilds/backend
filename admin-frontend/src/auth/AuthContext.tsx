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
    if (!resp.ok) {
      throw new Error("Неверный логин или пароль");
    }
    const { access_token } = await resp.json();
    const meResp = await fetch("/users/me", {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    if (!meResp.ok) {
      throw new Error("Не удалось получить пользователя");
    }
    const me: User = await meResp.json();
    if (!isAllowed(me.role)) {
      throw new Error("Недостаточно прав");
    }
    localStorage.setItem("token", access_token);
    setUser(me);
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    fetch("/users/me", { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => (res.ok ? res.json() : null))
      .then((me) => {
        if (me && isAllowed(me.role)) {
          setUser(me);
        } else {
          logout();
        }
      })
      .catch(() => logout());
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

