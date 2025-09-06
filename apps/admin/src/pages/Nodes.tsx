/* eslint-disable @typescript-eslint/no-explicit-any, react-hooks/rules-of-hooks, react-hooks/exhaustive-deps */
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { listNodes, type NodeListParams } from '../api/nodes';
import { createPreviewLink } from '../api/preview';
import { wsApi } from '../api/wsApi';
import FlagsCell from '../components/FlagsCell';
import ScopeControls from '../components/ScopeControls';
import StatusCell from '../components/StatusCell';
import { useToast } from '../components/ToastProvider';
import { Card, CardContent } from '../components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import type { Status as NodeStatus } from '../openapi';
import { Button } from '../shared/ui';
import { ensureArray } from '../shared/utils';
import { notify } from '../utils/notify';
import { useWorkspace } from '../workspace/WorkspaceContext';

  type NodeItem = {
    id: number;
    title?: string;
    slug?: string;
    status?: NodeStatus;
    is_visible: boolean;
    is_public: boolean;
    premium_only: boolean;
    is_recommendable: boolean;
    createdAt?: string;
    updatedAt?: string;
    type?: string;
    space?: string;
    [k: string]: any;
  };

const EMPTY_NODES: NodeItem[] = [];

type ChangeKey = 'is_visible' | 'is_public' | 'premium_only' | 'is_recommendable';
type ChangeSet = Partial<Record<ChangeKey, boolean>>;

