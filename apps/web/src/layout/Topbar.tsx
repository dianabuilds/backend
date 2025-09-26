import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../shared/auth/AuthContext';
import { apiGet, apiPost } from '../shared/api/client';
import {
  ArrowRightOnRectangleIcon,
  ChevronRightIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  BellAlertIcon,
  CreditCardIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import AlarmIconUrl from '@/assets/dualicons/alarm.svg';
import { Spinner } from '@ui';

interface ProfileSummary {
  avatar_url?: string | null;
}

type InboxNotification = {
  id: string;
  title?: string | null;
  message?: string | null;
  created_at?: string | null;
  read_at?: string | null;
  priority?: string | null;
};

type InboxResponse = { items?: InboxNotification[]; unread?: number };

type UserMenuItem = {
  to: string;
  label: string;
  description: string;
  accent: string;
  Icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
};

const USER_MENU_ITEMS: UserMenuItem[] = [
  {
    to: '/profile',
    label: 'Profile',
    description: 'Personal info and visibility',
    accent: 'bg-amber-500',
    Icon: UserCircleIcon,
  },
  {
    to: '/notifications',
    label: 'Notifications',
    description: 'Broadcasts & updates',
    accent: 'bg-sky-500',
    Icon: BellAlertIcon,
  },
  {
    to: '/billing',
    label: 'Billing',
    description: 'Plans, invoices and usage',
    accent: 'bg-rose-500',
    Icon: CreditCardIcon,
  },
  {
    to: '/settings/notifications',
    label: 'Settings',
    description: 'Preferences & automation',
    accent: 'bg-emerald-500',
    Icon: Cog6ToothIcon,
  },
];

function formatRelativeTime(value?: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const diff = Date.now() - date.getTime();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) return 'just now';
  if (diff < hour) {
    const mins = Math.round(diff / minute);
    return `${mins}m ago`;
  }
  if (diff < day) {
    const hrs = Math.round(diff / hour);
    return `${hrs}h ago`;
  }
  const days = Math.round(diff / day);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString();
}

