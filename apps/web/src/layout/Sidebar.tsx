import React from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import {
  ChevronDownIcon,
  BellIcon,
  Cog6ToothIcon,
  ShieldCheckIcon,
  Squares2X2Icon,
  DocumentTextIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../shared/auth';

type Group = {
  base: string;
  label: string;
  icon: React.ReactElement;
  children: Array<{ to: string; label: string }>;
};

type Section = {
  title: string;
  groups: Group[];
};

const sections: Section[] = [
  {
    title: 'Workspace',
    groups: [
      {
        base: '/nodes',
        label: 'Nodes',
        icon: <DocumentTextIcon className="h-5 w-5 text-gray-400 dark:text-dark-300" />,
        children: [
          { to: '/nodes', label: 'Overview' },
          { to: '/nodes/library', label: 'Library' },
          { to: '/nodes/relations', label: 'Relations' },
          { to: '/nodes/tags', label: 'Tags' },
        ],
      },
      {
        base: '/quests',
        label: 'Quests',
        icon: <UserGroupIcon className="h-5 w-5 text-gray-400 dark:text-dark-300" />,
        children: [
          { to: '/quests', label: 'Overview' },
          { to: '/quests/library', label: 'Library' },
          { to: '/quests/worlds', label: 'Worlds' },
          { to: '/quests/tags', label: 'Tags' },
          { to: '/quests/ai-studio', label: 'AI Studio' },
        ],
      },
    ],
  },
  {
    title: 'Engagement',
    groups: [
      {
        base: '/notifications',
        label: 'Notifications',
        icon: <BellIcon className="h-5 w-5 text-gray-400 dark:text-dark-300" />,
        children: [
          { to: '/notifications', label: 'Broadcasts' },
          { to: '/notifications/templates', label: 'Templates' },
          { to: '/notifications/channels', label: 'Channels' },
          { to: '/notifications/history', label: 'History' },
        ],
      },
    ],
  },
  {
    title: 'Revenue',
    groups: [
      {
        base: '/billing',
        label: 'Billing & Plans',
        icon: <CurrencyDollarIcon className="h-5 w-5 text-gray-400 dark:text-dark-300" />,
        children: [
          { to: '/billing', label: 'Overview' },
          { to: '/billing/payments', label: 'Payments' },
          { to: '/billing/payments/monitoring', label: 'Payments Monitoring' },
          { to: '/billing/tariffs', label: 'Tariffs' },
        ],
      },
    ],
  },
  {
    title: 'Operations',
    groups: [
      {
        base: '/platform',
        label: 'Platform Admin',
        icon: <Cog6ToothIcon className="h-5 w-5 text-gray-400 dark:text-dark-300" />,
        children: [
          { to: '/platform/ai', label: 'AI & LLM' },
          { to: '/platform/flags', label: 'Feature Flags' },
          { to: '/platform/integrations', label: 'Integrations' },
          { to: '/platform/system', label: 'System' },
          { to: '/platform/audit', label: 'Audit Logs' },
        ],
      },
      {
        base: '/observability',
        label: 'Observability',
        icon: <ChartBarIcon className="h-5 w-5 text-gray-400 dark:text-dark-300" />,
        children: [
          { to: '/observability', label: 'Overview' },
          { to: '/observability/api', label: 'API' },
          { to: '/observability/llm', label: 'LLM' },
          { to: '/observability/workers', label: 'Workers' },
          { to: '/observability/transitions', label: 'Transitions' },
          { to: '/observability/events', label: 'Events' },
          { to: '/observability/rum', label: 'RUM' },
        ],
      },
    ],
  },
  {
    title: 'Guardrails',
    groups: [
      {
        base: '/moderation',
        label: 'Moderation',
        icon: <ShieldCheckIcon className="h-5 w-5 text-gray-400 dark:text-dark-300" />,
        children: [
          { to: '/moderation', label: 'Overview' },
          { to: '/moderation/users', label: 'Users' },
          { to: '/moderation/content', label: 'Content' },
          { to: '/moderation/reports', label: 'Reports' },
          { to: '/moderation/tickets', label: 'Tickets' },
          { to: '/moderation/appeals', label: 'Appeals' },
          { to: '/moderation/ai-rules', label: 'AI Rules' },
        ],
      },
    ],
  },
];


function buildInitialState(pathname: string) {
  const state: Record<string, boolean> = {};
  for (const section of sections) {
    for (const group of section.groups) {
      state[group.base] = pathname.startsWith(group.base);
    }
  }
  return state;
}

export function Sidebar() {
  const { pathname } = useLocation();
  const { logout } = useAuth();
  const [open, setOpen] = React.useState<Record<string, boolean>>(() => buildInitialState(pathname));

  React.useEffect(() => {
    setOpen((prev) => {
      const next = { ...prev };
      for (const section of sections) {
        for (const group of section.groups) {
          if (pathname.startsWith(group.base)) {
            next[group.base] = true;
          }
        }
      }
      return next;
    });
  }, [pathname]);

  return (
    <aside className="sidebar-panel ltr:border-r rtl:border-l border-gray-200 dark:border-dark-600/80 bg-white dark:bg-dark-900 w-64 shrink-0 min-h-100vh">
      <div className="flex h-full flex-col">
        <header className="relative flex h-[61px] shrink-0 items-center justify-between ltr:pl-6 ltr:pr-3 rtl:pl-3 rtl:pr-6">
          <Link to="/" className="text-[18px] font-semibold tracking-wide text-gray-800 dark:text-dark-100">Tailux</Link>
        </header>

        <div className="flex min-h-0 flex-1 flex-col">
          <nav className="flex-1 overflow-y-auto pb-6">
            <div className="px-3 pt-3">
              <NavLink
                to="/dashboard"
                end
                className={({ isActive }) =>
                  `group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 ring-1 ring-inset ring-primary-100 dark:bg-primary-500/10 dark:text-primary-200 dark:ring-primary-500/20'
                      : 'text-gray-800 hover:bg-gray-100 hover:text-gray-950 dark:text-dark-100 dark:hover:bg-dark-700/50'
                  }`
                }
              >
                <Squares2X2Icon className="size-5 shrink-0 text-gray-500 dark:text-dark-300" />
                <span className="truncate">Dashboard</span>
              </NavLink>
            </div>

            <div className="mt-4 space-y-4">
              {sections.map((section) => (
                <div key={section.title} className="space-y-1">
                  <div className="px-6 text-[10px] font-semibold uppercase tracking-[0.32em] text-gray-400/80 dark:text-dark-400">
                    {section.title}
                  </div>
                  {section.groups.map((group) => {
                    const headerActive = pathname.startsWith(group.base);
                    const opened = open[group.base] ?? false;
                    return (
                      <div key={group.base} className="px-3">
                        <button
                          type="button"
                          onClick={() => setOpen((s) => ({ ...s, [group.base]: !opened }))}
                          className={`group flex w-full items-center justify-between rounded-lg px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] transition ${
                            headerActive
                              ? 'bg-primary-50 text-primary-700 ring-1 ring-inset ring-primary-100 dark:bg-primary-500/10 dark:text-primary-200 dark:ring-primary-500/20'
                              : 'text-gray-500 hover:bg-gray-100/70 hover:text-gray-800 dark:text-dark-300 dark:hover:bg-dark-700/40 dark:hover:text-dark-100'
                          }`}
                        >
                          <span className="flex items-center gap-3">
                            <span className="flex items-center justify-center rounded-md bg-white/80 p-2 shadow-sm shadow-gray-200 ring-1 ring-gray-200 transition group-hover:bg-white dark:bg-dark-800 dark:shadow-none dark:ring-dark-600">
                              {group.icon}
                            </span>
                            <span className="text-xs tracking-normal text-gray-700 dark:text-dark-50">
                              {group.label}
                            </span>
                          </span>
                          <ChevronDownIcon className={`h-4 w-4 transition-transform ${opened ? 'rotate-180' : ''}`} />
                        </button>
                        <div className={opened ? 'mt-1 space-y-1' : 'hidden'}>
                          {group.children.map((child) => (
                            <NavLink
                              key={child.to}
                              to={child.to}
                              end
                              className={({ isActive }) =>
                                `group relative block rounded-md text-sm font-medium transition-colors ${
                                  isActive
                                    ? 'bg-primary-50 text-primary-700 ring-1 ring-inset ring-primary-100 dark:bg-primary-500/10 dark:text-primary-200 dark:ring-primary-500/20'
                                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-dark-200 dark:hover:bg-dark-700/50 dark:hover:text-dark-50'
                                }`
                              }
                            >
                              {({ isActive }) => (
                                <div className="flex items-center gap-3 px-4 py-2">
                                  <span
                                    className={`h-2 w-2 rounded-full transition ${
                                      isActive
                                        ? 'bg-primary-500 dark:bg-primary-300'
                                        : 'bg-gray-300 group-hover:bg-gray-400 dark:bg-dark-500 dark:group-hover:bg-dark-300'
                                    }`}
                                  />
                                  <span className="truncate">{child.label}</span>
                                </div>
                              )}
                            </NavLink>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </nav>

          <div className="border-t border-gray-200 px-6 py-4 text-sm dark:border-dark-600">
            <button
              type="button"
              onClick={logout}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-gray-200 bg-gray-50 py-2 text-sm font-semibold text-gray-700 transition hover:bg-gray-100 dark:border-dark-600 dark:bg-dark-700 dark:text-dark-100 dark:hover:bg-dark-600"
            >
              Sign out
            </button>
            <div className="mt-3 text-xs text-gray-400 dark:text-dark-400">
              Flavour Trip Control - build {new Date().getFullYear()}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}


