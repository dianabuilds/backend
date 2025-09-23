import React from 'react';
import { Link } from 'react-router-dom';
import { Badge, Button, Card, Drawer, Input, Select, Spinner, Switch, Table, Textarea } from '@ui';
import { ContentLayout } from '../content/ContentLayout';
import { apiDelete, apiGet, apiPost } from '../../shared/api/client';
import { useAuth } from '../../shared/auth/AuthContext';

export type Campaign = {
  id: string;
  template_id?: string | null;
  title: string;
  message: string;
  type: string;
  filters?: Record<string, any> | null;
  status: string;
  total: number;
  sent: number;
  failed: number;
  created_by: string;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
};

type TemplateSummary = {
  id: string;
  slug: string;
  name: string;
  subject?: string | null;
  body: string;
  variables?: Record<string, unknown> | null;
};

const statusTheme: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  scheduled: 'bg-indigo-50 text-indigo-700',
  ready: 'bg-sky-50 text-sky-700',
  active: 'bg-emerald-50 text-emerald-700',
  finished: 'bg-emerald-50 text-emerald-700',
  failed: 'bg-rose-50 text-rose-700',
};

const typeLabels: Record<string, string> = {
  platform: 'Platform',
  maintenance: 'Maintenance',
  release: 'Launch',
  marketing: 'Marketing',
};

function formatDate(value?: string | null) {
  if (!value) return '-';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString();
}

