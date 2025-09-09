import { Link, Outlet } from 'react-router-dom';

import { useAuth } from '../../auth/AuthContext';
import AdminOverrideBanner from '../../components/AdminOverrideBanner';
import AlertsBadge from '../../components/AlertsBadge';
import Breadcrumbs from '../../components/Breadcrumbs';
import EnvBanner from '../../components/EnvBanner';
import HotfixBanner from '../../components/HotfixBanner';
import Sidebar from '../../components/Sidebar';
import SystemStatus from '../../components/SystemStatus';

export default function AdminLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      <Sidebar />
      <main className="flex-1 p-6 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2" />
          <div className="flex items-center gap-4">
            <AlertsBadge />
            <SystemStatus />
            {user && (
              <div className="flex items-center gap-3 text-sm text-gray-700 dark:text-gray-200">
                <Link to="/profile" className="hover:underline">
                  {user.username ?? user.email ?? user.id}
                </Link>
                <span className="px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-800">
                  {user.role}
                </span>
                <button
                  onClick={logout}
                  className="px-3 py-1 rounded bg-gray-800 text-white hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600"
                >
                  Выйти
                </button>
              </div>
            )}
          </div>
        </div>
        <EnvBanner />
        <HotfixBanner />
        <AdminOverrideBanner />
        <Breadcrumbs />
        <Outlet />
      </main>
    </div>
  );
}
