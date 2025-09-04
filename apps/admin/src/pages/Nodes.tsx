/* eslint-disable @typescript-eslint/no-explicit-any, react-hooks/rules-of-hooks, react-hooks/exhaustive-deps */
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { listNodes, type NodeListParams } from '../api/nodes';
import type { Status } from '../openapi';
import { createPreviewLink } from '../api/preview';
import { wsApi } from '../api/wsApi';
import FlagsCell from '../components/FlagsCell';
import StatusBadge from '../components/StatusBadge';
import { useToast } from '../components/ToastProvider';
import WorkspaceControlPanel from '../components/WorkspaceControlPanel';
import WorkspaceSelector from '../components/WorkspaceSelector';
import { ensureArray } from '../shared/utils';
import { confirmWithEnv } from '../utils/env';
import { useWorkspace } from '../workspace/WorkspaceContext';

type NodeItem = {
  id: number;
  title?: string;
  slug?: string;
  status?: Status;
  is_visible: boolean;
  is_public: boolean;
  premium_only: boolean;
  is_recommendable: boolean;
  createdAt?: string;
  updatedAt?: string;
  type?: string;
  [k: string]: any;
};

const EMPTY_NODES: NodeItem[] = [];

type ChangeKey = 'is_visible' | 'is_public' | 'premium_only' | 'is_recommendable';
type ChangeSet = Partial<Record<ChangeKey, boolean>>;

interface NodesProps {
  initialType?: string;
}