function preview(text: string, max = 80) {
  const clean = text.replace(/\s+/g, ' ').trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, Math.max(0, max - 3))}...`;
}

export default function CampaignsPage() {
  const { user } = useAuth();
  const [campaigns, setCampaigns] = React.useState<Campaign[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [title, setTitle] = React.useState('');
  const [message, setMessage] = React.useState('');
  const [type, setType] = React.useState<keyof typeof typeLabels>('platform');
  const [status, setStatus] = React.useState('draft');
  const [filtersPayload, setFiltersPayload] = React.useState('');
  const [startNow, setStartNow] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [deleting, setDeleting] = React.useState<string | null>(null);
  const [templates, setTemplates] = React.useState<TemplateSummary[]>([]);
  const [templatesLoading, setTemplatesLoading] = React.useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = React.useState('');

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiGet<{ items?: Campaign[] }>('/v1/notifications/admin/campaigns');
      setCampaigns(Array.isArray(res?.items) ? res.items : []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load notifications');
      setCampaigns([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadTemplates = React.useCallback(async () => {
    setTemplatesLoading(true);
    try {
      const res = await apiGet<{ items?: TemplateSummary[] }>('/v1/notifications/admin/templates');
      setTemplates(Array.isArray(res?.items) ? res.items : []);
    } catch {
      // templates optional
    } finally {
      setTemplatesLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
    void loadTemplates();
  }, [refresh, loadTemplates]);

  const templateMap = React.useMemo(() => new Map(templates.map((tpl) => [tpl.id, tpl])), [templates]);

  const openDrawer = () => {
    setTitle('');
    setMessage('');
    setType('platform');
    setStatus('draft');
    setFiltersPayload('');
    setStartNow(false);
    setSelectedTemplateId('');
    setFormError(null);
    setDrawerOpen(true);
  };

  const applyTemplate = (templateId: string) => {
    setSelectedTemplateId(templateId);
    if (!templateId) return;
    const template = templateMap.get(templateId);
    if (!template) return;
    setTitle((prev) => (prev.trim().length ? prev : template.name));
    setMessage(template.body);
  };

  const submit = async () => {
    setFormError(null);
    if (!title.trim() || !message.trim()) {
      setFormError('Title and message are required');
      return;
    }
    if (!user?.id) {
      setFormError('Current user id is missing; please re-login');
      return;
    }
    let filters: Record<string, any> | undefined;
    if (filtersPayload.trim()) {
      try {
        filters = JSON.parse(filtersPayload);
      } catch {
        setFormError('Audience filters must be valid JSON');
        return;
      }
    }
    const payload: any = {
      title: title.trim(),
      message: message.trim(),
      type,
      status,
      created_by: user.id,
    };
    if (filters !== undefined) payload.filters = filters;
    if (selectedTemplateId) payload.template_id = selectedTemplateId;
    if (startNow) {
      payload.started_at = new Date().toISOString();
      if (!payload.status || payload.status === 'draft') payload.status = 'scheduled';
    }
    setSaving(true);
    try {
      await apiPost('/v1/notifications/admin/campaigns', payload);
      setDrawerOpen(false);
      await refresh();
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save notification');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id: string) => {
    if (!window.confirm('Delete this notification campaign?')) return;
    setDeleting(id);
    try {
      await apiDelete(`/v1/notifications/admin/campaigns/${id}`);
      await refresh();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete notification');
    } finally {
      setDeleting(null);
    }
  };

  const totals = React.useMemo(() => {
    const count = campaigns.length;
    const active = campaigns.filter((c) => c.status === 'active').length;
    const draft = campaigns.filter((c) => c.status === 'draft').length;
    return { count, active, draft };
  }, [campaigns]);

  return (
    <ContentLayout context="notifications" title="Campaigns">
      <div className="space-y-6">
        <Card>
          <div className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">Notifications</div>
              <h1 className="text-2xl font-semibold text-gray-900">Broadcast center</h1>
              <p className="max-w-2xl text-sm text-gray-600">
                Publish global announcements or maintenance alerts that surface across the platform. Campaigns live inside the notifications domain so internal services can reuse and automate them later.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button as={Link as any} to="/notifications/templates" variant="outlined">
                Manage templates
              </Button>
              <Button onClick={openDrawer} disabled={!user?.id}>New notification</Button>
            </div>
          </div>
          <div className="grid gap-4 border-t border-gray-100 p-6 text-sm text-gray-600 sm:grid-cols-3">
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-400">Campaigns</div>
              <div className="text-xl font-semibold text-gray-900">{totals.count}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-400">Active</div>
              <div className="text-xl font-semibold text-emerald-600">{totals.active}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-400">Drafts</div>
              <div className="text-xl font-semibold text-indigo-600">{totals.draft}</div>
            </div>
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
                  <Table.TH className="w-[28%]">Title</Table.TH>
                  <Table.TH className="w-[18%]">Status</Table.TH>
                  <Table.TH className="w-[18%]">Audience</Table.TH>
                  <Table.TH className="w-[18%]">Metrics</Table.TH>
                  <Table.TH className="w-[18%]">Created</Table.TH>
                  <Table.TH className="w-[120px] text-right">Actions</Table.TH>
                </Table.TR>
              </Table.THead>
              <Table.TBody>
                {loading && (
                  <Table.TR>
                    <Table.TD colSpan={6}>
                      <div className="flex items-center justify-center gap-2 py-6 text-sm text-gray-500">
                        <Spinner size="sm" />
                        <span>Loading notifications...</span>
                      </div>
                    </Table.TD>
                  </Table.TR>
                )}
                {!loading && campaigns.map((c) => {
                  const statusCls = statusTheme[c.status] || 'bg-gray-100 text-gray-600';
                  const typeLabel = typeLabels[c.type] || c.type;
                  const audience = c.filters && Object.keys(c.filters).length ? 'Segmented' : 'All users';
                  const templateUsed = c.template_id ? templateMap.get(c.template_id) : null;
                  return (
                    <Table.TR key={c.id}>
                      <Table.TD>
                        <div className="font-medium text-gray-900">{c.title}</div>
                        <div className="mt-1 text-xs text-gray-500">{preview(c.message)}</div>
                      </Table.TD>
                      <Table.TD>
                        <div className="flex flex-col gap-2">
                          <span className={`inline-flex w-fit items-center rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${statusCls}`}>
                            {c.status}
                          </span>
                          <Badge color="info" variant="soft">{typeLabel}</Badge>
                          {templateUsed && (
                            <Badge color="neutral" variant="ghost">Template: {templateUsed.slug}</Badge>
                          )}
                        </div>
                      </Table.TD>
                      <Table.TD>
                        <div className="text-sm text-gray-700">{audience}</div>
                        {c.filters && Object.keys(c.filters).length ? (
                          <pre className="mt-1 max-h-24 overflow-auto rounded bg-gray-50 p-2 text-[11px] text-gray-500">{JSON.stringify(c.filters, null, 2)}</pre>
                        ) : null}
                      </Table.TD>
                      <Table.TD>
                        <div className="text-sm font-medium text-gray-900">{c.sent}/{c.total}</div>
                        <div className="text-xs text-gray-500">Failed: {c.failed}</div>
                      </Table.TD>
                      <Table.TD>
                        <div className="text-sm text-gray-700">{formatDate(c.created_at)}</div>
                        <div className="text-xs text-gray-500">Start: {formatDate(c.started_at)}</div>
                      </Table.TD>
                      <Table.TD className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outlined"
                            onClick={() => remove(c.id)}
                            disabled={deleting === c.id}
                          >
                            {deleting === c.id ? 'Deleting...' : 'Delete'}
                          </Button>
                        </div>
                      </Table.TD>
                    </Table.TR>
                  );
                })}
                {!loading && campaigns.length === 0 && (
                  <Table.TR>
                    <Table.TD colSpan={6} className="py-10 text-center text-sm text-gray-500">
                      No notifications yet.
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
          title="New notification"
          widthClass="w-full max-w-2xl"
          footer={
            <div className="flex justify-end gap-2">
              <Button variant="outlined" onClick={() => setDrawerOpen(false)} disabled={saving}>
                Cancel
              </Button>
              <Button onClick={submit} disabled={saving}>
                {saving ? 'Saving...' : 'Save notification'}
              </Button>
            </div>
          }
        >
          <div className="space-y-6 p-6">
            {formError && (
              <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</div>
            )}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Template</label>
              <Select value={selectedTemplateId} onChange={(e: any) => applyTemplate(e.target.value)} disabled={templatesLoading || templates.length === 0}>
                <option value="">No template</option>
                {templates.map((tpl) => (
                  <option key={tpl.id} value={tpl.id}>
                    {tpl.name} ({tpl.slug})
                  </option>
                ))}
              </Select>
              {templatesLoading && <div className="text-xs text-gray-500">Loading templates...</div>}
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Title</label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Maintenance window" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Message</label>
              <Textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={5} placeholder="What should people see?" />
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Category</label>
                <Select value={type} onChange={(e: any) => setType(e.target.value)}>
                  {Object.entries(typeLabels).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Status</label>
                <Select value={status} onChange={(e: any) => setStatus(e.target.value)}>
                  <option value="draft">Draft</option>
                  <option value="scheduled">Scheduled</option>
                  <option value="ready">Ready</option>
                  <option value="active">Active</option>
                </Select>
              </div>
              <div className="flex items-end">
                <Switch checked={startNow} onChange={(e) => setStartNow(e.target.checked)} label="Start immediately" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Audience filters (JSON)</label>
              <Textarea
                value={filtersPayload}
                onChange={(e) => setFiltersPayload(e.target.value)}
                placeholder='{"role":"creator"}'
                rows={4}
              />
              <p className="text-xs text-gray-500">Leave empty to reach every user. Provide JSON to target a segment (keys depend on downstream services).</p>
            </div>
          </div>
        </Drawer>
      </div>
    </ContentLayout>
  );
}






