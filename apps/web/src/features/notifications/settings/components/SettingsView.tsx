import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge, Button, Card, Select, Spinner, Switch } from '@ui';
import { SettingsLayout } from '@shared/settings/SettingsLayout';
import { useSettingsIdempotencyHeader } from '@shared/settings';
import { WalletConnectionCard } from '@shared/settings/WalletConnectionCard';
import { extractErrorMessage } from '@shared/utils/errors';
import { makeIdempotencyKey } from '@shared/utils/idempotency';
import { fetchNotificationPreferences, updateNotificationPreferences } from '@shared/api/notifications';
import type { NotificationPreferences } from '@shared/types/notifications';
import { NotificationSurface } from '../../common/NotificationSurface';

type PreferencesMap = NotificationPreferences;

type TopicMeta = {
  category?: string;
  display_name?: string;
  description?: string | null;
  position?: number;
};

type ChannelMeta = {
  category?: string;
  display_name?: string;
  description?: string | null;
  supports_digest?: boolean;
  requires_consent?: boolean;
  position?: number;
};

type ChannelState = {
  opt_in: boolean;
  digest?: string | null;
  locked?: boolean;
  delivery?: string;
  supports_digest?: boolean;
  requires_consent?: boolean;
};

type TopicView = {
  key: string;
  label: string;
  description?: string | null;
  channels: ChannelView[];
};

type ChannelView = {
  topicKey: string;
  key: string;
  label: string;
  description?: string | null;
  optIn: boolean;
  locked: boolean;
  delivery: string;
  supportsDigest: boolean;
  requiresConsent: boolean;
  digest?: string | null;
};

function deepClone<T>(value: T): T {
  if (value == null) return value;
  return JSON.parse(JSON.stringify(value));
}

function buildPayload(preferences: PreferencesMap): PreferencesMap {
  const payload: PreferencesMap = {};
  for (const [topicKey, topicValue] of Object.entries(preferences)) {
    if (topicKey.startsWith('__')) continue;
    if (!topicValue || typeof topicValue !== 'object') continue;
    const topicPayload: Record<string, any> = {};
    for (const [channelKey, raw] of Object.entries(topicValue as Record<string, any>)) {
      if (!raw || typeof raw !== 'object') continue;
      const entry: Record<string, any> = {};
      if ('opt_in' in raw) entry.opt_in = Boolean((raw as ChannelState).opt_in);
      if ('digest' in raw && (raw as ChannelState).digest) entry.digest = (raw as ChannelState).digest;
      if ('quiet_hours' in raw) entry.quiet_hours = (raw as any).quiet_hours;
      topicPayload[channelKey] = entry;
    }
    if (Object.keys(topicPayload).length) {
      payload[topicKey] = topicPayload;
    }
  }
  return payload;
}

function useRetentionConfig(): { days: number; maxPerUser: number } {
  const daysRaw = (import.meta as any).env?.VITE_NOTIFICATIONS_RETENTION_DAYS;
  const maxRaw = (import.meta as any).env?.VITE_NOTIFICATIONS_MAX_PER_USER;
  const days = Number.parseInt(daysRaw ?? '', 10);
  const maxPerUser = Number.parseInt(maxRaw ?? '', 10);
  return {
    days: Number.isFinite(days) && days > 0 ? days : 90,
    maxPerUser: Number.isFinite(maxPerUser) && maxPerUser > 0 ? maxPerUser : 200,
  };
}

const DELIVERY_BADGES: Record<string, { color: 'info' | 'primary' | 'neutral'; label: string }> = {
  mandatory: { color: 'info', label: 'Required' },
  default_on: { color: 'primary', label: 'Default on' },
  opt_in: { color: 'neutral', label: 'Opt-in' },
};

const DIGEST_OPTIONS = [
  { value: 'instant', label: 'Instant' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'none', label: 'Disabled' },
];

