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
import { Card, CardContent } from '../components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
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
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Aliases</TableHead>
                    <TableHead>Usage</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((t) => (
                    <TableRow key={t.id || t.slug}>
                      <TableCell className="font-mono">{t.id || '—'}</TableCell>
                      <TableCell>{t.name || t.slug || '—'}</TableCell>
                      <TableCell>
                        {typeof t.aliases_count === 'number' ? t.aliases_count : '—'}
                      </TableCell>
                      <TableCell>
                        {typeof t.usage_count === 'number' ? t.usage_count : '—'}
                      </TableCell>
                      <TableCell>
                        {t.created_at ? new Date(t.created_at).toLocaleString() : '—'}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          className="text-red-600 border-red-300"
                          onClick={async () => {
                            if (!t.id) return;
                            const ok = await confirmWithEnv(
                              `Delete tag "${t.name || t.slug}"? This cannot be undone.`,
                            );
                            if (!ok) return;
                            try {
                              await deleteAdminTag(t.id);
                              await reload();
                            } catch (e) {
                              // ignore error reporting here; page error state will show
                            }
                          }}
                        >
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="p-4 text-center text-gray-500">
                        No tags found
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
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
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Slug</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {blItems.map((b) => (
                    <TableRow key={b.slug}>
                      <TableCell className="font-mono">{b.slug}</TableCell>
                      <TableCell>{b.reason || '—'}</TableCell>
                      <TableCell>{new Date(b.created_at).toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          className="text-red-600 border-red-300"
                          onClick={async () => {
                            await removeFromBlacklist(b.slug);
                            await loadBlacklist();
                          }}
                        >
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {blItems.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="p-4 text-center text-gray-500">
                        No blacklist entries
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
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
              } catch (e) {
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
