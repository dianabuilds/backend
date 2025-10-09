import React from 'react';
import { Badge, Button, Spinner, Table } from '@ui';
import { NotificationSurface, notificationTableHeadCellClass, notificationTableRowClass } from '../../common/NotificationSurface';
import { formatDateTime } from '@shared/utils/format';
import type {
  NotificationChannelOverview,
  NotificationTopicOverview,
} from '@shared/types/notifications';
import { useNotificationsChannelsOverview } from '../../common/hooks';

const STATUS_META: Record<NotificationChannelOverview['status'], { label: string; color: 'warning' | 'info' | 'neutral' }> = {
  required: { label: 'Required', color: 'warning' },
  recommended: { label: 'Recommended', color: 'info' },
  optional: { label: 'Optional', color: 'neutral' },
};

const DELIVERY_LABELS: Record<string, string> = {
  mandatory: 'Mandatory',
  default_on: 'Default on',
  opt_in: 'Opt-in',
};

const DELIVERY_HINTS: Record<string, string> = {
  mandatory: 'Delivered automatically for every user.',
  default_on: 'Enabled by default, users may opt out.',
  opt_in: 'Disabled by default unless explicitly enabled.',
};

type SummaryProps = {
  channels: NotificationChannelOverview[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  onRefresh: () => void;
  activeChannels?: number;
  totalChannels?: number;
  emailDigest?: string | null;
  updatedAt?: string | null;
};

function SummaryCards({
  channels,
  loading,
  refreshing,
  error,
  onRefresh,
  activeChannels,
  totalChannels,
  emailDigest,
  updatedAt,
}: SummaryProps) {
  if (loading) {
    return (
      <div className="flex min-h-[160px] items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-indigo-600">
          <Spinner size="sm" />
          <span>Loading channels?</span>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">Notifications</div>
          <h2 className="text-2xl font-semibold text-gray-900">Channel coverage</h2>
          <p className="text-sm text-gray-600">
            Monitor which delivery paths are available to end users and how they are configured by default.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outlined" color="neutral" onClick={onRefresh} disabled={refreshing || loading}>
            {refreshing ? 'Refreshing?' : 'Refresh'}
          </Button>
        </div>
      </div>
      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      ) : null}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
          <div className="text-xs uppercase tracking-wide text-gray-500">Active channels</div>
          <div className="mt-2 text-2xl font-semibold text-gray-900">
            {activeChannels ?? 0}
            <span className="text-base font-medium text-gray-400"> / {totalChannels ?? channels.length}</span>
          </div>
          <p className="mt-1 text-xs text-gray-500">Counted across all delivery media.</p>
        </div>
        <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
          <div className="text-xs uppercase tracking-wide text-gray-500">Email digest mode</div>
          <div className="mt-2 text-2xl font-semibold text-gray-900">{emailDigest ?? 'instant'}</div>
          <p className="mt-1 text-xs text-gray-500">Most common digest cadence for email broadcasts.</p>
        </div>
        <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
          <div className="text-xs uppercase tracking-wide text-gray-500">Last update</div>
          <div className="mt-2 text-lg font-semibold text-gray-900">{formatDateTime(updatedAt) || '?'}</div>
          <p className="mt-1 text-xs text-gray-500">Latest change made by the user or operator.</p>
        </div>
      </div>
    </>
  );
}