function deriveTopics(preferences: PreferencesMap | null): TopicView[] {
  if (!preferences) return [];
  const topicsMeta = (preferences['__topics'] ?? {}) as Record<string, TopicMeta>;
  const channelsMeta = (preferences['__channels'] ?? {}) as Record<string, ChannelMeta>;
  return Object.keys(topicsMeta)
    .sort((a, b) => {
      const left = topicsMeta[a]?.position ?? 0;
      const right = topicsMeta[b]?.position ?? 0;
      return left - right;
    })
    .map((topicKey) => {
      const topicEntry = topicsMeta[topicKey] ?? {};
      const rawChannels = (preferences[topicKey] as Record<string, any>) ?? {};
      const channels = Object.keys(rawChannels)
        .sort((a, b) => {
          const left = channelsMeta[a]?.position ?? 0;
          const right = channelsMeta[b]?.position ?? 0;
          return left - right;
        })
        .map((channelKey) => {
          const meta = channelsMeta[channelKey] ?? {};
          const raw = (rawChannels[channelKey] ?? {}) as ChannelState;
          return {
            topicKey,
            key: channelKey,
            label: meta.display_name ?? channelKey,
            description: meta.description,
            optIn: !!raw.opt_in,
            locked: !!raw.locked,
            delivery: raw.delivery ?? 'opt_in',
            supportsDigest: Boolean(raw.supports_digest),
            requiresConsent: Boolean(raw.requires_consent ?? meta.requires_consent),
            digest: raw.digest ?? null,
          };
        });
      return {
        key: topicKey,
        label: topicEntry.display_name ?? topicKey,
        description: topicEntry.description,
        channels,
      };
    })
    .filter((topic) => topic.channels.length > 0);
}

