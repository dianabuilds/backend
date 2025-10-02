
import React from 'react';
import { AlertTriangle, Edit3, Plus, Send, Trash2 } from '@icons';
import { Badge, Button, Card, Drawer, Input, Select, Spinner, Table, TagInput } from '@ui';
import type { PageHeaderStat } from '@ui/patterns/PageHeader.tsx';
import { apiDelete, apiGet, apiPost } from '../../shared/api/client';
import { extractErrorMessage } from '../../shared/utils/errors';
import { useConfirmDialog } from '../../shared/hooks/useConfirmDialog';
import {
  PlatformAdminFrame,
  type PlatformAdminQuickLink,
} from './platform-admin/PlatformAdminFrame';

type FlagStatus = 'disabled' | 'testers' | 'premium' | 'all' | 'custom';

type FlagRow = {
  slug: string;
  label?: string | null;
  description?: string | null;
  status: FlagStatus;
  status_label?: string | null;
  audience?: string | null;
  enabled: boolean;
  effective?: boolean | null;
  rollout?: number | null;
  release_percent?: number | null;
  testers: string[];
  roles: string[];
  segments: string[];
  rules: Array<{ type: string; value: string; rollout: number | null; priority: number; meta?: Record<string, unknown> }>;
  meta?: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
  evaluated_at?: string | null;
};

type UserOption = {
  id: string;
  username?: string | null;
};

type AudienceValue = 'all' | 'premium' | 'testers' | 'custom' | 'disabled';

type FlagFormState = {
  slug: string;
  description: string;
  group: AudienceValue;
  rollout: number | null;
  testers: UserOption[];
  roles: string[];
  segments: string[];
};

const FLAG_PRESETS: Array<{ slug: string; label: string; description?: string }> = [
  { slug: 'content.nodes', label: 'Nodes workspace' },
  { slug: 'content.quests', label: 'Quests workspace' },
  { slug: 'notifications.broadcasts', label: 'Notifications & broadcasts' },
  { slug: 'billing.revenue', label: 'Billing & revenue' },
  { slug: 'observability.core', label: 'Observability suite' },
  { slug: 'moderation.guardrails', label: 'Moderation tools' },
];

const FLAG_DISPLAY_LABELS = FLAG_PRESETS.reduce<Record<string, string>>((acc, preset) => {
  acc[preset.slug] = preset.label;
  return acc;
}, {});

const AUDIENCE_OPTIONS: Array<{ value: AudienceValue; label: string }> = [
  { value: 'all', label: 'Everyone' },
  { value: 'premium', label: 'Premium customers' },
  { value: 'testers', label: 'Manual testers' },
  { value: 'custom', label: 'Custom targeting' },
  { value: 'disabled', label: 'Disabled' },
];

const QUICK_LINKS: PlatformAdminQuickLink[] = [
  {
    label: 'Runbook: Feature toggles',
    href: 'https://docs.caves.dev/platform-admin/feature-flags',
    description: 'Operational checklist for shipping with kill switches.',
  },
  {
    label: 'Experiment design toolkit',
    href: 'https://docs.caves.dev/experiments/overview',
  },
  {
    label: 'Audit trail',
    href: '/management/audit?module=flags',
    description: 'Inspect recent flag mutations and actors.',
  },
];

const ROLE_HINT = (
  <div className="space-y-2">
    <p>
      Only platform administrators can create or modify feature flags. Product owners and QA can view rollout status but
      changes require elevated access.
    </p>
    <p className="text-xs text-gray-500 dark:text-dark-200">
      Every upsert and delete is captured in <code>/management/audit</code> with before/after payloads.
    </p>
  </div>
);

const INITIAL_FORM: FlagFormState = {
  slug: '',
  description: '',
  group: 'disabled',
  rollout: null,
  testers: [],
  roles: [],
  segments: [],
};

const TESTER_SEARCH_DEBOUNCE = 250;

const FLAG_TABLE_WRAPPER_CLASS = 'overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-dark-600 dark:bg-dark-700';
const FLAG_TABLE_CLASS = 'min-w-[960px] w-full text-left text-sm text-gray-800 dark:text-dark-50';
const FLAG_TABLE_HEAD_CELL_CLASS = 'px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300 whitespace-nowrap';
const FLAG_TABLE_ROW_CLASS = 'border-b border-gray-100 bg-white transition-colors last:border-none hover:bg-indigo-50/30 dark:border-dark-600 dark:bg-dark-700 dark:hover:bg-dark-650';
const FLAG_TABLE_CELL_CLASS = 'px-4 py-4 align-top';

