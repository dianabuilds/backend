import { useMemo, useState } from 'react';

import {
  type AchievementAdmin,
  createAdminAchievement,
  deleteAdminAchievement,
  grantAchievement,
  listAdminAchievements,
  revokeAchievement,
  updateAdminAchievement,
} from '../api/achievements';
import { useToast } from '../components/ToastProvider';
import { useModal, usePaginatedList } from '../shared/hooks';
import { Button, Modal, PageLayout, SearchBar, Table, TextInput } from '../shared/ui';
import { confirmWithEnv } from '../utils/env';
import ConditionEditor, { type Condition } from './_shared/ConditionEditor';

export default function Achievements() {
  const { addToast } = useToast();
  const [q, setQ] = useState('');

  const {
    items,
    loading,
    error,
    limit,
    setLimit,
    nextPage,
    prevPage,
    hasNext,
    hasPrev,
    reset,
    reload,
  } = usePaginatedList<AchievementAdmin>((params) => listAdminAchievements({ ...params, q }));

  const createModal = useModal();
  const assignModal = useModal();

  const [cCode, setCCode] = useState('');
  const [cTitle, setCTitle] = useState('');
  const [cDesc, setCDesc] = useState('');
  const [cIcon, setCIcon] = useState('');
  const [cVisible, setCVisible] = useState(true);
  const [cCond, setCCond] = useState<Condition>({
    type: 'event_count',
    event: 'some_event',
    count: 1,
  });

  // edit state
  const [editId, setEditId] = useState<string | null>(null);
  const [editConditions, setEditConditions] = useState<Record<string, Condition>>({});

  // assign modal state
  const [aUser, setAUser] = useState('');
  const [aCode, setACode] = useState('');
  const [aAction, setAAction] = useState<'grant' | 'revoke'>('grant');
  const [aReason, setAReason] = useState('');

  const achievementMap = useMemo(
    () => Object.fromEntries(items.map((a) => [a.code, a.id])),
    [items],
  );

  const handleSearch = async () => {
    reset();
    await reload();
  };

  const onCreate = async () => {
    if (!cCode.trim() || !cTitle.trim()) return;
    try {
      await createAdminAchievement({
        code: cCode.trim(),
        title: cTitle.trim(),
        description: cDesc.trim() || undefined,
        icon: cIcon.trim() || undefined,
        visible: cVisible,
        condition: cCond as unknown as AchievementAdmin['condition'],
      });
      setCCode('');
      setCTitle('');
      setCDesc('');
      setCIcon('');
      setCVisible(true);
      setCCond({ type: 'event_count', event: 'some_event', count: 1 });
      createModal.close();
      reset();
      await reload();
      addToast({ title: 'Achievement created', variant: 'success' });
    } catch (e) {
      addToast({
        title: 'Create failed',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  const onSave = async (row: AchievementAdmin, patch: Partial<AchievementAdmin>) => {
    try {
      await updateAdminAchievement(row.id, patch);
      setEditId(null);
      await reload();
      addToast({ title: 'Saved', variant: 'success' });
    } catch (e) {
      addToast({
        title: 'Save failed',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  const onDelete = async (row: AchievementAdmin) => {
    if (!(await confirmWithEnv(`Delete achievement "${row.title}"?`))) return;
    try {
      await deleteAdminAchievement(row.id);
      await reload();
      addToast({ title: 'Deleted', variant: 'success' });
    } catch (e) {
      addToast({
        title: 'Delete failed',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  const handleAssign = async () => {
    const id = achievementMap[aCode.trim()];
    if (!id || !aUser.trim()) {
      addToast({
        title: 'Invalid input',
        description: 'Provide existing code and user',
        variant: 'error',
      });
      return;
    }
    try {
      if (aAction === 'grant') {
        await grantAchievement(id, aUser.trim(), aReason.trim() || undefined);
        addToast({ title: 'Achievement granted', variant: 'success' });
      } else {
        await revokeAchievement(id, aUser.trim(), aReason.trim() || undefined);
        addToast({ title: 'Achievement revoked', variant: 'success' });
      }
      assignModal.close();
    } catch (e) {
      addToast({
        title: 'Failed to apply',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  const exportLocal = () => {
    const blob = new Blob([JSON.stringify(items, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'achievements.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <PageLayout
      title="Achievements"
      actions={
        <div className="flex gap-2">
          <Button onClick={createModal.open}>Create achievement</Button>
          <Button
            onClick={() => {
              setAAction('grant');
              setACode('');
              setAUser('');
              setAReason('');
              assignModal.open();
            }}
          >
            Grant/Revoke
          </Button>
          <Button onClick={exportLocal}>Export</Button>
        </div>
      }
    >
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <SearchBar
          value={q}
          onChange={setQ}
          onSearch={handleSearch}
          placeholder="Search achievements..."
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
          <Button disabled={!hasPrev} onClick={prevPage} title="Previous page">
            ‹ Prev
          </Button>
          <Button disabled={!hasNext} onClick={nextPage} title="Next page">
            Next ›
          </Button>
        </div>
      </div>

      {loading && <p>Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && (
        <Table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Code</th>
              <th className="p-2 text-left">Title</th>
              <th className="p-2 text-left">Visible</th>
              <th className="p-2 text-left">Description</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => {
              const isEdit = editId === a.id;
              const [eCode, eTitle, eDesc, eIcon, eVisible] = isEdit
                ? [
                    a.code,
                    a.title,
                    a.description || '',
                    a.icon || '',
                    a.visible,
                    JSON.stringify(a.condition ?? {}, null, 2),
                  ]
                : [a.code, a.title, a.description || '', a.icon || '', a.visible, ''];
              return (
                <tr key={a.id} className="border-b align-top">
                  <td className="p-2 font-mono">
                    {isEdit ? (
                      <input
                        defaultValue={eCode}
                        onBlur={(ev) => (a.code = ev.currentTarget.value)}
                        className="border rounded px-2 py-1 w-40 font-mono"
                      />
                    ) : (
                      a.code
                    )}
                  </td>
                  <td className="p-2">
                    {isEdit ? (
                      <input
                        defaultValue={eTitle}
                        onBlur={(ev) => (a.title = ev.currentTarget.value)}
                        className="border rounded px-2 py-1 w-56"
                      />
                    ) : (
                      a.title
                    )}
                  </td>
                  <td className="p-2">
                    {isEdit ? (
                      <input
                        type="checkbox"
                        defaultChecked={eVisible}
                        onChange={(ev) => (a.visible = ev.currentTarget.checked)}
                      />
                    ) : (
                      String(a.visible)
                    )}
                  </td>
                  <td className="p-2">
                    {isEdit ? (
                      <div className="space-y-2">
                        <input
                          defaultValue={eDesc}
                          onBlur={(ev) => (a.description = ev.currentTarget.value)}
                          className="border rounded px-2 py-1 w-full"
                        />
                        <input
                          defaultValue={eIcon}
                          onBlur={(ev) => (a.icon = ev.currentTarget.value)}
                          className="border rounded px-2 py-1 w-full"
                          placeholder="icon"
                        />
                        <ConditionEditor
                          value={editConditions[a.id] ?? (a.condition as unknown as Condition)}
                          onChange={(v) => setEditConditions((m) => ({ ...m, [a.id]: v }))}
                        />
                      </div>
                    ) : (
                      (a.description ?? '')
                    )}
                  </td>
                  <td className="p-2 space-x-2">
                    {!isEdit ? (
                      <>
                        <button
                          className="px-2 py-1 rounded border"
                          onClick={() => {
                            setEditId(a.id);
                            setEditConditions((m) => ({
                              ...m,
                              [a.id]: (a.condition as unknown as Condition) || {
                                type: 'event_count',
                                event: 'some_event',
                                count: 1,
                              },
                            }));
                          }}
                        >
                          Edit
                        </button>
                        <button
                          className="px-2 py-1 rounded border text-red-600 border-red-300"
                          onClick={() => onDelete(a)}
                        >
                          Delete
                        </button>
                        <button
                          className="px-2 py-1 rounded border"
                          onClick={() => {
                            setAAction('grant');
                            setACode(a.code);
                            setAUser('');
                            setAReason('');
                            assignModal.open();
                          }}
                        >
                          Grant
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          className="px-2 py-1 rounded border"
                          onClick={async () => {
                            const patch: Partial<AchievementAdmin> = {
                              code: a.code,
                              title: a.title,
                              description: a.description || undefined,
                              icon: a.icon || undefined,
                              visible: a.visible,
                              condition:
                                (editConditions[
                                  a.id
                                ] as unknown as AchievementAdmin['condition']) ??
                                (a.condition || {}),
                            };
                            await onSave(a, patch);
                          }}
                        >
                          Save
                        </button>
                        <button
                          className="px-2 py-1 rounded border"
                          onClick={() => setEditId(null)}
                        >
                          Cancel
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              );
            })}
            {items.length === 0 && (
              <tr>
                <td className="p-2 text-gray-500" colSpan={5}>
                  No achievements
                </td>
              </tr>
            )}
          </tbody>
        </Table>
      )}

      <Modal isOpen={createModal.isOpen} onClose={createModal.close} title="Create achievement">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <TextInput placeholder="code" value={cCode} onChange={(e) => setCCode(e.target.value)} />
          <TextInput
            placeholder="title"
            value={cTitle}
            onChange={(e) => setCTitle(e.target.value)}
          />
          <TextInput
            className="md:col-span-2"
            placeholder="description (optional)"
            value={cDesc}
            onChange={(e) => setCDesc(e.target.value)}
          />
          <TextInput
            placeholder="icon (optional)"
            value={cIcon}
            onChange={(e) => setCIcon(e.target.value)}
          />
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={cVisible}
              onChange={(e) => setCVisible(e.target.checked)}
            />
            Visible
          </label>
          <div className="md:col-span-2">
            <ConditionEditor value={cCond} onChange={setCCond} />
          </div>
          <div className="md:col-span-2 mt-2 flex justify-end gap-2">
            <Button onClick={onCreate}>Create</Button>
            <Button onClick={createModal.close}>Cancel</Button>
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={assignModal.isOpen}
        onClose={assignModal.close}
        title="Grant/Revoke achievement"
      >
        <div className="space-y-2">
          <TextInput
            placeholder="user_id"
            value={aUser}
            onChange={(e) => setAUser(e.target.value)}
          />
          <TextInput
            placeholder="achievement code"
            value={aCode}
            onChange={(e) => setACode(e.target.value)}
          />
          <select
            value={aAction}
            onChange={(e) => setAAction(e.target.value as 'grant' | 'revoke')}
            className="border rounded px-2 py-1 w-full"
          >
            <option value="grant">grant</option>
            <option value="revoke">revoke</option>
          </select>
          <TextInput
            placeholder="reason (optional)"
            value={aReason}
            onChange={(e) => setAReason(e.target.value)}
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button onClick={handleAssign}>Apply</Button>
            <Button onClick={assignModal.close}>Cancel</Button>
          </div>
        </div>
      </Modal>
    </PageLayout>
  );
}
