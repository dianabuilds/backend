import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { type AlertItem, getAlerts, resolveAlert } from '../api/alerts';

export default function Alerts() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery<AlertItem[]>({
    queryKey: ['alerts'],
    queryFn: getAlerts,
    refetchInterval: 15000,
  });

  const resolveMut = useMutation({
    mutationFn: (id: string) => resolveAlert(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  });

  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const types = useMemo(
    () => Array.from(new Set((data || []).map((a) => a.type).filter(Boolean))),
    [data],
  );
  const severities = useMemo(
    () => Array.from(new Set((data || []).map((a) => a.severity).filter(Boolean))),
    [data],
  );

  const filtered = useMemo(
    () =>
      (data || []).filter((a) => {
        if (typeFilter && a.type !== typeFilter) return false;
        if (severityFilter && a.severity !== severityFilter) return false;
        if (statusFilter && a.status !== statusFilter) return false;
        if (search && !a.description.toLowerCase().includes(search.toLowerCase())) return false;
        return true;
      }),
    [data, typeFilter, severityFilter, statusFilter, search],
  );

  const rowClass = (level?: string) => {
    switch (level) {
      case 'critical':
      case 'high':
        return 'bg-red-50';
      case 'warning':
      case 'medium':
        return 'bg-yellow-50';
      case 'info':
      case 'low':
        return 'bg-blue-50';
      default:
        return '';
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Alerts</h1>
      {isLoading && <div className="text-sm text-gray-500">Loading...</div>}
      {error && <div className="text-sm text-red-600">Failed to load alerts</div>}
      {resolveMut.isError && (
        <div className="text-sm text-red-600">
          {(resolveMut.error as Error)?.message || 'Failed to resolve alert'}
        </div>
      )}
      {resolveMut.isSuccess && <div className="text-sm text-green-600">Alert marked resolved</div>}
      <div className="flex flex-wrap gap-2 text-sm">
        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border p-1"
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="border p-1"
        >
          <option value="">All types</option>
          {types.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="border p-1"
        >
          <option value="">All levels</option>
          {severities.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border p-1"
        >
          <option value="">All states</option>
          <option value="active">Active</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>
      <ul className="space-y-3">
        {filtered.map((a) => (
          <li key={a.id} className={`border-b p-2 ${rowClass(a.severity)}`}>
            {a.startsAt && (
              <div className="text-xs text-gray-500">{new Date(a.startsAt).toLocaleString()}</div>
            )}
            <div className="flex items-center justify-between">
              <span>{a.description}</span>
              <div className="flex gap-2 text-xs">
                {a.status !== 'resolved' && (
                  <button
                    onClick={() => a.id && resolveMut.mutate(a.id)}
                    disabled={resolveMut.isPending}
                    className="text-green-600 hover:underline disabled:opacity-50"
                  >
                    Mark resolved
                  </button>
                )}
                {a.url && (
                  <a
                    href={a.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    Source
                  </a>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