const audienceLabel = (flag: FlagRow): string => flag.audience ?? flag.status_label ?? flag.status;
const friendlyName = (flag: FlagRow): string => FLAG_DISPLAY_LABELS[flag.slug] ?? flag.label ?? flag.slug;

export default function ManagementFlags() {
  const { confirm, confirmationElement } = useConfirmDialog();
  const [items, setItems] = React.useState<FlagRow[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [search, setSearch] = React.useState('');

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [form, setForm] = React.useState<FlagFormState>({ ...INITIAL_FORM });
  const [editing, setEditing] = React.useState<FlagRow | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);

  const [userQuery, setUserQuery] = React.useState('');
  const [userOptions, setUserOptions] = React.useState<UserOption[]>([]);
  const [userSearching, setUserSearching] = React.useState(false);
  const searchTimer = React.useRef<number | undefined>();

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<{ items: FlagRow[] }>('/v1/flags');
      setItems(response?.items ?? []);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load feature flags'));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void load();
  }, [load]);

  React.useEffect(() => {
    if (!drawerOpen || (form.group !== 'testers' && form.group !== 'custom')) {
      setUserOptions([]);
      setUserSearching(false);
      return;
    }
    if (searchTimer.current) {
      window.clearTimeout(searchTimer.current);
    }
    const query = userQuery.trim();
    if (!query) {
      setUserOptions([]);
      setUserSearching(false);
      return;
    }
    setUserSearching(true);
    searchTimer.current = window.setTimeout(async () => {
      try {
        const result = await apiGet<UserOption[]>(`/v1/users/search?q=${encodeURIComponent(query)}&limit=10`);
        setUserOptions((result ?? []).filter((option) => option.id && !form.testers.some((tester) => tester.id === option.id)));
      } catch {
        setUserOptions([]);
      } finally {
        setUserSearching(false);
      }
    }, TESTER_SEARCH_DEBOUNCE);
    return () => {
      if (searchTimer.current) {
        window.clearTimeout(searchTimer.current);
      }
    };
  }, [drawerOpen, form.group, form.testers, userQuery]);

  const summary = React.useMemo(() => {
    const total = items.length;
    const enabled = items.filter((item) => item.enabled).length;
    const experiments = items.filter((item) => audienceLabel(item) === 'custom').length;
    const testersCount = items.filter((item) => audienceLabel(item) === 'testers').length;
    const disabled = items.filter((item) => item.status === 'disabled').length;
    return { total, enabled, experiments, testers: testersCount, disabled };
  }, [items]);

  const stats = React.useMemo<PageHeaderStat[]>(() => [
    {
      label: 'Active flags',
      value: summary.enabled,
      hint: `${summary.total} total`,
    },
    {
      label: 'Custom targeting',
      value: summary.experiments,
      hint: 'Flags with custom rules',
    },
    {
      label: 'Manual testers',
      value: summary.testers,
      hint: 'Managed allowlists',
    },
    {
      label: 'Disabled',
      value: summary.disabled,
      hint: 'Ready to reuse',
    },
  ], [summary]);

  const filteredItems = React.useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((flag) => {
      const haystack = [
        flag.slug,
        flag.label ?? '',
        friendlyName(flag),
        flag.description ?? '',
        audienceLabel(flag),
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [items, search]);
  const openCreateDrawer = React.useCallback(() => {
    setForm({ ...INITIAL_FORM });
    setEditing(null);
    setFormError(null);
    setDrawerOpen(true);
  }, []);

  const deriveGroupFromFlag = (flag: FlagRow): AudienceValue => {
    const value = audienceLabel(flag);
    if (value === 'all' || flag.status === 'all') return 'all';
    if (value === 'premium' || flag.status === 'premium') return 'premium';
    if (value === 'testers' || flag.status === 'testers') return 'testers';
    if (value === 'custom' || flag.status === 'custom') return 'custom';
    return 'disabled';
  };

  const openEditDrawer = React.useCallback((flag: FlagRow) => {
    const group = deriveGroupFromFlag(flag);
    setEditing(flag);
    setForm({
      slug: flag.slug,
      description: flag.description ?? '',
      group,
      rollout: flag.rollout ?? flag.release_percent ?? null,
      testers: (flag.testers || []).map((id) => ({ id, username: id })),
      roles: flag.roles || [],
      segments: flag.segments || [],
    });
    setFormError(null);
    setDrawerOpen(true);
  }, []);

  const closeDrawer = React.useCallback(() => {
    setDrawerOpen(false);
    setForm({ ...INITIAL_FORM });
    setEditing(null);
    setFormError(null);
    setUserQuery('');
    setUserOptions([]);
  }, []);

  const mutateFlag = React.useCallback(
    async (slug: string, action: () => Promise<unknown>) => {
      setError(null);
      try {
        await action();
        await load();
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to update flag'));
      }
    },
    [load],
  );

  const handleDelete = React.useCallback(
    async (slug: string) => {
      const confirmed = await confirm({
        title: 'Delete flag',
        description: `Delete flag "${slug}"? This action cannot be undone.`,
        confirmLabel: 'Delete',
        cancelLabel: 'Cancel',
        destructive: true,
      });
      if (!confirmed) return;
      void mutateFlag(slug, () => apiDelete(`/v1/flags/${slug}`));
    },
    [confirm, mutateFlag],
  );

  const handleKillSwitch = React.useCallback(
    (flag: FlagRow) => {
      void mutateFlag(flag.slug, () =>
        apiPost('/v1/flags', {
          slug: flag.slug,
          status: 'disabled',
          description: flag.description ?? undefined,
          testers: [],
          roles: [],
          segments: [],
          rollout: 0,
        }),
      );
    },
    [mutateFlag],
  );

  const handleEnableAll = React.useCallback(
    (flag: FlagRow) => {
      void mutateFlag(flag.slug, () =>
        apiPost('/v1/flags', {
          slug: flag.slug,
          status: 'all',
          description: flag.description ?? undefined,
          testers: [],
          roles: [],
          segments: [],
          rollout: 100,
        }),
      );
    },
    [mutateFlag],
  );
  const handleSubmitForm = React.useCallback(async () => {
    const slug = form.slug.trim();
    if (!slug) {
      setFormError('Slug is required');
      return;
    }
    const payload: Record<string, unknown> = { slug };
    const description = form.description.trim();
    if (description) {
      payload.description = description;
    }
    if (form.rollout !== null && !Number.isNaN(form.rollout)) {
      payload.rollout = Math.min(100, Math.max(0, form.rollout));
    }

    if (form.group === 'all') {
      payload.status = 'all';
    } else if (form.group === 'premium') {
      payload.status = 'premium';
      if (form.roles.length) payload.roles = form.roles;
      if (form.segments.length) payload.segments = form.segments;
    } else if (form.group === 'testers') {
      if (!form.testers.length) {
        setFormError('Add at least one tester');
        return;
      }
      payload.status = 'testers';
      payload.testers = form.testers.map((tester) => tester.id);
      if (form.segments.length) payload.segments = form.segments;
    } else if (form.group === 'custom') {
      payload.status = 'custom';
      if (form.testers.length) payload.testers = form.testers.map((tester) => tester.id);
      if (form.roles.length) payload.roles = form.roles;
      if (form.segments.length) payload.segments = form.segments;
    } else {
      payload.status = 'disabled';
      payload.rollout = 0;
      payload.testers = [];
      payload.roles = [];
      payload.segments = [];
    }

    setSaving(true);
    setFormError(null);
    try {
      await apiPost('/v1/flags', payload);
      await load();
      closeDrawer();
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Failed to save flag'));
    } finally {
      setSaving(false);
    }
  }, [closeDrawer, form, load]);

  const headerActions = (
    <div className="flex flex-wrap items-center gap-3">
      <Button onClick={openCreateDrawer} color="primary" size="sm">
        <Plus className="mr-1.5 h-4 w-4" /> New flag
      </Button>
      <Button
        variant="outlined"
        color="primary"
        size="sm"
        type="button"
        onClick={() => void load()}
        disabled={loading}
      >
        Refresh
      </Button>
    </div>
  );

  const applyPreset = (slug: string) => {
    const preset = FLAG_PRESETS.find((item) => item.slug === slug);
    if (!preset) return;
    setForm((prev) => ({
      ...prev,
      slug: preset.slug,
      description: prev.description || preset.description || '',
    }));
  };
  return (
    <>
      <PlatformAdminFrame
        title="Feature Flags"
        description="Control rollout of the major product areas from a single screen."
        actions={headerActions}
        stats={stats}
        roleHint={ROLE_HINT}
        helpText={(
          <div className="space-y-2 text-sm leading-relaxed text-gray-600 dark:text-dark-100">
            <p>
              Feature flags let you stage rollouts, run experiments, and execute kill switches without redeploying.
              Update a flag, refresh the settings provider, and clients will pick up the change instantly.
            </p>
            <p>
              Creating a flag registers it in the platform. Behaviour changes only after the flag is consumed in code or UI
              checks.
            </p>
          </div>
        )}
        quickLinks={QUICK_LINKS}
      >
        <Card className="space-y-5 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-white">Current flags</h2>
              <p className="text-sm text-gray-500 dark:text-dark-200">
                Use filters to locate rollouts quickly. Changes apply instantly after save.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
              <Badge color="neutral" variant="outline">
                {filteredItems.length} of {items.length} flags
              </Badge>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Input
              placeholder="Search slug, label, or description"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search flags"
              className="w-full max-w-sm"
            />
            {search ? (
              <Button variant="ghost" color="neutral" size="sm" type="button" onClick={() => setSearch('')}>
                Clear
              </Button>
            ) : null}
          </div>

          {error ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50/70 px-4 py-3 text-sm text-rose-700 dark:border-rose-400/30 dark:bg-rose-500/10 dark:text-rose-200">
              {error}
            </div>
          ) : null}

          {loading && !items.length ? (
            <div className="flex min-h-[160px] items-center justify-center">
              <Spinner />
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-gray-200 px-6 py-12 text-center text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
              {search ? 'No flags match your filter.' : 'No feature flags found yet.'}
            </div>
          ) : (
            <div className="-mx-4 overflow-x-auto sm:mx-0">
              <div className="inline-block min-w-full align-middle">
                <div className={FLAG_TABLE_WRAPPER_CLASS}>
                  <Table.Table hover className={FLAG_TABLE_CLASS}>
                    <Table.THead>
                      <Table.TR>
                        <Table.TH className={`${FLAG_TABLE_HEAD_CELL_CLASS} w-[40%] min-w-[280px]`}>Flag</Table.TH>
                        <Table.TH className={`${FLAG_TABLE_HEAD_CELL_CLASS} w-[12%] text-center`}>Rollout</Table.TH>
                        <Table.TH className={`${FLAG_TABLE_HEAD_CELL_CLASS} w-[26%] min-w-[220px]`}>Audience</Table.TH>
                        <Table.TH className={`${FLAG_TABLE_HEAD_CELL_CLASS} w-[12%] whitespace-nowrap`}>Updated</Table.TH>
                        <Table.TH className={`${FLAG_TABLE_HEAD_CELL_CLASS} w-[10%] text-right`}>Actions</Table.TH>
                      </Table.TR>
                    </Table.THead>
                    <Table.TBody>
                      {filteredItems.map((flag) => {
                        const rolloutValue = flag.rollout ?? flag.release_percent ?? null;
                        const testersPreview = flag.testers.length ? flag.testers.slice(0, 3).join(', ') : '-';
                        const rolesPreview = flag.roles.length ? flag.roles.join(', ') : '-';
                        const segmentsPreview = flag.segments.length ? flag.segments.join(', ') : '-';
                        const effectiveState = flag.effective;
                        const audienceValue = audienceLabel(flag);
                        return (
                          <Table.TR key={flag.slug} className={FLAG_TABLE_ROW_CLASS}>
                            <Table.TD className={FLAG_TABLE_CELL_CLASS}>
                              <div className="space-y-2">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="text-sm font-semibold text-gray-900 dark:text-white">{friendlyName(flag)}</span>
                                  <Badge
                                    color={flag.enabled ? 'success' : 'neutral'}
                                    variant="soft"
                                    className="uppercase tracking-wide text-[10px]"
                                  >
                                    {flag.status_label || flag.status}
                                  </Badge>
                                  <Badge color="neutral" variant="outline" className="uppercase tracking-wide text-[10px]">
                                    Audience: {audienceValue}
                                  </Badge>
                                  {typeof effectiveState === 'boolean' ? (
                                    <Badge
                                      color={effectiveState ? 'success' : 'neutral'}
                                      variant="outline"
                                      className="uppercase tracking-wide text-[10px]"
                                    >
                                      Effective {effectiveState ? 'on' : 'off'}
                                    </Badge>
                                  ) : null}
                                  {flag.rules.length ? (
                                    <Badge color="neutral" variant="outline" className="text-[10px]">
                                      {flag.rules.length} rule{flag.rules.length === 1 ? '' : 's'}
                                    </Badge>
                                  ) : null}
                                </div>
                                {flag.description ? (
                                  <div className="text-sm text-gray-600 dark:text-dark-100">{flag.description}</div>
                                ) : null}
                                <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-dark-200">
                                  <span className="flex items-center gap-1 uppercase tracking-wide text-gray-400 dark:text-dark-300">
                                    Slug
                                    <code className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-700 dark:bg-dark-700 dark:text-dark-100">
                                      {flag.slug}
                                    </code>
                                  </span>
                                </div>
                              </div>
                            </Table.TD>
                            <Table.TD className={`${FLAG_TABLE_CELL_CLASS} text-center text-sm font-medium text-gray-700 dark:text-dark-50`}>
                              {rolloutValue ?? '-'}
                            </Table.TD>
                            <Table.TD className={FLAG_TABLE_CELL_CLASS}>
                              <div className="space-y-1 text-xs text-gray-600 dark:text-dark-100">
                                <div className="flex items-center justify-between gap-2">
                                  <span className="font-medium text-gray-500 dark:text-dark-300">Testers</span>
                                  <span className="text-right">{testersPreview}</span>
                                </div>
                                <div className="flex items-center justify-between gap-2">
                                  <span className="font-medium text-gray-500 dark:text-dark-300">Roles</span>
                                  <span className="text-right">{rolesPreview}</span>
                                </div>
                                <div className="flex items-center justify-between gap-2">
                                  <span className="font-medium text-gray-500 dark:text-dark-300">Segments</span>
                                  <span className="text-right">{segmentsPreview}</span>
                                </div>
                              </div>
                            </Table.TD>
                            <Table.TD className={`${FLAG_TABLE_CELL_CLASS} text-xs text-gray-500 dark:text-dark-200 whitespace-nowrap`}>
                              {flag.updated_at ? new Date(flag.updated_at).toLocaleString() : '-'}
                            </Table.TD>
                            <Table.TD className={`${FLAG_TABLE_CELL_CLASS} whitespace-nowrap`}>
                              <div className="flex items-center justify-end gap-1">
                                <Button
                                  type="button"
                                  size="xs"
                                  variant="ghost"
                                  color="primary"
                                  className="gap-1"
                                  title="Edit flag"
                                  onClick={() => openEditDrawer(flag)}
                                >
                                  <Edit3 className="h-3.5 w-3.5" />
                                  Edit
                                </Button>
                                <Button
                                  type="button"
                                  size="xs"
                                  variant="ghost"
                                  color="error"
                                  className="gap-1"
                                  title="Kill switch"
                                  onClick={() => handleKillSwitch(flag)}
                                >
                                  <AlertTriangle className="h-3.5 w-3.5" />
                                  Kill
                                </Button>
                                <Button
                                  type="button"
                                  size="xs"
                                  variant="ghost"
                                  color="primary"
                                  className="gap-1"
                                  title="Enable 100% rollout"
                                  onClick={() => handleEnableAll(flag)}
                                >
                                  <Send className="h-3.5 w-3.5" />
                                  100%
                                </Button>
                                <Button
                                  type="button"
                                  size="xs"
                                  variant="ghost"
                                  color="error"
                                  className="gap-1"
                                  title="Delete flag"
                                  onClick={() => handleDelete(flag.slug)}
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                  Delete
                                </Button>
                              </div>
                            </Table.TD>
                          </Table.TR>
                        );
                      })}
                    </Table.TBody>
                  </Table.Table>
                </div>
              </div>
            </div>
          )}
        </Card>
      </PlatformAdminFrame>
      <Drawer
        open={drawerOpen}
        onClose={closeDrawer}
        title={editing ? 'Edit feature flag' : 'Create feature flag'}
        widthClass="w-[520px]"
        footer={(
          <div className="flex items-center justify-end gap-2">
            <Button variant="ghost" color="neutral" onClick={closeDrawer} disabled={saving}>
              Cancel
            </Button>
            <Button onClick={() => void handleSubmitForm()} disabled={saving}>
              {saving ? <Spinner size="sm" className="mr-2" /> : null}
              {editing ? 'Save changes' : 'Create flag'}
            </Button>
          </div>
        )}
      >
        <div className="space-y-4 px-4 py-5">
          {formError ? (
            <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-400/30 dark:bg-rose-500/10 dark:text-rose-200">
              {formError}
            </div>
          ) : null}

          <div className="space-y-2">
            <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Module presets</div>
            <div className="flex flex-wrap gap-2">
              {FLAG_PRESETS.map((preset) => (
                <Button
                  key={preset.slug}
                  type="button"
                  variant="outlined"
                  size="xs"
                  color={form.slug === preset.slug ? 'primary' : 'neutral'}
                  onClick={() => applyPreset(preset.slug)}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          </div>

          <Input
            label="Slug"
            placeholder="billing.contracts"
            value={form.slug}
            onChange={(event) => setForm((prev) => ({ ...prev, slug: event.target.value }))}
            disabled={Boolean(editing)}
            autoComplete="off"
            required
          />

          <Input
            label="Description"
            placeholder="Short sentence for teammates"
            value={form.description}
            onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
          />

          <Select
            label="Audience"
            value={form.group}
            onChange={(event) => {
              const value = event.target.value as AudienceValue;
              setForm((prev) => ({
                ...prev,
                group: value,
                testers: value === 'testers' || value === 'custom' ? prev.testers : [],
                roles: value === 'premium' || value === 'custom' ? prev.roles : [],
                segments: value === 'premium' || value === 'custom' || value === 'testers' ? prev.segments : [],
              }));
              setUserQuery('');
              setUserOptions([]);
            }}
          >
            {AUDIENCE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>

          <Input
            label="Rollout percentage"
            type="number"
            min={0}
            max={100}
            placeholder="0-100"
            value={form.rollout ?? ''}
            onChange={(event) => {
              const value = event.target.value;
              setForm((prev) => ({
                ...prev,
                rollout: value === '' ? null : Number(value),
              }));
            }}
          />

          {(form.group === 'premium' || form.group === 'custom') && (
            <TagInput
              label="Roles"
              value={form.roles}
              onChange={(roles) => setForm((prev) => ({ ...prev, roles }))}
              placeholder="premium, admin"
            />
          )}

          {(form.group === 'premium' || form.group === 'custom' || form.group === 'testers') && (
            <TagInput
              label="Segments"
              placeholder="beta, qa"
              value={form.segments}
              onChange={(segments) => setForm((prev) => ({ ...prev, segments }))}
            />
          )}

          {(form.group === 'testers' || form.group === 'custom') && (
            <div className="space-y-2">
              <div className="input-label">Testers</div>
              {form.testers.length ? (
                <div className="flex flex-wrap gap-2">
                  {form.testers.map((tester) => (
                    <Badge key={tester.id} color="neutral" variant="soft" className="flex items-center gap-1">
                      <span>{tester.username || tester.id}</span>
                      <button
                        type="button"
                        className="text-xs text-gray-500 hover:text-gray-700"
                        aria-label="Remove tester"
                        onClick={() =>
                          setForm((prev) => ({
                            ...prev,
                            testers: prev.testers.filter((item) => item.id !== tester.id),
                          }))
                        }
                      >
                        x
                      </button>
                    </Badge>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-gray-500 dark:text-dark-200">Add users that should see the flag.</div>
              )}
              <Input
                placeholder="Start typing username or email"
                value={userQuery}
                onChange={(event) => setUserQuery(event.target.value)}
              />
              {userSearching ? <Spinner size="sm" /> : null}
              {userOptions.length ? (
                <div className="max-h-40 overflow-auto rounded-md border border-gray-200 bg-white text-sm shadow-sm dark:border-dark-500 dark:bg-dark-700">
                  {userOptions.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-dark-600"
                      onClick={() => {
                        setForm((prev) => ({
                          ...prev,
                          testers: prev.testers.some((tester) => tester.id === option.id)
                            ? prev.testers
                            : [...prev.testers, option],
                        }));
                        setUserQuery('');
                        setUserOptions([]);
                      }}
                    >
                      <span>{option.username || option.id}</span>
                      <span className="text-xs text-gray-400">{option.id}</span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          )}
        </div>
      </Drawer>
      {confirmationElement}
    </>
  );
}








