import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { NotificationSurface, notificationTableHeadCellClass, notificationTableRowClass } from './NotificationSurface';
import { Badge, Button, Drawer, Input, Pagination, Select, Spinner, Switch, Table, Textarea } from '@ui';
import { apiDelete, apiGet, apiPost } from '../../shared/api/client';
import { useAuth } from '../../shared/auth/AuthContext';

export type NotificationTemplate = {
  id: string;
  slug: string;
  name: string;
  description?: string | null;
  subject?: string | null;
  body: string;
  locale?: string | null;
  variables?: Record<string, unknown> | null;
  meta?: Record<string, unknown> | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
};

function formatDate(value?: string | null) {
  if (!value) return '-';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString();
}

function preview(text: string, max = 90) {
  const clean = text.replace(/\s+/g, ' ').trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, Math.max(0, max - 3))}...`;
}

type TemplateFieldType = 'string' | 'text' | 'number' | 'boolean' | 'json';

type TemplateFieldRow = {
  id: number;
  key: string;
  type: TemplateFieldType;
  value: string;
};

const LOCALE_PRESETS = ['', 'en', 'ru'];

const TEMPLATE_FIELD_TYPES: Array<{ value: TemplateFieldType; label: string }> = [
  { value: 'string', label: 'Short text' },
  { value: 'text', label: 'Rich text' },
  { value: 'number', label: 'Number' },
  { value: 'boolean', label: 'Yes / No' },
  { value: 'json', label: 'JSON snippet' },
];

function createTemplateRow(id: number): TemplateFieldRow {
  return { id, key: '', type: 'string', value: '' };
}

function objectToTemplateRows(
  value: Record<string, unknown> | null | undefined,
  startId: number = 1,
): [TemplateFieldRow[], number] {
  const rows: TemplateFieldRow[] = [];
  let nextId = startId;
  if (value) {
    for (const [key, raw] of Object.entries(value)) {
      let type: TemplateFieldType = 'string';
      let stored = '';
      if (typeof raw === 'boolean') {
        type = 'boolean';
        stored = raw ? 'true' : 'false';
      } else if (typeof raw === 'number') {
        type = 'number';
        stored = String(raw);
      } else if (typeof raw === 'string') {
        type = raw.includes('\n') || raw.length > 80 ? 'text' : 'string';
        stored = raw;
      } else {
        type = 'json';
        try {
          stored = JSON.stringify(raw, null, 2);
        } catch {
          stored = '';
        }
      }
      rows.push({ id: nextId++, key, type, value: stored });
    }
  }
  if (rows.length === 0) {
    rows.push(createTemplateRow(nextId++));
  }
  return [rows, nextId];
}

function rowsToTemplateObject(rows: TemplateFieldRow[]): { result: Record<string, unknown> | null; error?: string } {
  const payload: Record<string, unknown> = {};
  for (const row of rows) {
    const key = row.key.trim();
    if (!key) {
      continue;
    }
    switch (row.type) {
      case 'string':
      case 'text':
        payload[key] = row.value;
        break;
      case 'number': {
        if (!row.value.trim()) {
          return { error: `Value for "${key}" must be a number.` };
        }
        const num = Number(row.value);
        if (Number.isNaN(num)) {
          return { error: `Value for "${key}" must be a number.` };
        }
        payload[key] = num;
        break;
      }
      case 'boolean':
        payload[key] = row.value === 'true';
        break;
      case 'json': {
        if (!row.value.trim()) {
          return { error: `Value for "${key}" must be valid JSON.` };
        }
        try {
          payload[key] = JSON.parse(row.value);
        } catch {
          return { error: `Value for "${key}" must be valid JSON.` };
        }
        break;
      }
    }
  }
  if (Object.keys(payload).length === 0) {
    return { result: null };
  }
  return { result: payload };
}

export default function TemplatesPage() {
  const { user } = useAuth();
  const [templates, setTemplates] = React.useState<NotificationTemplate[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<NotificationTemplate | null>(null);
  const [name, setName] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [subject, setSubject] = React.useState('');
  const [body, setBody] = React.useState('');
  const [localePreset, setLocalePreset] = React.useState<string>('');
  const [variablesMode, setVariablesMode] = React.useState<'builder' | 'json'>('builder');
  const [variablesRows, setVariablesRows] = React.useState<TemplateFieldRow[]>([createTemplateRow(1)]);
  const variablesNextId = React.useRef(2);
  const [variablesJson, setVariablesJson] = React.useState('');
  const [metaMode, setMetaMode] = React.useState<'builder' | 'json'>('builder');
  const [metaRows, setMetaRows] = React.useState<TemplateFieldRow[]>([createTemplateRow(1)]);
  const metaNextId = React.useRef(2);
  const [metaJson, setMetaJson] = React.useState('');
  const [formError, setFormError] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [deleting, setDeleting] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);

  const filteredTemplates = React.useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) {
      return templates;
    }
    return templates.filter((tpl) => {
      const fields: Array<string | undefined | null> = [
        tpl.name,
        tpl.slug,
        tpl.subject ?? undefined,
        tpl.description ?? undefined,
        tpl.locale ?? undefined,
        tpl.body,
      ];
      return fields.some((field) => field && field.toLowerCase().includes(q));
    });
  }, [templates, searchQuery]);

  const totalTemplates = filteredTemplates.length;
  const totalPages = Math.max(1, Math.ceil(totalTemplates / pageSize));

  React.useEffect(() => {
    setPage((prev) => (prev > totalPages ? totalPages : prev));
  }, [totalPages]);

  React.useEffect(() => {
    setPage(1);
  }, [searchQuery, pageSize]);

  const visibleTemplates = React.useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredTemplates.slice(start, start + pageSize);
  }, [filteredTemplates, page, pageSize]);

  const showingFrom = totalTemplates === 0 ? 0 : (page - 1) * pageSize + 1;
  const showingTo = totalTemplates === 0 ? 0 : (page - 1) * pageSize + visibleTemplates.length;




const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiGet<{ items?: NotificationTemplate[] }>('/v1/notifications/admin/templates');
      setTemplates(Array.isArray(res?.items) ? res.items : []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load templates');
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  const openDrawer = (template?: NotificationTemplate | null) => {
    setEditing(template ?? null);
    const initialName = template?.name ?? '';


    setName(initialName);
    setDescription(template?.description ?? '');
    setSubject(template?.subject ?? '');
    setBody(template?.body ?? '');
    const localeValue = template?.locale ?? '';
    if (LOCALE_PRESETS.includes(localeValue)) {
      setLocalePreset(localeValue);
    } else {
      setLocalePreset('');
    }

    const [variableRows, nextVariableId] = objectToTemplateRows(template?.variables ?? null, 1);
    setVariablesRows(variableRows);
    variablesNextId.current = nextVariableId;
    setVariablesMode('builder');
    setVariablesJson(template?.variables ? JSON.stringify(template.variables, null, 2) : '');

    const [metaRowsInitial, nextMetaId] = objectToTemplateRows(template?.meta ?? null, 1);
    setMetaRows(metaRowsInitial);
    metaNextId.current = nextMetaId;
    setMetaMode('builder');
    setMetaJson(template?.meta ? JSON.stringify(template.meta, null, 2) : '');

    setFormError(null);
    setDrawerOpen(true);
  };

  const submit = async () => {
    setFormError(null);
    if (!name.trim() || !body.trim()) {
      setFormError('Name and body are required');
      return;
    }

    const localeValue = localePreset;
    const payload: Record<string, any> = {
      id: editing?.id,

      name: name.trim(),
      body,
      description: description.trim() ? description.trim() : null,
      subject: subject.trim() ? subject.trim() : null,
      locale: localeValue ? localeValue : null,
      created_by: editing?.created_by ?? user?.id ?? null,
    };

    if (variablesMode === 'builder') {
      const { result, error } = rowsToTemplateObject(variablesRows);
      if (error) {
        setFormError(`Variables: ${error}`);
        return;
      }
      payload.variables = result;
    } else if (variablesJson.trim()) {
      try {
        payload.variables = JSON.parse(variablesJson);
      } catch {
        setFormError('Variables JSON must be valid.');
        return;
      }
    } else {
      payload.variables = null;
    }

    if (metaMode === 'builder') {
      const { result, error } = rowsToTemplateObject(metaRows);
      if (error) {
        setFormError(`Meta: ${error}`);
        return;
      }
      payload.meta = result;
    } else if (metaJson.trim()) {
      try {
        payload.meta = JSON.parse(metaJson);
      } catch {
        setFormError('Meta JSON must be valid.');
        return;
      }
    } else {
      payload.meta = null;
    }

    setSaving(true);
    try {
      await apiPost('/v1/notifications/admin/templates', payload);
      setDrawerOpen(false);
      await refresh();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  const emptyMessage = searchQuery.trim() ? 'No templates match your search.' : 'No templates yet.';

  const remove = async (id: string) => {
    if (!window.confirm('Delete this template?')) return;
    setDeleting(id);
    try {
      await apiDelete(`/v1/notifications/admin/templates/${id}`);
      await refresh();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete template');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <ContentLayout context="notifications" title="Notification templates" description="Coordinate announcements, automate broadcasts, and keep every player cohort informed.">
      <div className="space-y-6">
        <NotificationSurface className="p-6 space-y-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">Notifications</div>
              <h1 className="text-2xl font-semibold text-gray-900">Template library</h1>
              <p className="max-w-2xl text-sm text-gray-600">
                Reuse blueprints for broadcasts, set localized subjects, and manage merge variables without touching code.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outlined" color="neutral" onClick={() => { void refresh(); }} disabled={loading}>
                Refresh
              </Button>
              <Button onClick={() => openDrawer(null)}>New template</Button>
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-rose-200/70 bg-rose-50/80 px-4 py-3 text-sm text-rose-700 shadow-sm">
              {error}
            </div>
          )}

          <div className="rounded-2xl border border-white/60 bg-white/40 p-4 shadow-inner backdrop-blur-sm dark:border-dark-600/60 dark:bg-dark-700/40">
            <div className="flex flex-col gap-3 border-b border-white/50 pb-4 sm:flex-row sm:items-center sm:justify-between dark:border-dark-600/50">
              <div>
                <div className="text-sm font-semibold text-indigo-900 dark:text-dark-50">Template catalog</div>
                <div className="text-xs text-indigo-600/80 dark:text-dark-200">
                  {totalTemplates > 0 ? `Displaying ${showingFrom}-${showingTo} of ${totalTemplates} templates` : 'No templates to display'}
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2 rounded-xl border border-indigo-100 bg-white/80 px-3 py-1.5 shadow-sm focus-within:border-indigo-300 focus-within:ring-1 focus-within:ring-indigo-200 dark:border-dark-500 dark:bg-dark-700/80 dark:focus-within:border-primary-500/70 dark:focus-within:ring-primary-500/40">
                  <MagnifyingGlassIcon className="h-4 w-4 text-indigo-500 dark:text-dark-200" />
                  <input
                    type="search"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Search templates..."
                    className="h-8 w-52 bg-transparent text-sm text-indigo-900 placeholder:text-indigo-300 focus:outline-none dark:text-dark-100 dark:placeholder:text-dark-300"
                  />
                </div>
                {loading && <Spinner size="sm" />}
              </div>
            </div>

            <div className="hide-scrollbar mt-4 overflow-x-auto">
              <Table.Table className="min-w-[960px] text-left rtl:text-right">
                <Table.THead>
                  <Table.TR>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[26%]`}>Template</Table.TH>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[18%]`}>Locale</Table.TH>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[26%]`}>Preview</Table.TH>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[18%]`}>Updated</Table.TH>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[12%] text-right`}>Actions</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {loading && (
                    <Table.TR className={notificationTableRowClass}>
                      <Table.TD colSpan={5} className="px-5 py-10">
                        <div className="flex items-center justify-center gap-2 text-sm text-indigo-600 dark:text-dark-200">
                          <Spinner size="sm" />
                          <span>Loading templates...</span>
                        </div>
                      </Table.TD>
                    </Table.TR>
                  )}
                  {!loading &&
                    visibleTemplates.map((tpl) => (
                      <Table.TR key={tpl.id} className={notificationTableRowClass}>
                        <Table.TD className="px-5 py-4 align-top">
                          <div className="font-medium text-gray-900 dark:text-dark-50">{tpl.name}</div>
                          <div className="text-xs text-gray-500 dark:text-dark-300">/{tpl.slug}</div>
                          {tpl.description && (
                            <div className="mt-2 text-xs text-gray-500 dark:text-dark-300">{tpl.description}</div>
                          )}
                        </Table.TD>
                        <Table.TD className="px-5 py-4 align-top">
                          <div className="flex flex-col gap-2">
                            <Badge variant="soft" color={tpl.locale ? 'info' : 'neutral'}>
                              {tpl.locale || 'default'}
                            </Badge>
                            {tpl.subject && (
                              <div className="text-xs text-gray-500 dark:text-dark-300">Subject: {tpl.subject}</div>
                            )}
                          </div>
                        </Table.TD>
                        <Table.TD className="px-5 py-4 align-top">
                          <div className="text-sm text-gray-700 dark:text-dark-100">{preview(tpl.body)}</div>
                          {tpl.variables && (
                            <div className="mt-2 text-xs text-gray-500 dark:text-dark-300">
                              Vars: {Object.keys(tpl.variables).join(', ') || 'none'}
                            </div>
                          )}
                        </Table.TD>
                        <Table.TD className="px-5 py-4 align-top">
                          <div className="text-sm text-gray-700 dark:text-dark-100">{formatDate(tpl.updated_at)}</div>
                          <div className="text-xs text-gray-500 dark:text-dark-300">Created {formatDate(tpl.created_at)}</div>
                        </Table.TD>
                        <Table.TD className="px-5 py-4 align-top text-right">
                          <div className="flex justify-end gap-2">
                            <Button size="sm" variant="ghost" onClick={() => openDrawer(tpl)}>
                              Edit
                            </Button>
                            <Button
                              size="sm"
                              variant="outlined"
                              onClick={() => remove(tpl.id)}
                              disabled={deleting === tpl.id}
                            >
                              {deleting === tpl.id ? 'Deleting...' : 'Delete'}
                            </Button>
                          </div>
                        </Table.TD>
                      </Table.TR>
                    ))}
                  {!loading && visibleTemplates.length === 0 && (
                    <Table.TR className={notificationTableRowClass}>
                      <Table.TD colSpan={5} className="px-5 py-12 text-center text-sm text-gray-500 dark:text-dark-300">
                        {emptyMessage}
                      </Table.TD>
                    </Table.TR>
                  )}
                </Table.TBody>
              </Table.Table>
            </div>

            <div className="mt-4 flex flex-col gap-3 border-t border-white/50 pt-4 sm:flex-row sm:items-center sm:justify-between dark:border-dark-600/50">
              <div className="text-xs uppercase tracking-wide text-indigo-500/80 dark:text-dark-300">
                {totalTemplates > 0 ? `Displaying ${showingFrom}-${showingTo} of ${totalTemplates} templates` : 'No records'}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2 text-sm text-indigo-600 dark:text-dark-200">
                  <span>Rows</span>
                  <Select value={String(pageSize)} onChange={(event) => setPageSize(Number(event.target.value))} className="h-9 w-24 text-xs">
                    {[10, 20, 30, 50].map((size) => (
                      <option key={size} value={size}>
                        {size}
                      </option>
                    ))}
                  </Select>
                </div>
                <Pagination page={page} total={totalPages} onChange={setPage} className="justify-end" />
              </div>
            </div>
          </div>
        </NotificationSurface>
        <Drawer
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          title={editing ? 'Edit template' : 'New template'}
          widthClass="w-full max-w-2xl"
          footer={
            <div className="flex justify-end gap-2">
              <Button variant="outlined" onClick={() => setDrawerOpen(false)} disabled={saving}>
                Cancel
              </Button>
              <Button onClick={submit} disabled={saving}>
                {saving ? 'Saving...' : 'Save template'}
              </Button>
            </div>
          }
        >
          <div className="space-y-5 p-6">
            {formError && (
              <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</div>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Identifier</label>
                {editing?.slug ? (
                  <Input value={editing.slug} readOnly />
                ) : (
                  <p className="text-sm text-gray-500">Slug will be generated automatically from the name after saving.</p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Locale</label>
                <Select
                  value={localePreset}
                  onChange={(event) => setLocalePreset(event.currentTarget.value)}
                >
                  <option value="">Default (inherit)</option>
                  {LOCALE_PRESETS.filter((item) => item).map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </Select>
                <p className="text-xs text-gray-500">Leave empty to reuse the default locale for notifications.</p>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Launch announcement" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Description</label>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} placeholder="Optional context for teammates" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Subject (optional)</label>
              <Input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="The grid is coming back online" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Message body</label>
              <Textarea value={body} onChange={(e) => setBody(e.target.value)} rows={8} placeholder="Write the default message body here" />
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Variables</label>
                  <p className="text-xs text-gray-500">Merge variables render as <code>{'{{key}}'}</code> in templates. Define defaults for each placeholder.</p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  color="neutral"
                  onClick={() => {
                    setFormError(null);
                    if (variablesMode === 'builder') {
                      const { result, error } = rowsToTemplateObject(variablesRows);
                      if (error) {
                        setFormError(`Variables: ${error}`);
                        return;
                      }
                      setVariablesJson(result ? JSON.stringify(result, null, 2) : '');
                      setVariablesMode('json');
                    } else {
                      if (!variablesJson.trim()) {
                        setVariablesRows([createTemplateRow(variablesNextId.current++)]);
                        setVariablesMode('builder');
                        return;
                      }
                      try {
                        const parsed = JSON.parse(variablesJson);
                        const [rows, nextId] = objectToTemplateRows(parsed, variablesNextId.current);
                        setVariablesRows(rows);
                        variablesNextId.current = nextId;
                        setVariablesMode('builder');
                      } catch {
                        setFormError('Variables JSON must be valid.');
                      }
                    }
                  }}
                >
                  {variablesMode === 'builder' ? 'Advanced JSON' : 'Simple builder'}
                </Button>
              </div>
              {variablesMode === 'builder' ? (
                <div className="space-y-3">
                  {variablesRows.map((row) => (
                    <div key={row.id} className="space-y-2 rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
                      <div className="grid gap-2 sm:grid-cols-3">
                        <Input
                          className="sm:col-span-2"
                          placeholder="Key (e.g. cta_url)"
                          value={row.key}
                          onChange={(event) =>
                            setVariablesRows((rows) =>
                              rows.map((item) => (item.id === row.id ? { ...item, key: event.target.value } : item)),
                            )
                          }
                        />
                        <Select
                          value={row.type}
                          onChange={(event) => {
                            const nextType = event.currentTarget.value as TemplateFieldType;
                            setVariablesRows((rows) =>
                              rows.map((item) =>
                                item.id === row.id
                                  ? {
                                      ...item,
                                      type: nextType,
                                      value:
                                        nextType === 'boolean'
                                          ? (item.value === 'true' ? 'true' : 'false')
                                          : item.value,
                                    }
                                  : item,
                              ),
                            );
                          }}
                        >
                          {TEMPLATE_FIELD_TYPES.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </Select>
                      </div>
                      {row.type === 'boolean' ? (
                        <div className="flex items-center gap-3">
                          <Switch
                            checked={row.value === 'true'}
                            onChange={(event) =>
                              setVariablesRows((rows) =>
                                rows.map((item) =>
                                  item.id === row.id
                                    ? { ...item, value: event.target.checked ? 'true' : 'false' }
                                    : item,
                                ),
                              )
                            }
                            label={row.value === 'true' ? 'True' : 'False'}
                          />
                        </div>
                      ) : row.type === 'text' || row.type === 'json' ? (
                        <Textarea
                          rows={row.type === 'json' ? 4 : 3}
                          placeholder={row.type === 'json' ? 'JSON snippet' : 'Value'}
                          value={row.value}
                          onChange={(event) =>
                            setVariablesRows((rows) =>
                              rows.map((item) => (item.id === row.id ? { ...item, value: event.target.value } : item)),
                            )
                          }
                        />
                      ) : (
                        <Input
                          placeholder="Value"
                          value={row.value}
                          onChange={(event) =>
                            setVariablesRows((rows) =>
                              rows.map((item) => (item.id === row.id ? { ...item, value: event.target.value } : item)),
                            )
                          }
                        />
                      )}
                      <div className="flex justify-end">
                        <Button
                          type="button"
                          variant="ghost"
                          color="neutral"
                          disabled={variablesRows.length === 1}
                          onClick={() =>
                            setVariablesRows((rows) =>
                              rows.length === 1
                                ? [createTemplateRow(variablesNextId.current++)]
                                : rows.filter((item) => item.id !== row.id),
                            )
                          }
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                  <div className="flex justify-end">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() =>
                        setVariablesRows((rows) => [
                          ...rows,
                          createTemplateRow(variablesNextId.current++),
                        ])
                      }
                    >
                      Add variable
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <Textarea
                    value={variablesJson}
                    onChange={(event) => setVariablesJson(event.target.value)}
                    rows={5}
                    placeholder='{"cta_url": "/download"}'
                  />
                  <p className="text-xs text-gray-500">Provide a JSON object mapping variable names to default values.</p>
                </div>
              )}
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Meta attributes</label>
                  <p className="text-xs text-gray-500">Extra metadata travels with each delivery (e.g. <code>{'{ "priority": "high" }'}</code> or experiment flags).</p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  color="neutral"
                  onClick={() => {
                    setFormError(null);
                    if (metaMode === 'builder') {
                      const { result, error } = rowsToTemplateObject(metaRows);
                      if (error) {
                        setFormError(`Meta: ${error}`);
                        return;
                      }
                      setMetaJson(result ? JSON.stringify(result, null, 2) : '');
                      setMetaMode('json');
                    } else {
                      if (!metaJson.trim()) {
                        setMetaRows([createTemplateRow(metaNextId.current++)]);
                        setMetaMode('builder');
                        return;
                      }
                      try {
                        const parsed = JSON.parse(metaJson);
                        const [rows, nextId] = objectToTemplateRows(parsed, metaNextId.current);
                        setMetaRows(rows);
                        metaNextId.current = nextId;
                        setMetaMode('builder');
                      } catch {
                        setFormError('Meta JSON must be valid.');
                      }
                    }
                  }}
                >
                  {metaMode === 'builder' ? 'Advanced JSON' : 'Simple builder'}
                </Button>
              </div>
              {metaMode === 'builder' ? (
                <div className="space-y-3">
                  {metaRows.map((row) => (
                    <div key={row.id} className="space-y-2 rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
                      <div className="grid gap-2 sm:grid-cols-3">
                        <Input
                          className="sm:col-span-2"
                          placeholder="Key"
                          value={row.key}
                          onChange={(event) =>
                            setMetaRows((rows) =>
                              rows.map((item) => (item.id === row.id ? { ...item, key: event.target.value } : item)),
                            )
                          }
                        />
                        <Select
                          value={row.type}
                          onChange={(event) => {
                            const nextType = event.currentTarget.value as TemplateFieldType;
                            setMetaRows((rows) =>
                              rows.map((item) =>
                                item.id === row.id
                                  ? {
                                      ...item,
                                      type: nextType,
                                      value:
                                        nextType === 'boolean'
                                          ? (item.value === 'true' ? 'true' : 'false')
                                          : item.value,
                                    }
                                  : item,
                              ),
                            );
                          }}
                        >
                          {TEMPLATE_FIELD_TYPES.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </Select>
                      </div>
                      {row.type === 'boolean' ? (
                        <div className="flex items-center gap-3">
                          <Switch
                            checked={row.value === 'true'}
                            onChange={(event) =>
                              setMetaRows((rows) =>
                                rows.map((item) =>
                                  item.id === row.id
                                    ? { ...item, value: event.target.checked ? 'true' : 'false' }
                                    : item,
                                ),
                              )
                            }
                            label={row.value === 'true' ? 'True' : 'False'}
                          />
                        </div>
                      ) : row.type === 'text' || row.type === 'json' ? (
                        <Textarea
                          rows={row.type === 'json' ? 4 : 3}
                          placeholder={row.type === 'json' ? 'JSON snippet' : 'Value'}
                          value={row.value}
                          onChange={(event) =>
                            setMetaRows((rows) =>
                              rows.map((item) => (item.id === row.id ? { ...item, value: event.target.value } : item)),
                            )
                          }
                        />
                      ) : (
                        <Input
                          placeholder="Value"
                          value={row.value}
                          onChange={(event) =>
                            setMetaRows((rows) =>
                              rows.map((item) => (item.id === row.id ? { ...item, value: event.target.value } : item)),
                            )
                          }
                        />
                      )}
                      <div className="flex justify-end">
                        <Button
                          type="button"
                          variant="ghost"
                          color="neutral"
                          disabled={metaRows.length === 1}
                          onClick={() =>
                            setMetaRows((rows) =>
                              rows.length === 1
                                ? [createTemplateRow(metaNextId.current++)]
                                : rows.filter((item) => item.id !== row.id),
                            )
                          }
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                  <div className="flex justify-end">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() =>
                        setMetaRows((rows) => [
                          ...rows,
                          createTemplateRow(metaNextId.current++),
                        ])
                      }
                    >
                      Add attribute
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <Textarea
                    value={metaJson}
                    onChange={(event) => setMetaJson(event.target.value)}
                    rows={5}
                    placeholder='{"priority": "high"}'
                  />
                  <p className="text-xs text-gray-500">Provide a JSON object with extra metadata for downstream services.</p>
                </div>
              )}
            </div>
          </div>
        </Drawer>
      </div>
    </ContentLayout>
  );
}





























