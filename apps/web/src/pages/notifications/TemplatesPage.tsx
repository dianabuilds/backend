import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { Badge, Button, Card, Drawer, Input, Spinner, Table, Textarea } from '@ui';
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

export default function TemplatesPage() {
  const { user } = useAuth();
  const [templates, setTemplates] = React.useState<NotificationTemplate[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<NotificationTemplate | null>(null);
  const [slug, setSlug] = React.useState('');
  const [name, setName] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [subject, setSubject] = React.useState('');
  const [body, setBody] = React.useState('');
  const [locale, setLocale] = React.useState('');
  const [variablesPayload, setVariablesPayload] = React.useState('');
  const [metaPayload, setMetaPayload] = React.useState('');
  const [formError, setFormError] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [deleting, setDeleting] = React.useState<string | null>(null);

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
    setSlug(template?.slug ?? '');
    setName(template?.name ?? '');
    setDescription(template?.description ?? '');
    setSubject(template?.subject ?? '');
    setBody(template?.body ?? '');
    setLocale(template?.locale ?? '');
    setVariablesPayload(template?.variables ? JSON.stringify(template.variables, null, 2) : '');
    setMetaPayload(template?.meta ? JSON.stringify(template.meta, null, 2) : '');
    setFormError(null);
    setDrawerOpen(true);
  };

  const submit = async () => {
    setFormError(null);
    if (!slug.trim() || !name.trim() || !body.trim()) {
      setFormError('Slug, name, and body are required');
      return;
    }
    const payload: Record<string, any> = {
      id: editing?.id,
      slug: slug.trim(),
      name: name.trim(),
      body,
      description: description.trim() ? description.trim() : null,
      subject: subject.trim() ? subject.trim() : null,
      locale: locale.trim() ? locale.trim() : null,
      created_by: editing?.created_by ?? user?.id ?? null,
    };
    if (variablesPayload.trim()) {
      try {
        payload.variables = JSON.parse(variablesPayload);
      } catch {
        setFormError('Variables must be valid JSON');
        return;
      }
    } else {
      payload.variables = null;
    }
    if (metaPayload.trim()) {
      try {
        payload.meta = JSON.parse(metaPayload);
      } catch {
        setFormError('Meta must be valid JSON');
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
    <ContentLayout context="notifications" title="Notification templates" description="Coordinate announcements, automate campaigns, and keep every player cohort informed.">
      <div className="space-y-6">
        <Card>
          <div className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">Notifications</div>
              <h1 className="text-2xl font-semibold text-gray-900">Template library</h1>
              <p className="max-w-2xl text-sm text-gray-600">
                Reuse blueprints for campaigns, set localized subjects, and manage merge variables without touching code.
              </p>
            </div>
            <Button onClick={() => openDrawer(null)}>New template</Button>
          </div>
        </Card>

        {error && (
          <div className="rounded border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
        )}

        <Card className="overflow-hidden">
          <div className="p-4">
            <Table.Table>
              <Table.THead>
                <Table.TR>
                  <Table.TH className="w-[26%]">Template</Table.TH>
                  <Table.TH className="w-[18%]">Locale</Table.TH>
                  <Table.TH className="w-[26%]">Preview</Table.TH>
                  <Table.TH className="w-[18%]">Updated</Table.TH>
                  <Table.TH className="w-[12%] text-right">Actions</Table.TH>
                </Table.TR>
              </Table.THead>
              <Table.TBody>
                {loading && (
                  <Table.TR>
                    <Table.TD colSpan={5}>
                      <div className="flex items-center justify-center gap-2 py-6 text-sm text-gray-500">
                        <Spinner size="sm" />
                        <span>Loading templates...</span>
                      </div>
                    </Table.TD>
                  </Table.TR>
                )}
                {!loading && templates.map((tpl) => (
                  <Table.TR key={tpl.id}>
                    <Table.TD>
                      <div className="font-medium text-gray-900">{tpl.name}</div>
                      <div className="text-xs text-gray-500">/{tpl.slug}</div>
                      {tpl.description && (
                        <div className="mt-1 text-xs text-gray-500">{tpl.description}</div>
                      )}
                    </Table.TD>
                    <Table.TD>
                      <div className="flex flex-col gap-2">
                        <Badge variant="soft" color={tpl.locale ? 'info' : 'neutral'}>
                          {tpl.locale || 'default'}
                        </Badge>
                        {tpl.subject && (
                          <div className="text-xs text-gray-500">Subject: {tpl.subject}</div>
                        )}
                      </div>
                    </Table.TD>
                    <Table.TD>
                      <div className="text-sm text-gray-700">{preview(tpl.body)}</div>
                      {tpl.variables && (
                        <div className="mt-1 text-xs text-gray-500">
                          Vars: {Object.keys(tpl.variables).join(', ') || '�'}
                        </div>
                      )}
                    </Table.TD>
                    <Table.TD>
                      <div className="text-sm text-gray-700">{formatDate(tpl.updated_at)}</div>
                      <div className="text-xs text-gray-500">Created {formatDate(tpl.created_at)}</div>
                    </Table.TD>
                    <Table.TD className="text-right">
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
                {!loading && templates.length === 0 && (
                  <Table.TR>
                    <Table.TD colSpan={5} className="py-10 text-center text-sm text-gray-500">
                      No templates yet.
                    </Table.TD>
                  </Table.TR>
                )}
              </Table.TBody>
            </Table.Table>
          </div>
        </Card>

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
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Slug</label>
                <Input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="update-1-3" />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Locale</label>
                <Input value={locale} onChange={(e) => setLocale(e.target.value)} placeholder="en-US" />
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
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Variables (JSON)</label>
              <Textarea value={variablesPayload} onChange={(e) => setVariablesPayload(e.target.value)} rows={4} placeholder='{"cta":"/download"}' />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Meta (JSON)</label>
              <Textarea value={metaPayload} onChange={(e) => setMetaPayload(e.target.value)} rows={3} placeholder='{"priority": "high"}' />
            </div>
          </div>
        </Drawer>
      </div>
    </ContentLayout>
  );
}



