import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import React from 'react';
import { Badge, Button, Drawer, Input, TablePagination, Select, Spinner, Switch, Table, Textarea } from '@ui';
import { NotificationSurface, notificationTableHeadCellClass, notificationTableRowClass } from '../../common/NotificationSurface';
import { useNotificationTemplates } from '../hooks';
import { useAuth } from '@shared/auth';
import type { NotificationTemplate, NotificationTemplatePayload } from '@shared/types/notifications';
import { formatDateTime } from '@shared/utils/format';
import {
  LOCALE_PRESETS,
  TEMPLATE_FIELD_TYPES,
  TemplateFieldRow,
  TemplateFieldType,
  createTemplateRow,
  objectToTemplateRows,
  rowsToTemplateObject,
} from '../utils';

const PAGE_SIZE_OPTIONS = [10, 20, 30, 50];

function preview(text: string, max = 90) {
  const clean = text.replace(/\s+/g, ' ').trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, Math.max(0, max - 3))}...`;
}

function formatDate(value?: string | null) {
  return formatDateTime(value ?? undefined, { withSeconds: true, fallback: '-' }) || '-';
}

type TemplateDrawerState = {
  open: boolean;
  editing: NotificationTemplate | null;
};

export function NotificationTemplates(): React.ReactElement {
  const { user } = useAuth();
  const {
    templates,
    loading,
    saving,
    deletingId,
    error,
    refresh,
    saveTemplate: persistTemplate,
    deleteTemplate: removeTemplate,
    clearError,
  } = useNotificationTemplates();

  const [drawer, setDrawer] = React.useState<TemplateDrawerState>({ open: false, editing: null });
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
  const [searchQuery, setSearchQuery] = React.useState('');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(PAGE_SIZE_OPTIONS[0]);

  const filteredTemplates = React.useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return templates;
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

  const closeDrawer = () => setDrawer({ open: false, editing: null });

  const openDrawer = (template?: NotificationTemplate | null) => {
    const editingTemplate = template ?? null;
    clearError();
    setDrawer({ open: true, editing: editingTemplate });

    setName(editingTemplate?.name ?? '');
    setDescription(editingTemplate?.description ?? '');
    setSubject(editingTemplate?.subject ?? '');
    setBody(editingTemplate?.body ?? '');

    const localeValue = editingTemplate?.locale ?? '';
    setLocalePreset(LOCALE_PRESETS.includes(localeValue) ? localeValue : '');

    const [variableRows, nextVariableId] = objectToTemplateRows(editingTemplate?.variables ?? null, 1);
    setVariablesRows(variableRows);
    variablesNextId.current = nextVariableId;
    setVariablesMode('builder');
    setVariablesJson(editingTemplate?.variables ? JSON.stringify(editingTemplate.variables, null, 2) : '');

    const [metaRowsInitial, nextMetaId] = objectToTemplateRows(editingTemplate?.meta ?? null, 1);
    setMetaRows(metaRowsInitial);
    metaNextId.current = nextMetaId;
    setMetaMode('builder');
    setMetaJson(editingTemplate?.meta ? JSON.stringify(editingTemplate.meta, null, 2) : '');

    setFormError(null);
  };

  const switchVariablesMode = () => {
    setFormError(null);
    if (variablesMode === 'builder') {
      const { result, error } = rowsToTemplateObject(variablesRows);
      if (error) {
        setFormError(`Variables: ${error}`);
        return;
      }
      setVariablesJson(result ? JSON.stringify(result, null, 2) : '');
      setVariablesMode('json');
      return;
    }
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
  };

  const switchMetaMode = () => {
    setFormError(null);
    if (metaMode === 'builder') {
      const { result, error } = rowsToTemplateObject(metaRows);
      if (error) {
        setFormError(`Meta: ${error}`);
        return;
      }
      setMetaJson(result ? JSON.stringify(result, null, 2) : '');
      setMetaMode('json');
      return;
    }
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
  };

  const handleSubmit = async () => {
    setFormError(null);
    if (!name.trim() || !body.trim()) {
      setFormError('Name and body are required');
      return;
    }

    const payload: NotificationTemplatePayload = {
      id: drawer.editing?.id,
      name: name.trim(),
      body,
      description: description.trim() ? description.trim() : null,
      subject: subject.trim() ? subject.trim() : null,
      locale: localePreset || null,
      created_by: drawer.editing?.created_by ?? user?.id ?? null,
      variables: null,
      meta: null,
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
    }

    try {
      await persistTemplate(payload);
      closeDrawer();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save template');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this template?')) return;
    try {
      await removeTemplate(id);
    } catch {
      // error state handled by the data hook
    }
  };
  const emptyMessage = searchQuery.trim()
    ? 'No templates match your search.'
    : 'No templates yet.';

  return (
    <div className="space-y-6">
      <NotificationSurface className="space-y-6 p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">Notifications</div>
            <h1 className="text-2xl font-semibold text-gray-900">Template library</h1>
            <p className="max-w-2xl text-sm text-gray-600">
              Reuse blueprints for broadcasts, set localized subjects, and manage merge variables without touching code.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outlined" color="neutral" onClick={() => void refresh()} disabled={loading}>
              Refresh
            </Button>
            <Button onClick={() => openDrawer(null)}>New template</Button>
          </div>
        </div>

        {error ? (
          <div className="rounded-xl border border-rose-200/70 bg-rose-50/80 px-4 py-3 text-sm text-rose-700 shadow-sm">
            {error}
          </div>
        ) : null}

        <div className="rounded-2xl border border-white/60 bg-white/40 p-4 shadow-inner backdrop-blur-sm dark:border-dark-600/60 dark:bg-dark-700/40">
          <div className="flex flex-col gap-3 border-b border-white/50 pb-4 sm:flex-row sm:items-center sm:justify-between dark:border-dark-600/50">
            <div>
              <div className="text-sm font-semibold text-indigo-900 dark:text-dark-50">Template catalog</div>
              <div className="text-xs text-indigo-600/80 dark:text-dark-200">
                {totalTemplates > 0
                  ? `Displaying ${showingFrom}-${showingTo} of ${totalTemplates} templates`
                  : 'No templates to display'}
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
              <Select value={String(pageSize)} onChange={(event) => setPageSize(Number(event.target.value))} className="h-9 w-28 text-sm">
                {PAGE_SIZE_OPTIONS.map((size) => (
                  <option key={size} value={size}>
                    {size} per page
                  </option>
                ))}
              </Select>
            </div>
          </div>

          {loading ? (
            <div className="flex min-h-[180px] items-center justify-center">
              <div className="flex items-center gap-2 text-sm text-indigo-600">
                <Spinner size="sm" /> Loading templates...
              </div>
            </div>
          ) : null}

          {!loading && visibleTemplates.length === 0 ? (
            <div className="py-12 text-center text-sm text-gray-500">{emptyMessage}</div>
          ) : null}

          {!loading && visibleTemplates.length > 0 ? (
            <div className="space-y-4 pt-4">
              <div className="hide-scrollbar overflow-x-auto">
                <Table.Table className="min-w-[960px] text-left rtl:text-right">
                  <Table.THead>
                    <Table.TR>
                      <Table.TH className={`${notificationTableHeadCellClass} w-[32%]`}>Template</Table.TH>
                      <Table.TH className={`${notificationTableHeadCellClass} w-[12%]`}>Locale</Table.TH>
                      <Table.TH className={`${notificationTableHeadCellClass} w-[18%]`}>Subject</Table.TH>
                      <Table.TH className={`${notificationTableHeadCellClass} w-[20%]`}>Created</Table.TH>
                      <Table.TH className={`${notificationTableHeadCellClass} w-[18%]`}>Actions</Table.TH>
                    </Table.TR>
                  </Table.THead>
                  <Table.TBody>
                    {visibleTemplates.map((tpl) => (
                      <Table.TR key={tpl.id} className={notificationTableRowClass}>
                        <Table.TD className="px-6 py-4">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-semibold text-gray-900 dark:text-dark-50">{tpl.name}</span>
                              <Badge color="neutral" variant="soft">
                                {tpl.slug}
                              </Badge>
                            </div>
                            <p className="text-xs text-gray-500">{preview(tpl.description ?? tpl.body)}</p>
                          </div>
                        </Table.TD>
                        <Table.TD className="px-6 py-4">
                          <Badge variant="soft" color="neutral">
                            {tpl.locale || 'default'}
                          </Badge>
                        </Table.TD>
                        <Table.TD className="px-6 py-4 text-sm text-gray-600">
                          {tpl.subject || '—'}
                        </Table.TD>
                        <Table.TD className="px-6 py-4 text-sm text-gray-600">
                          <div className="flex flex-col">
                            <span>{formatDate(tpl.created_at)}</span>
                            <span className="text-xs text-gray-400">Updated {formatDate(tpl.updated_at)}</span>
                          </div>
                        </Table.TD>
                        <Table.TD className="px-6 py-4">
                          <div className="flex flex-wrap items-center gap-2">
                            <Button size="sm" variant="ghost" color="neutral" onClick={() => openDrawer(tpl)}>
                              Edit
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              color="neutral"
                              disabled={deletingId === tpl.id}
                              onClick={() => void handleDelete(tpl.id)}
                            >
                              {deletingId === tpl.id ? 'Deleting...' : 'Delete'}
                            </Button>
                          </div>
                        </Table.TD>
                      </Table.TR>
                    ))}
                  </Table.TBody>
                </Table.Table>
              </div>

              <TablePagination
                page={page}
                pageSize={pageSize}
                currentCount={visibleTemplates.length}
                totalItems={totalTemplates}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
                pageSizeOptions={PAGE_SIZE_OPTIONS}
                className="mt-4"
              />
            </div>
          ) : null}
        </div>
      </NotificationSurface>

      <Drawer open={drawer.open} onClose={closeDrawer} widthClass="w-[720px]" title={drawer.editing ? 'Edit template' : 'New template'}>
        <div className="space-y-5 p-6">
          {formError ? (
            <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</div>
          ) : null}

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Identifier</label>
              {drawer.editing?.slug ? (
                <Input value={drawer.editing.slug} readOnly />
              ) : (
                <p className="text-sm text-gray-500">Slug will be generated automatically after saving.</p>
              )}
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Locale preset</label>
              <Select value={localePreset} onChange={(event) => setLocalePreset(event.target.value)}>
                {LOCALE_PRESETS.map((locale) => (
                  <option key={locale || 'default'} value={locale}>
                    {locale || 'Default'}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="Template name" value={name} onChange={(event) => setName(event.target.value)} required />
            <Input label="Email subject" value={subject} onChange={(event) => setSubject(event.target.value)} />
            <Textarea
              className="sm:col-span-2"
              rows={4}
              label="Description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Explain when to use this template."
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Body</label>
            <Textarea
              rows={12}
              value={body}
              onChange={(event) => setBody(event.target.value)}
              placeholder="Write the message body with merge variables like {{ name }}"
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Variables</label>
                <p className="text-xs text-gray-500">
                  Define merge fields for dynamic content. Switch to JSON for advanced payloads.
                </p>
              </div>
              <Button type="button" variant="ghost" color="neutral" onClick={switchVariablesMode}>
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
                        placeholder="Key"
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
                                        ? item.value === 'true'
                                          ? 'true'
                                          : 'false'
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
                  rows={6}
                  placeholder='{"cta_url": "https://example.com"}'
                />
                <p className="text-xs text-gray-500">Provide a JSON object with defaults for variables.</p>
              </div>
            )}
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Meta attributes</label>
                <p className="text-xs text-gray-500">
                  Extra metadata travels with each delivery (for example <code>{'{ "priority": "high" }'}</code>).
                </p>
              </div>
              <Button type="button" variant="ghost" color="neutral" onClick={switchMetaMode}>
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
                                        ? item.value === 'true'
                                          ? 'true'
                                          : 'false'
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

          <div className="flex items-center justify-between">
            <Button type="button" variant="ghost" color="neutral" onClick={closeDrawer}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={saving}>
              {saving ? 'Saving...' : 'Save template'}
            </Button>
          </div>
        </div>
      </Drawer>
    </div>
  );
}



