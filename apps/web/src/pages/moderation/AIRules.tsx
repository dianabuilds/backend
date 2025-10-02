import React from 'react';
import { Card, Spinner, TablePagination, Drawer, Input, Textarea, Switch, Button, Badge, Accordion, Select } from '@ui';
import { apiGet, apiPost, apiPatch, apiDelete } from '../../shared/api/client';

type Rule = {
  id: string;
  category: string;
  enabled: boolean;
  updated_by?: string | null;
  updated_at?: string | null;
  description?: string | null;
  default_action?: string | null;
  threshold?: number | null;
  metrics?: Record<string, any>;
  meta?: Record<string, any>;
};

type RuleDraft = {
  category: string;
  description: string;
  defaultAction: string;
  threshold: string;
};

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString();
}

function ensureArray<T = Record<string, any>>(value: any): T[] {
  if (Array.isArray(value)) return value as T[];
  return [];
}

const defaultActions = ['flag', 'hide', 'escalate', 'restrict', 'delete'];

export default function ModerationAIRules() {
  const [items, setItems] = React.useState<Rule[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [newRule, setNewRule] = React.useState<RuleDraft>({ category: '', description: '', defaultAction: 'flag', threshold: '' });

  const [search, setSearch] = React.useState('');
  const [enabledOnly, setEnabledOnly] = React.useState(false);

  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [totalItems, setTotalItems] = React.useState<number | undefined>(undefined);

  const [selectedRule, setSelectedRule] = React.useState<Rule | null>(null);
  const [editing, setEditing] = React.useState<{ description: string; defaultAction: string; threshold: string; enabled: boolean }>({
    description: '',
    defaultAction: 'flag',
    threshold: '',
    enabled: true,
  });

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
      const r = await apiGet<{ items?: Rule[]; total?: number }>(`/api/moderation/ai-rules?limit=${pageSize}&offset=${offset}`);
      const fetched = Array.isArray(r?.items) ? r.items : [];
      setItems(fetched);
      const total = typeof r?.total === 'number' ? Number(r.total) : undefined;
      setTotalItems(total);
      if (total != null) {
        setHasNext(page * pageSize < total);
      } else {
        setHasNext(fetched.length === pageSize);
      }
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
      setHasNext(false);
      setTotalItems(undefined);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  React.useEffect(() => {
    void load();
  }, [load]);

  const create = React.useCallback(async () => {
    if (!newRule.category.trim()) return;
    try {
      await apiPost('/api/moderation/ai-rules', {
        category: newRule.category.trim(),
        enabled: true,
        description: newRule.description.trim() || undefined,
        default_action: newRule.defaultAction,
        threshold: newRule.threshold ? Number(newRule.threshold) : undefined,
      });
      setNewRule({ category: '', description: '', defaultAction: 'flag', threshold: '' });
      if (page !== 1) {
        resetPagination();
      } else {
        await load();
      }
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    }
  }, [newRule, page, load, resetPagination]);

  const toggle = React.useCallback(async (rule: Rule) => {
    try {
      await apiPatch(`/api/moderation/ai-rules/${encodeURIComponent(rule.id)}`, { enabled: !rule.enabled });
      await load();
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    }
  }, [load]);

  const remove = React.useCallback(async (rule: Rule) => {
    try {
      await apiDelete(`/api/moderation/ai-rules/${encodeURIComponent(rule.id)}`);
      await load();
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    }
  }, [load]);

  const openDrawer = React.useCallback((rule: Rule) => {
    setSelectedRule(rule);
    setEditing({
      description: rule.description ?? '',
      defaultAction: rule.default_action ?? 'flag',
      threshold: rule.threshold != null ? String(rule.threshold) : '',
      enabled: rule.enabled,
    });
  }, []);

  const closeDrawer = React.useCallback(() => {
    setSelectedRule(null);
  }, []);

  const saveRule = React.useCallback(async () => {
    if (!selectedRule) return;
    try {
      await apiPatch(`/api/moderation/ai-rules/${encodeURIComponent(selectedRule.id)}`, {
        description: editing.description || null,
        default_action: editing.defaultAction,
        threshold: editing.threshold ? Number(editing.threshold) : null,
        enabled: editing.enabled,
      });
      await load();
      closeDrawer();
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    }
  }, [selectedRule, editing, load, closeDrawer]);

  const normalizedSearch = search.trim().toLowerCase();
  const filteredItems = React.useMemo(() => {
    return items.filter((rule) => {
      if (enabledOnly && !rule.enabled) return false;
      const haystack = [rule.category, rule.description ?? '', rule.default_action ?? '', rule.updated_by ?? '']
        .filter(Boolean)
        .map((value) => String(value).toLowerCase());
      return normalizedSearch ? haystack.some((value) => value.includes(normalizedSearch)) : true;
    });
  }, [items, normalizedSearch, enabledOnly]);

  const enabledCount = items.filter((rule) => rule.enabled).length;
  const disabledCount = items.length - enabledCount;

  const drawerHistory = React.useMemo(() => {
    if (!selectedRule) return [] as Record<string, any>[];
    const history = selectedRule.meta?.history ?? selectedRule.meta?.changes ?? selectedRule.meta?.audit;
    return ensureArray(history);
  }, [selectedRule]);

  const drawerMetrics = React.useMemo(() => {
    if (!selectedRule?.metrics) return [] as Array<[string, any]>;
    return Object.entries(selectedRule.metrics);
  }, [selectedRule?.metrics]);

  return (
    <div className="p-6 space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <Card skin="shadow" className="p-4"><div className="text-xs text-gray-500">Total rules</div><div className="text-2xl font-semibold">{items.length}</div></Card>
        <Card skin="shadow" className="p-4"><div className="text-xs text-gray-500">Enabled</div><div className="text-2xl font-semibold text-emerald-600">{enabledCount}</div></Card>
        <Card skin="shadow" className="p-4"><div className="text-xs text-gray-500">Disabled</div><div className="text-2xl font-semibold text-amber-600">{disabledCount}</div></Card>
      </div>

      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">AI Rules</h1>
        <div className="flex items-center gap-2">
          {loading && <Spinner size="sm" />}
          <Button variant="outlined" onClick={load}>Refresh</Button>
        </div>
      </div>

      {error && <Card skin="shadow" className="p-3 text-red-600">{error}</Card>}

      <Card skin="shadow" className="p-4 space-y-4">
        <div className="grid gap-3 md:grid-cols-4">
          <Input
            className="form-input h-9"
            placeholder="Search by category, description, owner"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Switch checked={enabledOnly} onChange={() => setEnabledOnly((prev) => !prev)} />
            <span>Enabled only</span>
          </div>
          <Input
            className="form-input h-9"
            placeholder="Default action (e.g. escalate)"
            value={newRule.defaultAction}
            onChange={(e) => setNewRule((prev) => ({ ...prev, defaultAction: e.target.value }))}
          />
          <Input
            className="form-input h-9"
            placeholder="Threshold (optional)"
            value={newRule.threshold}
            onChange={(e) => setNewRule((prev) => ({ ...prev, threshold: e.target.value }))}
          />
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <Input
            className="form-input h-9"
            placeholder="New rule category (e.g. toxicity)"
            value={newRule.category}
            onChange={(e) => setNewRule((prev) => ({ ...prev, category: e.target.value }))}
          />
          <Textarea
            rows={1}
            className="form-textarea"
            placeholder="Description (optional)"
            value={newRule.description}
            onChange={(e) => setNewRule((prev) => ({ ...prev, description: e.target.value }))}
          />
          <Button className="h-9" onClick={create}>
            Create rule
          </Button>
        </div>

        <div className="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-500">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-3 py-2">Category</th>
                <th className="px-3 py-2">Description</th>
                <th className="px-3 py-2">Default action</th>
                <th className="px-3 py-2">Threshold</th>
                <th className="px-3 py-2">Updated</th>
                <th className="px-3 py-2">By</th>
                <th className="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((rule) => (
                <tr key={rule.id} className="border-b border-gray-200">
                  <td className="px-3 py-2 font-medium">
                    <div className="flex items-center gap-2">
                      <Badge color={rule.enabled ? 'success' : 'warning'} variant="soft">
                        {rule.enabled ? 'enabled' : 'disabled'}
                      </Badge>
                      <span>{rule.category}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-600">{rule.description || '—'}</td>
                  <td className="px-3 py-2 text-sm text-gray-600">{rule.default_action || '—'}</td>
                  <td className="px-3 py-2 text-sm text-gray-600">{rule.threshold != null ? rule.threshold : '—'}</td>
                  <td className="px-3 py-2 text-sm text-gray-600">{formatDate(rule.updated_at)}</td>
                  <td className="px-3 py-2 text-sm text-gray-500">{rule.updated_by || 'system'}</td>
                  <td className="px-3 py-2">
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="ghost" onClick={() => openDrawer(rule)}>
                        Detail
                      </Button>
                      <Button size="sm" variant="outlined" onClick={() => toggle(rule)}>
                        {rule.enabled ? 'Disable' : 'Enable'}
                      </Button>
                      <Button size="sm" color="error" variant="ghost" onClick={() => remove(rule)}>
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredItems.length === 0 && (
                <tr>
                  <td className="px-3 py-4 text-center text-sm text-gray-500" colSpan={7}>
                    No rules match the current filters
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {loading && (
            <div className="flex items-center justify-center py-6 text-sm text-gray-500">
              <Spinner size="sm" />
              <span className="ml-2">Loading rules...</span>
            </div>
          )}
        </div>

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
        onClose={closeDrawer}
        title={selectedRule ? `Rule details: ${selectedRule.category}` : 'Rule details'}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outlined" onClick={closeDrawer}>
              Cancel
            </Button>
            <Button onClick={saveRule}>Save changes</Button>
          </div>
        }
        widthClass="w-full max-w-2xl"
      >
        {selectedRule ? (
          <div className="space-y-4 p-2">
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
                  onChange={(e: any) => setEditing((prev) => ({ ...prev, defaultAction: e.target.value }))}
                >
                  {defaultActions.map((action) => (
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
                  onChange={(e) => setEditing((prev) => ({ ...prev, threshold: e.target.value }))}
                  placeholder="e.g. 0.8"
                />
              </div>
            </div>

            <div>
              <div className="mb-1 text-xs text-gray-500">Description</div>
              <Textarea
                rows={3}
                value={editing.description}
                onChange={(e) => setEditing((prev) => ({ ...prev, description: e.target.value }))}
              />
            </div>

            <div className="flex items-center gap-3">
              <Switch checked={editing.enabled} onChange={() => setEditing((prev) => ({ ...prev, enabled: !prev.enabled }))} />
              <span className="text-sm text-gray-600">
                {editing.enabled ? 'Rule active and applied to incoming content' : 'Rule disabled'}
              </span>
            </div>

            {drawerMetrics.length > 0 ? (
              <Card skin="shadow" className="p-4">
                <div className="text-sm font-semibold text-gray-700">Recent metrics</div>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {drawerMetrics.map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-xs text-gray-600">
                      <span className="uppercase tracking-wide text-gray-500">{key}</span>
                      <span className="font-semibold text-gray-700">{typeof value === 'number' ? value.toLocaleString() : String(value)}</span>
                    </div>
                  ))}
                </div>
              </Card>
            ) : null}

            {drawerHistory.length > 0 ? (
              <Accordion title="Change history" defaultOpen={false}>
                <div className="max-h-72 overflow-auto px-4 py-3 text-xs text-gray-600 dark:text-dark-200">
                  {drawerHistory.map((entry, index) => (
                    <div key={index} className="border-b border-gray-200 py-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-gray-700">{entry.action ?? entry.event ?? 'Update'}</span>
                        <span className="text-[11px] text-gray-400">{formatDate(entry.timestamp ?? entry.at)}</span>
                      </div>
                      <div className="text-gray-500">{entry.actor ? `by ${entry.actor}` : 'system'}</div>
                      {entry.diff ? (
                        <pre className="mt-1 whitespace-pre-wrap rounded bg-gray-100 p-2 text-[11px] text-gray-600">
                          {JSON.stringify(entry.diff, null, 2)}
                        </pre>
                      ) : null}
                    </div>
                  ))}
                </div>
              </Accordion>
            ) : null}

            <Accordion title="Raw payload" defaultOpen={false}>
              <div className="max-h-72 overflow-auto px-4 py-3 text-xs text-gray-600 dark:text-dark-200">
                <pre>{JSON.stringify(selectedRule, null, 2)}</pre>
              </div>
            </Accordion>
          </div>
        ) : null}
      </Drawer>
    </div>
  );
}
