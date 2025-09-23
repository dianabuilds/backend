import React from 'react';
import { useAuth } from '../shared/auth/AuthContext';
import { apiGet } from '../shared/api/client';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRightOnRectangleIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import AlarmIconUrl from '@/assets/dualicons/alarm.svg';
import UserIconUrl from '@/assets/nav-icons/user.svg';

export function Topbar() {
  const { user, logout, isAuthenticated, isReady } = useAuth();
  const [inbox, setInbox] = React.useState<any[]>([]);
  const [notifOpen, setNotifOpen] = React.useState(false);
  const [userOpen, setUserOpen] = React.useState(false);
  const nav = useNavigate();
  const notifRef = React.useRef<HTMLDivElement | null>(null);
  const userRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (!isReady || !isAuthenticated) return;
    (async () => {
      try {
        const r = await apiGet('/v1/notifications?limit=10');
        setInbox(r?.items || []);
      } catch {}
    })();
  }, [isReady, isAuthenticated]);

  React.useEffect(() => {
    function onDocClick(e: MouseEvent) {
      const t = e.target as Node;
      if (notifRef.current && !notifRef.current.contains(t)) setNotifOpen(false);
      if (userRef.current && !userRef.current.contains(t)) setUserOpen(false);
    }
    function onEsc(e: KeyboardEvent) { if (e.key === 'Escape') { setNotifOpen(false); setUserOpen(false); } }
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onEsc);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onEsc);
    };
  }, []);

  const onLogout = async () => {
    await logout();
    nav('/login');
  };

  return (
    <header className="app-header sticky top-0 z-20 flex h-[65px] shrink-0 items-center justify-between border-b border-gray-200 bg-white/80 px-4 backdrop-blur-sm backdrop-saturate-150 dark:border-dark-600 dark:bg-dark-900/80">
      <div className="flex items-center gap-2">
        <button className="h-8 w-64 justify-between gap-2 rounded-full border border-gray-200 px-3 text-xs-plus hover:border-gray-400 dark:border-dark-500 dark:hover:border-dark-400 max-sm:hidden flex items-center">
          <div className="flex items-center gap-2 text-gray-400 dark:text-dark-300">
            <MagnifyingGlassIcon className="size-4" />
            <span>Search here...</span>
          </div>
          <span className="text-gray-400">/</span>
        </button>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative" ref={notifRef}>
          <button
            className="relative size-9 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-dark-700"
            onClick={() => setNotifOpen((v) => !v)}
          >
            <span className="sr-only">Notifications</span>
            <img src={AlarmIconUrl} alt="" className="size-6" />
            {inbox.length > 0 && (
              <span className="absolute top-0 ltr:right-0 rtl:left-0 m-1 inline-flex h-2.5 w-2.5 rounded-full bg-error ring-2 ring-white dark:ring-dark-900" />
            )}
          </button>
          {notifOpen && (
            <div className="absolute right-0 mt-2 w-80 rounded-lg border border-gray-150 bg-white shadow-soft dark:border-dark-800 dark:bg-dark-700">
              <div className="p-2">
                <div className="px-2 pb-1 text-xs text-gray-400">Notifications</div>
                <ul className="max-h-72 overflow-auto">
                  {inbox.length === 0 ? (
                    <li className="px-3 py-2 text-sm text-gray-500">No notifications</li>
                  ) : (
                    inbox.map((n) => (
                      <li key={n.id} className="rounded-md px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-dark-600">
                        <div className="font-medium">{n.title || 'Message'}</div>
                        <div className="text-xs text-gray-500">{n.message}</div>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>
          )}
        </div>

        <div className="relative" ref={userRef}>
          <button className="size-9 rounded-full flex items-center justify-center hover:bg-gray-100 dark:hover:bg-dark-700" onClick={() => setUserOpen((v) => !v)}>
            <img src={UserIconUrl} alt="" className="size-6" />
          </button>
          {userOpen && (
            <div className="absolute right-0 mt-2 w-72 rounded-xl border border-gray-200 bg-white p-3 shadow-soft dark:border-dark-600 dark:bg-dark-800">
              <div className="flex items-center gap-3 p-2">
                <img src="/images/avatar/avatar-5.jpg" alt="User avatar" className="h-10 w-10 rounded-full object-cover" />
                <div>
                  <div className="font-medium">{user?.username || 'User'}</div>
                  <div className="text-xs text-gray-500">{user?.email || ''}</div>
                </div>
              </div>
              <div className="mt-2 space-y-1 text-sm">
                <Link className="block rounded-md px-3 py-2 hover:bg-gray-100 dark:hover:bg-dark-700" to="/profile" onClick={() => setUserOpen(false)}>Profile</Link>
                <Link className="block rounded-md px-3 py-2 hover:bg-gray-100 dark:hover:bg-dark-700" to="/notifications" onClick={() => setUserOpen(false)}>Notifications</Link>
                <Link className="block rounded-md px-3 py-2 hover:bg-gray-100 dark:hover:bg-dark-700" to="/billing" onClick={() => setUserOpen(false)}>Billing</Link>
              </div>
              <button onClick={onLogout} className="mt-3 w-full btn-base btn bg-gray-150 text-gray-900 hover:bg-gray-200 flex items-center justify-center gap-2">
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