export function Topbar(): React.ReactElement {
  const { user, logout, isAuthenticated, isReady } = useAuth();
  const [inbox, setInbox] = React.useState<InboxNotification[]>([]);
  const [unreadTotal, setUnreadTotal] = React.useState(0);
  const [inboxLoading, setInboxLoading] = React.useState(false);
  const [marking, setMarking] = React.useState<Record<string, boolean>>({});
  const [notifOpen, setNotifOpen] = React.useState(false);
  const [userOpen, setUserOpen] = React.useState(false);
  const [profileAvatar, setProfileAvatar] = React.useState<string | null>(null);
  const [avatarBroken, setAvatarBroken] = React.useState(false);
  const nav = useNavigate();
  const notifRef = React.useRef<HTMLDivElement | null>(null);
  const userRef = React.useRef<HTMLDivElement | null>(null);

  const refreshInbox = React.useCallback(async () => {
    if (!isReady || !isAuthenticated) {
      setInbox([]);
      setUnreadTotal(0);
      return;
    }
    setInboxLoading(true);
    try {
      const response = await apiGet<InboxResponse>('/v1/notifications?limit=8');
      const rows = Array.isArray(response?.items) ? response.items : [];
      const unread = typeof response?.unread === 'number' ? response.unread : rows.filter((item) => !item.read_at).length;
      setInbox(rows);
      setUnreadTotal(unread);
    } catch {
      setInbox([]);
      setUnreadTotal(0);
    } finally {
      setInboxLoading(false);
    }
  }, [isAuthenticated, isReady]);

  React.useEffect(() => {
    void refreshInbox();
  }, [refreshInbox]);

  React.useEffect(() => {
    const handler = () => {
      void refreshInbox();
    };
    window.addEventListener('notifications:refresh', handler);
    return () => {
      window.removeEventListener('notifications:refresh', handler);
    };
  }, [refreshInbox]);

  React.useEffect(() => {
    if (!isReady || !isAuthenticated) return;
    let active = true;
    (async () => {
      try {
        const profile = (await apiGet('/v1/profile/me')) as ProfileSummary;
        if (!active) return;
        const avatar = typeof profile?.avatar_url === 'string' ? profile.avatar_url.trim() : '';
        setProfileAvatar(avatar || null);
      } catch {
        if (!active) return;
      }
    })();
    return () => {
      active = false;
    };
  }, [isReady, isAuthenticated]);

  React.useEffect(() => {
    function onDocClick(event: MouseEvent) {
      const target = event.target as Node;
      if (notifRef.current && !notifRef.current.contains(target)) setNotifOpen(false);
      if (userRef.current && !userRef.current.contains(target)) setUserOpen(false);
    }
    function onEsc(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setNotifOpen(false);
        setUserOpen(false);
      }
    }
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onEsc);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onEsc);
    };
  }, []);

  React.useEffect(() => {
    if (notifOpen) {
      void refreshInbox();
    }
  }, [notifOpen, refreshInbox]);

  const handleLogout = async () => {
    setUserOpen(false);
    await logout();
    nav('/login');
  };

  const displayName = user?.username || user?.email || 'User';
  const secondaryLine = user?.email || user?.username || '';
  const initials = React.useMemo(() => {
    if (!displayName) return 'U';
    const segments = displayName.trim().split(/\s+/).filter(Boolean);
    if (segments.length === 0) return 'U';
    const letters = segments.map((part) => part.charAt(0)?.toUpperCase() || '').join('');
    return letters.slice(0, 2) || 'U';
  }, [displayName]);
  const fallbackAvatar = React.useMemo(() => {
    const seed = encodeURIComponent(displayName || 'user');
    const textParam = encodeURIComponent(initials || 'U');
    return `https://avatar.vercel.sh/${seed}.svg?text=${textParam}&background=f0f2f8`;
  }, [displayName, initials]);
  const profileAvatarNormalized = typeof profileAvatar === 'string' ? profileAvatar.trim() : '';
  const userAvatarNormalized = (user as any)?.avatar_url ? String((user as any)?.avatar_url).trim() : '';
  const baseAvatar = profileAvatarNormalized || userAvatarNormalized || null;
  React.useEffect(() => {
    setAvatarBroken(false);
  }, [baseAvatar]);
  const resolvedAvatar = !baseAvatar || avatarBroken ? fallbackAvatar : baseAvatar;

  const hasUnread = unreadTotal > 0;

  const handleToggleNotifications = () => {
    setNotifOpen((prev) => {
      const next = !prev;
      if (!prev) {
        void refreshInbox();
      }
      return next;
    });
  };

  const handleMarkRead = React.useCallback(
    async (notificationId: string) => {
      setMarking((prev) => ({ ...prev, [notificationId]: true }));
      try {
        const response = await apiPost<{ notification?: InboxNotification }>(
          `/v1/notifications/read/${notificationId}`,
          {},
        );
        const updated = response?.notification;
        const fallbackReadAt = new Date().toISOString();
        let wasUnread = false;
        setInbox((prev) =>
          prev.map((item) => {
            if (item.id !== notificationId) {
              return item;
            }
            if (!item.read_at) {
              wasUnread = true;
            }
            return {
              ...item,
              ...(updated ?? {}),
              read_at:
                updated?.read_at ??
                updated?.created_at ??
                item.read_at ??
                fallbackReadAt,
            };
          }),
        );
        if (wasUnread) {
          setUnreadTotal((value) => (value > 0 ? value - 1 : 0));
        }
        window.dispatchEvent(new CustomEvent('notifications:refresh'));
      } catch {
        // ignore dropdown errors
      } finally {
        setMarking((prev) => {
          const next = { ...prev };
          delete next[notificationId];
          return next;
        });
      }
    },
    [],
  );

  return (
    <header className="app-header sticky top-0 z-20 flex h-[65px] shrink-0 items-center justify-between border-b border-gray-200 bg-white/85 px-4 backdrop-blur-sm backdrop-saturate-150 dark:border-dark-600 dark:bg-dark-900/80">
      <div className="flex items-center gap-2">
        <button className="max-sm:hidden flex h-8 w-64 items-center justify-between gap-2 rounded-full border border-gray-200 px-3 text-xs-plus text-gray-400 transition hover:border-gray-400 hover:text-gray-500 dark:border-dark-500 dark:text-dark-300 dark:hover:border-dark-400">
          <span className="flex items-center gap-2">
            <MagnifyingGlassIcon className="size-4" />
            <span>Search here...</span>
          </span>
          <span className="text-gray-400">/</span>
        </button>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative" ref={notifRef}>
          <button
            className="flex size-9 items-center justify-center rounded-full transition hover:bg-gray-100 dark:hover:bg-dark-700"
            onClick={handleToggleNotifications}
          >
            <span className="sr-only">Notifications</span>
            <img src={AlarmIconUrl} alt="" className="size-6" />
            {hasUnread && (
              <span className="absolute top-0 ltr:right-0 rtl:left-0 m-1 inline-flex h-2.5 w-2.5 rounded-full bg-error ring-2 ring-white dark:ring-dark-900" />
            )}
          </button>
          {notifOpen && (
            <div className="absolute right-0 mt-2 w-80 rounded-lg border border-gray-150 bg-white shadow-soft dark:border-dark-800 dark:bg-dark-700">
              <div className="p-2">
                <div className="flex items-center justify-between px-2 pb-1 text-xs text-gray-400">
                  <span>Notifications</span>
                  <button
                    type="button"
                    className="text-[11px] font-medium uppercase tracking-wide text-primary-600 hover:text-primary-500"
                    onClick={() => void refreshInbox()}
                    disabled={inboxLoading}
                  >
                    Refresh
                  </button>
                </div>
                <ul className="max-h-72 overflow-auto">
                  {inboxLoading ? (
                    <li className="px-3 py-6 text-sm text-gray-500">
                      <div className="flex items-center justify-center gap-2 text-indigo-600 dark:text-dark-200">
                        <Spinner size="sm" />
                        <span>Loading...</span>
                      </div>
                    </li>
                  ) : inbox.length === 0 ? (
                    <li className="px-3 py-2 text-sm text-gray-500">No notifications yet</li>
                  ) : (
                    inbox.map((item) => (
                      <li
                        key={item.id}
                        className={`rounded-md px-3 py-2 text-sm transition hover:bg-gray-100 dark:hover:bg-dark-600 ${
                          item.read_at ? '' : 'bg-indigo-50/60 dark:bg-dark-700/70'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900 dark:text-dark-50">
                                {item.title || 'Message'}
                              </span>
                              {!item.read_at && <span className="inline-flex h-2 w-2 rounded-full bg-primary-500" />}
                            </div>
                            {item.message && (
                              <div className="mt-0.5 text-xs text-gray-500 dark:text-dark-200">
                                {item.message}
                              </div>
                            )}
                            <div className="mt-1 text-[11px] uppercase tracking-wide text-gray-400">
                              {formatRelativeTime(item.created_at)}
                            </div>
                          </div>
                          <button
                            type="button"
                            className="text-[11px] font-semibold uppercase tracking-wide text-primary-600 hover:text-primary-500"
                            onClick={() => handleMarkRead(item.id)}
                            disabled={!!item.read_at || marking[item.id]}
                          >
                            {marking[item.id] ? '...' : item.read_at ? 'Read' : 'Mark as read'}
                          </button>
                        </div>
                      </li>
                    ))
                  )}
                </ul>
                <div className="mt-2 flex justify-end">
                  <Link
                    to="/settings/notifications/inbox"
                    onClick={() => setNotifOpen(false)}
                    className="inline-flex items-center gap-1 rounded-md px-3 py-2 text-xs font-semibold text-primary-600 transition hover:bg-primary-600/10"
                  >
                    View inbox
                    <ChevronRightIcon className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="relative" ref={userRef}>
          <button
            className="relative flex size-10 items-center justify-center rounded-full border border-gray-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-dark-600 dark:bg-dark-700"
            onClick={() => setUserOpen((v) => !v)}
          >
            <img
              src={resolvedAvatar}
              alt={displayName}
              className="h-9 w-9 rounded-full object-cover"
              onError={() => setAvatarBroken(true)}
            />
            <span className="absolute bottom-1 right-1 inline-flex h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500 dark:border-dark-700" />
          </button>
          {userOpen && (
            <div className="absolute right-0 mt-3 w-80 rounded-3xl border border-gray-200/80 bg-white/95 p-4 shadow-xl shadow-gray-200/70 backdrop-blur-md dark:border-dark-600 dark:bg-dark-800/95 dark:shadow-none">
              <div className="flex items-center gap-3 rounded-2xl bg-gradient-to-br from-slate-50 via-white to-slate-100 px-3 py-4 dark:from-dark-700 dark:via-dark-700/90 dark:to-dark-600/80">
                <div className="relative">
                  <img
                    src={resolvedAvatar}
                    alt={displayName}
                    className="h-12 w-12 rounded-full object-cover shadow-sm"
                    onError={() => setAvatarBroken(true)}
                  />
                  <span className="absolute bottom-0 right-0 inline-flex h-3 w-3 rounded-full border-2 border-white bg-emerald-500 dark:border-dark-700" />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-gray-900 dark:text-dark-50">{displayName}</div>
                  <div className="truncate text-xs text-gray-500 dark:text-dark-200">{secondaryLine}</div>
                </div>
              </div>

              <div className="mt-4 space-y-1.5">
                {USER_MENU_ITEMS.map((item) => {
                  const Icon = item.Icon;
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      onClick={() => setUserOpen(false)}
                      className="group flex items-center gap-3 rounded-2xl px-3 py-2.5 transition hover:bg-gray-100/80 hover:shadow-sm dark:hover:bg-dark-700/60"
                    >
                      <span className={`flex h-10 w-10 items-center justify-center rounded-xl text-white shadow-sm ${item.accent}`}>
                        <Icon className="h-5 w-5" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-semibold text-gray-900 dark:text-dark-50">{item.label}</span>
                        <span className="block text-xs text-gray-500 group-hover:text-gray-600 dark:text-dark-200 dark:group-hover:text-dark-100">
                          {item.description}
                        </span>
                      </span>
                      <ChevronRightIcon className="h-4 w-4 text-gray-300 transition group-hover:text-gray-400 dark:text-dark-300" />
                    </Link>
                  );
                })}
              </div>

              <button
                type="button"
                onClick={handleLogout}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl border border-gray-200 bg-gray-50 py-2.5 text-sm font-semibold text-gray-700 transition hover:bg-gray-100 dark:border-dark-600 dark:bg-dark-700 dark:text-dark-100 dark:hover:bg-dark-600"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}


