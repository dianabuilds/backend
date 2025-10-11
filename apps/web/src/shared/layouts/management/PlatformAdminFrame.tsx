import React from 'react';
import { AlertTriangle, ExternalLink, FileCode2, Link2, Users } from '@icons';
import { Badge, Button, Card, PageHeader } from '@ui';
import type {
  PlatformAdminChangelogEntry as SharedPlatformAdminChangelogEntry,
  PlatformAdminIntegrationSummary as SharedPlatformAdminIntegrationSummary,
  PlatformAdminQuickLink as SharedPlatformAdminQuickLink,
} from '@shared/types/management';
import type { PageHeaderStat } from '@ui/patterns/PageHeader';

export type PlatformAdminQuickLink = SharedPlatformAdminQuickLink;
export type PlatformAdminChangelogEntry = SharedPlatformAdminChangelogEntry;
export type PlatformAdminIntegration = SharedPlatformAdminIntegrationSummary;

export type PlatformAdminFrameProps = {
  title: string;
  description?: React.ReactNode;
  breadcrumbs?: Array<{ label: string; to?: string }>;
  actions?: React.ReactNode;
  stats?: PageHeaderStat[];
  roleHint?: React.ReactNode;
  quickLinks?: PlatformAdminQuickLink[];
  helpText?: React.ReactNode;
  slackUrl?: string | null;
  changelog?: PlatformAdminChangelogEntry[] | null;
  integrations?: PlatformAdminIntegration[] | null;
  children: React.ReactNode;
};

export function PlatformAdminFrame({
  title,
  description,
  breadcrumbs,
  actions,
  stats,
  roleHint,
  quickLinks,
  helpText,
  slackUrl,
  changelog,
  integrations,
  children,
}: PlatformAdminFrameProps) {
  const hasQuickLinks = Boolean(quickLinks && quickLinks.length);
  const hasHelpCopy = Boolean(helpText);
  const hasSlackLink = Boolean(slackUrl);
  const hasIntegrations = Boolean(integrations && integrations.length);
  const hasChangelog = Boolean(changelog && changelog.length);
  const hasAsideContent = Boolean(
    roleHint || hasQuickLinks || hasHelpCopy || hasSlackLink || hasIntegrations || hasChangelog,
  );

  const mainColumnClass = hasAsideContent ? 'space-y-6 lg:col-span-8' : 'space-y-6 lg:col-span-12';

  return (
    <div className="space-y-8">
      <PageHeader
        title={title}
        description={description}
        breadcrumbs={breadcrumbs}
        actions={actions}
        stats={stats}
        kicker="Platform Admin"
        pattern="subtle"
      />

      <div className="grid gap-6 lg:grid-cols-12">
        <div className={mainColumnClass}>{children}</div>
        {hasAsideContent ? (
          <aside className="space-y-6 lg:col-span-4">
            {roleHint ? <RoleHintCard>{roleHint}</RoleHintCard> : null}
            {hasQuickLinks || hasHelpCopy || hasSlackLink ? (
              <NeedHelpCard quickLinks={quickLinks} helpText={helpText} slackUrl={slackUrl ?? undefined} />
            ) : null}
            {hasIntegrations ? <IntegrationsCard items={integrations ?? []} /> : null}
            {hasChangelog ? <ChangelogCard entries={changelog ?? []} /> : null}
          </aside>
        ) : null}
      </div>
    </div>
  );
}

type RoleHintCardProps = {
  children: React.ReactNode;
};

function RoleHintCard({ children }: RoleHintCardProps) {
  return (
    <Card
      skin="bordered"
      className="space-y-3 border-primary-200/60 bg-primary-50/60 p-5 text-sm text-primary-700 shadow-soft dark:border-primary-500/30 dark:bg-primary-500/10 dark:text-primary-200"
    >
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-primary-600 dark:text-primary-300">
        <Users className="h-4 w-4" /> Доступ
      </div>
      <div className="space-y-2 leading-relaxed">{children}</div>
    </Card>
  );
}

type NeedHelpCardProps = {
  quickLinks?: PlatformAdminQuickLink[];
  helpText?: React.ReactNode;
  slackUrl?: string;
};

