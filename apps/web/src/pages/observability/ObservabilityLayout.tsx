import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Button, PageHeader, Surface } from '@ui';
import { ChartBarIcon } from '@heroicons/react/24/outline';

const links = [
  { to: '/observability', label: 'Overview', exact: true },
  { to: '/observability/api', label: 'API' },
  { to: '/observability/llm', label: 'LLM' },
  { to: '/observability/workers', label: 'Workers' },
  { to: '/observability/transitions', label: 'Transitions' },
  { to: '/observability/events', label: 'Events' },
  { to: '/observability/rum', label: 'RUM' },
];

type Props = {
  title?: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  stats?: Parameters<typeof PageHeader>[0]['stats'];
  children: React.ReactNode;
};

export function ObservabilityLayout({
  title = 'Telemetry and experience lab',
  description = 'Debug journeys, latency, and AI behaviour with cinematic monitoring panels.',
  actions,
  stats,
  children,
}: Props) {
  const defaultActions = (
    <Button as={Link} to="/observability/rum" variant="filled" className="shadow-[0_18px_45px_-25px_rgba(79,70,229,0.6)]">
      <ChartBarIcon className="size-4" /> Realtime RUM
    </Button>
  );

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHeader
        kicker="Telemetry"
        title={title}
        description={description}
        actions={actions ?? defaultActions}
        stats={stats}
      />

      <Surface variant="soft" className="px-3 py-3">
        <div className="custom-scrollbar -mx-1 overflow-x-auto px-1">
          <div className="flex gap-2">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.exact as any}
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 text-xs-plus font-semibold transition ${
                    isActive
                      ? 'bg-emerald-500 text-white shadow-[0_12px_30px_-18px_rgba(16,185,129,0.65)]'
                      : 'bg-white/70 text-gray-600 shadow-[0_6px_20px_-15px_rgba(17,24,39,0.4)] hover:text-emerald-600 dark:bg-dark-700/70 dark:text-dark-100'
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </div>
        </div>
      </Surface>

      {children}
    </div>
  );
}
