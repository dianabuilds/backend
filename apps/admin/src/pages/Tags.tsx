import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  addToBlacklist,
  type BlacklistItem,
  createAdminTag,
  deleteAdminTag,
  getBlacklist,
  listAdminTags,
  removeFromBlacklist,
} from '../api/tags';
import DataTable from '../components/DataTable';
import type { Column } from '../components/DataTable.helpers';
import { Card, CardContent } from '../components/ui/card';
import { useModal, usePaginatedList } from '../shared/hooks';
import { Button, Modal, SearchBar, TextInput } from '../shared/ui';
import { confirmWithEnv } from '../utils/env';
import PageLayout from './_shared/PageLayout';

type TagItem = {
  id?: string;
  slug?: string;
  name?: string;
  usage_count?: number;
  aliases_count?: number;
  created_at?: string;
};

export default function Tags() {
  const [q, setQ] = useState('');

  const {
    items,
    loading,
    error,
    limit,
    setLimit,
    nextPage,
    prevPage,
    hasPrev,
    hasNext,
    reset,
    reload,
  } = usePaginatedList<TagItem>((params) => listAdminTags({ ...params, q }));

  const navigate = useNavigate();

  const createModal = useModal();
  const [newSlug, setNewSlug] = useState('');
  const [newName, setNewName] = useState('');

  const handleSearch = async () => {
    reset();
    await reload();
  };

  const [blItems, setBlItems] = useState<BlacklistItem[]>([]);
  const [blSlug, setBlSlug] = useState('');
  const [blReason, setBlReason] = useState('');

  const loadBlacklist = async () => {
    try {
      const rows = await getBlacklist();
      setBlItems(rows);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    void loadBlacklist();
  }, []);

  return (
    <PageLayout
      title="Tags"
      actions={
        <div className="flex gap-2">
          <Button onClick={() => navigate('/tags/merge')}>Merge…</Button>
          <Button onClick={createModal.open}>New tag</Button>
        </div>
      }
    >
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <SearchBar
          value={q}
          onChange={setQ}
          onSearch={handleSearch}
          placeholder="Search by tag name..."
        />
        <div className="ml-auto flex items-center gap-2">
          <label className="text-sm text-gray-600">Page size</label>
          <TextInput
            type="number"
            min={1}
            max={1000}
            value={limit}
            onChange={(e) => setLimit(Math.max(1, Math.min(1000, Number(e.target.value) || 1)))}
            className="w-20"
          />
        </div>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <>
          <Card className="mb-6">
            <CardContent className="p-0">
              {(() => {
                const columns: Column<TagItem>[] = [
                  { key: 'id', title: 'ID', accessor: (r) => r.id || '—', className: 'font-mono' },
                  { key: 'name', title: 'Name', accessor: (r) => r.name || r.slug || '—' },
                  {
                    key: 'aliases',
                    title: 'Aliases',
                    accessor: (r) =>
                      typeof r.aliases_count === 'number' ? String(r.aliases_count) : '—',
                  },
                  {
                    key: 'usage',
                    title: 'Usage',
                    accessor: (r) =>
                      typeof r.usage_count === 'number' ? String(r.usage_count) : '—',
                  },
                  {
                    key: 'created',
                    title: 'Created',
                    accessor: (r) => (r.created_at ? new Date(r.created_at).toLocaleString() : '—'),
                  },
                  {
                    key: 'actions',
                    title: 'Actions',
                    className: 'text-right',
                    render: (row) => (
                      <Button
                        className="text-red-600 border-red-300"
                        onClick={async () => {
                          const t = row as TagItem;
                          if (!t.id) return;
                          const ok = await confirmWithEnv(
                            `Delete tag "${t.name || t.slug}"? This cannot be undone.`,
                          );
                          if (!ok) return;
                          try {
                            await deleteAdminTag(t.id);
                            await reload();
                          } catch {
                            // ignore
                          }
                        }}
                      >
                        Delete
                      </Button>
                    ),
                  },
                ];
                return (
                  <DataTable
                    columns={columns}
                    rows={items}
                    rowKey={(r) => String(r.id || r.slug || Math.random())}
                    emptyText="No tags found"
                  />
                );
              })()}
              <div className="flex justify-end gap-2 border-t p-4">
                <Button disabled={!hasPrev} onClick={prevPage} title="Previous page">
                  ‹ Prev
                </Button>
                <Button disabled={!hasNext} onClick={nextPage} title="Next page">
                  Next ›
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <h2 className="mb-2 font-semibold">Blacklist</h2>
              <div className="mb-3 flex items-center gap-2">
                <TextInput
                  placeholder="tag slug…"
                  value={blSlug}
                  onChange={(e) => setBlSlug(e.target.value)}
                />
                <TextInput
                  className="w-64"
                  placeholder="reason (optional)"
                  value={blReason}
                  onChange={(e) => setBlReason(e.target.value)}
                />
                <Button
                  className="bg-gray-200 dark:bg-gray-800"
                  onClick={async () => {
                    if (!blSlug.trim()) return;
                    await addToBlacklist(blSlug.trim(), blReason.trim() || undefined);
                    setBlSlug('');
                    setBlReason('');
                    await loadBlacklist();
                  }}
                >
                  Add
                </Button>
              </div>
              {(() => {
                const columns: Column<BlacklistItem>[] = [
                  { key: 'slug', title: 'Slug', accessor: (r) => r.slug, className: 'font-mono' },
                  { key: 'reason', title: 'Reason', accessor: (r) => r.reason || '—' },
                  {
                    key: 'created',
                    title: 'Created',
                    accessor: (r) => new Date(r.created_at).toLocaleString(),
                  },
                  {
                    key: 'actions',
                    title: '',
                    render: (r) => (
                      <Button
                        className="text-red-600 border-red-300"
                        onClick={async () => {
                          await removeFromBlacklist(r.slug);
                          await loadBlacklist();
                        }}
                      >
                        Delete
                      </Button>
                    ),
                  },
                ];
                return (
                  <DataTable
                    columns={columns}
                    rows={blItems}
                    rowKey={(r) => r.slug}
                    emptyText="No blacklist entries"
                  />
                );
              })()}
            </CardContent>
          </Card>
        </>
      )}

      <Modal isOpen={createModal.isOpen} onClose={createModal.close} title="Create tag">
        <div className="flex flex-wrap items-center gap-2">
          <TextInput
            placeholder="slug"
            value={newSlug}
            onChange={(e) => setNewSlug(e.target.value)}
          />
          <TextInput
            className="w-64"
            placeholder="name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <Button
            className="bg-gray-200 dark:bg-gray-800"
            onClick={async () => {
              const slug = newSlug.trim();
              const name = newName.trim();
              if (!slug || !name) return;
              try {
                await createAdminTag(slug, name);
                setNewSlug('');
                setNewName('');
                createModal.close();
                reset();
                await reload();
              } catch {
                // ignore error here; overall error state
              }
            }}
          >
            Create
          </Button>
        </div>
      </Modal>
    </PageLayout>
  );
}