function NeedHelpCard({ quickLinks, helpText, slackUrl }: NeedHelpCardProps) {
  const hasQuickLinks = Boolean(quickLinks && quickLinks.length);
  return (
    <Card skin="shadow" className="space-y-4 p-6">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-5 w-5 text-primary-500" />
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Нужна помощь?</h3>
      </div>
      <p className="text-sm text-gray-600 dark:text-dark-100">
        {helpText || 'Используйте быстрые ссылки или обратитесь к команде поддержки.'}
      </p>
      {hasQuickLinks ? (
        <div className="space-y-3">
          {quickLinks!.map((link) => (
            <a
              key={link.href}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="group block rounded-xl border border-gray-200/70 p-3 transition hover:border-primary-200 hover:bg-primary-50/50 dark:border-dark-600 dark:hover:border-primary-500/50 dark:hover:bg-primary-500/10"
            >
              <span className="flex items-center justify-between gap-4">
                <span>
                  <span className="text-sm font-medium text-primary-600 dark:text-primary-300">{link.label}</span>
                  {link.description ? (
                    <span className="block text-xs text-gray-500 dark:text-dark-200">{link.description}</span>
                  ) : null}
                </span>
                <ExternalLink className="mt-0.5 h-4 w-4 text-gray-400 opacity-0 transition group-hover:opacity-100" />
              </span>
            </a>
          ))}
        </div>
      ) : null}
      {slackUrl ? (
        <Button
          as="a"
          href={slackUrl}
          target="_blank"
          rel="noopener noreferrer"
          variant="outlined"
          color="primary"
          className="w-full justify-center text-sm"
        >
          Открыть канал поддержки
        </Button>
      ) : null}
    </Card>
  );
}

type IntegrationsCardProps = {
  items: PlatformAdminIntegration[];
};

function IntegrationsCard({ items }: IntegrationsCardProps) {
  if (!items.length) return null;
  const colorForStatus = (status: string): 'success' | 'warning' | 'error' | 'neutral' => {
    const normalized = status.toLowerCase();
    if (["ok", "connected", "active"].includes(normalized)) return 'success';
    if (["warning", "pending", "degraded"].includes(normalized)) return 'warning';
    if (["error", "disconnected", "failed"].includes(normalized)) return 'error';
    return 'neutral';
  };
  return (
    <Card className="space-y-4 p-6">
      <div className="flex items-center gap-2">
        <Link2 className="h-5 w-5 text-primary-500" />
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Системные интеграции</h3>
      </div>
      <div className="space-y-3">
        {items.map((integration) => (
          <div key={integration.id} className="rounded-xl border border-gray-200/70 px-3 py-2 dark:border-dark-600">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-gray-900 dark:text-white">{integration.label}</span>
              <Badge color={colorForStatus(integration.status)} variant="soft">
                {integration.status}
              </Badge>
            </div>
            {integration.hint ? (
              <p className="mt-1 text-xs text-gray-500 dark:text-dark-200">{integration.hint}</p>
            ) : null}
            {integration.link ? (
              <a
                href={integration.link}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:underline dark:text-primary-300"
              >
                Открыть
                <ExternalLink className="h-3 w-3" />
              </a>
            ) : null}
          </div>
        ))}
      </div>
    </Card>
  );
}

type ChangelogCardProps = {
  entries: PlatformAdminChangelogEntry[];
};

function ChangelogCard({ entries }: ChangelogCardProps) {
  if (!entries.length) return null;
  return (
    <Card className="space-y-4 p-6">
      <div className="flex items-center gap-2">
        <FileCode2 className="h-5 w-5 text-primary-500" />
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Changelog</h3>
      </div>
      <div className="space-y-4">
        {entries.map((entry) => (
          <div key={entry.id} className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900 dark:text-white">{entry.title}</span>
              {entry.category ? (
                <Badge
                  color={
                    entry.category === 'feature'
                      ? 'primary'
                      : entry.category === 'improvement'
                      ? 'info'
                      : 'neutral'
                  }
                  variant="soft"
                >
                  {entry.category}
                </Badge>
              ) : null}
            </div>
            {entry.published_at ? (
              <div className="text-xs text-gray-500 dark:text-dark-200">
                {new Date(entry.published_at).toLocaleString()}
              </div>
            ) : null}
            {entry.highlights?.length ? (
              <ul className="space-y-1 text-xs text-gray-600 dark:text-dark-100">
                {entry.highlights.map((highlight: string, index: number) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="mt-1 h-1 w-1 rounded-full bg-primary-400" />
                    <span>{highlight}</span>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ))}
      </div>
    </Card>
  );
}
