import React from 'react';
import { Link } from 'react-router-dom';
import { ContentLayout } from '../ContentLayout';
import { Card, Table, Pagination, Skeleton, Spinner, Input as TInput, Textarea, Button } from '@ui';
import { apiGet, apiPost, apiPatch, apiDelete } from '../../../shared/api/client';

type World = { id: string; title: string; locale?: string; description?: string };
type Character = { id: string; name: string; role?: string };

export default function WorldsPage() {
  const [worlds, setWorlds] = React.useState<World[]>([]);
  const [selected, setSelected] = React.useState<string>('');
  const [chars, setChars] = React.useState<Character[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);
  const [hasNext, setHasNext] = React.useState(false);
  const [q, setQ] = React.useState('');
  const [editing, setEditing] = React.useState<World | null>(null);
  const [newCharName, setNewCharName] = React.useState('');
  const [newCharRole, setNewCharRole] = React.useState('');

  const headerStats = React.useMemo(() => [
    { label: 'Worlds', value: worlds.length.toLocaleString() },
    { label: 'Characters in view', value: chars.length.toLocaleString() },
  ], [worlds.length, chars.length]);

  function filteredWorlds() {
    const f = (worlds || []).filter((w) => (q ? (w.title || '').toLowerCase().includes(q.toLowerCase()) : true));
    return f;
  }

  async function loadWorlds() {
    setError(null);
    setLoading(true);
    try {
      const data = await apiGet(`/v1/admin/worlds`);
      const arr = Array.isArray(data) ? data : [];
      setWorlds(arr);
      setSelected('');
      setChars([]);
      const total = arr.length;
      const offset = (page - 1) * pageSize;
      setHasNext(offset + pageSize < total);
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  async function loadChars(id: string) {
    setError(null);
    setSelected(id);
    setChars([]);
    try {
      const data = await apiGet(`/v1/admin/worlds/${encodeURIComponent(id)}/characters`);
      setChars(Array.isArray(data) ? data : []);
      const world = worlds.find((w) => w.id === id) || null;
      setEditing(world || null);
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  }

  React.useEffect(() => {
    void loadWorlds();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize]);

  const list = filteredWorlds();
  const pageWorlds = list.slice((page - 1) * pageSize, (page - 1) * pageSize + pageSize);

  return (
    <ContentLayout context="quests"
      title="World templates"
      description="Design playable universes and supporting casts for creative AI tools."
      stats={headerStats}
      actions={(
        <Link to="/quests/worlds/new">
          <Button>New world</Button>
        </Link>
      )}
    >
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-4">
          <div className="mb-2 flex items-center gap-2">
            <input className="form-input-base form-input w-56" placeholder="Search world..." value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
            <button className="btn-base btn bg-gray-150 text-gray-900 hover:bg-gray-200" onClick={loadWorlds}>Reload</button>
          </div>
          {error && <div className="mb-2 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}
          {loading && (
            <div className="my-2">
              <Spinner size="sm" />
            </div>
          )}
          <div className="border rounded">
            <Table.Table hover zebra>
              <Table.THead>
                <Table.TR>
                  <Table.TH>Title</Table.TH>
                  <Table.TH>Locale</Table.TH>
                  <Table.TH className="text-right">Actions</Table.TH>
                </Table.TR>
              </Table.THead>
              <Table.TBody>
                {loading &&
                  Array.from({ length: 6 }).map((_, i) => (
                    <Table.TR key={`sk-${i}`}>
                      <Table.TD>
                        <Skeleton className="h-4 w-40" />
                      </Table.TD>
                      <Table.TD>
                        <Skeleton className="h-4 w-20" />
                      </Table.TD>
                      <Table.TD />
                    </Table.TR>
                  ))}
                {!loading &&
                  pageWorlds.map((w) => (
                    <Table.TR key={w.id} className="hover:bg-gray-50">
                      <Table.TD className="cursor-pointer" onClick={() => loadChars(String(w.id))}>{w.title}</Table.TD>
                      <Table.TD>{w.locale || '-'}</Table.TD>
                      <Table.TD className="text-right">
                        <button className="btn-base btn h-7 bg-gray-100 px-2 text-xs hover:bg-gray-200" onClick={() => { setEditing(w); setSelected(w.id); }}>
                          Edit
                        </button>
                        <button
                          className="btn-base btn h-7 bg-red-600 px-2 text-xs text-white hover:bg-red-700 ml-2"
                          onClick={async () => {
                            if (!confirm(`Delete world “${w.title}”?`)) return;
                            try {
                              await apiDelete(`/v1/admin/worlds/${encodeURIComponent(w.id)}`);
                              await loadWorlds();
                            } catch {}
                          }}
                        >
                          Delete
                        </button>
                      </Table.TD>
                    </Table.TR>
                  ))}
                {!loading && list.length === 0 && (
                  <Table.TR>
                    <Table.TD className="py-6 text-center text-sm text-gray-500">No worlds yet</Table.TD>
                    <Table.TD />
                    <Table.TD />
                  </Table.TR>
                )}
              </Table.TBody>
            </Table.Table>
          </div>
          <div className="mt-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">Rows per page</span>
              <select className="form-select h-8 w-20" value={String(pageSize)} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
                {[10, 20, 30, 40, 50].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
              <span className="text-gray-500">items</span>
            </div>
            <Pagination page={page} total={hasNext ? page + 1 : page} onChange={setPage} />
            <div className="text-sm text-gray-500">{Math.min((page - 1) * pageSize + 1, list.length)}-{Math.min(page * pageSize, list.length)} of {list.length}</div>
          </div>
        </Card>
        <Card className="p-4">
          <h2 className="mb-3 text-base font-semibold">{selected ? `World details` : 'Select a world'}</h2>
          {editing && (
            <div className="mb-4 grid gap-2">
              <TInput label="Title" value={editing.title} onChange={(e: any) => setEditing({ ...editing, title: e.target.value })} />
              <TInput label="Locale" value={editing.locale || ''} onChange={(e: any) => setEditing({ ...editing, locale: e.target.value })} />
              <Textarea label="Description" value={editing.description || ''} onChange={(e: any) => setEditing({ ...editing, description: e.target.value })} />
              <div>
                <Button
                  onClick={async () => {
                    if (!editing) return;
                    try {
                      await apiPatch(`/v1/admin/worlds/${encodeURIComponent(editing.id)}` , {
                        title: editing.title,
                        locale: editing.locale,
                        description: editing.description,
                      });
                      await loadWorlds();
                    } catch {}
                  }}
                >
                  Save
                </Button>
              </div>
            </div>
          )}
          <div className="rounded border">
            <Table.Table>
              <Table.THead>
                <Table.TR>
                  <Table.TH>Name</Table.TH>
                  <Table.TH>Role</Table.TH>
                  <Table.TH className="text-right">Actions</Table.TH>
                </Table.TR>
              </Table.THead>
              <Table.TBody>
                {chars.map((c) => (
                  <Table.TR key={c.id}>
                    <Table.TD>{c.name}</Table.TD>
                    <Table.TD>{c.role || '-'}</Table.TD>
                    <Table.TD className="text-right">
                      <button
                        className="btn-base btn h-7 bg-red-600 px-2 text-xs text-white hover:bg-red-700"
                        onClick={async () => {
                          try {
                            await apiDelete(`/v1/admin/worlds/characters/${encodeURIComponent(c.id)}`);
                            await loadChars(selected);
                          } catch {}
                        }}
                      >
                        Delete
                      </button>
                    </Table.TD>
                  </Table.TR>
                ))}
                {selected && chars.length === 0 && (
                  <Table.TR>
                    <Table.TD className="py-6 text-center text-sm text-gray-500">No characters</Table.TD>
                    <Table.TD />
                    <Table.TD />
                  </Table.TR>
                )}
                {!selected && (
                  <Table.TR>
                    <Table.TD className="py-6 text-center text-sm text-gray-500">Select a world to manage characters</Table.TD>
                    <Table.TD />
                    <Table.TD />
                  </Table.TR>
                )}
              </Table.TBody>
            </Table.Table>
          </div>
          {selected && (
            <div className="mt-3 grid grid-cols-3 gap-2">
              <TInput label="Character name" value={newCharName} onChange={(e: any) => setNewCharName(e.target.value)} />
              <TInput label="Role" value={newCharRole} onChange={(e: any) => setNewCharRole(e.target.value)} />
              <div className="flex items-end">
                <Button
                  disabled={!newCharName.trim()}
                  onClick={async () => {
                    try {
                      await apiPost(`/v1/admin/worlds/${encodeURIComponent(selected)}/characters`, {
                        name: newCharName.trim(),
                        role: newCharRole.trim() || undefined,
                      });
                      setNewCharName('');
                      setNewCharRole('');
                      await loadChars(selected);
                    } catch {}
                  }}
                >
                  Add character
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </ContentLayout>
  );
}








