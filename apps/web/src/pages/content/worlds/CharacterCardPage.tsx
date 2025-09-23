import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ContentLayout } from '../ContentLayout';
import { Card, Input as TInput, Textarea, Button } from '@ui';
import { apiGet, apiPost, apiPatch } from '../../../shared/api/client';

export default function CharacterCardPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const charId = params.get('id');
  const worldId = params.get('world_id');
  const [name, setName] = React.useState('');
  const [role, setRole] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const mode: 'create' | 'edit' = charId ? 'edit' : 'create';

  React.useEffect(() => {
    if (mode === 'edit' && charId) {
      (async () => {
        setError(null);
        try {
          const data = await apiGet(`/v1/admin/worlds/characters/${encodeURIComponent(charId)}`);
          setName(String(data?.name || ''));
          setRole(String(data?.role || ''));
          setDescription(String(data?.description || ''));
        } catch (e: any) {
          setError(String(e?.message || e));
        }
      })();
    }
  }, [charId]);

  async function save() {
    setBusy(true);
    setError(null);
    try {
      if (mode === 'edit' && charId) {
        await apiPatch(`/v1/admin/worlds/characters/${encodeURIComponent(charId)}` , {
          name: name.trim() || undefined,
          role: role.trim() || undefined,
          description: description.trim() || undefined,
        });
      } else {
        if (!worldId) throw new Error('world_id обязателен');
        await apiPost(`/v1/admin/worlds/${encodeURIComponent(worldId)}/characters`, {
          name: name.trim(),
          role: role.trim() || undefined,
          description: description.trim() || undefined,
        });
      }
      navigate('/quests/worlds');
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function createChar() {
    if (!worldId) { setError('Укажите world_id'); return; }
    setBusy(true);
    setError(null);
    try {
      await apiPost(`/v1/admin/worlds/${encodeURIComponent(worldId)}/characters`, {
        name: name.trim(),
        role: role.trim() || undefined,
        description: description.trim() || undefined,
      });
      navigate('/quests/worlds');
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <ContentLayout context="quests">
      <Card className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-800 dark:text-dark-100">{mode === 'edit' ? 'Edit Character' : 'Create Character'}</h2>
          <Button variant="outlined" onClick={() => navigate('/quests/worlds')}>Back</Button>
        </div>
        {error && <div className="mb-2 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}
        <div className="grid gap-3 sm:grid-cols-2">
          {mode === 'create' && (
            <TInput label="World ID" placeholder="UUID world" value={worldId || ''} readOnly />
          )}
          <TInput label="Name" value={name} onChange={(e: any) => setName(e.target.value)} />
          <TInput label="Role" value={role} onChange={(e: any) => setRole(e.target.value)} />
          <Textarea label="Description" value={description} onChange={(e: any) => setDescription(e.target.value)} className="sm:col-span-2" />
        </div>
        <div className="mt-3">
          {mode === 'edit' ? (
            <Button disabled={busy || !name.trim()} onClick={save}>{busy ? 'Saving…' : 'Save'}</Button>
          ) : (
            <Button disabled={busy || !name.trim() || !worldId} onClick={createChar}>{busy ? 'Creating…' : 'Create'}</Button>
          )}
        </div>
      </Card>
    </ContentLayout>
  );
}