export default function Nodes({ initialType = '' }: NodesProps = {}) {
  const { addToast } = useToast();
  const { workspaceId } = useWorkspace();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const copySlug = (slug: string) => {
    if (typeof navigator !== 'undefined' && slug) {
      void navigator.clipboard?.writeText(slug);
    }
  };

  if (!workspaceId) {
    return (
      <div className="p-4">
        <p className="mb-4">Выберите воркспейс, чтобы создать контент</p>
        <WorkspaceSelector />
      </div>
    );
  }

  // Пагинация/поиск
  const [q, setQ] = useState(() => searchParams.get('q') || '');
  const [visibility, setVisibility] = useState<'all' | 'visible' | 'hidden'>(() => {
    const vis = searchParams.get('visible');
    return vis === 'true' ? 'visible' : vis === 'false' ? 'hidden' : 'all';
  });
  const [nodeType, setNodeType] = useState(() => searchParams.get('type') || initialType);
  const [status, setStatus] = useState<Status | 'all'>(
    () => (searchParams.get('status') as Status | null) || 'all',
  );
  const [isPublic, setIsPublic] = useState<'all' | 'true' | 'false'>(
    () => searchParams.get('is_public') ?? 'all',
  );
  const [premium, setPremium] = useState<'all' | 'true' | 'false'>(
    () => searchParams.get('premium_only') ?? 'all',
  );
  const [recommendable, setRecommendable] = useState<'all' | 'true' | 'false'>(
    () => searchParams.get('recommendable') ?? 'all',
  );
  const [page, setPage] = useState(() => {
    const p = Number(searchParams.get('page') || '1');
    return p > 0 ? p - 1 : 0;
  });
  const [limit, setLimit] = useState(() => {
    const rawLimit = Number(searchParams.get('limit') || '20');
    return Number.isFinite(rawLimit) && rawLimit > 0 ? rawLimit : 20;
  });

  // Данные
  const [items, setItems] = useState<NodeItem[]>([]);
  const [baseline, setBaseline] = useState<Map<number, NodeItem>>(new Map()); // снимок исходных значений
  const [hasMore, setHasMore] = useState(false);

  // Выделение и отложенные изменения
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [pending, setPending] = useState<Map<number, ChangeSet>>(new Map());
  const changesCount = useMemo(
    () => Array.from(pending.values()).reduce((acc, cs) => acc + Object.keys(cs).length, 0),
    [pending],
  );
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (nodeType) params.set('type', nodeType);
    if (status !== 'all') params.set('status', status);
    if (visibility !== 'all') params.set('visible', visibility === 'visible' ? 'true' : 'false');
    if (isPublic !== 'all') params.set('is_public', isPublic);
    if (premium !== 'all') params.set('premium_only', premium);
    if (recommendable !== 'all') params.set('recommendable', recommendable);
    if (limit !== 20) params.set('limit', String(limit));
    if (page > 0) params.set('page', String(page + 1));
    if (params.toString() !== searchParams.toString()) {
      setSearchParams(params);
    }
  }, [
    q,
    nodeType,
    status,
    visibility,
    isPublic,
    premium,
    recommendable,
    page,
    limit,
    setSearchParams,
  ]);

  // Модерация: скрытие с причиной / восстановление
  const [modOpen, setModOpen] = useState(false);
  const [modTarget, setModTarget] = useState<NodeItem | null>(null);
  const [modReason, setModReason] = useState('');
  const [modBusy, setModBusy] = useState(false);

  // Превью ноды

  const openModerationFor = (node: NodeItem) => {
    // Если нода сейчас видима — запрашиваем причину и скрываем
    if (node.is_visible) {
      setModTarget(node);
      setModReason('');
      setModOpen(true);
    } else {
      // Восстановление: confirm и прямой вызов
      if (!node.slug) {
        addToast({
          title: 'Restore failed',
          description: 'Slug is missing',
          variant: 'error',
        });
        return;
      }
      if (!confirmWithEnv('Restore this node?')) return;
      (async () => {
        try {
          setModBusy(true);
          await wsApi.post(
            `/admin/moderation/nodes/${encodeURIComponent(String(node.slug))}/restore`,
          );
          // Оптимистично обновляем строку и baseline
          setItems((prev) => prev.map((n) => (n.id === node.id ? { ...n, is_visible: true } : n)));
          setBaseline((prev) => {
            const m = new Map(prev);
            const base = m.get(node.id) || node;
            m.set(node.id, { ...base, is_visible: true });
            return m;
          });
          addToast({ title: 'Node restored', variant: 'success' });
          // Фоновая верификация
          await refetch();
        } catch (e) {
          addToast({
            title: 'Restore failed',
            description: e instanceof Error ? e.message : String(e),
            variant: 'error',
          });
        } finally {
          setModBusy(false);
        }
      })();
    }
  };

  const submitModerationHide = async () => {
    if (!modTarget) return;
    if (!modTarget.slug) {
      addToast({
        title: 'Hide failed',
        description: 'Slug is missing',
        variant: 'error',
      });
      return;
    }
    try {
      setModBusy(true);
      await wsApi.post(
        `/admin/moderation/nodes/${encodeURIComponent(String(modTarget.slug))}/hide`,
        { reason: modReason || '' },
      );
      setModOpen(false);
      // Оптимистично: делаем ноду невидимой и фиксируем в baseline
      setItems((prev) =>
        prev.map((n) => (n.id === modTarget.id ? { ...n, is_visible: false } : n)),
      );
      setBaseline((prev) => {
        const m = new Map(prev);
        const base = m.get(modTarget.id) || modTarget;
        m.set(modTarget.id, { ...base, is_visible: false });
        return m;
      });
      addToast({ title: 'Node hidden', variant: 'success' });
      await refetch();
    } catch (e) {
      addToast({
        title: 'Hide failed',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    } finally {
      setModBusy(false);
    }
  };

  const {
    data: nodesData = EMPTY_NODES,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery<NodeItem[]>({
    queryKey: [
      'nodes',
      workspaceId,
      q,
      nodeType,
      status,
      visibility,
      isPublic,
      premium,
      recommendable,
      page,
      limit,
    ],
    queryFn: async () => {
      const params: NodeListParams = {
        limit,
        offset: page * limit,
      };
      if (q) params.q = q;
      if (status !== 'all') params.status = status;
      if (visibility !== 'all') params.visible = visibility === 'visible';
      if (isPublic !== 'all') params.is_public = isPublic === 'true';
      if (premium !== 'all') params.premium_only = premium === 'true';
      if (recommendable !== 'all') params.recommendable = recommendable === 'true';
      const res = await listNodes(workspaceId, params);
      return ensureArray<NodeItem>(res);
    },
    enabled: !!workspaceId,
    placeholderData: (prev) => prev,
    onError: (e) => {
      const msg = e instanceof Error ? e.message : String(e);
      addToast({
        title: 'Failed to load nodes',
        description: msg,
        variant: 'error',
      });
    },
  });

  useEffect(() => {
    const arr = nodesData || [];
    setItems(arr);
    setHasMore(arr.length === limit);
    const snap = new Map<number, NodeItem>();
    arr.forEach((n: NodeItem) => snap.set(n.id, { ...n }));
    setBaseline(snap);
    setPending(new Map());
  }, [nodesData, limit]);

  const loading = isLoading || isFetching;
  const errorMsg = error ? (error instanceof Error ? error.message : String(error)) : null;

  // Локальные изменения без немедленного вызова API.
  // Для is_visible используем модерационные ручки (hide с причиной / restore) — без staging.
  const toggleField = (id: number, field: ChangeKey) => {
    if (field === 'is_visible') {
      const node = items.find((n) => n.id === id);
      if (node) openModerationFor(node);
      return;
    }

    // Остальные флаги работают в staged-режиме
    const current =
      (items.find((n) => n.id === id)?.[field] as boolean | undefined) ??
      (baseline.get(id)?.[field] as boolean | undefined) ??
      false;
    const nextVal = !current;

    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, [field]: nextVal } : n)));

    setPending((prev) => {
      const next = new Map(prev);
      const cs = { ...(next.get(id) || {}) } as ChangeSet;
      const base = baseline.get(id);
      const baseVal = base ? (base as any)[field] : undefined;
      if (baseVal === nextVal) {
        delete cs[field];
      } else {
        cs[field] = nextVal;
      }
      if (Object.keys(cs).length === 0) {
        next.delete(id);
      } else {
        next.set(id, cs);
      }
      return next;
    });
  };

  const applyChanges = async () => {
    if (changesCount === 0) return;
    setApplying(true);
    const groups = new Map<string, { ids: number[]; changes: ChangeSet }>();

    for (const [id, cs] of pending.entries()) {
      const base = baseline.get(id);
      if (!base) continue;
      const diff: ChangeSet = {};
      for (const key of Object.keys(cs) as ChangeKey[]) {
        const nextVal = cs[key];
        const baseVal = (base as any)[key];
        if (nextVal !== undefined && nextVal !== baseVal) {
          diff[key] = nextVal;
        }
      }
      if (Object.keys(diff).length === 0) continue;
      const hash = JSON.stringify(diff);
      const entry = groups.get(hash);
      if (entry) {
        entry.ids.push(id);
      } else {
        groups.set(hash, { ids: [id], changes: diff });
      }
    }

    const results: string[] = [];
    try {
      for (const { ids, changes } of groups.values()) {
        await wsApi.patch(`/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/bulk`, {
          ids,
          changes,
        });
        results.push(`${Object.keys(changes).join(',')}: ${ids.length}`);
      }
      if (results.length > 0) {
        addToast({
          title: 'Changes applied',
          description: results.join(', '),
          variant: 'success',
        });
        // Оптимистично фиксируем новые значения как базовые,
        // чтобы статус в таблице не «откатывался» визуально.
        setBaseline(new Map(items.map((n) => [n.id, { ...n }])));
        setPending(new Map());
        // Фоновая верификация серверного состояния
        await refetch();
      } else {
        addToast({ title: 'No changes to apply', variant: 'info' });
      }
    } catch (e) {
      addToast({
        title: 'Failed to apply changes',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    } finally {
      setApplying(false);
    }
  };

  const discardChanges = () => {
    // Откатываем к baseline
    setItems(Array.from(baseline.values()));
    setPending(new Map());
  };

  // Выделение строк
  const toggleSelect = (id: number) => {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const previewSelected = async (id: number) => {
    if (!workspaceId) return;
    const node = items.find((n) => n.id === id);
    if (!node) return;
    try {
      const { url } = await createPreviewLink(workspaceId);
      const t = node.type || nodeType || 'article';
      window.open(`${url}/nodes/${t}/${id}`, '_blank');
    } catch (e) {
      addToast({
        title: 'Preview failed',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  const deleteSelected = async () => {
    const ids = Array.from(selected);
    if (ids.length === 0) return;
    if (!confirmWithEnv(`Delete ${ids.length} node${ids.length === 1 ? '' : 's'}?`)) return;
    try {
      for (const id of ids) {
        await wsApi.delete(
          `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(id)}`,
        );
      }
      setItems((prev) => prev.filter((n) => !selected.has(n.id)));
      setSelected(new Set());
      addToast({ title: 'Deleted', variant: 'success' });
    } catch (e) {
      addToast({
        title: 'Delete failed',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLElement &&
        (e.target.tagName === 'INPUT' ||
          e.target.tagName === 'TEXTAREA' ||
          e.target.isContentEditable)
      ) {
        return;
      }
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const first = Array.from(selected)[0];
      if (e.key === 'e' || e.key === 'E') {
        if (first) {
          const item = baseline.get(first);
          if (item) {
            const t = item.type || nodeType || 'article';
            navigate(`/nodes/${t}/${first}?workspace_id=${workspaceId}`);
          }
        }
      } else if (e.key === 'p' || e.key === 'P') {
        if (first) void previewSelected(first);
      } else if (e.key === 'Delete') {
        e.preventDefault();
        void deleteSelected();
      } else if (e.key === 's' || e.key === 'S') {
        e.preventDefault();
        void applyChanges();
      } else if (e.key === 'Escape') {
        setSelected(new Set());
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [selected, items, workspaceId, navigate, applyChanges]);

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <h1 className="text-2xl font-bold mb-4">Nodes</h1>

        <WorkspaceControlPanel />

        {/* Панель поиска и применения изменений */}
        <div className="mb-3 flex items-center gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by title or slug..."
            className="border rounded px-2 py-1"
          />
          <input
            value={nodeType}
            onChange={(e) => {
              setNodeType(e.target.value);
              setPage(0);
              setTimeout(() => {
                setPage(0);
                void refetch();
              });
            }}
            placeholder="node type"
            className="border rounded px-2 py-1"
          />
          <select
            className="border rounded px-2 py-1"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(0);
              setTimeout(() => {
                setPage(0);
                void refetch();
              });
            }}
          >
            <option value="all">all statuses</option>
            <option value="draft">draft</option>
            <option value="in_review">in_review</option>
            <option value="published">published</option>
            <option value="archived">archived</option>
          </select>
          <select
            className="border rounded px-2 py-1"
            value={visibility}
            onChange={(e) => {
              setVisibility(e.target.value as any);
              setPage(0);
              // Подгружаем заново с новым фильтром
              setTimeout(() => {
                setPage(0);
                void refetch();
              });
            }}
          >
            <option value="all">all</option>
            <option value="visible">visible</option>
            <option value="hidden">hidden</option>
          </select>
          <select
            className="border rounded px-2 py-1"
            value={isPublic}
            onChange={(e) => {
              setIsPublic(e.target.value as any);
              setPage(0);
              setTimeout(() => {
                setPage(0);
                void refetch();
              });
            }}
          >
            <option value="all">all</option>
            <option value="true">public</option>
            <option value="false">private</option>
          </select>
          <select
            className="border rounded px-2 py-1"
            value={premium}
            onChange={(e) => {
              setPremium(e.target.value as any);
              setPage(0);
              setTimeout(() => {
                setPage(0);
                void refetch();
              });
            }}
          >
            <option value="all">all</option>
            <option value="true">premium</option>
            <option value="false">free</option>
          </select>
          <select
            className="border rounded px-2 py-1"
            value={recommendable}
            onChange={(e) => {
              setRecommendable(e.target.value as any);
              setPage(0);
              setTimeout(() => {
                setPage(0);
                void refetch();
              });
            }}
          >
            <option value="all">all</option>
            <option value="true">recommendable</option>
            <option value="false">not recommendable</option>
          </select>
          <button
            type="button"
            onClick={() => {
              setPage(0);
              setPage(0);
              void refetch();
            }}
            className="px-3 py-1 rounded border"
          >
            Search
          </button>

          <label className="ml-2 text-sm text-gray-600">
            per page:
            <select
              className="ml-2 border rounded px-2 py-1"
              value={limit}
              onChange={(e) => {
                const val = Number(e.target.value) || 10;
                setLimit(val);
                setPage(0);
                // перегружаем список с новым лимитом
                setTimeout(() => {
                  setPage(0);
                  void refetch();
                });
              }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>

          <div className="ml-auto flex items-center gap-2">
            <button
              type="button"
              className="px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50"
              disabled={changesCount === 0 || loading || applying}
              onClick={applyChanges}
            >
              {applying
                ? 'Applying…'
                : `Apply changes${changesCount > 0 ? ` (${changesCount})` : ''}`}
            </button>
            <button
              type="button"
              className="px-3 py-1 rounded border disabled:opacity-50"
              disabled={changesCount === 0 || loading || applying}
              onClick={discardChanges}
            >
              Discard
            </button>
            <button
              type="button"
              className="px-3 py-1 rounded bg-blue-600 text-white"
              onClick={() => {
                const qs = workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : '';
                navigate(`/nodes/${nodeType || 'article'}/new${qs}`);
              }}
            >
              Add node
            </button>
          </div>
        </div>

        {loading && <p>Loading...</p>}
        {errorMsg && <p className="text-red-600">{errorMsg}</p>}

        {/* Bulk по выделению (по-прежнему доступно) */}
        {selected.size > 0 && (
          <div className="mb-2 flex gap-2">
            <span className="self-center text-sm">Selected {selected.size}</span>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={() => {
                setItems(items.map((n) => (selected.has(n.id) ? { ...n, is_visible: false } : n)));
                setPending((p) => {
                  const m = new Map(p);
                  Array.from(selected).forEach((id) => {
                    const cs = { ...(m.get(id) || {}) };
                    cs.is_visible = false;
                    m.set(id, cs);
                  });
                  return m;
                });
              }}
            >
              Hide
            </button>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={() => {
                setItems(items.map((n) => (selected.has(n.id) ? { ...n, is_visible: true } : n)));
                setPending((p) => {
                  const m = new Map(p);
                  Array.from(selected).forEach((id) => {
                    const cs = { ...(m.get(id) || {}) };
                    cs.is_visible = true;
                    m.set(id, cs);
                  });
                  return m;
                });
              }}
            >
              Show
            </button>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={() => {
                setItems(items.map((n) => (selected.has(n.id) ? { ...n, is_public: true } : n)));
                setPending((p) => {
                  const m = new Map(p);
                  Array.from(selected).forEach((id) => {
                    const cs = { ...(m.get(id) || {}) };
                    cs.is_public = true;
                    m.set(id, cs);
                  });
                  return m;
                });
              }}
            >
              Public
            </button>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={() => {
                setItems(items.map((n) => (selected.has(n.id) ? { ...n, is_public: false } : n)));
                setPending((p) => {
                  const m = new Map(p);
                  Array.from(selected).forEach((id) => {
                    const cs = { ...(m.get(id) || {}) };
                    cs.is_public = false;
                    m.set(id, cs);
                  });
                  return m;
                });
              }}
            >
              Private
            </button>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={() => {
                setItems(items.map((n) => (selected.has(n.id) ? { ...n, premium_only: true } : n)));
                setPending((p) => {
                  const m = new Map(p);
                  Array.from(selected).forEach((id) => {
                    const cs = { ...(m.get(id) || {}) };
                    cs.premium_only = true;
                    m.set(id, cs);
                  });
                  return m;
                });
              }}
            >
              Premium
            </button>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={() => {
                setItems(
                  items.map((n) => (selected.has(n.id) ? { ...n, premium_only: false } : n)),
                );
                setPending((p) => {
                  const m = new Map(p);
                  Array.from(selected).forEach((id) => {
                    const cs = { ...(m.get(id) || {}) };
                    cs.premium_only = false;
                    m.set(id, cs);
                  });
                  return m;
                });
              }}
            >
              Free
            </button>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={() => {
                setItems(
                  items.map((n) =>
                    selected.has(n.id) ? { ...n, is_recommendable: !n.is_recommendable } : n,
                  ),
                );
                setPending((p) => {
                  const m = new Map(p);
                  Array.from(selected).forEach((id) => {
                    const cs = { ...(m.get(id) || {}) };
                    cs.is_recommendable = !(baseline.get(id)?.is_recommendable ?? false);
                    m.set(id, cs);
                  });
                  return m;
                });
              }}
            >
              Toggle recommendable
            </button>
            <button
              type="button"
              className="ml-auto px-2 py-1 border rounded"
              onClick={() => setSelected(new Set())}
            >
              Clear
            </button>
          </div>
        )}

        {/* Таблица нод */}
        {!loading && !errorMsg && (
          <>
            <table className="min-w-full text-sm text-left">
              <thead>
                <tr className="border-b">
                  <th className="p-2">
                    <input
                      type="checkbox"
                      checked={items.length > 0 && selected.size === items.length}
                      onChange={(e) =>
                        setSelected(e.target.checked ? new Set(items.map((i) => i.id)) : new Set())
                      }
                    />
                  </th>
                  <th className="p-2">ID</th>
                  <th className="p-2">Title</th>
                  <th className="p-2">Status</th>
                  <th className="p-2">Flags</th>
                  <th className="p-2">Created</th>
                  <th className="p-2">Updated</th>
                  <th className="p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((n, i) => {
                  const base = baseline.get(n.id);
                  const changed =
                    !!base &&
                    (base.is_visible !== n.is_visible ||
                      base.is_public !== n.is_public ||
                      base.premium_only !== n.premium_only ||
                      base.is_recommendable !== n.is_recommendable);

                  return (
                    <tr
                      key={n.id ?? i}
                      className={`border-b hover:bg-gray-50 dark:hover:bg-gray-800 ${changed ? 'bg-amber-50 dark:bg-amber-900/20' : ''}`}
                    >
                      <td className="p-2">
                        <input
                          type="checkbox"
                          checked={selected.has(n.id)}
                          onChange={() => toggleSelect(n.id)}
                        />
                      </td>
                      <td className="p-2 font-mono">{n.id ?? '-'}</td>
                      <td className="p-2">
                        <div className="relative group pr-16">
                          <div className="font-bold">{n.title?.trim() || 'Untitled'}</div>
                          <div className="text-gray-500 text-xs font-mono">{n.slug ?? '-'}</div>
                          {n.slug && (
                            <button
                              type="button"
                              className="absolute top-0 right-0 text-xs text-blue-600 opacity-0 group-hover:opacity-100"
                              onClick={() => copySlug(n.slug ?? '')}
                            >
                              Copy slug
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="p-2">{n.status ? <StatusBadge status={n.status} /> : '-'}</td>
                      <td className="p-2 text-center">
                        <FlagsCell
                          value={{
                            is_visible: n.is_visible,
                            is_public: n.is_public,
                            premium_only: n.premium_only,
                            is_recommendable: n.is_recommendable,
                          }}
                          onToggle={(f) => toggleField(n.id, f)}
                          disabledVisible={applying || loading || modBusy}
                        />
                      </td>
                      <td className="p-2">
                        {n.createdAt ? new Date(n.createdAt).toLocaleString() : '-'}
                      </td>
                      <td className="p-2">
                        {n.updatedAt ? new Date(n.updatedAt).toLocaleString() : '-'}
                      </td>
                      <td className="p-2 space-x-2">
                        <button
                          type="button"
                          className="px-2 py-1 border rounded"
                          onClick={() => {
                            const t = n.type || nodeType || 'article';
                            navigate(`/nodes/${t}/${n.id}?workspace_id=${workspaceId}`);
                          }}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="px-2 py-1 border rounded"
                          onClick={async () => {
                            if (!workspaceId) return;
                            try {
                              const { url } = await createPreviewLink(workspaceId);
                              const t = n.type || nodeType || 'article';
                              window.open(`${url}/nodes/${t}/${n.id}`, '_blank');
                            } catch (e) {
                              addToast({
                                title: 'Preview failed',
                                description: e instanceof Error ? e.message : String(e),
                                variant: 'error',
                              });
                            }
                          }}
                        >
                          Preview
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={8} className="p-4 text-center text-gray-500">
                      No nodes found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            <div className="flex items-center gap-2 mt-2">
              <button
                type="button"
                className="px-2 py-1 border rounded"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Prev
              </button>
              <span className="text-sm">Page {page + 1}</span>
              <button
                type="button"
                className="px-2 py-1 border rounded"
                disabled={!hasMore}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          </>
        )}

        {/* Moderation modal: hide with reason */}
        {modOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded bg-white p-4 shadow dark:bg-gray-900">
              <h3 className="mb-3 text-lg font-semibold">Hide node</h3>
              <p className="mb-2 text-sm text-gray-600">
                Provide a reason for hiding this node. The action will be logged in audit.
              </p>
              <input
                className="mb-3 w-full rounded border px-2 py-1"
                placeholder="Reason (optional)"
                value={modReason}
                onChange={(e) => setModReason(e.target.value)}
                disabled={modBusy}
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  className="px-3 py-1 rounded border"
                  onClick={() => setModOpen(false)}
                  disabled={modBusy}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="px-3 py-1 rounded bg-gray-800 text-white disabled:opacity-50"
                  onClick={submitModerationHide}
                  disabled={modBusy}
                >
                  {modBusy ? 'Hiding…' : 'Hide'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
