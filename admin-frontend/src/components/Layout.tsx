import { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Home, Users } from "lucide-react";

interface Props {
  children: ReactNode;
}

export default function Layout({ children }: Props) {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      <aside className="w-64 bg-white dark:bg-gray-900 p-4 shadow-sm">
        <nav className="space-y-2">
          <Link to="/" className="flex items-center space-x-2 text-gray-700 dark:text-gray-200">
            <Home className="w-4 h-4" />
            <span>Dashboard</span>
          </Link>
          <Link to="/users" className="flex items-center space-x-2 text-gray-700 dark:text-gray-200">
            <Users className="w-4 h-4" />
            <span>Users</span>
          </Link>
        </nav>
      </aside>
      <main className="flex-1 p-6 overflow-y-auto">{children}</main>
    </div>
  );
}
