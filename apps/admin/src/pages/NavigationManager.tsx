import * as Tabs from '@radix-ui/react-tabs';
import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { api, ApiError } from '../api/client';
import {
  bulkUpdate,
  createTransition,
  listTransitions,
  type Transition,
  updateTransition,
} from '../api/transitions';
import LimitBadge from '../components/LimitBadge';
import { handleLimit429, refreshLimits } from '../components/LimitBadgeController';
import Tooltip from '../components/Tooltip';
import Simulation from './Simulation';

interface RunResponse {
  transitions?: unknown[];
}

export default function NavigationManager() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [tab, setTab] = useState(searchParams.get('tab') || 'manual');

  // Manual transitions state
  const [from, setFrom] = useState(() => searchParams.get('from_slug') || '');
  const [to, setTo] = useState(() => searchParams.get('to_slug') || '');
  const [label, setLabel] = useState('');
  const [weight, setWeight] = useState('');
  const [enableId, setEnableId] = useState('');
  const [disableId, setDisableId] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Transitions list state
  const [transitions, setTransitions] = useState<Transition[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [filterFrom, setFilterFrom] = useState('');
  const [filterTo, setFilterTo] = useState('');
  const [filterStatus, setFilterStatus] = useState<'any' | 'enabled' | 'disabled'>('any');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkLabel, setBulkLabel] = useState('');
  const [bulkWeight, setBulkWeight] = useState('');

  const loadTransitions = useCallback(async () => {
    setLoadingList(true);
    setListError(null);
    try {
      const rows = await listTransitions({
        from_slug: filterFrom || undefined,
        to_slug: filterTo || undefined,
        status: filterStatus,
      });
      setTransitions(rows);
    } catch (e: unknown) {
      setListError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingList(false);
    }
  }, [filterFrom, filterTo, filterStatus]);

  useEffect(() => {
    void loadTransitions();
  }, [loadTransitions]);

  // Autogeneration state
  const [nodeSlug, setNodeSlug] = useState('');
  const [userId, setUserId] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState('');

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTransition({
        from_slug: from.trim(),
        to_slug: to.trim(),
        label: label.trim() || undefined,
        weight: weight.trim() ? Number(weight.trim()) : undefined,
        priority: weight.trim() ? Number(weight.trim()) : undefined,
        disabled: false,
      });
      setMessage('Transition created');
      setFrom('');
      setTo('');
      setLabel('');
      setWeight('');
      await loadTransitions();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleEnable = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateTransition(enableId.trim(), { disabled: false });
      setMessage('Transition enabled');
      setEnableId('');
      await loadTransitions();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleDisable = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateTransition(disableId.trim(), { disabled: true });
      setMessage('Transition disabled');
      setDisableId('');
      await loadTransitions();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const run = async () => {
    setRunning(true);
    setResult('');
    try {
      const payload: Record<string, unknown> = { node_slug: nodeSlug.trim() };
      if (userId.trim()) payload.user_id = userId.trim();
      const res = await api.post<unknown, RunResponse>('/admin/navigation/run', payload);
      const count = Array.isArray(res.data?.transitions)
        ? (res.data?.transitions as unknown[]).length
        : 0;
      setResult(`Generated transitions: ${count}`);
      await refreshLimits();
    } catch (e: unknown) {
      if (e instanceof ApiError && e.status === 429) {
        const retry = Number(e.headers?.get('Retry-After') || 0);
        await handleLimit429('compass_calls', retry);
        setResult('Rate limit exceeded');
      } else {
        setResult(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setRunning(false);
    }
  };

  const handleLabelChange = (id: string, value: string) => {
    setTransitions((prev) => prev.map((t) => (t.id === id ? { ...t, label: value } : t)));
  };

  const handleWeightChange = (id: string, value: string) => {
    const num = Number(value);
    setTransitions((prev) => prev.map((t) => (t.id === id ? { ...t, weight: num } : t)));
  };

  const commitUpdate = async (id: string, patch: { label?: string | null; weight?: number }) => {
    try {
      await updateTransition(id, patch);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const toggleSelect = (id: string, checked: boolean) => {
    setSelectedIds((prev) => (checked ? [...prev, id] : prev.filter((x) => x !== id)));
  };

  const applyBulk = async () => {
    const patch: { label?: string; weight?: number } = {};
    if (bulkLabel.trim()) patch.label = bulkLabel.trim();
    if (bulkWeight.trim()) patch.weight = Number(bulkWeight.trim());
    if (selectedIds.length === 0 || Object.keys(patch).length === 0) return;
    try {
      await bulkUpdate(selectedIds, patch);
      setTransitions((prev) =>
        prev.map((t) => (selectedIds.includes(t.id) ? { ...t, ...patch } : t)),
      );
      setSelectedIds([]);
      setBulkLabel('');
      setBulkWeight('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const changeTab = (value: string) => {
    setTab(value);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('tab', value);
      return next;
    });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Navigation manager</h1>
      <Tabs.Root value={tab} onValueChange={changeTab}>
        <Tabs.List className="flex border-b mb-4 gap-4">
          <Tabs.Trigger
            value="manual"
            className="px-3 py-2 text-sm data-[state=active]:border-b-2 data-[state=active]:border-blue-500"
          >
            Manual transitions
          </Tabs.Trigger>
          <Tabs.Trigger
            value="auto"
            className="px-3 py-2 text-sm data-[state=active]:border-b-2 data-[state=active]:border-blue-500"
          >
            Autogeneration
          </Tabs.Trigger>
          <Tabs.Trigger
            value="sim"
            className="px-3 py-2 text-sm data-[state=active]:border-b-2 data-[state=active]:border-blue-500"
          >
            Simulation
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="manual" className="space-y-6">
          {error && <div className="text-red-600">{error}</div>}
          {message && <div className="text-green-600">{message}</div>}

          <section className="space-y-2">
            <h2 className="font-semibold">Transitions</h2>
            <div className="flex flex-wrap items-center gap-2">
              <input
                value={filterFrom}
                onChange={(e) => setFilterFrom(e.target.value)}
                placeholder="from slug filter"
                className="border rounded px-2 py-1"
              />
              <input
                value={filterTo}
                onChange={(e) => setFilterTo(e.target.value)}
                placeholder="to slug filter"
                className="border rounded px-2 py-1"
              />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as 'any' | 'enabled' | 'disabled')}
                className="border rounded px-2 py-1"
              >
                <option value="any">any</option>
                <option value="enabled">enabled</option>
                <option value="disabled">disabled</option>
              </select>
              <button onClick={loadTransitions} className="px-3 py-1 rounded border">
                Filter
              </button>
            </div>
            {listError && <div className="text-red-600">{listError}</div>}
            {loadingList ? (
              <div>Loading...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-left text-gray-500">
                    <tr>
                      <th className="w-4" />
                      <th>ID</th>
                      <th>From</th>
                      <th>To</th>
                      <th>Label</th>
                      <th>Weight</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transitions.map((t) => (
                      <tr key={t.id} className="border-t border-gray-200">
                        <td>
                          <input
                            type="checkbox"
                            aria-label={`select ${t.id}`}
                            checked={selectedIds.includes(t.id)}
                            onChange={(e) => toggleSelect(t.id, e.target.checked)}
                          />
                        </td>
                        <td className="font-mono">{t.id}</td>
                        <td>{t.from_slug}</td>
                        <td>{t.to_slug}</td>
                        <td>
                          <input
                            value={t.label || ''}
                            onChange={(e) => handleLabelChange(t.id, e.target.value)}
                            onBlur={(e) =>
                              commitUpdate(t.id, {
                                label: e.target.value || null,
                              })
                            }
                            className="border rounded px-1 py-0.5"
                            placeholder="label"
                          />
                        </td>
                        <td>
                          <input
                            type="number"
                            value={t.weight ?? 0}
                            onChange={(e) => handleWeightChange(t.id, e.target.value)}
                            onBlur={(e) =>
                              commitUpdate(t.id, {
                                weight: Number(e.target.value),
                              })
                            }
                            className="w-20 border rounded px-1 py-0.5"
                            placeholder="weight"
                          />
                        </td>
                        <td>{t.disabled ? 'disabled' : 'enabled'}</td>
                      </tr>
                    ))}
                    {transitions.length === 0 && (
                      <tr>
                        <td colSpan={7} className="p-2 text-center text-gray-500">
                          No transitions
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
            {selectedIds.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 mt-2">
                <input
                  value={bulkLabel}
                  onChange={(e) => setBulkLabel(e.target.value)}
                  placeholder="bulk label"
                  className="border rounded px-2 py-1"
                />
                <input
                  type="number"
                  value={bulkWeight}
                  onChange={(e) => setBulkWeight(e.target.value)}
                  placeholder="bulk weight"
                  className="border rounded px-2 py-1 w-24"
                />
                <button
                  onClick={applyBulk}
                  className="px-3 py-1 rounded border"
                  disabled={!bulkLabel.trim() && !bulkWeight.trim()}
                >
                  Apply
                </button>
              </div>
            )}
          </section>

          <section className="space-y-2">
            <h2 className="font-semibold">Add transition</h2>
            <form onSubmit={handleAdd} className="flex flex-wrap items-center gap-2">
              <input
                value={from}
                onChange={(e) => setFrom(e.target.value)}
                placeholder="from slug"
                className="border rounded px-2 py-1"
              />
              <input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="to slug"
                className="border rounded px-2 py-1"
              />
              <input
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="label (optional)"
                className="border rounded px-2 py-1 w-48"
              />
              <input
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                placeholder="weight"
                className="border rounded px-2 py-1 w-24"
              />
              <button type="submit" className="px-3 py-1 rounded border">
                Add
              </button>
            </form>
          </section>

          <section className="space-y-2">
            <h2 className="font-semibold">Enable transition</h2>
            <form onSubmit={handleEnable} className="flex items-center gap-2">
              <input
                value={enableId}
                onChange={(e) => setEnableId(e.target.value)}
                placeholder="transition id"
                className="border rounded px-2 py-1"
              />
              <button type="submit" className="px-3 py-1 rounded border">
                Enable
              </button>
            </form>
          </section>

          <section className="space-y-2">
            <h2 className="font-semibold">Disable transition</h2>
            <form onSubmit={handleDisable} className="flex items-center gap-2">
              <input
                value={disableId}
                onChange={(e) => setDisableId(e.target.value)}
                placeholder="transition id"
                className="border rounded px-2 py-1"
              />
              <button type="submit" className="px-3 py-1 rounded border">
                Disable
              </button>
            </form>
          </section>
        </Tabs.Content>

        <Tabs.Content value="auto" className="space-y-4">
          <div className="flex flex-col gap-2 max-w-xl">
            <label className="flex flex-col gap-1">
              <span className="text-sm text-gray-600">
                Node slug <Tooltip text="Slug of the starting node" />
              </span>
              <input
                value={nodeSlug}
                onChange={(e) => setNodeSlug(e.target.value)}
                className="border rounded px-2 py-1"
                placeholder="node-slug"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-sm text-gray-600">
                User ID (optional) <Tooltip text="UUID of user; leave empty for anonymous" />
              </span>
              <input
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="border rounded px-2 py-1"
                placeholder="uuid or empty for anon"
              />
            </label>
            <div className="flex items-center gap-2">
              <button
                disabled={!nodeSlug || running}
                onClick={run}
                className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-50"
              >
                {running ? 'Running...' : 'Run generation'}
              </button>
              <LimitBadge limitKey="compass_calls" />
            </div>
            {result && <div className="text-sm mt-2">{result}</div>}
          </div>
        </Tabs.Content>

        <Tabs.Content value="sim">
          <Simulation />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}
