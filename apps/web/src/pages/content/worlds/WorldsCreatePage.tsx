import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ContentLayout } from '../ContentLayout';
import { Card, Input as TInput, Textarea, Button } from '@ui';
import { apiGet, apiPost, apiPatch } from '../../../shared/api/client';

export default function WorldsCreatePage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const worldId = params.get('id');
  const [title, setTitle] = React.useState('');
  const [locale, setLocale] = React.useState('ru-RU');
  const [description, setDescription] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [created, setCreated] = React.useState<any | null>(null);
  const mode: 'create' | 'edit' = worldId ? 'edit' : 'create';

  React.useEffect(() => {
    if (mode === 'edit' && worldId) {
      (async () => {
        setError(null);
        try {
          const data = await apiGet(`/v1/admin/worlds/${encodeURIComponent(worldId)}`);
          setTitle(String(data?.title || ''));
          setLocale(String(data?.locale || ''));
          setDescription(String(data?.description || ''));
        } catch (e: any) {
          setError(String(e?.message || e));
        }
      })();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [worldId]);

  async function createWorld() {
    setBusy(true);
    setError(null);
    setCreated(null);
    try {
      const body: any = { title: title.trim(), locale: locale.trim() || undefined, description: description.trim() || undefined };
      if (!body.title) throw new Error('Введите название');
      const data = await apiPost(`/v1/admin/worlds`, body);
      setCreated(data);
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function saveWorld() {
    setBusy(true);
    setError(null);
    try {
      if (!worldId) throw new Error('world_id отсутствует');
      const body: any = { title: title.trim() || undefined, locale: locale.trim() || undefined, description: description.trim() || undefined };
      await apiPatch(`/v1/admin/worlds/${encodeURIComponent(worldId)}`, body);
      navigate('/quests/worlds');
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <ContentLayout context="quests"
      title={mode === 'edit' ? 'Update world' : 'Create world'}
      description="Define narrative settings and supporting lore for Flavour Trip."
      actions={(
        <Button variant="outlined" onClick={() => navigate('/quests/worlds')}>
          Back to worlds
        </Button>
      )}
    >
      <Card className="p-4">
        <h2 className="mb-3 text-base font-semibold">{mode==='edit'?'Edit World':'Create World'}</h2>
        {error && <div className="mb-2 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}
        <div className="grid gap-3 sm:grid-cols-2">
          <TInput label="Locale" placeholder="ru-RU" value={locale} onChange={(e: any) => setLocale(e.target.value)} />
          <TInput label="Title" placeholder="World title" value={title} onChange={(e: any) => setTitle(e.target.value)} className="sm:col-span-2" />
          <Textarea label="Description" placeholder="Optional description" value={description} onChange={(e: any) => setDescription(e.target.value)} className="sm:col-span-2" />
        </div>
        <div className="mt-3">
          {mode==='edit' ? (
            <Button className="btn-base btn bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-60" disabled={busy} onClick={saveWorld}>
              {busy ? 'Saving…' : 'Save'}
            </Button>
          ) : (
            <Button className="btn-base btn bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-60" disabled={busy} onClick={createWorld}>
              {busy ? 'Creating…' : 'Create'}
            </Button>
          )}
        </div>
        {created && <div className="mt-2 text-sm text-gray-700">World created: id={created.id}</div>}
      </Card>
    </ContentLayout>
  );
}
