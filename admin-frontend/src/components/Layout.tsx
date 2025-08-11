import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Home, Users, Ban } from "lucide-react";
import { useAuth } from "../auth/AuthContext";

interface Props {
  children: ReactNode;
}

export default function Layout({ children }: Props) {
  const { user, logout } = useAuth();
  const menuItems = [
    { to: "/", label: "Dashboard", Icon: Home },
    { to: "/users", label: "Users", Icon: Users },
    { to: "/restrictions", label: "Restrictions", Icon: Ban },
  ];
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      <aside className="w-64 bg-white dark:bg-gray-900 p-4 shadow-sm">
        <nav className="space-y-2">
          {menuItems.map(({ to, label, Icon }) => (
            <Link key={to} to={to} className="flex items-center space-x-2 text-gray-700 dark:text-gray-200">
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </Link>
          ))}

        </nav>
      </aside>
      <main className="flex-1 p-6 overflow-y-auto">
        <div className="flex items-center justify-end mb-4">
          {user && (
            <div className="flex items-center gap-3 text-sm text-gray-700 dark:text-gray-200">
              <span>{user.username ?? user.email ?? user.id}</span>
              <span className="px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-800">{user.role}</span>
              <button
                onClick={logout}
                className="px-3 py-1 rounded bg-gray-800 text-white hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600"
              >
                Выйти
              </button>
            </div>
          )}
        </div>
        {children}
      </main>
    </div>
  );
}