export default function NotificationSettingsView(): React.ReactElement {
  const navigate = useNavigate();
  const idempotencyHeader = useSettingsIdempotencyHeader();
  const { days, maxPerUser } = useRetentionConfig();

  const [preferences, setPreferences] = React.useState<PreferencesMap | null>(null);
  const [baseline, setBaseline] = React.useState<PreferencesMap | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [dirty, setDirty] = React.useState(false);
  const [flash, setFlash] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [etag, setEtag] = React.useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = React.useState<number | null>(null);

  const loadPreferences = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { preferences: fetched, etag: nextEtag } = await fetchNotificationPreferences();
      const next = deepClone(fetched);
      setPreferences(next);
      setBaseline(deepClone(next));
      setDirty(false);
      setEtag(nextEtag);
    } catch (err) {
      const message = extractErrorMessage(err, 'Failed to load notification preferences');
      setError(
        message?.startsWith('Request failed')
          ? 'Notification preferences are temporarily unavailable.'
          : message,
      );
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadPreferences();
  }, [loadPreferences]);

  React.useEffect(() => {
    if (!flash) return;
    const timer = window.setTimeout(() => setFlash(null), 3500);
    return () => window.clearTimeout(timer);
  }, [flash]);

  const topics = React.useMemo(() => deriveTopics(preferences), [preferences]);
  const totalChannels = React.useMemo(
    () => topics.reduce((total, topic) => total + topic.channels.length, 0),
    [topics],
  );
  const activeChannels = React.useMemo(
    () => topics.reduce((total, topic) => total + topic.channels.filter((c) => c.optIn).length, 0),
    [topics],
  );
  const digestFrequency = React.useMemo(() => {
    for (const topic of topics) {
      for (const channel of topic.channels) {
        if (channel.supportsDigest && channel.optIn) {
          const entry = DIGEST_OPTIONS.find((option) => option.value === channel.digest);
          return entry?.label ?? 'Daily';
        }
      }
    }
    return 'Disabled';
  }, [topics]);
  const customizationOptions = React.useMemo(() => {
    const features = new Set<string>();
    let hasToggleable = false;
    let hasDigest = false;
    let hasConsent = false;
    for (const topic of topics) {
      for (const channel of topic.channels) {
        if (!channel.locked) {
          hasToggleable = true;
        }
        if (channel.supportsDigest) {
          hasDigest = true;
        }
        if (channel.requiresConsent) {
          hasConsent = true;
        }
      }
    }
    if (hasToggleable) {
      features.add('Enable or disable individual channels');
    }
    if (hasDigest) {
      features.add('Choose digest frequency where it is supported');
    }
    if (hasConsent) {
      features.add('Capture explicit consent before joining certain channels');
    }
    features.add('Send yourself a test notification safely');
    features.add('Reset notification preferences at any time');
    return Array.from(features);
  }, [topics]);

  const lastSavedLabel = React.useMemo(() => {
    if (!lastSavedAt) return 'Not yet saved';
    return new Date(lastSavedAt).toLocaleString();
  }, [lastSavedAt]);

  const updateChannel = React.useCallback(
    (topicKey: string, channelKey: string, updater: (channel: ChannelState) => ChannelState) => {
      setPreferences((prev) => {
        if (!prev) return prev;
        const next = deepClone(prev);
        const topic = (next[topicKey] as Record<string, any>) ?? {};
        const current = (topic[channelKey] as ChannelState) ?? {};
        topic[channelKey] = updater({ ...current });
        next[topicKey] = topic;
        return next;
      });
      setDirty(true);
      setFlash(null);
    },
    [],
  );

  const handleToggle = React.useCallback(
    (topicKey: string, channelKey: string, locked: boolean, enabled: boolean) => {
      if (locked) return;
      updateChannel(topicKey, channelKey, (channel) => ({
        ...channel,
        opt_in: enabled,
      }));
    },
    [updateChannel],
  );

  const handleDigestChange = React.useCallback(
    (topicKey: string, channelKey: string, value: string) => {
      updateChannel(topicKey, channelKey, (channel) => ({
        ...channel,
        digest: value,
        opt_in: channel.locked ? true : channel.opt_in ?? true,
      }));
    },
    [updateChannel],
  );

  const savePreferences = React.useCallback(async () => {
    if (saving || !dirty || !preferences) return;
    setSaving(true);
    setError(null);
    try {
      const payload = buildPayload(preferences);
      const headers: Record<string, string> = { [idempotencyHeader]: makeIdempotencyKey() };
      if (etag) headers['If-Match'] = etag;
      const { preferences: updated, etag: nextEtag } = await updateNotificationPreferences(payload, {
        headers,
      });
      const next = deepClone(updated);
      setPreferences(next);
      setBaseline(deepClone(next));
      setDirty(false);
      setEtag(nextEtag);
      setLastSavedAt(Date.now());
      setFlash('Preferences saved.');
    } catch (err) {
      const message = extractErrorMessage(err, 'Failed to save notification preferences');
      setError(
        message?.startsWith('Request failed')
          ? 'Unable to save preferences right now.'
          : message,
      );
    } finally {
      setSaving(false);
    }
  }, [dirty, etag, idempotencyHeader, preferences, saving]);

  const resetChanges = React.useCallback(() => {
    setPreferences(baseline ? deepClone(baseline) : baseline);
    setDirty(false);
    setFlash(null);
  }, [baseline]);

  const handleSendTest = React.useCallback((label: string) => {
    setFlash(`Queued a test notification via ${label}.`);
  }, []);

  const errorBanner = error ? (
    <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
  ) : null;

  const sidePanel = loading ? (
    <Card className="flex items-center gap-2 p-5 text-sm text-gray-500">
      <Spinner size="sm" /> Loading summary...
    </Card>
  ) : (
    <>
      <Card className="space-y-4 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm">
        <div className="flex items-start justify-between">
          <h2 className="text-sm font-semibold text-gray-700">Snapshot</h2>
          <Badge color="neutral" variant="soft">
            Overview
          </Badge>
        </div>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex items-center justify-between">
            <span>Active channels</span>
            <span className="font-semibold text-gray-900">
              {activeChannels}/{totalChannels}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Email digest</span>
            <span className="font-semibold text-gray-900">{digestFrequency}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Last updated</span>
            <span className="font-semibold text-gray-900">{lastSavedLabel}</span>
          </div>
        </div>
      </Card>
      <Card className="space-y-4 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm">
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-gray-700">Personalise delivery</h2>
          <p className="text-xs text-gray-500">
            Keep inbox noise low while mission-critical alerts still arrive on time.
          </p>
        </div>
        <ul className="list-disc space-y-1 pl-5 text-xs text-gray-500">
          {customizationOptions.map((item) => (
            <li key={item} className="leading-relaxed">
              {item}
            </li>
          ))}
        </ul>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            size="sm"
            variant="ghost"
            color="neutral"
            onClick={() => navigate('/settings/notifications/inbox')}
          >
            Open inbox
          </Button>
          <Button type="button" size="sm" color="primary" onClick={() => navigate('/notifications')}>
            Notifications hub
          </Button>
        </div>
      </Card>
      <WalletConnectionCard />
    </>
  );

  return (
    <SettingsLayout
      title="Personal delivery settings"
      description={`Tune how and where we reach you. Inbox keeps notifications for ${days} days (latest ${maxPerUser} entries).`}
      error={errorBanner}
      side={sidePanel}
    >
      {loading || !preferences ? (
        <NotificationSurface className="flex flex-1 items-center justify-center gap-3 p-6 sm:p-8 text-sm text-gray-500">
          <Spinner size="sm" /> Loading notification preferences...
        </NotificationSurface>
      ) : (
        <NotificationSurface className="flex-1 space-y-6 p-6 sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-gray-900">Notification channels</h2>
              <p className="text-sm text-gray-500">
                Enable the touchpoints that work best for your team. Required channels are always on.
              </p>
            </div>
            <div className="flex flex-col items-end gap-2 sm:flex-row">
              <div>
                {saving ? (
                  <Badge color="primary" variant="soft">
                    Saving...
                  </Badge>
                ) : dirty ? (
                  <Badge color="warning" variant="soft">
                    Unsaved changes
                  </Badge>
                ) : (
                  <Badge color="success" variant="soft">
                    Up to date
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button type="button" variant="ghost" color="neutral" onClick={resetChanges} disabled={saving || !dirty}>
                  Reset changes
                </Button>
                <Button type="button" color="primary" onClick={savePreferences} disabled={!dirty || saving}>
                  {saving ? 'Saving...' : 'Save preferences'}
                </Button>
              </div>
            </div>
          </div>

          {flash && (
            <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {flash}
            </div>
          )}

          <div className="pt-2 space-y-6">
            {topics.map((topic) => (
              <div key={topic.key} className="space-y-4">
                <div className="space-y-1">
                  <h3 className="text-sm font-semibold text-gray-700">{topic.label}</h3>
                  {topic.description ? <p className="text-xs text-gray-500">{topic.description}</p> : null}
                </div>
                <div className="space-y-3">
                  {topic.channels.map((channel) => {
                    const deliveryBadge = DELIVERY_BADGES[channel.delivery] ?? DELIVERY_BADGES.opt_in;
                    return (
                      <div
                        key={`${topic.key}:${channel.key}`}
                        className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm transition dark:border-dark-600/60 dark:bg-dark-700/70"
                      >
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                          <div className="flex flex-col gap-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-semibold text-gray-900">{channel.label}</span>
                              <Badge color={deliveryBadge.color} variant="soft">
                                {deliveryBadge.label}
                              </Badge>
                              {channel.locked ? (
                                <Badge color="info" variant="soft">
                                  Required
                                </Badge>
                              ) : null}
                              {channel.requiresConsent ? (
                                <Badge color="warning" variant="soft">
                                  Consent
                                </Badge>
                              ) : null}
                            </div>
                            {channel.description ? (
                              <p className="text-xs text-gray-500">{channel.description}</p>
                            ) : null}
                          </div>
                          <div className="flex items-center sm:items-start">
                            <Switch
                              checked={channel.locked ? true : channel.optIn}
                              disabled={channel.locked}
                              onChange={(event) =>
                                handleToggle(channel.topicKey, channel.key, channel.locked, event.currentTarget.checked)
                              }
                              aria-label={`Toggle ${channel.label}`}
                            />
                          </div>
                        </div>
                        {channel.supportsDigest ? (
                          <div className="mt-3 max-w-sm">
                            <Select
                              label="Digest frequency"
                              value={channel.digest ?? 'instant'}
                              onChange={(event) =>
                                handleDigestChange(channel.topicKey, channel.key, event.target.value)
                              }
                              disabled={channel.locked ? false : !channel.optIn}
                            >
                              {DIGEST_OPTIONS.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </Select>
                          </div>
                        ) : null}
                        {!channel.supportsDigest && !channel.optIn && !channel.locked ? (
                          <div className="mt-3 text-[11px] text-gray-400">
                            Disable to stop delivery for this topic. You can re-enable at any time.
                          </div>
                        ) : null}
                        <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-gray-400">
                          <span>{channel.locked ? 'Always on' : 'Personal preference'}</span>
                          <span aria-hidden="true">/</span>
                          <button
                            type="button"
                            className="font-medium text-primary-600 hover:text-primary-500"
                            onClick={() => handleSendTest(channel.label)}
                          >
                            Send test
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </NotificationSurface>
      )}
    </SettingsLayout>
  );
}