export default function Nodes() {
  const { addToast } = useToast();
  const { workspaceId } = useWorkspace();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [scopeMode, setScopeMode] = useState('member');
  const [roles, setRoles] = useState<string[]>([]);

  const copySlug = (slug: string) => {
    if (typeof navigator !== 'undefined' && slug) {
      void navigator.clipboard?.writeText(slug);
    }
  };

  if (!workspaceId) {
    return (
      <div className="p-4">
        <ScopeControls
          scopeMode={scopeMode}
          onScopeModeChange={setScopeMode}
          roles={roles}
          onRolesChange={setRoles}
        />
      </div>
    );
  }

  // Пагинация/поиск
  const [q, setQ] = useState(() => searchParams.get('q') || '');
  const [visibility, setVisibility] = useState<'all' | 'visible' | 'hidden'>(() => {
    const vis = searchParams.get('visible');
    return vis === 'true' ? 'visible' : vis === 'false' ? 'hidden' : 'all';
  });
  const [status, setStatus] = useState<NodeStatus | 'all'>(
    () => (searchParams.get('status') as NodeStatus | null) || 'all',
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
        const msg = 'Отсутствует slug';
        notify(`Не удалось восстановить: ${msg}`);
        addToast({ title: 'Не удалось восстановить', description: msg, variant: 'error' });
        return;
      }
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
          notify('Нода восстановлена');
          addToast({ title: 'Нода восстановлена', variant: 'success' });
          // Фоновая верификация
          await refetch();
        } catch (e) {
          const msg = e instanceof Error ? e.message : String(e);
          notify(`Не удалось восстановить: ${msg}`);
          addToast({ title: 'Не удалось восстановить', description: msg, variant: 'error' });
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
        title: 'Не удалось скрыть',
        description: 'Отсутствует slug',
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
      addToast({ title: 'Нода скрыта', variant: 'success' });
      await refetch();
    } catch (e) {
      addToast({
        title: 'Не удалось скрыть',
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
      status,
      visibility,
      isPublic,
      premium,
      recommendable,
      page,
      limit,
      scopeMode,
    ],
    queryFn: async () => {
      const params: NodeListParams = {
        limit,
        offset: page * limit,
        scope_mode: scopeMode === 'space' ? `space:${workspaceId}` : scopeMode,
        space_id: workspaceId,
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
        title: 'Не удалось загрузить ноды',
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
          title: 'Изменения применены',
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
        addToast({ title: 'Нет изменений для применения', variant: 'info' });
      }
    } catch (e) {
      addToast({
        title: 'Не удалось применить изменения',
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
      const t = node.type || 'article';
      window.open(`${url}/nodes/${t}/${id}`, '_blank');
    } catch (e) {
      addToast({
        title: 'Предпросмотр не удалось',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  const deleteSelected = async () => {
    const ids = Array.from(selected);
    if (ids.length === 0) return;
    if (!(await confirmWithEnv(`Удалить ${ids.length} нод${ids.length === 1 ? 'у' : 'ы'}?`))) return;
    try {
      for (const id of ids) {
        await wsApi.delete(
          `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(id)}`,
        );
      }
      setItems((prev) => prev.filter((n) => !selected.has(n.id)));
      setSelected(new Set());
      addToast({ title: 'Удалено', variant: 'success' });
    } catch (e) {
      addToast({
        title: 'Не удалось удалить',
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
            const t = item.type || 'article';
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
        <h1 className="text-2xl font-bold mb-4">Ноды</h1>

        <ScopeControls
          scopeMode={scopeMode}
          onScopeModeChange={setScopeMode}
          roles={roles}
          onRolesChange={setRoles}
        />

        <Card className="sticky top-0 z-10 mb-4">
          <CardContent className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <input
                value={q}
                onChange={(e) => {
                  setQ(e.target.value);
                  setPage(0);
                }}
                placeholder="Поиск по названию или slug..."
                className="border rounded px-2 py-1 flex-1 min-w-[180px]"
              />
              <select
                className="border rounded px-2 py-1"
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value as any);
                  setPage(0);
                }}
              >
                <option value="all">Все статусы</option>
                <option value="draft">черновик</option>
                <option value="in_review">на проверке</option>
                <option value="published">опубликовано</option>
                <option value="archived">архив</option>
              </select>
              <select
                className="border rounded px-2 py-1"
                value={visibility}
                onChange={(e) => {
                  setVisibility(e.target.value as any);
                  setPage(0);
                }}
              >
                <option value="all">Все</option>
                <option value="visible">видимые</option>
                <option value="hidden">скрытые</option>
              </select>
              <select
                className="border rounded px-2 py-1"
                value={isPublic}
                onChange={(e) => {
                  setIsPublic(e.target.value as any);
                  setPage(0);
                }}
              >
                <option value="all">Все</option>
                <option value="true">публичные</option>
                <option value="false">приватные</option>
              </select>
              <select
                className="border rounded px-2 py-1"
                value={premium}
                onChange={(e) => {
                  setPremium(e.target.value as any);
                  setPage(0);
                }}
              >
                <option value="all">Все</option>
                <option value="true">премиум</option>
                <option value="false">бесплатно</option>
              </select>
              <select
                className="border rounded px-2 py-1"
                value={recommendable}
                onChange={(e) => {
                  setRecommendable(e.target.value as any);
                  setPage(0);
                }}
              >
                <option value="all">Все</option>
                <option value="true">рекомендуемые</option>
                <option value="false">не рекомендуемые</option>
              </select>
              <Button type="button" onClick={() => void refetch()}>
                Поиск
              </Button>

              <label className="ml-2 text-sm text-gray-600">
                на странице:
                <select
                  className="ml-2 border rounded px-2 py-1"
                  value={limit}
                  onChange={(e) => {
                    const val = Number(e.target.value) || 10;
                    setLimit(val);
                    setPage(0);
                  }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </label>

              <div className="ml-auto flex items-center gap-2">
                <Button
                  type="button"
                  className="bg-green-600 text-white disabled:opacity-50"
                  disabled={changesCount === 0 || loading || applying}
                  onClick={applyChanges}
                >
                  {applying
                    ? 'Применение…'
                    : `Применить изменения${changesCount > 0 ? ` (${changesCount})` : ''}`}
                </Button>
                <Button
                  type="button"
                  className="disabled:opacity-50"
                  disabled={changesCount === 0 || loading || applying}
                  onClick={discardChanges}
                >
                  Отменить
                </Button>
                <Button
                  type="button"
                  className="bg-blue-600 text-white"
                  onClick={() => {
                    const qs = workspaceId
                      ? `?workspace_id=${encodeURIComponent(workspaceId)}`
                      : '';
                    navigate(`/nodes/article/new${qs}`);
                  }}
                >
                  Добавить ноду
                </Button>
              </div>
            </div>
            {selected.size > 0 && (
              <div className="flex flex-wrap gap-2">
                <span className="self-center text-sm">Выбрано {selected.size}</span>
                <Button
                  type="button"
                  onClick={() => {
                    setItems(
                      items.map((n) => (selected.has(n.id) ? { ...n, is_visible: false } : n)),
                    );
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
                  Скрыть
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setItems(
                      items.map((n) => (selected.has(n.id) ? { ...n, is_visible: true } : n)),
                    );
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
                  Показать
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setItems(
                      items.map((n) => (selected.has(n.id) ? { ...n, is_public: true } : n)),
                    );
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
                  Публично
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setItems(
                      items.map((n) => (selected.has(n.id) ? { ...n, is_public: false } : n)),
                    );
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
                  Приватно
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setItems(
                      items.map((n) => (selected.has(n.id) ? { ...n, premium_only: true } : n)),
                    );
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
                  Премиум
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setItems(
                      items.map((n) =>
                        selected.has(n.id) ? { ...n, premium_only: false } : n,
                      ),
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
                  Бесплатно
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setItems(
                      items.map((n) =>
                        selected.has(n.id)
                          ? { ...n, is_recommendable: !n.is_recommendable }
                          : n,
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
                  Переключить рекомендование
                </Button>
                <Button type="button" className="ml-auto" onClick={() => setSelected(new Set())}>
                  Очистить
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {loading && <p>Загрузка...</p>}
        {errorMsg && <p className="text-red-600">{errorMsg}</p>}

        {!loading && !errorMsg && (
          <>
            <div className="overflow-x-auto">
              <Table className="min-w-full text-left">
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-8">
                      <input
                        type="checkbox"
                        checked={items.length > 0 && selected.size === items.length}
                        onChange={(e) =>
                          setSelected(e.target.checked ? new Set(items.map((i) => i.id)) : new Set())
                        }
                      />
                    </TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead>Название</TableHead>
                    <TableHead className="w-32 text-center">Статус</TableHead>
                    <TableHead className="w-32 text-center">Флаги</TableHead>
                    <TableHead className="hidden md:table-cell">Создано</TableHead>
                    <TableHead className="hidden md:table-cell">Обновлено</TableHead>
                    <TableHead>Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((n, i) => {
                    const base = baseline.get(n.id);
                    const changed =
                      !!base &&
                      (base.is_visible !== n.is_visible ||
                        base.is_public !== n.is_public ||
                        base.premium_only !== n.premium_only ||
                        base.is_recommendable !== n.is_recommendable);

                    return (
                      <TableRow key={n.id ?? i} className={changed ? 'bg-amber-50 dark:bg-amber-900/20' : ''}>
                        <TableCell>
                          <input
                            type="checkbox"
                            checked={selected.has(n.id)}
                            onChange={() => toggleSelect(n.id)}
                          />
                        </TableCell>
                        <TableCell className="font-mono">{n.id ?? '-'}</TableCell>
                        <TableCell>
                          <div className="relative group pr-16">
                            <div className="font-bold">{n.title?.trim() || 'Без названия'}</div>
                            <div className="text-gray-500 text-xs font-mono">{n.slug ?? '-'}</div>
                            {n.space && (
                              <span
                                className="ml-2 text-xs rounded bg-blue-100 text-blue-800 px-1"
                                data-testid="space-badge"
                              >
                                space: {n.space}
                              </span>
                            )}
                            {n.slug && (
                              <Button
                                type="button"
                                className="absolute top-0 right-0 text-xs text-blue-600 opacity-0 group-hover:opacity-100 border-none px-1 py-0"
                                onClick={() => copySlug(n.slug ?? '')}
                              >
                                Копировать slug
                              </Button>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="w-32 text-center">
                          <StatusCell status={n.status as any} />
                        </TableCell>
                        <TableCell className="w-32 text-center">
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
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          {n.createdAt ? new Date(n.createdAt).toLocaleString() : '-'}
                        </TableCell>
                        <TableCell className="hidden md:table-cell">
                          {n.updatedAt ? new Date(n.updatedAt).toLocaleString() : '-'}
                        </TableCell>
                        <TableCell className="space-x-2">
                          <Button
                            type="button"
                            onClick={() => {
                              const t = n.type || 'article';
                              navigate(`/nodes/${t}/${n.id}?workspace_id=${workspaceId}`);
                            }}
                          >
                            Редактировать
                          </Button>
                          <Button
                            type="button"
                            onClick={async () => {
                              if (!workspaceId) return;
                              try {
                                const { url } = await createPreviewLink(workspaceId);
                                const t = n.type || 'article';
                                window.open(`${url}/nodes/${t}/${n.id}`, '_blank');
                              } catch (e) {
                                  addToast({
                                    title: 'Предпросмотр не удалось',
                                    description: e instanceof Error ? e.message : String(e),
                                    variant: 'error',
                                  });
                              }
                            }}
                          >
                            Предпросмотр
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  {items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="p-4 text-center text-gray-500">
                        Ноды не найдены
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Button
                type="button"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Назад
              </Button>
              <span className="text-sm">Страница {page + 1}</span>
              <Button
                type="button"
                disabled={!hasMore}
                onClick={() => setPage((p) => p + 1)}
              >
                Вперед
              </Button>
            </div>
          </>
        )}

        {/* Moderation modal: hide with reason */}
        {modOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded bg-white p-4 shadow dark:bg-gray-900">
              <h3 className="mb-3 text-lg font-semibold">Скрыть ноду</h3>
              <p className="mb-2 text-sm text-gray-600">
                Укажите причину скрытия этой ноды. Действие будет записано в аудит.
              </p>
              <input
                className="mb-3 w-full rounded border px-2 py-1"
                placeholder="Причина (необязательно)"
                value={modReason}
                onChange={(e) => setModReason(e.target.value)}
                disabled={modBusy}
              />
              <div className="flex justify-end gap-2">
                <Button type="button" onClick={() => setModOpen(false)} disabled={modBusy}>
                  Отмена
                </Button>
                <Button
                  type="button"
                  className="bg-gray-800 text-white disabled:opacity-50"
                  onClick={submitModerationHide}
                  disabled={modBusy}
                >
                  {modBusy ? 'Скрытие…' : 'Скрыть'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
