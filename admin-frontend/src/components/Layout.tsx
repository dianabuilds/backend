import { Outlet, Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import Sidebar from "./Sidebar";
import WorkspaceSelector from "./WorkspaceSelector";
import HotfixBanner from "./HotfixBanner";

export default function Layout() {
  const { user, logout } = useAuth();
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      <Sidebar />
      <main className="flex-1 p-6 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <WorkspaceSelector />
          {user && (
            <div className="flex items-center gap-3 text-sm text-gray-700 dark:text-gray-200">
              <Link to="/profile" className="hover:underline">
                {user.username ?? user.email ?? user.id}
              </Link>
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
        <HotfixBanner />
        <Outlet />
      </main>
    </div>
  );
}
