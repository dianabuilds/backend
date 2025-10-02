import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, Switch, Input, Select, Badge, Spinner } from "@ui";
import { SettingsLayout } from '../../shared/settings/SettingsLayout';
import { WalletConnectionCard } from '../../shared/settings/WalletConnectionCard';
import { apiGetWithResponse, apiPutWithResponse } from '../../shared/api/client';
import { useSettingsIdempotencyHeader } from '../../shared/settings';
import { extractErrorMessage } from '../../shared/utils/errors';
import { makeIdempotencyKey } from '../../shared/utils/idempotency';

type PreferenceValue = {
  enabled: boolean;
  config?: Record<string, any>;
};

type PreferenceState = Record<string, PreferenceValue>;

type ChannelConfigInput = {
  type: 'input';
  field: string;
  label: string;
  placeholder?: string;
  helper?: string;
  inputMode?: React.HTMLAttributes<HTMLInputElement>['inputMode'];
  pattern?: string;
};

type ChannelConfigSelect = {
  type: 'select';
  field: string;
  label: string;
  options: Array<{ value: string; label: string }>;
};

type ChannelConfig = ChannelConfigInput | ChannelConfigSelect;

type ChannelDefinition = {
  key: string;
  label: string;
  icon: string;
  description: string;
  helper?: string;
  recommended?: boolean;
  locked?: boolean;
  beta?: boolean;
  soon?: boolean;
  defaultEnabled?: boolean;
  defaultConfig?: Record<string, any>;
  config?: ChannelConfig;
  testable?: boolean;
};

type ChannelGroup = {
  title: string;
  description: string;
  channels: ChannelDefinition[];
};

