import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { listFlags, updateFlag } from '../api/flags';
import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import KpiCard from '../components/KpiCard';
import { AdminService, type DraftIssueOut, type FeatureFlagOut } from '../openapi';
import { getIconComponent } from '../icons/registry';

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      className={`inline-flex items-center rounded px-2 py-1 ${checked ? 'bg-green-600 text-white' : 'bg-gray-200 dark:bg-gray-800'}`}
      onClick={() => onChange(!checked)}
      aria-pressed={checked}
    >
      {checked ? 'On' : 'Off'}
    </button>
  );
}

export default function Dashboard() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: async () => (await api.get('/admin/dashboard')).data,
  });
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  interface QueueItem {
    id: string;
    type: string;
    reason: string;
    status: string;
  }

  const { data: queue } = useQuery<QueueItem[]>({
    queryKey: ['admin', 'moderation', 'queue', typeFilter, statusFilter],
    queryFn: async () =>
      (
        await api.get('/admin/moderation/queue', {
          params: { type: typeFilter || undefined, status: statusFilter || undefined },
        })
      ).data,
  });

  const { data: draftIssues = [] } = useQuery<DraftIssueOut[]>({
    queryKey: ['admin', 'drafts', 'issues'],
    queryFn: () => AdminService.listDraftIssuesAdminDraftsIssuesGet(),
  });

  const { data: flags = [], isLoading: flagsLoading } = useQuery<FeatureFlagOut[]>({
    queryKey: ['admin', 'flags'],
    queryFn: () => listFlags(),
  });

  async function onFlagToggle(f: FeatureFlagOut, v: boolean) {
    await updateFlag(f.key, { value: v });
    queryClient.invalidateQueries({ queryKey: ['admin', 'flags'] });
  }

  async function approve(id: string) {
    await api.post(`/admin/moderation/queue/${id}/approve`);
    queryClient.invalidateQueries({ queryKey: ['admin', 'moderation', 'queue'] });
  }

  async function reject(id: string) {
    await api.post(`/admin/moderation/queue/${id}/reject`);
    queryClient.invalidateQueries({ queryKey: ['admin', 'moderation', 'queue'] });
  }

  async function details(id: string) {
    const res = await api.get(`/admin/moderation/queue/${id}`);
    alert(JSON.stringify(res.data, null, 2));
  }

  const kpi = data?.kpi || {};
  const subsChange = kpi.active_subscriptions_change_pct ?? 0;
  const subsChangeColor = subsChange >= 0 ? 'text-green-600' : 'text-red-600';
  const DashboardIcon = getIconComponent('home');
  const FlagIcon = getIconComponent('flag');
  const FileIcon = getIconComponent('file');
  const UsersIcon = getIconComponent('users');

  const statusColors: Record<string, string> = {
    approved: 'text-green-600',
    pending: 'text-yellow-600',
    rejected: 'text-red-600',
  };

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="flex items-center text-2xl font-bold">
          <DashboardIcon className="mr-2 h-6 w-6" />
          Dashboard
        </h1>
        <div className="flex gap-2 text-sm">
          <Link
            to="/ops/health"
            className="rounded bg-green-100 px-2 py-1 text-green-800 dark:bg-green-900 dark:text-green-100"
          >
            System OK
          </Link>
          <Link
            to="/ops/monitoring"
            className="rounded bg-yellow-100 px-2 py-1 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100"
          >
            Global
          </Link>
          <Link
            to="/users?status=active"
            className="rounded bg-red-100 px-2 py-1 text-red-800 dark:bg-red-900 dark:text-red-100"
          >
            active
          </Link>
        </div>
      </header>

      {isLoading && <div className="text-sm text-gray-500">Loading…</div>}
      {!isLoading && (
        <div className="grid gap-4 md:grid-cols-5">
          <Link to="/users" className="block">
            <KpiCard
              title="Active users (24h)"
              value={kpi.active_users_24h ?? 0}
              className="dashboard-card"
            />
          </Link>
          <Link to="/users" className="block">
            <KpiCard
              title="New registrations (24h)"
              value={kpi.new_registrations_24h ?? 0}
              className="dashboard-card"
            />
          </Link>
          <Link to="/users?premium=1" className="block">
            <KpiCard
              title="Active premium"
              value={kpi.active_premium ?? 0}
              className="dashboard-card"
            />
          </Link>
          <Link to="/payments/transactions" className="block">
            <KpiCard
              title="Active subscriptions"
              value={
                <>
                  {kpi.active_subscriptions ?? 0}
                  <span className={`ml-1 text-sm ${subsChangeColor}`}>
                    {subsChange >= 0 ? '+' : ''}
                    {subsChange.toFixed(1)}%
                  </span>
                </>
              }
              className="dashboard-card"
            />
          </Link>
          <Link to="/nodes" className="block">
            <KpiCard
              title="Nodes (7d)"
              value={kpi.nodes_7d ?? 0}
              className="dashboard-card"
            />
          </Link>
          <Link to="/nodes" className="block">
            <KpiCard
              title="Nodes w/o transitions"
              value={`${(kpi.nodes_without_outgoing_pct ?? 0).toFixed(1)}%`}
              className="dashboard-card"
            />
          </Link>
          <Link to="/quests" className="block">
            <KpiCard
              title="Quests (24h)"
              value={kpi.quests_24h ?? 0}
              className="dashboard-card"
            />
          </Link>
          <Link to="/ops/alerts" className="block">
            <KpiCard
              title="Incidents (24h)"
              value={
                <span className={kpi.incidents_24h ? 'text-red-600' : ''}>
                  {kpi.incidents_24h ?? 0}
                </span>
              }
              className="dashboard-card"
            />
          </Link>
        </div>
      )}

      <section>
        <h2 className="mb-2 flex items-center text-xl font-bold">
          <FlagIcon className="mr-2 h-5 w-5" /> Feature Flags
        </h2>
        {flagsLoading && (
          <div className="text-sm text-gray-500">Loading...</div>
        )}
        {!flagsLoading && (
          <table className="min-w-full text-sm">
            <thead className="text-left text-gray-500">
              <tr>
                <th className="p-1">Key</th>
                <th className="p-1">Enabled</th>
              </tr>
            </thead>
            <tbody>
              {flags.map((f) => (
                <tr key={f.key} className="border-t">
                  <td className="p-1">{f.key}</td>
                  <td className="p-1">
                    {user?.role === 'admin' ? (
                      <Toggle
                        checked={!!f.value}
                        onChange={(v) => onFlagToggle(f, v)}
                      />
                    ) : f.value ? (
                      'On'
                    ) : (
                      'Off'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2 className="mb-2 flex items-center text-xl font-bold">
          <FileIcon className="mr-2 h-5 w-5" /> Drafts with issues
        </h2>
        <ul className="mb-2 list-disc pl-5 text-sm">
          {draftIssues.map((d) => (
            <li key={d.id}>{d.title || d.slug}</li>
          ))}
        </ul>
        <a
          href="/content/all?status=draft"
          className="text-sm text-blue-600 hover:underline"
        >
          See all drafts
        </a>
      </section>

      <section>
        <h2 className="mb-2 flex items-center text-xl font-bold">
          <UsersIcon className="mr-2 h-5 w-5" /> Moderation queue
        </h2>
        <div className="mb-2 flex gap-2 text-sm">
          <select
            className="rounded border px-2 py-1"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">All types</option>
            <option value="user">user</option>
            <option value="content">content</option>
          </select>
          <select
            className="rounded border px-2 py-1"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            <option value="pending">pending</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
          </select>
        </div>
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left">
              <th className="p-1">ID</th>
              <th className="p-1">Type</th>
              <th className="p-1">Reason</th>
              <th className="p-1">Status</th>
              <th className="p-1">Actions</th>
            </tr>
          </thead>
          <tbody>
            {queue?.map((item: QueueItem) => (
              <tr key={item.id} className="border-t">
                <td className="p-1 align-top">{item.id}</td>
                <td className="p-1 align-top">{item.type}</td>
                <td className="p-1 align-top">{item.reason}</td>
                <td className={`p-1 align-top ${statusColors[item.status] ?? ''}`}>
                  <Link
                    to={`/moderation?status=${item.status}`}
                    className="hover:underline"
                  >
                    {item.status}
                  </Link>
                </td>
                <td className="p-1 align-top space-x-1">
                  <button
                    className="text-green-600 hover:underline"
                    onClick={() => approve(item.id)}
                  >
                    Approve
                  </button>
                  <button className="text-red-600 hover:underline" onClick={() => reject(item.id)}>
                    Reject
                  </button>
                  <button
                    className="text-blue-600 hover:underline"
                    onClick={() => details(item.id)}
                  >
                    Подробнее
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
