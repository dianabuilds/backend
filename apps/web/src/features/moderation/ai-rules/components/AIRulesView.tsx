import clsx from 'clsx';
import React from 'react';
import {
  Badge,
  Button,
  Card,
  Drawer,
  Input,
  PageHero,
  Select,
  Spinner,
  Switch,
  TablePagination,
  Textarea,
} from '@ui';
import type { PageHeroMetric } from '@ui/patterns/PageHero';
import { Table as UITable } from '@ui/table';
import { ArrowPathIcon, ArrowUpTrayIcon, PlusIcon } from '@heroicons/react/24/outline';

import {
  fetchModerationAIRules,
  createModerationAIRule,
  updateModerationAIRule,
  deleteModerationAIRule,
} from '@shared/api/moderation';
import type { ModerationAIRule } from '@shared/types/moderation';

type RuleDraft = {
  category: string;
  description: string;
  defaultAction: string;
  threshold: string;
};

function formatDate(value?: string | null): string {
  if (!value) return 'N/A';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString();
}

function formatRelativeTime(value?: string | null): string {
  if (!value) return 'N/A';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  const diffMs = Date.now() - dt.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return dt.toLocaleDateString();
}

function ensureArray<T = Record<string, unknown>>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  return [];
}

const DEFAULT_ACTIONS = ['flag', 'hide', 'escalate', 'restrict', 'delete'];

