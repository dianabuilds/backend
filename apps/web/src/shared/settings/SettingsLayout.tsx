import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { Card } from '../ui';

export type SettingsNavItem = {
  key: string;
  label: string;
  description: string;
  path: string;
};

const SETTINGS_NAV: SettingsNavItem[] = [
  { key: 'profile', label: 'Profile', description: 'Identity & avatar', path: '/profile' },
  { key: 'security', label: 'Security', description: 'Passwords & sessions', path: '/settings/security' },
  { key: 'notifications', label: 'Notifications', description: 'Channels & digests', path: '/settings/notifications' },
  { key: 'notifications-inbox', label: 'Inbox', description: 'Recent alerts', path: '/settings/notifications/inbox' },
  { key: 'billing', label: 'Billing', description: 'Plan & payouts', path: '/billing' },
];

type SettingsLayoutProps = {
  title: string;
  description: string;
  error?: React.ReactNode;
  children: React.ReactNode;
  side?: React.ReactNode;
};

export function SettingsLayout({ title, description, error, children, side }: SettingsLayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 pb-12">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
        <p className="mt-1 text-sm text-gray-500">{description}</p>
      </div>

      {error}

      <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[220px_minmax(0,1fr)] lg:items-start">
        <aside className="order-last lg:order-first">
          <Card className="sticky top-6 space-y-4 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm">
            <div>
              <h2 className="text-sm font-semibold text-gray-700">Settings navigation</h2>
              <p className="mt-1 text-xs text-gray-500">Jump between profile, security, notifications and billing.</p>
            </div>
            <div className="space-y-1">
              {SETTINGS_NAV.map((item) => {
                const active =
                  location.pathname === item.path ||
                  (item.key === 'notifications' && location.pathname === '/settings/notifications') ||
                  (item.key === 'notifications-inbox' && location.pathname.startsWith('/settings/notifications/inbox')) ||
                  (item.key === 'security' && location.pathname.startsWith('/settings/security'));
                return (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => {
                      if (!active) navigate(item.path);
                    }}
                    className={
                      active
                        ? 'w-full rounded-2xl px-3 py-2 text-left text-sm transition bg-primary-50 text-primary-700 ring-1 ring-primary-100'
                        : 'w-full rounded-2xl px-3 py-2 text-left text-sm transition text-gray-600 hover:bg-gray-100/70 hover:text-gray-900'
                    }
                    aria-current={active ? 'page' : undefined}
                    disabled={active}
                  >
                    <div className="font-medium">{item.label}</div>
                    <div className="text-xs text-gray-500">{item.description}</div>
                  </button>
                );
              })}
            </div>
          </Card>
        </aside>

        <div className="flex flex-col gap-6">
          <div className={side ? 'flex flex-col gap-6 xl:flex-row' : 'flex flex-col gap-6'}>
            <div className={side ? 'flex-1' : 'w-full'}>{children}</div>
            {side ? <div className="flex w-full flex-col gap-6 xl:w-[22rem]">{side}</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
