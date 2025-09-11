/* eslint-disable @typescript-eslint/no-explicit-any, react-hooks/exhaustive-deps */
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { useAccount } from '../account/AccountContext';
import { accountApi } from '../api/accountApi';
import { api } from '../api/client';
import { listNodes, listNodesGlobal, type NodeListParams } from '../api/nodes';
import { createPreviewLink } from '../api/preview';
import FlagsCell from '../components/FlagsCell';
// ScopeControls removed from this page to avoid duplicate scope UI
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
import { useDebounce } from '../shared/hooks/useDebounce';
import { Button } from '../shared/ui';
import { ensureArray } from '../shared/utils';
import { confirmWithEnv } from '../utils/env';
import { notify } from '../utils/notify';

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
  const { accountId } = useAccount();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [scopeMode, setScopeMode] = useState(() => searchParams.get('scope') || 'mine');
  const [authorTab, setAuthorTab] = useState(false);
  // Selected author's UUID (sent to backend)
  const [authorId, setAuthorId] = useState('');
  // Text in the author search input; used to search by username/email
  const [authorQuery, setAuthorQuery] = useState('');
  const debouncedAuthor = useDebounce(authorQuery, 300);
  type AuthorOption = { id: string; username?: string | null; email?: string | null };
  const [authorOptions, setAuthorOptions] = useState<AuthorOption[]>([]);
  const [, setAuthorLoading] = useState(false);

  const copySlug = (slug: string) => {
    if (typeof navigator !== 'undefined' && slug) {
      void navigator.clipboard?.writeText(slug);
    }
  };

  // РџР°РіРёРЅР°С†РёСЏ/РїРѕРёСЃРє
  const [q, setQ] = useState(() => searchParams.get('q') || '');
  const [visibility, setVisibility] = useState<'all' | 'visible' | 'hidden'>(() => {
    const vis = searchParams.get('visible');
    return vis === 'true' ? 'visible' : vis === 'false' ? 'hidden' : 'all';
  });
  const [status, setStatus] = useState<NodeStatus | 'all'>(
    () => (searchParams.get('status') as NodeStatus | null) || 'all',
  );
  const [isPublic, setIsPublic] = useState<'all' | 'true' | 'false'>(
    () => (searchParams.get('is_public') as 'all' | 'true' | 'false' | null) ?? 'all',
  );
  const [premium, setPremium] = useState<'all' | 'true' | 'false'>(
    () => (searchParams.get('premium_only') as 'all' | 'true' | 'false' | null) ?? 'all',
  );
  const [recommendable, setRecommendable] = useState<'all' | 'true' | 'false'>(
    () => (searchParams.get('recommendable') as 'all' | 'true' | 'false' | null) ?? 'all',
  );
  const [page, setPage] = useState(() => {
    const p = Number(searchParams.get('page') || '1');
    return p > 0 ? p - 1 : 0;
  });
  const [limit, setLimit] = useState(() => {
    const rawLimit = Number(searchParams.get('limit') || '20');
    return Number.isFinite(rawLimit) && rawLimit > 0 ? rawLimit : 20;
  });

  // If no account is selected, restrict the scope to personal/global options
  useEffect(() => {
    if (!accountId && scopeMode && scopeMode !== 'mine' && scopeMode !== 'global') {
      setScopeMode('mine');
    }
  }, [accountId]);

  // Р”Р°РЅРЅС‹Рµ
  const [items, setItems] = useState<NodeItem[]>([]);
  const [baseline, setBaseline] = useState<Map<number, NodeItem>>(new Map()); // СЃРЅРёРјРѕРє РёСЃС…РѕРґРЅС‹С… Р·РЅР°С‡РµРЅРёР№
  const [hasMore, setHasMore] = useState(false);

  // Р’С‹РґРµР»РµРЅРёРµ Рё РѕС‚Р»РѕР¶РµРЅРЅС‹Рµ РёР·РјРµРЅРµРЅРёСЏ
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
    if (scopeMode) params.set('scope', scopeMode);
    if (authorTab && authorId) params.set('author', authorId);
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
    scopeMode,
    authorTab,
    authorId,
    status,
    visibility,
    isPublic,
    premium,
    recommendable,
    page,
    limit,
    setSearchParams,
  ]);

  // РњРѕРґРµСЂР°С†РёСЏ: СЃРєСЂС‹С‚РёРµ СЃ РїСЂРёС‡РёРЅРѕР№ / РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёРµ
  const [modOpen, setModOpen] = useState(false);
  const [modTarget, setModTarget] = useState<NodeItem | null>(null);
  const [modReason, setModReason] = useState('');
  const [modBusy, setModBusy] = useState(false);

  // РџСЂРµРІСЊСЋ РЅРѕРґС‹

  const openModerationFor = (node: NodeItem) => {
    if (!accountId) return;
    // Р•СЃР»Рё РЅРѕРґР° СЃРµР№С‡Р°СЃ РІРёРґРёРјР° вЂ” Р·Р°РїСЂР°С€РёРІР°РµРј РїСЂРёС‡РёРЅСѓ Рё СЃРєСЂС‹РІР°РµРј
    if (node.is_visible) {
      setModTarget(node);
      setModReason('');
      setModOpen(true);
    } else {
      // Р’РѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёРµ: confirm Рё РїСЂСЏРјРѕР№ РІС‹Р·РѕРІ
      if (!node.slug) {
        const msg = 'РћС‚СЃСѓС‚СЃС‚РІСѓРµС‚ slug';
        notify(`РќРµ СѓРґР°Р»РѕСЃСЊ РІРѕСЃСЃС‚Р°РЅРѕРІРёС‚СЊ: ${msg}`);
        addToast({ title: 'Error', description: 'Operation failed', variant: 'error' });
        return;
      }
      (async () => {
        try {
          setModBusy(true);
          await accountApi.post(
            `/admin/moderation/nodes/${encodeURIComponent(String(node.slug))}/restore`,
            undefined,
            { accountId },
          );
          // РћРїС‚РёРјРёСЃС‚РёС‡РЅРѕ РѕР±РЅРѕРІР»СЏРµРј СЃС‚СЂРѕРєСѓ Рё baseline
          setItems((prev) => prev.map((n) => (n.id === node.id ? { ...n, is_visible: true } : n)));
          setBaseline((prev) => {
            const m = new Map(prev);
            const base = m.get(node.id) || node;
            m.set(node.id, { ...base, is_visible: true });
            return m;
          });
          notify('РќРѕРґР° РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅР°');
          addToast({ title: 'OK', variant: 'success' });
          // Р¤РѕРЅРѕРІР°СЏ РІРµСЂРёС„РёРєР°С†РёСЏ
          await refetch();
        } catch (e) {
          const msg = e instanceof Error ? e.message : String(e);
          notify(`РќРµ СѓРґР°Р»РѕСЃСЊ РІРѕСЃСЃС‚Р°РЅРѕРІРёС‚СЊ: ${msg}`);
          addToast({ title: 'Error', description: 'Operation failed', variant: 'error' });
        } finally {
          setModBusy(false);
        }
      })();
    }
  };

  const submitModerationHide = async () => {
    if (!modTarget || !accountId) return;
    if (!modTarget.slug) {
      addToast({ title: 'РќРµ СѓРґР°Р»РѕСЃСЊ СЃРєСЂС‹С‚СЊ', description: 'РћС‚СЃСѓС‚СЃС‚РІСѓРµС‚ slug', variant: 'error' });
      return;
    }
    try {
      setModBusy(true);
      await accountApi.post(
        `/admin/moderation/nodes/${encodeURIComponent(String(modTarget.slug))}/hide`,
        { reason: modReason || '' },
        { accountId },
      );
      setModOpen(false);
      // РћРїС‚РёРјРёСЃС‚РёС‡РЅРѕ: РґРµР»Р°РµРј РЅРѕРґСѓ РЅРµРІРёРґРёРјРѕР№ Рё С„РёРєСЃРёСЂСѓРµРј РІ baseline
      setItems((prev) =>
        prev.map((n) => (n.id === modTarget.id ? { ...n, is_visible: false } : n)),
      );
      setBaseline((prev) => {
        const m = new Map(prev);
        const base = m.get(modTarget.id) || modTarget;
        m.set(modTarget.id, { ...base, is_visible: false });
        return m;
      });
      addToast({ title: 'OK', variant: 'success' });
      await refetch();
    } catch (e) {
      addToast({
        title: 'РќРµ СѓРґР°Р»РѕСЃСЊ СЃРєСЂС‹С‚СЊ',
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
  } = useQuery<NodeItem[], Error>({
    queryKey: [
      'nodes',
      accountId,
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
        scope_mode: scopeMode === 'space' ? `space:${accountId}` : scopeMode,
      };
      if (q) params.q = q;
      if (status !== 'all') params.status = status;
      if (visibility !== 'all') params.visible = visibility === 'visible';
      if (isPublic !== 'all') params.is_public = isPublic === 'true';
      if (premium !== 'all') params.premium_only = premium === 'true';
      if (recommendable !== 'all') params.recommendable = recommendable === 'true';
      if (!accountId && params.scope_mode === 'global') {
        const res = await listNodesGlobal(params);
        return ensureArray<NodeItem>(res as unknown);
      }
      const res = await listNodes(params);
      return ensureArray<NodeItem>(res as unknown);
    },
    enabled: true,
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

  // Load author suggestions when searching by name/email (not a UUID)
  useEffect(() => {
    const isUuid =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        debouncedAuthor.trim(),
      );
    if (!authorTab) {
      setAuthorOptions([]);
      return;
    }
    if (debouncedAuthor && !isUuid) {
      (async () => {
        try {
          setAuthorLoading(true);
          const params = new URLSearchParams();
          params.set('q', debouncedAuthor);
          params.set('limit', '10');
          const res = await api.get(`/admin/users?${params.toString()}`);
          setAuthorOptions(ensureArray<AuthorOption>(res.data));
        } catch {
          setAuthorOptions([]);
        } finally {
          setAuthorLoading(false);
        }
      })();
    } else {
      setAuthorOptions([]);
    }
  }, [debouncedAuthor, authorTab]);

  const loading = isLoading || isFetching;
  const errorMsg = error ? error.message : null;

  // Р›РѕРєР°Р»СЊРЅС‹Рµ РёР·РјРµРЅРµРЅРёСЏ Р±РµР· РЅРµРјРµРґР»РµРЅРЅРѕРіРѕ РІС‹Р·РѕРІР° API.
  // Р”Р»СЏ is_visible РёСЃРїРѕР»СЊР·СѓРµРј РјРѕРґРµСЂР°С†РёРѕРЅРЅС‹Рµ СЂСѓС‡РєРё (hide СЃ РїСЂРёС‡РёРЅРѕР№ / restore) вЂ” Р±РµР· staging.
  const toggleField = (id: number, field: ChangeKey) => {
    if (field === 'is_visible') {
      const node = items.find((n) => n.id === id);
      if (node) openModerationFor(node);
      return;
    }

    // РћСЃС‚Р°Р»СЊРЅС‹Рµ С„Р»Р°РіРё СЂР°Р±РѕС‚Р°СЋС‚ РІ staged-СЂРµР¶РёРјРµ
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
      const baseVal = base ? (base as Record<string, unknown>)[field] : undefined;
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
        const baseVal = (base as Record<string, unknown>)[key];
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
        const bulkUrl = accountId ? `/admin/nodes/bulk` : `/admin/nodes/bulk`;
        await accountApi.patch(
          bulkUrl,
          { ids, changes },
          { accountId: accountId || '', account: false },
        );
        results.push(`${Object.keys(changes).join(',')}: ${ids.length}`);
      }
      if (results.length > 0) {
        addToast({
          title: 'РР·РјРµРЅРµРЅРёСЏ РїСЂРёРјРµРЅРµРЅС‹',
          description: results.join(', '),
          variant: 'success',
        });
        // РћРїС‚РёРјРёСЃС‚РёС‡РЅРѕ С„РёРєСЃРёСЂСѓРµРј РЅРѕРІС‹Рµ Р·РЅР°С‡РµРЅРёСЏ РєР°Рє Р±Р°Р·РѕРІС‹Рµ,
        // С‡С‚РѕР±С‹ СЃС‚Р°С‚СѓСЃ РІ С‚Р°Р±Р»РёС†Рµ РЅРµ В«РѕС‚РєР°С‚С‹РІР°Р»СЃСЏВ» РІРёР·СѓР°Р»СЊРЅРѕ.
        setBaseline(new Map(items.map((n) => [n.id, { ...n }])));
        setPending(new Map());
        // Р¤РѕРЅРѕРІР°СЏ РІРµСЂРёС„РёРєР°С†РёСЏ СЃРµСЂРІРµСЂРЅРѕРіРѕ СЃРѕСЃС‚РѕСЏРЅРёСЏ
        await refetch();
      } else {
        addToast({ title: 'OK', variant: 'success' });
      }
    } catch (e) {
      addToast({
        title: 'РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРёРјРµРЅРёС‚СЊ РёР·РјРµРЅРµРЅРёСЏ',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    } finally {
      setApplying(false);
    }
  };

  const discardChanges = () => {
    // РћС‚РєР°С‚С‹РІР°РµРј Рє baseline
    setItems(Array.from(baseline.values()));
    setPending(new Map());
  };

  // Р’С‹РґРµР»РµРЅРёРµ СЃС‚СЂРѕРє
  const toggleSelect = (id: number) => {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const previewSelected = async (id: number) => {
    if (!accountId) return;
    const node = items.find((n) => n.id === id);
    if (!node) return;
    try {
      const { url } = await createPreviewLink();
      const t = node.type || 'article';
      window.open(`${url}/nodes/${t}/${id}`, '_blank');
    } catch (e) {
      addToast({
        title: 'РџСЂРµРґРїСЂРѕСЃРјРѕС‚СЂ РЅРµ РѕС‚РєСЂС‹Р»СЃСЏ',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  const deleteSelected = async () => {
    const ids = Array.from(selected);
    if (ids.length === 0) return;
    if (!(await confirmWithEnv(`РЈРґР°Р»РёС‚СЊ ${ids.length} РЅРѕРґ${ids.length === 1 ? 'Сѓ' : 'С‹'}?`)))
      return;
    try {
      for (const id of ids) {
        const delUrl = `/admin/nodes/${encodeURIComponent(id)}`;
        await accountApi.delete(delUrl, { accountId: accountId || '', account: false });
      }
      setItems((prev) => prev.filter((n) => !selected.has(n.id)));
      setSelected(new Set());
      addToast({ title: 'OK', variant: 'success' });
    } catch (e) {
      addToast({
        title: 'РќРµ СѓРґР°Р»РѕСЃСЊ СѓРґР°Р»РёС‚СЊ',
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
            navigate(`/nodes/${t}/${first}`);
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
  }, [selected, items, accountId, navigate, applyChanges]);

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold">РќРѕРґС‹</h1>
          <Button
            type="button"
            onClick={() => {
              navigate(`/nodes/article/new`);
            }}
          >
            РЎРѕР·РґР°С‚СЊ
          </Button>
        </div>

        {/* Quick scope filter */}
        <div className="flex items-center gap-2 mb-2">
          <Button
            type="button"
            onClick={() => {
              setAuthorTab(false);
              setScopeMode('global');
              setPage(0);
            }}
          >
            Р’СЃРµ
          </Button>
          <Button
            type="button"
            onClick={() => {
              setAuthorTab(false);
              setScopeMode('mine');
              setPage(0);
            }}
          >
            РњРѕРё
          </Button>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              onClick={() => {
                setAuthorTab(true);
                setScopeMode('global');
                setPage(0);
              }}
            >
              РђРІС‚РѕСЂ
            </Button>
            {authorTab && (
              <input
                className="border rounded px-2 py-1 text-sm w-64"
                placeholder="UUID Р°РІС‚РѕСЂР°"
                value={authorQuery}
                onChange={(e) => {
                  setAuthorQuery(e.target.value);
                  setAuthorId('');
                  setPage(0);
                }}
                onBlur={() => {
                  if (!authorId && authorOptions.length > 0) {
                    const u = authorOptions[0] as {
                      id: string;
                      username?: string | null;
                      email?: string | null;
                    };
                    setAuthorId(u.id);
                    setAuthorQuery(u.username || u.email || u.id);
                  }
                }}
              />
            )}
          </div>
        </div>

        {/* ScopeControls removed to avoid duplicated filters; Admin override lives elsewhere. */}

        <Card className="sticky top-0 z-10 mb-4">
          <CardContent className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <input
                value={q}
                onChange={(e) => {
                  setQ(e.target.value);
                  setPage(0);
                }}
                placeholder="РџРѕРёСЃРє РїРѕ РЅР°Р·РІР°РЅРёСЋ РёР»Рё slug..."
                className="border rounded px-2 py-1 flex-1 min-w-[180px]"
              />
              <select
                className="border rounded px-2 py-1"
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value as NodeStatus | 'all');
                  setPage(0);
                }}
              >
                <option value="all">Р’СЃРµ СЃС‚Р°С‚СѓСЃС‹</option>
                <option value="draft">С‡РµСЂРЅРѕРІРёРє</option>
                <option value="in_review">РЅР° РїСЂРѕРІРµСЂРєРµ</option>
                <option value="published">РѕРїСѓР±Р»РёРєРѕРІР°РЅРѕ</option>
                <option value="archived">Р°СЂС…РёРІ</option>
              </select>
              <select
                className="border rounded px-2 py-1"
                value={visibility}
                onChange={(e) => {
                  setVisibility(e.target.value as 'all' | 'visible' | 'hidden');
                  setPage(0);
                }}
              >
                <option value="all">Р’СЃРµ</option>
                <option value="visible">РІРёРґРёРјС‹Рµ</option>
                <option value="hidden">СЃРєСЂС‹С‚С‹Рµ</option>
              </select>
              <select
                className="border rounded px-2 py-1"
                value={isPublic}
                onChange={(e) => {
                  setIsPublic(e.target.value as 'all' | 'true' | 'false');
                  setPage(0);
                }}
              >
                <option value="all">Р’СЃРµ</option>
                <option value="true">РїСѓР±Р»РёС‡РЅС‹Рµ</option>
                <option value="false">РїСЂРёРІР°С‚РЅС‹Рµ</option>
              </select>
              <select
                className="border rounded px-2 py-1"
                value={premium}
                onChange={(e) => {
                  setPremium(e.target.value as 'all' | 'true' | 'false');
                  setPage(0);
                }}
              >
                <option value="all">Р’СЃРµ</option>
                <option value="true">РїСЂРµРјРёСѓРј</option>
                <option value="false">Р±РµСЃРїР»Р°С‚РЅРѕ</option>
              </select>
              <select
                className="border rounded px-2 py-1"
                value={recommendable}
                onChange={(e) => {
                  setRecommendable(e.target.value as 'all' | 'true' | 'false');
                  setPage(0);
                }}
              >
                <option value="all">Р’СЃРµ</option>
                <option value="true">СЂРµРєРѕРјРµРЅРґСѓРµРјС‹Рµ</option>
                <option value="false">РЅРµ СЂРµРєРѕРјРµРЅРґСѓРµРјС‹Рµ</option>
              </select>
              <Button type="button" onClick={() => void refetch()}>
                РџРѕРёСЃРє
              </Button>

              <label className="ml-2 text-sm text-gray-600">
                РЅР° СЃС‚СЂР°РЅРёС†Рµ:
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
                    ? 'РџСЂРёРјРµРЅРµРЅРёРµвЂ¦'
                    : `РџСЂРёРјРµРЅРёС‚СЊ РёР·РјРµРЅРµРЅРёСЏ${changesCount > 0 ? ` (${changesCount})` : ''}`}
                </Button>
                <Button
                  type="button"
                  className="disabled:opacity-50"
                  disabled={changesCount === 0 || loading || applying}
                  onClick={discardChanges}
                >
                  РћС‚РјРµРЅРёС‚СЊ
                </Button>
                <Button
                  type="button"
                  className="bg-blue-600 text-white"
                  onClick={() => {
                    navigate(`/nodes/article/new`);
                  }}
                >
                  Р”РѕР±Р°РІРёС‚СЊ РЅРѕРґСѓ
                </Button>
              </div>
            </div>
            {selected.size > 0 && (
              <div className="flex flex-wrap gap-2">
                <span className="self-center text-sm">Р’С‹Р±СЂР°РЅРѕ {selected.size}</span>
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
                  РЎРєСЂС‹С‚СЊ
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
                  РџРѕРєР°Р·Р°С‚СЊ
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
                  РџСѓР±Р»РёС‡РЅРѕ
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
                  РџСЂРёРІР°С‚РЅРѕ
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
                  РџСЂРµРјРёСѓРј
                </Button>
                <Button
                  type="button"
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
                  Р‘РµСЃРїР»Р°С‚РЅРѕ
                </Button>
                <Button
                  type="button"
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
                  РџРµСЂРµРєР»СЋС‡РёС‚СЊ СЂРµРєРѕРјРµРЅРґРѕРІР°РЅРёРµ
                </Button>
                <Button type="button" className="ml-auto" onClick={() => setSelected(new Set())}>
                  РћС‡РёСЃС‚РёС‚СЊ
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {loading && <p>Р—Р°РіСЂСѓР·РєР°...</p>}
        {errorMsg && <p className="text-red-600">{errorMsg}</p>}

        {!loading && !errorMsg && (
          <>
            {!accountId && scopeMode === 'mine' && items.length === 0 ? (
              <div className="my-4 p-3 border rounded bg-yellow-50 text-sm text-gray-700 dark:bg-yellow-900/20 dark:text-gray-200">
                Р Р°Р·РґРµР» "РњРѕРё" РїСѓСЃС‚. РџРѕРєР°Р·Р°С‚СЊ РіР»РѕР±Р°Р»СЊРЅС‹Рµ РЅРѕРґС‹?
                <Button
                  type="button"
                  className="ml-2 px-2 py-1 border rounded"
                  onClick={() => {
                    setScopeMode('global');
                    const sp = new URLSearchParams(searchParams);
                    sp.set('scope', 'global');
                    setSearchParams(sp, { replace: true });
                  }}
                >
                  РџРµСЂРµРєР»СЋС‡РёС‚СЊ РЅР° Global
                </Button>
              </div>
            ) : null}
            <div className="overflow-x-auto">
              <Table className="min-w-full text-left">
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-8">
                      <input
                        type="checkbox"
                        checked={items.length > 0 && selected.size === items.length}
                        onChange={(e) =>
                          setSelected(
                            e.target.checked ? new Set(items.map((i) => i.id)) : new Set(),
                          )
                        }
                      />
                    </TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead>РќР°Р·РІР°РЅРёРµ</TableHead>
                    <TableHead className="w-32 text-center">РЎС‚Р°С‚СѓСЃ</TableHead>
                    <TableHead className="w-32 text-center">Р¤Р»Р°РіРё</TableHead>
                    <TableHead className="hidden md:table-cell">РЎРѕР·РґР°РЅРѕ</TableHead>
                    <TableHead className="hidden md:table-cell">РћР±РЅРѕРІР»РµРЅРѕ</TableHead>
                    <TableHead>Р”РµР№СЃС‚РІРёСЏ</TableHead>
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
                      <TableRow
                        key={n.id ?? i}
                        className={changed ? 'bg-amber-50 dark:bg-amber-900/20' : ''}
                      >
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
                            <div className="font-bold">{n.title?.trim() || 'Р‘РµР· РЅР°Р·РІР°РЅРёСЏ'}</div>
                            <div className="text-gray-500 text-xs font-mono">{n.slug ?? '-'}</div>
                            {n.space && (
                              <span
                                className="ml-2 text-xs rounded bg-blue-100 text-blue-800 px-1"
                                data-testid="space-badge"
                              >
                                space:{n.space}
                              </span>
                            )}
                            {n.slug && (
                              <Button
                                type="button"
                                className="absolute top-0 right-0 text-xs text-blue-600 opacity-0 group-hover:opacity-100 border-none px-1 py-0"
                                onClick={() => copySlug(n.slug ?? '')}
                              >
                                РљРѕРїРёСЂРѕРІР°С‚СЊ slug
                              </Button>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="w-32 text-center">
                          <StatusCell status={(n.status as NodeStatus | undefined) ?? 'draft'} />
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
                              navigate(`/nodes/${t}/${n.id}`);
                            }}
                          >
                            Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ
                          </Button>
                          <Button
                            type="button"
                            onClick={async () => {
                              if (!accountId) return;
                              try {
                                const { url } = await createPreviewLink();
                                const t = n.type || 'article';
                                window.open(`${url}/nodes/${t}/${n.id}`, '_blank');
                              } catch (e) {
                                addToast({
                                  title: 'РџСЂРµРґРїСЂРѕСЃРјРѕС‚СЂ РЅРµ РѕС‚РєСЂС‹Р»СЃСЏ',
                                  description: e instanceof Error ? e.message : String(e),
                                  variant: 'error',
                                });
                              }
                            }}
                          >
                            РџСЂРµРґРїСЂРѕСЃРјРѕС‚СЂ
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  {items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="p-4 text-center text-gray-500">
                        РќРѕРґС‹ РЅРµ РЅР°Р№РґРµРЅС‹
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
                РќР°Р·Р°Рґ
              </Button>
              <span className="text-sm">РЎС‚СЂР°РЅРёС†Р° {page + 1}</span>
              <Button type="button" disabled={!hasMore} onClick={() => setPage((p) => p + 1)}>
                Р’РїРµСЂРµРґ
              </Button>
            </div>
          </>
        )}

        {/* Moderation modal: hide with reason */}
        {modOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded bg-white p-4 shadow dark:bg-gray-900">
              <h3 className="mb-3 text-lg font-semibold">РЎРєСЂС‹С‚СЊ РЅРѕРґСѓ</h3>
              <p className="mb-2 text-sm text-gray-600">
                РЈРєР°Р¶РёС‚Рµ РїСЂРёС‡РёРЅСѓ СЃРєСЂС‹С‚РёСЏ СЌС‚РѕР№ РЅРѕРґС‹. Р”РµР№СЃС‚РІРёРµ Р±СѓРґРµС‚ Р·Р°РїРёСЃР°РЅРѕ РІ Р°СѓРґРёС‚.
              </p>
              <input
                className="mb-3 w-full rounded border px-2 py-1"
                placeholder="РџСЂРёС‡РёРЅР° (РЅРµРѕР±СЏР·Р°С‚РµР»СЊРЅРѕ)"
                value={modReason}
                onChange={(e) => setModReason(e.target.value)}
                disabled={modBusy}
              />
              <div className="flex justify-end gap-2">
                <Button type="button" onClick={() => setModOpen(false)} disabled={modBusy}>
                  РћС‚РјРµРЅР°
                </Button>
                <Button
                  type="button"
                  className="bg-gray-800 text-white disabled:opacity-50"
                  onClick={submitModerationHide}
                  disabled={modBusy}
                >
                  {modBusy ? 'РЎРєСЂС‹С‚РёРµвЂ¦' : 'РЎРєСЂС‹С‚СЊ'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

