import React from 'react';
import { AlertTriangle, Edit3, Plus, Send, Trash2 } from '@icons';
import { Badge, Button, Card, Drawer, Input, Select, Spinner, Table } from '@ui';
import type { PageHeaderStat } from '@ui/patterns/PageHeader';
import { extractErrorMessage } from '@shared/utils/errors';
import { useConfirmDialog } from '@shared/hooks/useConfirmDialog';
import {
  PlatformAdminFrame,
  type PlatformAdminQuickLink,
} from '../../../../pages/management/platform-admin/PlatformAdminFrame';
import { useManagementFlags } from '../hooks';
import type { FeatureFlag, FeatureFlagStatus, FeatureFlagUpsertPayload } from '@shared/types/management';

const QUICK_LINKS: PlatformAdminQuickLink[] = [
  {
    label: 'Runbook: Feature toggles',
    href: 'https://docs.caves.dev/platform-admin/feature-flags',
    description: 'Operational checklist for shipping with kill switches.',
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

type FlagFormState = {
  slug: string;
  description: string;
  status: FeatureFlagStatus;
  rollout: number | null;
  testers: string;
  roles: string;
};

const INITIAL_FORM: FlagFormState = {
  slug: '',
  description: '',
  status: 'disabled',
  rollout: null,
  testers: '',
  roles: '',
};

const STATUS_OPTIONS: Array<{ value: FeatureFlagStatus; label: string }> = [
  { value: 'all', label: 'Everyone' },
  { value: 'premium', label: 'Premium customers' },
  { value: 'testers', label: 'Manual testers' },
  { value: 'custom', label: 'Custom targeting' },
  { value: 'disabled', label: 'Disabled' },
];

export default function ManagementFlags(): React.ReactElement {
  const { confirm, confirmationElement } = useConfirmDialog();
  const { loading, error, items, refresh, clearError, saveFlag, deleteFlag } = useManagementFlags();

  const [search, setSearch] = React.useState('');
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [form, setForm] = React.useState<FlagFormState>({ ...INITIAL_FORM });
  const [editing, setEditing] = React.useState<FeatureFlag | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);

  const filteredItems = React.useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((flag) => {
      const haystack = [flag.slug, flag.label ?? '', flag.description ?? '', flag.status]
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [items, search]);

  const summary = React.useMemo(() => {
    const total = items.length;
    const enabled = items.filter((item) => item.enabled).length;
    const disabled = items.filter((item) => item.status === 'disabled').length;
    const experiments = items.filter((item) => item.status === 'custom').length;
    return { total, enabled, disabled, experiments };
  }, [items]);

  const stats = React.useMemo<PageHeaderStat[]>(
    () => [
      { label: 'Active', value: summary.enabled, hint: `${summary.total} total` },
      { label: 'Disabled', value: summary.disabled },
      { label: 'Custom', value: summary.experiments },
    ],
    [summary],
  );

  const openCreate = React.useCallback(() => {
    setForm({ ...INITIAL_FORM });
    setEditing(null);
    setFormError(null);
    setDrawerOpen(true);
  }, []);

  const openEdit = React.useCallback((flag: FeatureFlag) => {
    setEditing(flag);
    setForm({
      slug: flag.slug,
      description: flag.description ?? '',
      status: flag.status,
      rollout: flag.rollout ?? flag.release_percent ?? null,
      testers: flag.testers.join(', '),
      roles: flag.roles.join(', '),
    });
    setFormError(null);
    setDrawerOpen(true);
  }, []);

  const closeDrawer = React.useCallback(() => {
    setDrawerOpen(false);
    setForm({ ...INITIAL_FORM });
    setEditing(null);
    setFormError(null);
  }, []);

  const buildPayload = React.useCallback((): FeatureFlagUpsertPayload | null => {
    const slug = form.slug.trim();
    if (!slug) {
      setFormError('Slug is required.');
      return null;
    }
    const payload: FeatureFlagUpsertPayload = {
      slug,
      status: form.status,
      description: form.description.trim() || undefined,
      rollout: form.rollout,
    };
    const testers = form.testers
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean);
    const roles = form.roles
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean);
    if (testers.length) payload.testers = testers;
    if (roles.length) payload.roles = roles;
    return payload;
  }, [form]);

  const handleSubmit = React.useCallback(async () => {
    const payload = buildPayload();
    if (!payload) return;
    setSaving(true);
    setFormError(null);
    try {
      await saveFlag(payload);
      closeDrawer();
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Не удалось сохранить фичефлаг.'));
    } finally {
      setSaving(false);
    }
  }, [buildPayload, closeDrawer, saveFlag]);

  const handleDelete = React.useCallback(
    async (flag: FeatureFlag) => {
      const confirmed = await confirm({
        title: 'Delete flag',
        description: `Delete flag "${flag.slug}"? This action cannot be undone.`,
        confirmLabel: 'Delete',
        cancelLabel: 'Cancel',
        destructive: true,
      });
      if (!confirmed) return;
      try {
        await deleteFlag(flag.slug);
      } catch {
        // handled in hook
      }
    },
    [confirm, deleteFlag],
  );

  const handleDisable = React.useCallback(
    async (flag: FeatureFlag) => {
      const payload: FeatureFlagUpsertPayload = {
        slug: flag.slug,
        status: 'disabled',
        description: flag.description ?? undefined,
        testers: [],
        roles: [],
        rollout: 0,
      };
      try {
        await saveFlag(payload);
      } catch {
        // handled in hook
      }
    },
    [saveFlag],
  );

  const handleEnableAll = React.useCallback(
    async (flag: FeatureFlag) => {
      const payload: FeatureFlagUpsertPayload = {
        slug: flag.slug,
        status: 'all',
        description: flag.description ?? undefined,
        testers: [],
        roles: [],
        rollout: 100,
      };
      try {
        await saveFlag(payload);
      } catch {
        // handled in hook
      }
    },
    [saveFlag],
  );

  const handleRefresh = React.useCallback(() => {
    clearError();
    void refresh();
  }, [clearError, refresh]);

  return (
    <>
      <PlatformAdminFrame
        title="Feature Flags"
        description="Control rollouts and safeguards for the platform."
        actions={(
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={openCreate} color="primary" size="sm">
              <Plus className="mr-1.5 h-4 w-4" /> New flag
            </Button>
            <Button variant="outlined" size="sm" onClick={handleRefresh} disabled={loading}>
              Refresh
            </Button>
          </div>
        )}
        stats={stats}
        roleHint={ROLE_HINT}
        quickLinks={QUICK_LINKS}
      >
        <Card className="space-y-5 p-6">
          {error ? (
            <div className="flex items-start justify-between gap-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-400/30 dark:bg-rose-500/10 dark:text-rose-200">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <span>{error}</span>
              </div>
              <Button size="xs" variant="ghost" onClick={clearError}>
                Dismiss
              </Button>
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <Input
              placeholder="Search by slug or description"
              className="w-full max-w-xs"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <Button variant="ghost" size="sm" onClick={() => setSearch('')} disabled={!search.length}>
              Reset
            </Button>
          </div>

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
              <Table.Table className="min-w-[720px] text-left text-sm">
                <Table.THead>
                  <Table.TR>
                    <Table.TH className="px-4 py-3">Flag</Table.TH>
                    <Table.TH className="px-4 py-3">Audience</Table.TH>
                    <Table.TH className="px-4 py-3">Updated</Table.TH>
                    <Table.TH className="px-4 py-3 text-right">Actions</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {filteredItems.map((flag) => (
                    <Table.TR key={flag.slug}>
                      <Table.TD className="px-4 py-3 align-top">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-900 dark:text-white">{flag.label || flag.slug}</span>
                            <Badge color={flag.enabled ? 'success' : 'neutral'} variant="soft">
                              {flag.status}
                            </Badge>
                          </div>
                          <div className="text-xs text-gray-500 dark:text-dark-200">{flag.description || '—'}</div>
                        </div>
                      </Table.TD>
                      <Table.TD className="px-4 py-3 align-top text-xs text-gray-500 dark:text-dark-200">
                        {flag.audience || flag.status_label || flag.status}
                      </Table.TD>
                      <Table.TD className="px-4 py-3 align-top text-xs text-gray-500 dark:text-dark-200">
                        {flag.updated_at ? new Date(flag.updated_at).toLocaleString() : '—'}
                      </Table.TD>
                      <Table.TD className="px-4 py-3 text-right align-top">
                        <div className="inline-flex items-center gap-2">
                          <Button size="xs" variant="ghost" onClick={() => openEdit(flag)}>
                            <Edit3 className="h-3.5 w-3.5" />
                            Edit
                          </Button>
                          <Button size="xs" variant="ghost" color="error" onClick={() => void handleDisable(flag)}>
                            <AlertTriangle className="h-3.5 w-3.5" />
                            Kill
                          </Button>
                          <Button size="xs" variant="ghost" color="primary" onClick={() => void handleEnableAll(flag)}>
                            <Send className="h-3.5 w-3.5" />
                            100%
                          </Button>
                          <Button size="xs" variant="ghost" color="error" onClick={() => void handleDelete(flag)}>
                            <Trash2 className="h-3.5 w-3.5" />
                            Delete
                          </Button>
                        </div>
                      </Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
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
            <Button onClick={() => void handleSubmit()} disabled={saving}>
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

          <Input
            label="Slug"
            placeholder="billing.contracts"
            value={form.slug}
            onChange={(event) => setForm((prev) => ({ ...prev, slug: event.target.value }))}
            disabled={Boolean(editing)}
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
            value={form.status}
            onChange={(event) => {
              const value = event.target.value as FeatureFlagStatus;
              setForm((prev) => ({ ...prev, status: value }));
            }}
          >
            {STATUS_OPTIONS.map((option) => (
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
              setForm((prev) => ({ ...prev, rollout: value === '' ? null : Number(value) }));
            }}
          />

          <Input
            label="Testers (comma separated)"
            placeholder="user@caves.dev, qa@caves.dev"
            value={form.testers}
            onChange={(event) => setForm((prev) => ({ ...prev, testers: event.target.value }))}
          />

          <Input
            label="Roles (comma separated)"
            placeholder="premium, admin"
            value={form.roles}
            onChange={(event) => setForm((prev) => ({ ...prev, roles: event.target.value }))}
          />
        </div>
      </Drawer>
      {confirmationElement}
    </>
  );
}