function ChannelsTable({ channels }: { channels: NotificationChannelOverview[] }) {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-800">Channel status</h3>
      </div>
      <div className="hide-scrollbar overflow-x-auto">
        <Table.Table className="min-w-[720px] text-left rtl:text-right">
          <Table.THead>
            <Table.TR>
              <Table.TH className={`${notificationTableHeadCellClass} w-[40%]`}>Channel</Table.TH>
              <Table.TH className={`${notificationTableHeadCellClass} w-[20%]`}>Status</Table.TH>
              <Table.TH className={`${notificationTableHeadCellClass} w-[20%]`}>Default state</Table.TH>
              <Table.TH className={`${notificationTableHeadCellClass} w-[20%]`}>Notes</Table.TH>
            </Table.TR>
          </Table.THead>
          <Table.TBody>
            {channels.map((channel) => {
              const statusMeta = STATUS_META[channel.status] ?? STATUS_META.optional;
              return (
                <Table.TR key={channel.key} className={notificationTableRowClass}>
                  <Table.TD className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 dark:text-dark-50">{channel.label}</div>
                    <div className="text-xs text-gray-500">{channel.key}</div>
                  </Table.TD>
                  <Table.TD className="px-6 py-4">
                    <Badge color={statusMeta.color} variant="soft">
                      {statusMeta.label}
                    </Badge>
                  </Table.TD>
                  <Table.TD className="px-6 py-4">
                    <Badge color={channel.opt_in ? 'success' : 'neutral'} variant="soft">
                      {channel.opt_in ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </Table.TD>
                  <Table.TD className="px-6 py-4 text-sm text-gray-500">
                    {channel.status === 'required'
                      ? 'Enforced for every user.'
                      : channel.status === 'recommended'
                      ? 'Enabled by default with opt-out available.'
                      : 'Users opt in manually.'}
                  </Table.TD>
                </Table.TR>
              );
            })}
          </Table.TBody>
        </Table.Table>
      </div>
    </section>
  );
}

function TopicsGrid({ topics }: { topics: NotificationTopicOverview[] }) {
  return (
    <section className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-800">Topics & delivery rules</h3>
      <div className="space-y-4">
        {topics.map((topic) => (
          <div key={topic.key} className="space-y-3 rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
            <div className="flex flex-col gap-1">
              <div className="text-sm font-semibold text-gray-900">{topic.label}</div>
              {topic.description ? <p className="text-xs text-gray-500">{topic.description}</p> : null}
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {topic.channels.map((channel) => {
                const deliveryLabel = DELIVERY_LABELS[channel.delivery] ?? channel.delivery;
                const deliveryHint = DELIVERY_HINTS[channel.delivery] ?? '';
                return (
                  <div key={channel.key} className="space-y-2 rounded-xl border border-indigo-100/60 bg-white/90 p-3 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{channel.label}</div>
                        <div className="text-xs text-gray-500">{deliveryLabel}</div>
                      </div>
                      <Badge color={channel.opt_in ? 'success' : 'neutral'} variant="soft">
                        {channel.opt_in ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    {deliveryHint ? <p className="text-xs text-gray-500">{deliveryHint}</p> : null}
                    {channel.locked ? <Badge color="warning" variant="soft">Locked</Badge> : null}
                    {channel.supports_digest && channel.digest ? (
                      <p className="text-xs text-gray-500">Digest cadence: {channel.digest}</p>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
        {topics.length === 0 && (
          <div className="rounded-2xl border border-dashed border-gray-200 p-6 text-sm text-gray-500">
            No topics found in the notification matrix.
          </div>
        )}
      </div>
    </section>
  );
}

export function NotificationChannels(): React.ReactElement {
  const { overview, loading, refreshing, error, reload } = useNotificationsChannelsOverview();
  const channels = overview?.channels ?? [];
  const topics = overview?.topics ?? [];
  const summary = overview?.summary;

  return (
    <NotificationSurface className="space-y-6 p-6">
      <SummaryCards
        channels={channels}
        loading={loading}
        refreshing={refreshing}
        error={error}
        onRefresh={() => void reload('refresh')}
        activeChannels={summary?.active_channels}
        totalChannels={summary?.total_channels}
        emailDigest={summary?.email_digest}
        updatedAt={summary?.updated_at}
      />
      {!loading && overview ? (
        <>
          <ChannelsTable channels={channels} />
          <TopicsGrid topics={topics} />
        </>
      ) : null}
    </NotificationSurface>
  );
}