const digestOptions = [
  { value: 'instant', label: 'Instant' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
];

const CHANNEL_GROUPS: ChannelGroup[] = [
  {
    title: 'In-app notifications',
    description: 'Keep important updates visible inside Caves.',
    channels: [
      {
        key: 'inbox.critical',
        label: 'In-app critical alerts',
        icon: 'IN',
        description: 'Security, billing and availability incidents delivered in the product.',
        helper: 'Required for audit trails and access recovery.',
        locked: true,
        defaultEnabled: true,
      },
      {
        key: 'inbox.activity',
        label: 'In-app activity',
        icon: 'IA',
        description: 'Mentions, comments and collaboration updates from your spaces.',
        defaultEnabled: true,
      },
      {
        key: 'inbox.product',
        label: 'Product highlights',
        icon: 'PR',
        description: 'Product tips, release notes and feature announcements.',
        defaultEnabled: false,
      },
    ],
  },
  {
    title: 'Email notifications',
    description: 'Messages sent to your inbox when you are away from Caves.',
    channels: [
      {
        key: 'email.security',
        label: 'Security alerts',
        icon: 'EM',
        description: 'Sign-in attempts, billing failures and policy actions.',
        recommended: true,
        defaultEnabled: true,
      },
      {
        key: 'email.digest',
        label: 'Digest summary',
        icon: 'DG',
        description: 'A digest of site news and content updates.',
        helper: 'Choose how often you receive round-ups.',
        recommended: true,
        defaultEnabled: true,
        defaultConfig: { frequency: 'daily' },
        config: {
          type: 'select',
          field: 'frequency',
          label: 'Digest frequency',
          options: digestOptions,
        },
        testable: true,
      },
      {
        key: 'email.news',
        label: 'Product announcements',
        icon: 'PN',
        description: 'Occasional product updates, roadmap notes and change logs.',
        defaultEnabled: false,
      },
      {
        key: 'email.content',
        label: 'Content updates',
        icon: 'CU',
        description: 'New quests, community drops and publishing milestones.',
        defaultEnabled: false,
      },
    ],
  },
  {
    title: 'Integrations (coming soon)',
    description: 'We are preparing ChatOps and automation hooks.',
    channels: [
      {
        key: 'slack.channel',
        label: 'Slack channel',
        icon: 'SL',
        description: 'Send alerts to Slack workspaces once the integration opens.',
        helper: 'We will share setup instructions with beta testers first.',
        beta: true,
        soon: true,
      },
      {
        key: 'telegram.direct',
        label: 'Telegram direct',
        icon: 'TG',
        description: 'Receive direct messages from our Telegram bot when the beta launches.',
        helper: 'Request access in the operator chat to join the pilot.',
        beta: true,
        soon: true,
      },
      {
        key: 'webhook.automation',
        label: 'Custom webhook',
        icon: 'WB',
        description: 'Signed JSON payloads for automation workflows.',
        helper: 'Will launch for system actions before we roll it out widely.',
        beta: true,
        soon: true,
      },
    ],
  },
];
const ALL_CHANNELS = CHANNEL_GROUPS.flatMap((group) => group.channels);
const ACTIVE_CHANNELS = ALL_CHANNELS.filter((channel) => !channel.soon);
const LOCKED_CHANNEL_KEYS = new Set(ACTIVE_CHANNELS.filter((channel) => channel.locked).map((channel) => channel.key));
const TOTAL_KNOWN_CHANNELS = ACTIVE_CHANNELS.length;






function clonePreferenceValue(value: PreferenceValue | undefined): PreferenceValue {
  return {
    enabled: value?.enabled ?? false,
    config: value?.config ? { ...value.config } : undefined,
  };
}

function clonePreferences(source: PreferenceState): PreferenceState {
  const next: PreferenceState = {};
  for (const [key, value] of Object.entries(source)) {
    next[key] = clonePreferenceValue(value);
  }
  return next;
}

function parsePreferenceValue(raw: unknown, key: string): PreferenceValue {
  if (raw && typeof raw === 'object') {
    const cast = raw as Record<string, any>;
    if (typeof cast.enabled === 'boolean') {
      const { enabled, config, ...rest } = cast;
      const mergedConfig = typeof config === 'object' && config ? { ...config } : { ...rest };
      const sanitized = sanitizeConfig(mergedConfig);
      const normalized: PreferenceValue = { enabled, config: Object.keys(sanitized).length ? sanitized : undefined };
      if (LOCKED_CHANNEL_KEYS.has(key)) normalized.enabled = true;
      return normalized;
    }
    if ('value' in cast && typeof cast.value === 'boolean') {
      return { enabled: Boolean(cast.value) };
    }
  }
  const fallback: PreferenceValue = { enabled: Boolean(raw) };
  if (LOCKED_CHANNEL_KEYS.has(key)) fallback.enabled = true;
  return fallback;
}

function sanitizeConfig(config: Record<string, any> | undefined): Record<string, any> {
  if (!config) return {};
  const entries = Object.entries(config)
    .map(([k, v]) => [k, typeof v === 'string' ? v.trim() : v])
    .filter(([, v]) => v !== undefined && v !== null && `${v}`.trim().length);
  return Object.fromEntries(entries);
}

function mergePreferences(base: PreferenceState, incoming?: Record<string, any>): PreferenceState {
  const merged = clonePreferences(base);
  if (incoming && typeof incoming === 'object') {
    for (const [key, raw] of Object.entries(incoming)) {
      merged[key] = parsePreferenceValue(raw, key);
    }
  }
  return merged;
}

function buildPayload(state: PreferenceState): Record<string, any> {
  const payload: Record<string, any> = {};
  for (const [key, value] of Object.entries(state)) {
    const config = sanitizeConfig(value.config);
    if (Object.keys(config).length) {
      payload[key] = { enabled: value.enabled, ...config };
    } else {
      payload[key] = value.enabled;
    }
  }
  return payload;
}

function preferenceEqual(a: PreferenceValue, b: PreferenceValue): boolean {
  if (a.enabled !== b.enabled) return false;
  const aConfig = sanitizeConfig(a.config);
  const bConfig = sanitizeConfig(b.config);
  const keys = new Set([...Object.keys(aConfig), ...Object.keys(bConfig)]);
  for (const key of keys) {
    if ((aConfig[key] ?? '') !== (bConfig[key] ?? '')) return false;
  }
  return true;
}

const DEFAULT_PREFERENCES: PreferenceState = (() => {
  const initial: PreferenceState = {};
  for (const group of CHANNEL_GROUPS) {
    for (const channel of group.channels) {
      initial[channel.key] = {
        enabled: channel.locked ? true : channel.defaultEnabled ?? false,
        config: channel.defaultConfig ? { ...channel.defaultConfig } : undefined,
      };
    }
  }
  return initial;
})();

export default function NotificationSettingsPage() {
  const idempotencyHeader = useSettingsIdempotencyHeader();
  const navigate = useNavigate();

  const [preferences, setPreferences] = React.useState<PreferenceState>(() => clonePreferences(DEFAULT_PREFERENCES));
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [dirty, setDirty] = React.useState(false);
  const [etag, setEtag] = React.useState<string | null>(null);
  const [flash, setFlash] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = React.useState<number | null>(null);

  const channelMap = React.useMemo(() => {
    const map: Record<string, ChannelDefinition> = {};
    CHANNEL_GROUPS.forEach((group) => {
      group.channels.forEach((channel) => {
        map[channel.key] = channel;
      });
    });
    return map;
  }, []);

  const loadPreferences = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data, response } = await apiGetWithResponse<{ preferences?: Record<string, any> }>('/v1/me/settings/notifications/preferences');
      const merged = mergePreferences(DEFAULT_PREFERENCES, data?.preferences);
      setPreferences(merged);
      setDirty(false);
      setEtag(response.headers.get('ETag'));
    } catch (err) {
      const message = extractErrorMessage(err, 'Failed to load notification preferences');
      const friendly = message?.startsWith('Request failed') ? 'Notification preferences are temporarily unavailable.' : message;
      setError(friendly);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadPreferences();
  }, [loadPreferences]);

  React.useEffect(() => {
    if (!flash) return;
    const id = window.setTimeout(() => setFlash(null), 3500);
    return () => window.clearTimeout(id);
  }, [flash]);

  const enabledCount = React.useMemo(() => {
    return ACTIVE_CHANNELS.reduce((total, channel) => (preferences[channel.key]?.enabled ? total + 1 : total), 0);
  }, [preferences]);

  const digestFrequency = React.useMemo(() => {
    const digestPref = preferences['email.digest'];
    if (!digestPref?.enabled) return 'Disabled';
    const value = digestPref.config?.frequency;
    return digestOptions.find((opt) => opt.value === value)?.label || 'Daily';
  }, [preferences]);

  const lastSavedLabel = React.useMemo(() => {
    if (!lastSavedAt) return 'Not yet saved';
    return new Date(lastSavedAt).toLocaleString();
  }, [lastSavedAt]);
  const handleToggle = React.useCallback(
    (key: string, nextEnabled: boolean) => {
      const channel = channelMap[key];
      if (channel?.locked) return;
      let changed = false;
      setPreferences((prev) => {
        const current = clonePreferenceValue(prev[key]);
        if (current.enabled === nextEnabled) return prev;
        changed = true;
        return { ...prev, [key]: { ...current, enabled: nextEnabled } };
      });
      if (changed) {
        setDirty(true);
        setFlash(null);
      }
    },
    [channelMap],
  );

  const handleConfigChange = React.useCallback((key: string, field: string, value: string) => {
    let changed = false;
    setPreferences((prev) => {
      const current = clonePreferenceValue(prev[key]);
      const nextConfig = { ...(current.config || {}), [field]: value };
      const next: PreferenceValue = { enabled: current.enabled, config: nextConfig };
      if (preferenceEqual(current, next)) return prev;
      changed = true;
      return { ...prev, [key]: next };
    });
    if (changed) {
      setDirty(true);
      setFlash(null);
    }
  }, []);

  const savePreferences = React.useCallback(async () => {
    if (saving || !dirty) return;
    setSaving(true);
    setError(null);
    try {
      const headers: Record<string, string> = { [idempotencyHeader]: makeIdempotencyKey() };
      if (etag) headers['If-Match'] = etag;
      const payload = buildPayload(preferences);
      const { data, response } = await apiPutWithResponse<{ preferences?: Record<string, any> }>(
        '/v1/me/settings/notifications/preferences',
        { preferences: payload },
        { headers },
      );
      const merged = mergePreferences(preferences, data?.preferences);
      setPreferences(merged);
      setEtag(response.headers.get('ETag'));
      setDirty(false);
      setLastSavedAt(Date.now());
      setFlash('Preferences saved.');
    } catch (err) {
      const message = extractErrorMessage(err, 'Failed to save preferences');
      const friendly = message?.startsWith('Request failed') ? 'Unable to save preferences right now.' : message;
      setError(friendly);
    } finally {
      setSaving(false);
    }
  }, [dirty, etag, idempotencyHeader, preferences, saving]);

  const resetToDefaults = React.useCallback(() => {
    setPreferences((prev) => {
      const base = clonePreferences(DEFAULT_PREFERENCES);
      for (const [key, value] of Object.entries(prev)) {
        if (!(key in base)) {
          base[key] = clonePreferenceValue(value);
        }
      }
      return base;
    });
    setDirty(true);
    setFlash('Restored recommended defaults. Remember to save.');
  }, []);

  const handleSendTest = React.useCallback(
    (key: string) => {
      const label = channelMap[key]?.label || key;
      setFlash('Queued a test notification via ' + label + '.');
    },
    [channelMap],
  );

  const renderChannelConfig = React.useCallback(
    (channel: ChannelDefinition, pref: PreferenceValue, isEnabled: boolean) => {
      const config = channel.config;
      if (!config) return null;
      const disabled = channel.locked ? false : !isEnabled;
      if (config.type === 'select') {
        const selectValue = pref.config?.[config.field] ?? config.options[0]?.value ?? '';
        return (
          <div className="mt-3 max-w-sm">
            <Select
              label={config.label}
              value={selectValue}
              onChange={(event) => handleConfigChange(channel.key, config.field, event.target.value)}
              disabled={disabled}
            >
              {config.options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
        );
      }
      const inputValue = pref.config?.[config.field] ?? '';
      return (
        <div className="mt-3 max-w-sm space-y-2">
          <Input
            label={config.label}
            value={inputValue}
            onChange={(event) => handleConfigChange(channel.key, config.field, event.target.value)}
            placeholder={config.placeholder}
            inputMode={config.inputMode}
            pattern={config.pattern}
            disabled={disabled}
          />
          {config.helper && <p className="text-[11px] text-gray-400">{config.helper}</p>}
        </div>
      );
    },
    [handleConfigChange],
  );

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
          <Badge color="neutral" variant="soft">Overview</Badge>
        </div>
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex items-center justify-between">
            <span>Active channels</span>
            <span className="font-semibold text-gray-900">{enabledCount}/{TOTAL_KNOWN_CHANNELS}</span>
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
      <WalletConnectionCard />
      <Card className="space-y-4 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm">
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-gray-700">More settings</h2>
          <p className="text-xs text-gray-500">Quickly switch between profile, security and billing without leaving notifications.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" size="sm" variant="ghost" color="neutral" onClick={() => navigate('/profile')}>
            Profile
          </Button>
          <Button type="button" size="sm" variant="ghost" color="neutral" onClick={() => navigate('/settings/security')}>
            Security
          </Button>
          <Button type="button" size="sm" color="primary" onClick={() => navigate('/billing')}>
            Billing
          </Button>
        </div>
      </Card>
    </>
  );

  return (
    <SettingsLayout
      title="Personal delivery settings"
      description="Tune how we reach you across in-app and email channels."
      error={errorBanner}
      side={sidePanel}
    >
      {loading ? (
        <Card className="flex flex-1 items-center gap-3 p-6 text-sm text-gray-500">
          <Spinner size="sm" /> Loading notification preferences...
        </Card>
      ) : (
        <Card
          skin="none"
          className="flex-1 rounded-3xl bg-gradient-to-br from-white via-[#f4f6ff] to-[#e8edff] p-6 shadow-xl ring-1 ring-white/60"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-gray-900">Notification channels</h2>
              <p className="text-sm text-gray-500">Enable the touchpoints that work best for your team.</p>
            </div>
            <div className="flex flex-col items-end gap-2 sm:flex-row">
              <div>
                {saving ? (
                  <Badge color="primary" variant="soft">Saving...</Badge>
                ) : dirty ? (
                  <Badge color="warning" variant="soft">Unsaved changes</Badge>
                ) : (
                  <Badge color="success" variant="soft">Up to date</Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button type="button" variant="ghost" color="neutral" onClick={resetToDefaults} disabled={saving}>
                  Restore recommended
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

          <div className="mt-6 space-y-6">
            {CHANNEL_GROUPS.map((group) => (
              <div key={group.title} className="space-y-4">
                <div className="space-y-1">
                  <h3 className="text-sm font-semibold text-gray-700">{group.title}</h3>
                  <p className="text-xs text-gray-500">{group.description}</p>
                </div>
                <div className="space-y-3">
                  {group.channels.map((channel) => {
                    const stored = clonePreferenceValue(preferences[channel.key] ?? DEFAULT_PREFERENCES[channel.key]);
                    const forcedEnabled = channel.locked ? true : stored.enabled;
                    return (
                      <div
                        key={channel.key}
                        className={
                          channel.soon
                            ? 'rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm transition opacity-60'
                            : 'rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm transition'
                        }
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex flex-col gap-2">
                            <div className="flex items-center gap-2">
                              <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary-50 text-lg">{channel.icon}</span>
                              <span className="text-sm font-semibold text-gray-900">{channel.label}</span>
                              {channel.recommended && <Badge color="primary" variant="soft">Recommended</Badge>}
                              {channel.locked && <Badge color="info" variant="soft">Required</Badge>}
                              {channel.beta && <Badge color="info" variant="soft">Beta</Badge>}
                              {channel.soon && <Badge color="neutral" variant="soft">Soon</Badge>}
                            </div>
                            <p className="text-xs text-gray-500">{channel.description}</p>
                            {channel.helper && <p className="text-[11px] text-gray-400">{channel.helper}</p>}
                          </div>
                          <Switch
                            checked={forcedEnabled}
                            disabled={channel.locked || channel.soon}
                            onChange={(event) => handleToggle(channel.key, event.currentTarget.checked)}
                            aria-label={'Toggle ' + channel.label}
                          />
                        </div>
                        {renderChannelConfig(channel, stored, forcedEnabled)}
                        {channel.testable && forcedEnabled && (
                          <div className="mt-3">
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              color="neutral"
                              onClick={() => handleSendTest(channel.key)}
                            >
                              Send test
                            </Button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </SettingsLayout>
  );
}







