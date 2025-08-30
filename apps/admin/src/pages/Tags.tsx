import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Button,
  Modal,
  PageLayout,
  Table,
  TextInput,
  SearchBar,
} from "../shared/ui";
import { useModal, usePaginatedList } from "../shared/hooks";
import { confirmWithEnv } from "../utils/env";
import {
  addToBlacklist,
  type BlacklistItem,
  createAdminTag,
  deleteAdminTag,
  getBlacklist,
  listAdminTags,
  removeFromBlacklist,
} from "../api/tags";

type TagItem = {
  id?: string;
  slug?: string;
  name?: string;
  usage_count?: number;
  aliases_count?: number;
  created_at?: string;
};

export default function Tags() {
  const [q, setQ] = useState("");

  const {
    items,
    loading,
    error,
    limit,
    offset,
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
  const [newSlug, setNewSlug] = useState("");
  const [newName, setNewName] = useState("");

  const handleSearch = async () => {
    reset();
    await reload();
  };

  const [blItems, setBlItems] = useState<BlacklistItem[]>([]);
  const [blSlug, setBlSlug] = useState("");
  const [blReason, setBlReason] = useState("");

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
    <PageLayout title="Tags">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <SearchBar
          value={q}
          onChange={setQ}
          onSearch={handleSearch}
          placeholder="Search by tag name..."
        />
        <Button onClick={() => navigate("/tags/merge")}>Merge…</Button>
        <Button onClick={createModal.open}>New tag</Button>
        <div className="ml-auto flex items-center gap-2">
          <label className="text-sm text-gray-600">Page size</label>
          <TextInput
            type="number"
            min={1}
            max={1000}
            value={limit}
            onChange={(e) =>
              setLimit(
                Math.max(1, Math.min(1000, Number(e.target.value) || 1)),
              )
            }
            className="w-20"
          />
          <Button disabled={!hasPrev} onClick={prevPage} title="Previous page">
            ‹ Prev
          </Button>
          <Button disabled={!hasNext} onClick={nextPage} title="Next page">
            Next ›
          </Button>
        </div>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <>
          <Table className="mb-6">
            <thead>
              <tr className="border-b">
                <th className="p-2">ID</th>
                <th className="p-2">Name</th>
                <th className="p-2">Aliases</th>
                <th className="p-2">Usage</th>
                <th className="p-2">Created</th>
                <th className="p-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((t) => (
                <tr key={t.id || t.slug} className="border-b">
                  <td className="p-2 font-mono">{t.id || "—"}</td>
                  <td className="p-2">{t.name || t.slug || "—"}</td>
                  <td className="p-2">
                    {typeof t.aliases_count === "number"
                      ? t.aliases_count
                      : "—"}
                  </td>
                  <td className="p-2">
                    {typeof t.usage_count === "number" ? t.usage_count : "—"}
                  </td>
                  <td className="p-2">
                    {t.created_at
                      ? new Date(t.created_at).toLocaleString()
                      : "—"}
                  </td>
                  <td className="p-2 text-right">
                    <Button
                      className="text-red-600 border-red-300"
                      onClick={async () => {
                        if (!t.id) return;
                        const ok = confirmWithEnv(
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
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-gray-500">
                    No tags found
                  </td>
                </tr>
              )}
            </tbody>
          </Table>

          <div className="rounded border p-3">
            <h2 className="font-semibold mb-2">Blacklist</h2>
            <div className="flex items-center gap-2 mb-3">
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
                  await addToBlacklist(
                    blSlug.trim(),
                    blReason.trim() || undefined,
                  );
                  setBlSlug("");
                  setBlReason("");
                  await loadBlacklist();
                }}
              >
                Add
              </Button>
            </div>
            <Table>
              <thead>
                <tr className="border-b">
                  <th className="p-2">Slug</th>
                  <th className="p-2">Reason</th>
                  <th className="p-2">Created</th>
                  <th className="p-2" />
                </tr>
              </thead>
              <tbody>
                {blItems.map((b) => (
                  <tr key={b.slug} className="border-b">
                    <td className="p-2 font-mono">{b.slug}</td>
                    <td className="p-2">{b.reason || "—"}</td>
                    <td className="p-2">
                      {new Date(b.created_at).toLocaleString()}
                    </td>
                    <td className="p-2 text-right">
                      <Button
                        className="text-red-600 border-red-300"
                        onClick={async () => {
                          await removeFromBlacklist(b.slug);
                          await loadBlacklist();
                        }}
                      >
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))}
                {blItems.length === 0 && (
                  <tr>
                    <td className="p-4 text-center text-gray-500" colSpan={4}>
                      No blacklist entries
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          </div>
        </>
      )}

      <Modal
        isOpen={createModal.isOpen}
        onClose={createModal.close}
        title="Create tag"
      >
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
                setNewSlug("");
                setNewName("");
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
