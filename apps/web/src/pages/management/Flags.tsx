import React from 'react';
import { Button, Card, Input, Spinner, Table } from '@ui';
import { apiDelete, apiGet, apiPost } from '../../shared/api/client';

export default function ManagementFlags() {
  const [items, setItems] = React.useState<any[]>([]);
  const [slug, setSlug] = React.useState('');
  const [desc, setDesc] = React.useState('');
  const [enabled, setEnabled] = React.useState(true);
  const [rollout, setRollout] = React.useState<number>(100);
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(async () => {
    const r = await apiGet<{ items: any[] }>('/v1/flags');
    setItems(r?.items || []);
  }, []);
  React.useEffect(() => { void load(); }, [load]);

  const onSave = async () => {
    setBusy(true);
    try {
      await apiPost('/v1/flags', { slug, description: desc || undefined, enabled, rollout });
      setSlug(''); setDesc(''); setEnabled(true); setRollout(100);
      void load();
    } finally { setBusy(false); }
  };

  const onDelete = async (s: string) => {
    await apiDelete(`/v1/flags/${encodeURIComponent(s)}`);
    void load();
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <div className="p-4 space-y-2">
          <div className="text-sm font-medium">Create/Update Flag</div>
          <div className="grid grid-cols-4 gap-2">
            <Input placeholder="slug" value={slug} onChange={(e) => setSlug(e.target.value)} />
            <Input placeholder="description" value={desc} onChange={(e) => setDesc(e.target.value)} />
            <Input placeholder="enabled (true/false)" value={String(enabled)} onChange={(e) => setEnabled(String(e.target.value).toLowerCase() !== 'false')} />
            <Input placeholder="rollout 0..100" type="number" value={rollout} onChange={(e) => setRollout(parseInt(e.target.value || '0', 10))} />
          </div>
          <div className="flex gap-2">
            <Button onClick={onSave} disabled={!slug || busy}>Save</Button>
            {busy && <Spinner />}
          </div>
        </div>
      </Card>
      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Flags</div>
          <Table.Table>
            <Table.THead>
              <Table.TR>
                <Table.TH>Slug</Table.TH>
                <Table.TH>Desc</Table.TH>
                <Table.TH>Enabled</Table.TH>
                <Table.TH>Rollout</Table.TH>
                <Table.TH>Actions</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {(items || []).map((f) => (
                <Table.TR key={f.slug}>
                  <Table.TD>{f.slug}</Table.TD>
                  <Table.TD>{f.description || '-'}</Table.TD>
                  <Table.TD>{String(f.enabled)}</Table.TD>
                  <Table.TD>{f.rollout}</Table.TD>
                  <Table.TD>
                    <Button onClick={() => onDelete(f.slug)}>Delete</Button>
                  </Table.TD>
                </Table.TR>
              ))}
            </Table.TBody>
          </Table.Table>
        </div>
      </Card>
    </div>
  );
}