export default function ModerationAIRules(): React.ReactElement {
  const [items, setItems] = React.useState<ModerationAIRule[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [lastLoadedAt, setLastLoadedAt] = React.useState<string | null>(null);

  const [newRule, setNewRule] = React.useState<RuleDraft>({
    category: '',
    description: '',
    defaultAction: 'flag',
    threshold: '',
  });

  const [search, setSearch] = React.useState('');
  const [enabledOnly, setEnabledOnly] = React.useState(false);

  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [totalItems, setTotalItems] = React.useState<number | undefined>(undefined);

  const [selectedRule, setSelectedRule] = React.useState<ModerationAIRule | null>(null);
  const [editing, setEditing] = React.useState<{
    description: string;
    defaultAction: string;
    threshold: string;
    enabled: boolean;
  }>({
    description: '',
    defaultAction: 'flag',
    threshold: '',
    enabled: true,
  });

  const [createDrawerOpen, setCreateDrawerOpen] = React.useState(false);
  const [createStep, setCreateStep] = React.useState(1);
  const [createTestInput, setCreateTestInput] = React.useState('');
  const [createTestResult, setCreateTestResult] = React.useState<string | null>(null);
  const [testingRule, setTestingRule] = React.useState(false);

  const [importDrawerOpen, setImportDrawerOpen] = React.useState(false);
  const [importPayload, setImportPayload] = React.useState('');
  const [importing, setImporting] = React.useState(false);
  const [importError, setImportError] = React.useState<string | null>(null);

  const resetPagination = React.useCallback(() => {
    setPage(1);
    setHasNext(false);
    setTotalItems(undefined);
  }, []);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = Math.max(0, (page - 1) * pageSize);
      const result = await fetchModerationAIRules({ limit: pageSize, offset });
      setItems(result.items);
      setTotalItems(result.total);
      setHasNext(result.hasNext);
      setLastLoadedAt(new Date().toISOString());
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
      setItems([]);
      setHasNext(false);
      setTotalItems(undefined);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  React.useEffect(() => {
    void load();
  }, [load]);

  const createRule = React.useCallback(async () => {
    if (!newRule.category.trim()) {
      setError('Rule category is required.');
      return false;
    }
    try {
      await createModerationAIRule({
        category: newRule.category.trim(),
        description: newRule.description.trim() || null,
        defaultAction: newRule.defaultAction,
        threshold: newRule.threshold ? Number(newRule.threshold) : null,
        enabled: true,
      });
      setNewRule({ category: '', description: '', defaultAction: 'flag', threshold: '' });
      setCreateStep(1);
      setCreateTestInput('');
      setCreateTestResult(null);
      if (page !== 1) {
        resetPagination();
      }
      await load();
      return true;
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
      return false;
    }
  }, [newRule, page, load, resetPagination]);

  const toggleRule = React.useCallback(
    async (rule: ModerationAIRule) => {
      try {
        await updateModerationAIRule(rule.id, { enabled: !rule.enabled });
        await load();
      } catch (e: any) {
        setError(String(e?.message || e || 'error'));
      }
    },
    [load],
  );

  const removeRule = React.useCallback(
    async (rule: ModerationAIRule) => {
      try {
        await deleteModerationAIRule(rule.id);
        await load();
      } catch (e: any) {
        setError(String(e?.message || e || 'error'));
      }
    },
    [load],
  );

  const openRuleDrawer = React.useCallback((rule: ModerationAIRule) => {
    setSelectedRule(rule);
    setEditing({
      description: rule.description ?? '',
      defaultAction: rule.default_action ?? 'flag',
      threshold: rule.threshold != null ? String(rule.threshold) : '',
      enabled: rule.enabled,
    });
  }, []);

  const closeRuleDrawer = React.useCallback(() => {
    setSelectedRule(null);
  }, []);

  const saveRule = React.useCallback(async () => {
    if (!selectedRule) return;
    try {
      await updateModerationAIRule(selectedRule.id, {
        description: editing.description || null,
        defaultAction: editing.defaultAction,
        threshold: editing.threshold ? Number(editing.threshold) : null,
        enabled: editing.enabled,
      });
      await load();
      closeRuleDrawer();
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    }
  }, [selectedRule, editing, load, closeRuleDrawer]);

  const normalizedSearch = search.trim().toLowerCase();
  const filteredItems = React.useMemo(() => {
    return items.filter((rule) => {
      if (enabledOnly && !rule.enabled) return false;
      const haystack = [rule.category, rule.description ?? '', rule.default_action ?? '', rule.updated_by ?? '']
        .filter(Boolean)
        .map((value) => String(value).toLowerCase());
      return normalizedSearch ? haystack.some((value) => value.includes(normalizedSearch)) : true;
    });
  }, [enabledOnly, items, normalizedSearch]);

  const enabledCount = items.filter((rule) => rule.enabled).length;
  const disabledCount = items.length - enabledCount;

  const drawerHistory = React.useMemo(() => {
    if (!selectedRule) return [] as Record<string, unknown>[];
    const history = selectedRule.meta?.history ?? selectedRule.meta?.changes ?? selectedRule.meta?.audit;
    return ensureArray(history);
  }, [selectedRule]);

  const drawerMetrics = React.useMemo(() => {
    if (!selectedRule?.metrics) return [] as Array<[string, unknown]>;
    return Object.entries(selectedRule.metrics);
  }, [selectedRule?.metrics]);

  const heroMetrics = React.useMemo<PageHeroMetric[]>(
    () => [
      {
        id: 'total-rules',
        label: 'Total rules',
        value: items.length.toLocaleString(),
        helper: 'Across moderation workspace',
        accent: items.length > 0 ? 'positive' : 'neutral',
      },
      {
        id: 'enabled-rules',
        label: 'Enabled',
        value: enabledCount.toLocaleString(),
        helper: disabledCount > 0 ? `${disabledCount.toLocaleString()} disabled` : 'All active',
        accent: enabledCount > 0 ? 'positive' : 'neutral',
      },
      {
        id: 'disabled-rules',
        label: 'Disabled',
        value: disabledCount.toLocaleString(),
        helper: 'Paused moderation logic',
        accent: disabledCount > 0 ? 'warning' : 'neutral',
      },
    ],
    [disabledCount, enabledCount, items.length],
  );

  const refreshStatus = loading
    ? 'Refreshing…'
    : error
    ? 'Last refresh failed'
    : lastLoadedAt
    ? `Updated ${formatRelativeTime(lastLoadedAt)}`
    : 'Waiting for data';

  const statusToneClass = error ? 'text-rose-500 dark:text-rose-300' : 'text-gray-500 dark:text-dark-200/80';
  const statusDotClass = clsx(
    'inline-flex h-2 w-2 rounded-full',
    loading ? 'animate-pulse' : '',
    error ? 'bg-rose-400 dark:bg-rose-300' : 'bg-emerald-400 dark:bg-emerald-300',
  );

  const handleCreateNext = React.useCallback(() => {
    setCreateStep((prev) => Math.min(prev + 1, 4));
  }, []);

  const handleCreateBack = React.useCallback(() => {
    setCreateStep((prev) => Math.max(prev - 1, 1));
  }, []);

  const handleCreateSubmit = React.useCallback(async () => {
    const success = await createRule();
    if (success) {
      setCreateDrawerOpen(false);
    }
  }, [createRule]);

  const handleRunTest = React.useCallback(async () => {
    if (!createTestInput.trim()) {
      setCreateTestResult('Provide sample text to run a check.');
      return;
    }
    setTestingRule(true);
    await new Promise((resolve) => window.setTimeout(resolve, 400));
    const simulatedScore = Math.random();
    const action = simulatedScore >= (Number(newRule.threshold) || 0.5) ? newRule.defaultAction : 'allow';
    setCreateTestResult(`Score ${simulatedScore.toFixed(2)} · Simulated action: ${action}`);
    setTestingRule(false);
  }, [createTestInput, newRule.defaultAction, newRule.threshold]);

  const handleImportApply = React.useCallback(async () => {
    if (!importPayload.trim()) return;
    setImporting(true);
    setImportError(null);
    try {
      const parsed = JSON.parse(importPayload);
      if (!Array.isArray(parsed)) {
        throw new Error('Expected an array of rules.');
      }
      for (const entry of parsed) {
        if (!entry?.category) continue;
        await createModerationAIRule({
          category: String(entry.category),
          description: entry.description ? String(entry.description) : null,
          defaultAction: entry.default_action ? String(entry.default_action) : 'flag',
          threshold:
            entry.threshold != null && Number.isFinite(Number(entry.threshold)) ? Number(entry.threshold) : null,
          enabled: entry.enabled !== false,
        });
      }
      setImportPayload('');
      setImportDrawerOpen(false);
      await load();
    } catch (err: any) {
      setImportError(String(err?.message || 'Failed to import rules'));
    } finally {
      setImporting(false);
    }
  }, [importPayload, load]);

  const canAdvanceFromStep1 = Boolean(newRule.category.trim());

  return (
    <div className="space-y-6 p-6">
      <PageHero
        eyebrow="Guardrails"
        title="AI Moderation Rules"
        description="Automate content decisions, triage events, and keep enforcement consistent."
        metrics={heroMetrics}
        align="start"
        variant="metrics"
        tone="light"
        className="ring-1 ring-primary-500/10 dark:ring-primary-400/15"
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <div className={clsx('flex items-center gap-2 text-xs', statusToneClass)}>
              <span className={statusDotClass} aria-hidden="true" />
              <span>{refreshStatus}</span>
            </div>
            <Button variant="ghost" color="neutral" size="sm" onClick={() => void load()} disabled={loading}>
              {loading ? <Spinner size="sm" className="mr-1" /> : <ArrowPathIcon className="size-4" aria-hidden="true" />}
              Refresh
            </Button>
            <Button
              size="sm"
              onClick={() => {
                setCreateDrawerOpen(true);
                setCreateStep(1);
              }}
            >
              <PlusIcon className="mr-1 size-4" aria-hidden="true" />
              Create rule
            </Button>
            <Button size="sm" variant="outlined" onClick={() => setImportDrawerOpen(true)}>
              <ArrowUpTrayIcon className="mr-1 size-4" aria-hidden="true" />
              Import template
            </Button>
          </div>
        }
      />

      {error ? (
        <Card skin="shadow" className="border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
          {error}
        </Card>
      ) : null}

      <Card skin="shadow" className="space-y-6 rounded-2xl border border-gray-200 bg-white/95 p-5 dark:border-dark-700/70 dark:bg-dark-900/94">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-[260px] flex-1 items-center gap-3">
            <Input
              className="w-full"
              placeholder="Search by category, description, owner"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-dark-200/80">
            <Switch checked={enabledOnly} onChange={() => setEnabledOnly((prev) => !prev)} />
            <span>Enabled only</span>
          </div>
        </div>

        <div className="relative overflow-x-auto rounded-2xl border border-gray-200 dark:border-dark-600">
          <UITable preset="surface" className="min-w-[900px]" hover>
            <UITable.THead>
              <UITable.TR>
                <UITable.TH>Category</UITable.TH>
                <UITable.TH>Description</UITable.TH>
                <UITable.TH>Default action</UITable.TH>
                <UITable.TH>Threshold</UITable.TH>
                <UITable.TH>Updated</UITable.TH>
                <UITable.TH>By</UITable.TH>
                <UITable.TH className="text-right">Actions</UITable.TH>
              </UITable.TR>
            </UITable.THead>
            <UITable.TBody>
              {filteredItems.length === 0 ? (
                loading ? (
                  <UITable.Loading rows={3} colSpan={7} />
                ) : (
                  <UITable.Empty
                    colSpan={7}
                    title="No rules match the current filters"
                    description="Adjust the search criteria or create a new AI moderation rule."
                  />
                )
              ) : (
                filteredItems.map((rule) => (
                  <UITable.TR key={rule.id}>
                    <UITable.TD>
                      <div className="flex items-center gap-2">
                        <Badge color={rule.enabled ? 'success' : 'warning'} variant="soft">
                          {rule.enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                        <span className="font-medium text-gray-900 dark:text-gray-100">{rule.category}</span>
                      </div>
                    </UITable.TD>
                    <UITable.TD className="text-sm text-gray-600 dark:text-dark-200">
                      {rule.description || 'N/A'}
                    </UITable.TD>
                    <UITable.TD className="text-sm text-gray-600 dark:text-dark-200">
                      {rule.default_action || 'N/A'}
                    </UITable.TD>
                    <UITable.TD className="text-sm text-gray-600 dark:text-dark-200">
                      {rule.threshold != null ? rule.threshold : 'N/A'}
                    </UITable.TD>
                    <UITable.TD className="text-sm text-gray-600 dark:text-dark-200">{formatDate(rule.updated_at)}</UITable.TD>
                    <UITable.TD className="text-sm text-gray-500 dark:text-dark-300">{rule.updated_by || 'system'}</UITable.TD>
                    <UITable.TD>
                      <div className="flex justify-end gap-2">
                        <Button size="sm" variant="ghost" onClick={() => openRuleDrawer(rule)}>
                          Details
                        </Button>
                        <Button size="sm" variant="outlined" onClick={() => toggleRule(rule)}>
                          {rule.enabled ? 'Disable' : 'Enable'}
                        </Button>
                        <Button size="sm" color="error" variant="ghost" onClick={() => removeRule(rule)}>
                          Delete
                        </Button>
                      </div>
                    </UITable.TD>
                  </UITable.TR>
                ))
              )}
            </UITable.TBody>
          </UITable>
          {loading && filteredItems.length > 0 ? (
            <div className="flex items-center justify-center py-6 text-sm text-gray-500 dark:text-dark-300">
              <Spinner size="sm" />
              <span className="ml-2">Loading rules…</span>
            </div>
          ) : null}
        </div>

        {!loading && filteredItems.length === 0 ? (
          <Card skin="bordered" className="mt-2 rounded-2xl border-dashed border-gray-300 p-6 text-sm text-gray-600 dark:border-dark-600 dark:text-dark-200/80">
            <h3 className="text-base font-semibold text-gray-800 dark:text-gray-100">Get started with AI moderation</h3>
            <ul className="mt-3 space-y-2 text-gray-600 dark:text-dark-200/80">
              <li>• Connect your telemetry feed or upload historical incidents.</li>
              <li>• Create rule categories (toxicity, spam, copyright, etc.).</li>
              <li>• Define default actions and thresholds for automation confidence.</li>
              <li>• Test the rule on sample text before enabling it.</li>
            </ul>
            <Button className="mt-4" onClick={() => setCreateDrawerOpen(true)}>
              Create first rule
            </Button>
          </Card>
        ) : null}

        <TablePagination
          page={page}
          pageSize={pageSize}
          currentCount={filteredItems.length}
          hasNext={hasNext}
          totalItems={totalItems}
          onPageChange={(value) => setPage(value)}
          onPageSizeChange={(value) => {
            setPageSize(value);
            resetPagination();
          }}
        />
      </Card>

      <Drawer
        open={!!selectedRule}
        onClose={closeRuleDrawer}
        title={selectedRule ? `Rule details: ${selectedRule.category}` : 'Rule details'}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={closeRuleDrawer}>
              Cancel
            </Button>
            <Button onClick={saveRule}>Save changes</Button>
          </div>
        }
        widthClass="w-full max-w-2xl"
      >
        {selectedRule ? (
          <div className="space-y-6 p-2">
            <section className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Configuration</h3>
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <div className="mb-1 text-xs text-gray-500">Category</div>
                  <Input value={selectedRule.category} disabled />
                </div>
                <div>
                  <div className="mb-1 text-xs text-gray-500">Rule ID</div>
                  <Input value={selectedRule.id} disabled />
                </div>
                <div>
                  <div className="mb-1 text-xs text-gray-500">Default action</div>
                  <Select
                    value={editing.defaultAction}
                    onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                      setEditing((prev) => ({ ...prev, defaultAction: event.target.value }))
                    }
                  >
                    {DEFAULT_ACTIONS.map((action) => (
                      <option key={action} value={action}>
                        {action}
                      </option>
                    ))}
                  </Select>
                </div>
                <div>
                  <div className="mb-1 text-xs text-gray-500">Threshold</div>
                  <Input
                    value={editing.threshold}
                    onChange={(event) => setEditing((prev) => ({ ...prev, threshold: event.target.value }))}
                    placeholder="e.g. 0.85"
                  />
                </div>
              </div>
            </section>

            <section className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Description</h3>
              <Textarea
                rows={3}
                value={editing.description}
                onChange={(event) => setEditing((prev) => ({ ...prev, description: event.target.value }))}
              />
            </section>

            <section className="space-y-3">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Status</h3>
              <div className="flex items-center gap-3">
                <Switch checked={editing.enabled} onChange={() => setEditing((prev) => ({ ...prev, enabled: !prev.enabled }))} />
                <span className="text-sm text-gray-600 dark:text-dark-200/80">
                  {editing.enabled ? 'Rule active and applied to new events' : 'Rule disabled'}
                </span>
              </div>
            </section>

            {drawerMetrics.length > 0 ? (
              <Card skin="bordered" className="space-y-3 rounded-xl border-gray-200 p-4 dark:border-dark-600">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Recent metrics</h4>
                <div className="grid gap-2 sm:grid-cols-2">
                  {drawerMetrics.map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-xs text-gray-600 dark:text-dark-200/80">
                      <span className="uppercase tracking-wide text-gray-500">{key}</span>
                      <span className="font-semibold text-gray-700 dark:text-gray-100">
                        {typeof value === 'number' ? value.toLocaleString() : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            ) : null}

            {drawerHistory.length > 0 ? (
              <Card skin="bordered" className="space-y-3 rounded-xl border-gray-200 p-4 dark:border-dark-600">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Change log</h4>
                <div className="space-y-2">
                  {drawerHistory.map((entry, index) => {
                    const actionLabel = String(entry.action ?? entry.type ?? 'Update');
                    const actorLabel = entry.actor != null ? String(entry.actor) : null;
                    const detailsLabel = entry.details != null ? String(entry.details) : null;
                    const timestamp = entry.timestamp ?? entry.created_at ?? entry.updated_at;
                    return (
                      <div
                        key={index}
                        className="rounded-lg border border-gray-200 p-3 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200/80"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-gray-700 dark:text-gray-100">{actionLabel}</span>
                          <span className="text-[11px] text-gray-400 dark:text-dark-400">
                            {formatDate(typeof timestamp === 'string' ? timestamp : undefined)}
                          </span>
                        </div>
                        {actorLabel ? (
                          <div className="mt-1 text-[11px] text-gray-400 dark:text-dark-400">by {actorLabel}</div>
                        ) : null}
                        {detailsLabel ? (
                          <div className="mt-2 text-[11px] text-gray-500 dark:text-dark-300">{detailsLabel}</div>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              </Card>
            ) : null}
          </div>
        ) : null}
      </Drawer>

      <Drawer
        open={createDrawerOpen}
        onClose={() => {
          setCreateDrawerOpen(false);
          setCreateStep(1);
        }}
        title="Create AI moderation rule"
        footer={
          <div className="flex justify-between gap-2">
            <div>{createStep > 1 ? <Button variant="ghost" onClick={handleCreateBack}>Back</Button> : null}</div>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => setCreateDrawerOpen(false)}>
                Cancel
              </Button>
              {createStep < 4 ? (
                <Button onClick={handleCreateNext} disabled={createStep === 1 && !canAdvanceFromStep1}>
                  Next
                </Button>
              ) : (
                <Button onClick={handleCreateSubmit}>Create rule</Button>
              )}
            </div>
          </div>
        }
        widthClass="w-full max-w-2xl"
      >
        <div className="space-y-6 p-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            Step {createStep} of 4
          </div>

          {createStep === 1 ? (
            <div className="space-y-4">
              <div>
                <div className="mb-1 text-xs text-gray-500">Rule category</div>
                <Input
                  value={newRule.category}
                  onChange={(event) => setNewRule((prev) => ({ ...prev, category: event.target.value }))}
                  placeholder="e.g. toxicity"
                />
              </div>
              <div>
                <div className="mb-1 text-xs text-gray-500">Description</div>
                <Textarea
                  rows={3}
                  value={newRule.description}
                  onChange={(event) => setNewRule((prev) => ({ ...prev, description: event.target.value }))}
                  placeholder="Describe what this rule should catch and why."
                />
              </div>
            </div>
          ) : null}

          {createStep === 2 ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <div className="mb-1 text-xs text-gray-500">Default action</div>
                <Select
                  value={newRule.defaultAction}
                  onChange={(event: React.ChangeEvent<HTMLSelectElement>) =>
                    setNewRule((prev) => ({ ...prev, defaultAction: event.target.value }))
                  }
                >
                  {DEFAULT_ACTIONS.map((action) => (
                    <option key={action} value={action}>
                      {action}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <div className="mb-1 text-xs text-gray-500">Threshold</div>
                <Input
                  value={newRule.threshold}
                  onChange={(event) => setNewRule((prev) => ({ ...prev, threshold: event.target.value }))}
                  placeholder="0.0 - 1.0 (optional)"
                />
                <div className="mt-1 text-xs text-gray-400">
                  Model confidence required before the action triggers.
                </div>
              </div>
            </div>
          ) : null}

          {createStep === 3 ? (
            <div className="space-y-4">
              <div>
                <div className="mb-1 text-xs text-gray-500">Test with sample content</div>
                <Textarea
                  rows={4}
                  value={createTestInput}
                  onChange={(event) => setCreateTestInput(event.target.value)}
                  placeholder="Paste sample content to simulate a decision."
                />
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outlined" onClick={handleRunTest} disabled={testingRule}>
                  {testingRule ? <Spinner size="sm" className="mr-1" /> : null}
                  Run test
                </Button>
                {createTestResult ? (
                  <span className="text-sm text-gray-600 dark:text-dark-200/80">{createTestResult}</span>
                ) : null}
              </div>
            </div>
          ) : null}

          {createStep === 4 ? (
            <Card skin="bordered" className="space-y-3 rounded-xl border-gray-200 p-4 dark:border-dark-600">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Review</h3>
              <div className="grid gap-2 text-sm text-gray-600 dark:text-dark-200/80">
                <div>
                  <span className="font-medium text-gray-700 dark:text-gray-100">Category:</span> {newRule.category || 'N/A'}
                </div>
                <div>
                  <span className="font-medium text-gray-700 dark:text-gray-100">Description:</span>{' '}
                  {newRule.description || 'N/A'}
                </div>
                <div>
                  <span className="font-medium text-gray-700 dark:text-gray-100">Default action:</span>{' '}
                  {newRule.defaultAction}
                </div>
                <div>
                  <span className="font-medium text-gray-700 dark:text-gray-100">Threshold:</span>{' '}
                  {newRule.threshold || 'N/A'}
                </div>
                <div>
                  <span className="font-medium text-gray-700 dark:text-gray-100">Test result:</span>{' '}
                  {createTestResult || 'Not run'}
                </div>
              </div>
            </Card>
          ) : null}
        </div>
      </Drawer>

      <Drawer
        open={importDrawerOpen}
        onClose={() => {
          setImportDrawerOpen(false);
          setImportPayload('');
          setImportError(null);
        }}
        title="Import rules template"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setImportDrawerOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleImportApply} disabled={importing || !importPayload.trim()}>
              {importing ? <Spinner size="sm" className="mr-1" /> : null}
              Import rules
            </Button>
          </div>
        }
        widthClass="w-full max-w-2xl"
      >
        <div className="space-y-4 p-2 text-sm text-gray-600 dark:text-dark-200/80">
          <p>Paste a JSON array of rules. Each entry should include at least a <code>category</code>.</p>
          <Textarea
            rows={10}
            value={importPayload}
            onChange={(event) => setImportPayload(event.target.value)}
            placeholder={`[
  {"category": "toxicity", "description": "Toxic language", "default_action": "flag", "threshold": 0.65},
  {"category": "spam", "default_action": "hide"}
]`}
          />
          {importError ? <div className="text-sm text-rose-600">{importError}</div> : null}
          <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-3 text-xs text-gray-500 dark:border-dark-600 dark:bg-dark-800/40 dark:text-dark-200/80">
            Tip: combine import with rule tagging to organise enforcement by product surface.
          </div>
        </div>
      </Drawer>
    </div>
  );
}
