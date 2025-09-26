import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { PageHeader } from '@ui';

type ContentTab = { to: string; label: React.ReactNode };

type ContentContext = 'legacy' | 'nodes' | 'quests' | 'notifications';

type LayoutPreset = {
  tabs: ContentTab[];
  description: React.ReactNode;
  actions: React.ReactNode;
};

const legacyTabs: ContentTab[] = [
  { to: '/content', label: 'Dashboard' },
  { to: '/content/nodes', label: 'Nodes' },
  { to: '/content/quests', label: 'Quests' },
  { to: '/content/tags', label: 'Tags' },
  { to: '/content/relations', label: 'Relations' },
  { to: '/content/worlds', label: 'Worlds' },
  { to: '/content/drafts', label: 'Drafts' },
  { to: '/content/import-export', label: 'Import & Export' },
];

const nodesTabs: ContentTab[] = [
  { to: '/nodes', label: 'Overview' },
  { to: '/nodes/library', label: 'Library' },
  { to: '/nodes/relations', label: 'Relations' },
  { to: '/nodes/tags', label: 'Tags' },
];

const questsTabs: ContentTab[] = [
  { to: '/quests', label: 'Overview' },
  { to: '/quests/library', label: 'Library' },
  { to: '/quests/worlds', label: 'Worlds' },
  { to: '/quests/tags', label: 'Tags' },
  { to: '/quests/ai-studio', label: 'AI Studio' },
];

const notificationsTabs: ContentTab[] = [
  { to: '/notifications', label: 'Broadcasts' },
  { to: '/notifications/templates', label: 'Templates' },
  { to: '/notifications/channels', label: 'Channels' },
  { to: '/notifications/history', label: 'History' },
];

const presetDescriptions: Record<ContentContext, React.ReactNode> = {
  legacy: 'Unified workspace for narrative objects, tagging, relations, and experimentation across the Flavour Trip worlds.',
  nodes: 'Dedicated cockpit for the narrative graph: monitor, grow, and curate nodes powering every player journey.',
  quests: 'Plan, validate, and launch quests with confidence - from authoring pipelines to AI-assisted ideation.',
  notifications: 'Coordinate announcements, automate broadcasts, and keep every player cohort informed.',
};

const buttonBase = 'btn-base btn h-9 rounded-full px-4 text-sm font-medium shadow-sm transition focus-visible:outline-none focus-visible:ring-2';
const primaryBtn = `${buttonBase} bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500/70`;
const outlineBtn = `${buttonBase} bg-white text-primary-600 ring-1 ring-primary-200 hover:bg-primary-50 focus-visible:ring-primary-500/70`;
const mutedBtn = `${buttonBase} bg-white/80 text-gray-700 ring-1 ring-gray-200 hover:bg-white focus-visible:ring-primary-500/40 dark:bg-dark-700/80 dark:text-dark-100 dark:ring-dark-500/60`;

const legacyActions = (
  <div className="flex flex-wrap items-center gap-2">
    <NavLink to="/nodes/new" className={primaryBtn}>
      New Node
    </NavLink>
    <NavLink to="/quests/new" className={outlineBtn}>
      New Quest
    </NavLink>
    <NavLink to="/quests/worlds/new" className={mutedBtn}>
      New World
    </NavLink>
  </div>
);

const nodesActions = (
  <div className="flex flex-wrap items-center gap-2">
    <NavLink to="/nodes/new" className={primaryBtn}>
      New Node
    </NavLink>
    <NavLink to="/tools/import-export?scope=nodes" className={outlineBtn}>
      Import / Export
    </NavLink>
    <NavLink to="/notifications?compose=nodes" className={mutedBtn}>
      Broadcast update
    </NavLink>
  </div>
);

const questsActions = (
  <div className="flex flex-wrap items-center gap-2">
    <NavLink to="/quests/new" className={primaryBtn}>
      New Quest
    </NavLink>
    <NavLink to="/tools/import-export?scope=quests" className={outlineBtn}>
      Import / Export
    </NavLink>
    <NavLink to="/notifications?compose=quests" className={mutedBtn}>
      Broadcast quest
    </NavLink>
  </div>
);

const notificationsActions = (
  <div className="flex flex-wrap items-center gap-2">
    <NavLink to="/notifications?compose=1" className={primaryBtn}>
      New broadcast
    </NavLink>
    <NavLink to="/notifications/templates" className={outlineBtn}>
      Manage templates
    </NavLink>
  </div>
);

const contextPresets: Record<ContentContext, LayoutPreset> = {
  legacy: { tabs: legacyTabs, description: presetDescriptions.legacy, actions: legacyActions },
  nodes: { tabs: nodesTabs, description: presetDescriptions.nodes, actions: nodesActions },
  quests: { tabs: questsTabs, description: presetDescriptions.quests, actions: questsActions },
  notifications: { tabs: notificationsTabs, description: presetDescriptions.notifications, actions: notificationsActions },
};

type ContentLayoutProps = {
  children: React.ReactNode;
  title?: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  tabs?: Array<{ to: string; label: React.ReactNode }>;
  stats?: Parameters<typeof PageHeader>[0]['stats'];
  breadcrumbs?: Parameters<typeof PageHeader>[0]['breadcrumbs'];
  kicker?: Parameters<typeof PageHeader>[0]['kicker'];
  context?: ContentContext;
};

export function ContentLayout({
  children,
  title = 'Content Hub',
  description,
  actions,
  tabs,
  stats,
  breadcrumbs,
  kicker,
  context = 'legacy',
}: ContentLayoutProps) {
  const location = useLocation();
  const activePath = location.pathname.replace(/\/$/, '');
  const preset = contextPresets[context];
  const resolvedTabs = tabs ?? preset.tabs;
  const resolvedDescription = description ?? preset.description;
  const resolvedActions = actions ?? preset.actions;
  const tabEntries = React.useMemo(() => resolvedTabs.map((tab) => ({ tab, target: tab.to.replace(/\/$/, '') })), [resolvedTabs]);
  const activeTabEntry = React.useMemo(
    () =>
      tabEntries.reduce<{ tab: ContentTab; target: string } | null>((best, entry) => {
        const { target } = entry;
        if (activePath === target || activePath.startsWith(`${target}/`)) {
          if (!best || target.length > best.target.length) {
            return entry;
          }
        }
        return best;
      }, null),
    [tabEntries, activePath],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        description={resolvedDescription}
        actions={resolvedActions}
        stats={stats}
        breadcrumbs={breadcrumbs}
        kicker={kicker}
        pattern="subtle"
      />

      {resolvedTabs.length > 0 && (
        <div className="custom-scrollbar -mx-4 overflow-x-auto px-4">
          <nav className="flex gap-2 pb-1">
            {tabEntries.map(({ tab }) => {
              const isActive = activeTabEntry?.tab === tab;
              return (
                <NavLink
                  key={tab.to}
                  to={tab.to}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                    isActive
                      ? 'bg-primary-600 text-white shadow-sm'
                      : 'bg-white/70 text-gray-600 ring-1 ring-gray-200 hover:bg-white hover:text-gray-900 dark:bg-dark-700/70 dark:text-dark-100 dark:ring-dark-500/60 dark:hover:bg-dark-650'
                  }`}
                >
                  {tab.label}
                </NavLink>
              );
            })}
          </nav>
        </div>
      )}

      <div className="space-y-6">{children}</div>
    </div>
  );
}

