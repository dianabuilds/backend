import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ContentLayout } from '../ContentLayout';
import { apiGet, apiPost } from '../../../shared/api/client';
import { formatDateTime } from '../../../shared/utils/format';
import { Card, Input as TInput, Textarea, Switch, Badge, Spinner, Skeleton, Pagination, Table } from '@ui';

type Quest = { id: string; title: string; slug?: string; is_public?: boolean; status?: string; updated_at?: string };

type QuestStatus = 'all' | 'draft' | 'published';

const QUEST_STATUS_OPTIONS: Array<{ value: QuestStatus; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'draft', label: 'Draft' },
  { value: 'published', label: 'Published' },
];

const mock: Quest[] = Array.from({ length: 12 }).map((_, i) => ({ id: String(i + 1), title: `РљРІРµСЃС‚ ${i + 1}`, slug: `quest-${i + 1}`, is_public: i % 2 === 0, updated_at: new Date(Date.now() - i * 864e5).toISOString() }));

export default function QuestsPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [items, setItems] = React.useState<Quest[]>([]);
  const [status, setStatus] = React.useState<QuestStatus>('all');
  const [q, setQ] = React.useState('');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [createOpen, setCreateOpen] = React.useState<boolean>(params.get('create') === '1');
  const isDraftFilter = status === 'draft';
  const hasCustomStatus = status !== 'all';
  React.useEffect(() => { if (params.get('create') === '1') setCreateOpen(true); }, [params]);

  React.useEffect(() => {
    const preset = params.get('status');
    if (preset && (preset === 'draft' || preset === 'published' || preset === 'all') && preset !== status) {
      setStatus(preset as QuestStatus);
      setPage(1);
    }
  }, [params, status]);

  const load = React.useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const offset = (page - 1) * pageSize;
      const statusParam = status === 'all' ? '' : `&status=${encodeURIComponent(status)}`;
      let data: any = null;
      try {
        data = await apiGet(`/v1/quests?limit=${pageSize}&offset=${offset}&q=${encodeURIComponent(q)}${statusParam}`);
      } catch {
        try {
          data = await apiGet(`/v1/admin/quests/list?limit=${pageSize}&offset=${offset}&q=${encodeURIComponent(q)}${statusParam}`);
        } catch {}
      }
      if (Array.isArray(data)) {
        let list = data as Quest[];
        if (status !== 'all') {
          list = list.filter((item) => {
            const s = (item.status || '').toLowerCase();
            if (status === 'published') return s === 'published' || item.is_public === true;
            if (status === 'draft') return s === 'draft' || item.is_public === false;
            return true;
          });
        }
        setItems(list);
        setHasNext(list.length === pageSize);
      } else {
        const filtered = mock.filter((n) => n.title.toLowerCase().includes(q.toLowerCase()));
        let slice = filtered.slice(offset, offset + pageSize);
        if (status !== 'all') {
          slice = slice.filter((item) => {
            const s = (item.status || '').toLowerCase();
            if (status === 'published') return s === 'published' || item.is_public === true;
            if (status === 'draft') return s === 'draft' || item.is_public === false;
            return true;
          });
        }
        setItems(slice);
        setHasNext(offset + pageSize < filtered.length);
      }
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally { setLoading(false); }
  }, [page, pageSize, q, status]);

  React.useEffect(() => {
    const t = setTimeout(() => { void load(); }, 200);
    return () => clearTimeout(t);
  }, [load]);

  const applyStatus = React.useCallback((value: QuestStatus) => {
    setStatus(value);
    setPage(1);
    if (value === 'all') params.delete('status');
    else params.set('status', value);
    setParams(params, { replace: true });
  }, [params, setParams]);

  // Create form state
  const [title, setTitle] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [tags, setTags] = React.useState('');
  const [isPublic, setIsPublic] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [created, setCreated] = React.useState<{ id: string; slug?: string } | null>(null);

  async function createQuest() {
    setBusy(true); setError(null); setCreated(null);
    try {
      const payload = {
        title: title.trim(),
        description: description.trim() || undefined,
        tags: tags.split(',').map((s) => s.trim()).filter(Boolean),
        is_public: isPublic,
      };
      if (!payload.title) throw new Error('РЈРєР°Р¶РёС‚Рµ РЅР°Р·РІР°РЅРёРµ');
      const res = await apiPost('/v1/quests', payload);
      setCreated(res);
      setTitle(''); setDescription(''); setTags(''); setIsPublic(false);
      setCreateOpen(false);
      void load();
      params.delete('create'); setParams(params, { replace: true });
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally { setBusy(false); }
  }

  function closeCreate() { setCreateOpen(false); params.delete('create'); setParams(params, { replace: true }); }

  return (
    <ContentLayout context="quests">
      {/* Header actions specific to page */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <TInput className="w-80" placeholder="Search quests" value={q} onChange={(e:any)=>{ setQ(e.target.value); setPage(1); }} />
            {loading && <Spinner size="sm" />}
          </div>
          <div className="flex items-center gap-2">
            <button
              className="btn-base btn bg-primary-600 text-white hover:bg-primary-700"
              onClick={() => navigate('/quests/new')}
            >
              Search quests'?? ???????'
            </button>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-1.5 dark:border-dark-500 dark:bg-dark-700">
            <span className="text-xs text-gray-500">Status</span>
            <select className="form-select h-8 w-36 text-xs" value={status} onChange={(e) => applyStatus(e.target.value as QuestStatus)}>
              {QUEST_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <button
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${isDraftFilter ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-600/60 dark:bg-primary-900/30 dark:text-primary-300' : 'border-gray-300 text-gray-600 hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60'}`}
            onClick={() => applyStatus('draft')}
          >
            Drafts only
          </button>
          {hasCustomStatus && (
            <button
              className="rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60"
              onClick={() => applyStatus('all')}
            >
              Clear filter
            </button>
          )}
          <button
            className="rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60"
            onClick={() => navigate('/tools/import-export?scope=quests')}
          >
            Import / export
          </button>
          <button
            className="rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60"
            onClick={() => navigate('/notifications?compose=quests')}
          >
            Announce update
          </button>
        </div>
      </div>

{/* Create panel */}
      {createOpen && (
        <Card className="p-4 mt-3">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-base font-semibold">РЎРѕР·РґР°С‚СЊ РєРІРµСЃС‚</h2>
            <button className="btn-base btn bg-gray-150 text-gray-900 hover:bg-gray-200" onClick={closeCreate}>Р—Р°РєСЂС‹С‚СЊ</button>
          </div>
          {error && <div className="mb-2 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}
          <div className="grid gap-3 sm:grid-cols-2">
            <TInput label="РќР°Р·РІР°РЅРёРµ" placeholder="Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ" value={title} onChange={(e: any) => setTitle(e.target.value)} className="sm:col-span-2" />
            <Textarea label="РћРїРёСЃР°РЅРёРµ" placeholder="РљСЂР°С‚РєРѕРµ РѕРїРёСЃР°РЅРёРµ" value={description} onChange={(e: any) => setDescription(e.target.value)} className="sm:col-span-2" />
            <TInput label="РўРµРіРё (С‡РµСЂРµР· Р·Р°РїСЏС‚СѓСЋ)" placeholder="story, ai, demo" value={tags} onChange={(e: any) => setTags(e.target.value)} className="sm:col-span-2" />
            <div className="sm:col-span-2 flex items-center gap-3">
              <Switch checked={isPublic} onChange={(e: any) => setIsPublic(e.currentTarget.checked)} />
              <span className="text-sm">РћРїСѓР±Р»РёРєРѕРІР°С‚СЊ</span>
            </div>
            <div className="sm:col-span-2">
              <button className="btn-base btn bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-60" disabled={busy} onClick={createQuest}>{busy ? 'РЎРѕС…СЂР°РЅРµРЅРёРµвЂ¦' : 'РЎРѕР·РґР°С‚СЊ'}</button>
              {created && (<span className="ml-3 text-sm text-gray-700">РЎРѕР·РґР°РЅРѕ: id={created.id}{created.slug ? `, slug=${created.slug}` : ''}</span>)}
            </div>
          </div>
        </Card>
      )}

      {/* List */}
      <Card className="mt-3">
        <div className="hide-scrollbar overflow-x-auto">
          <Table.Table hover className="min-w-[720px] w-full">
            <Table.THead>
              <Table.TR>
                <Table.TH className="bg-gray-200 text-gray-800 uppercase py-3 px-4">РќР°Р·РІР°РЅРёРµ</Table.TH>
                <Table.TH className="bg-gray-200 text-gray-800 uppercase py-3 px-4">Slug</Table.TH>
                <Table.TH className="bg-gray-200 text-gray-800 uppercase py-3 px-4">РЎС‚Р°С‚СѓСЃ</Table.TH>
                <Table.TH className="bg-gray-200 text-gray-800 uppercase py-3 px-4">РћР±РЅРѕРІР»РµРЅРѕ</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {loading && Array.from({ length: 6 }).map((_, i) => (
                <Table.TR key={`sk-${i}`} className="dark:border-b-dark-500 border-b border-gray-200">
                  <Table.TD className="py-2 px-4"><Skeleton className="h-4 w-48" /></Table.TD>
                  <Table.TD className="py-2 px-4"><Skeleton className="h-4 w-28" /></Table.TD>
                  <Table.TD className="py-2 px-4"><Skeleton className="h-4 w-20" /></Table.TD>
                  <Table.TD className="py-2 px-4"><Skeleton className="h-4 w-24" /></Table.TD>
                </Table.TR>
              ))}
              {!loading && items.map((q) => (
                <Table.TR key={q.id} className="dark:border-b-dark-500 border-b border-gray-200">
                  <Table.TD className="py-2 px-4 font-medium text-gray-800 dark:text-dark-100">{q.title}</Table.TD>
                  <Table.TD className="py-2 px-4 text-gray-600">{q.slug || 'вЂ”'}</Table.TD>
                  <Table.TD className="py-2 px-4">
                    <Badge color={q.is_public || (q.status||'').toLowerCase()==='published' ? 'success' : 'warning'}>
                      {q.is_public || (q.status||'').toLowerCase()==='published' ? 'РћРїСѓР±Р»РёРєРѕРІР°РЅРѕ' : 'Р§РµСЂРЅРѕРІРёРє'}
                    </Badge>
                  </Table.TD>
                  <Table.TD className="py-2 px-4 text-gray-500">{formatDateTime(q.updated_at)}</Table.TD>
                </Table.TR>
              ))}
            </Table.TBody>
          </Table.Table>
        </div>
        <div className="mt-4 flex items-center justify-between p-4 pt-2">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">РџРѕРєР°Р·Р°С‚СЊ</span>
            <select className="form-select h-8 w-20" value={String(pageSize)} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
              {[10,20,30,40,50,100].map((n) => (<option key={n} value={n}>{n}</option>))}
            </select>
            <span className="text-gray-500">Р·Р°РїРёСЃРµР№</span>
          </div>
          <Pagination page={page} total={hasNext ? page + 1 : page} onChange={setPage} />
          <div className="text-sm text-gray-500">{(page-1)*pageSize + (items.length?1:0)}вЂ“{(page-1)*pageSize + items.length} Р·Р°РїРёСЃРµР№</div>
        </div>
      </Card>
    </ContentLayout>
  );
}



