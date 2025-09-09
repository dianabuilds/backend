import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAccount } from '../account/AccountContext';
import { createDraft, createQuest } from '../api/questEditor';
import { autofixQuest, listQuests, publishQuest, validateQuest } from '../api/quests';
import type { ValidateResult } from '../openapi';
type ValidationReport = {
  errors: number;
  warnings: number;
  items: Array<{ level: string; code: string; message: string }>;
};
import PageLayout from './_shared/PageLayout';

interface QuestItem {
  id: string;
  slug: string;
  title: string;
  is_draft: boolean;
  created_at: string;
  published_at?: string | null;
  structure?: string | null;
  length?: 'short' | 'long' | null;
  cost_generation?: number | null;
}

export default function QuestsList() {
  const nav = useNavigate();
  const { accountId } = useAccount();

  // filters
  const [search, setSearch] = useState('');
  const [draftOnly, setDraftOnly] = useState<boolean>(false);
  const [lenFilter, setLenFilter] = useState<'' | 'short' | 'long'>('');
  const [createdFrom, setCreatedFrom] = useState<string>('');
  const [createdTo, setCreatedTo] = useState<string>('');

  // validation panel state
  const [activeQuestId, setActiveQuestId] = useState<string | null>(null);
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [publishAccess, setPublishAccess] = useState<'premium_only' | 'everyone' | 'early_access'>(
    'everyone',
  );
  const [publishCover, setPublishCover] = useState<string>('');

  const {
    data: items = [],
    isLoading,
    error,
    refetch,
  } = useQuery<QuestItem[]>({
    queryKey: ['quests', accountId, search, draftOnly, lenFilter, createdFrom, createdTo],
    queryFn: async () => {
      const rows = await listQuests({
        q: search.trim() || undefined,
        draft: draftOnly,
        length: lenFilter || undefined,
        created_from: createdFrom || undefined,
        created_to: createdTo || undefined,
      });
      return rows as QuestItem[];
    },
    enabled: !!accountId,
    placeholderData: (prev) => prev,
  });

  const onApplyFilters = async () => {
    setActiveQuestId(null);
    setReport(null);
    await refetch();
  };

  const onValidate = async (id: string) => {
    setActiveQuestId(id);
    setReport(null);
    try {
      const r = await validateQuest(id);
      setReport(mapValidateResult(r));
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const onPublish = async (id: string) => {
    try {
      setPublishing(true);
      await publishQuest(id, {
        access: publishAccess,
        coverUrl: publishCover || undefined,
      });
      setPublishing(false);
      setActiveQuestId(null);
      setReport(null);
      await refetch();
    } catch (e) {
      setPublishing(false);
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const onNewQuest = async () => {
    // Создаём черновой квест с дефолтным заголовком без диалогов
    try {
      const defaultTitle = 'New quest';
      const id = await createQuest(defaultTitle);
      if (!id) {
        console.error('createQuest returned invalid id:', id);
        alert('Failed to create quest: invalid server response (id is empty).');
        return;
      }
      const ver = await createDraft(id);
      if (!ver) {
        console.error('createDraft returned invalid versionId:', ver);
        alert('Failed to create draft: invalid server response (versionId is empty).');
        return;
      }
      // Обновим список квестов и сразу откроем редактор
      await refetch();
      nav(`/quests/${id}/versions/${ver}`);
    } catch (e) {
      console.error('New quest flow failed:', e);
      const msg = e instanceof Error ? e.message : String(e);
      alert(`Failed to create quest: ${msg}`);
    }
  };

  const onNewDraft = async (id: string) => {
    try {
      const ver = await createDraft(id);
      if (!ver) {
        console.error('createDraft returned invalid versionId:', ver);
        alert('Failed to create draft: invalid server response (versionId is empty).');
        return;
      }
      nav(`/quests/${id}/versions/${ver}`);
    } catch (e) {
      console.error('Create draft failed:', e);
      alert(`Failed to create draft: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const content = (() => {
    if (isLoading) return <div className="text-sm text-gray-500">Loading...</div>;
    if (error) return <div className="text-sm text-red-600">{error.message}</div>;
    return (
      <>
        <table className="min-w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-2 pr-4">Title</th>
              <th className="py-2 pr-4">Slug</th>
              <th className="py-2 pr-4">Structure</th>
              <th className="py-2 pr-4">Length</th>
              <th className="py-2 pr-4">Cost</th>
              <th className="py-2 pr-4">Created</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((q) => (
              <tr key={q.id} className="border-t border-gray-200 dark:border-gray-800">
                <td className="py-2 pr-4">{q.title}</td>
                <td className="py-2 pr-4 font-mono">{q.slug}</td>
                <td className="py-2 pr-4">{q.structure || '-'}</td>
                <td className="py-2 pr-4">{q.length || '-'}</td>
                <td className="py-2 pr-4">
                  {typeof q.cost_generation === 'number'
                    ? (q.cost_generation / 100).toFixed(2)
                    : '-'}
                </td>
                <td className="py-2 pr-4">{new Date(q.created_at).toLocaleString()}</td>
                <td className="py-2 pr-4">
                  {q.published_at ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-green-100 text-green-800">
                      Published {new Date(q.published_at).toLocaleDateString()}
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-yellow-100 text-yellow-800">
                      Draft
                    </span>
                  )}
                </td>
                <td className="py-2 pr-4 space-x-2">
                  <button className="px-2 py-1 rounded border" onClick={() => onNewDraft(q.id)}>
                    New draft
                  </button>
                  <button className="px-2 py-1 rounded border" onClick={() => onValidate(q.id)}>
                    Validate
                  </button>
                  {!q.published_at && (
                    <button
                      className="px-2 py-1 rounded border"
                      onClick={() => {
                        setActiveQuestId(q.id);
                        setPublishAccess('everyone');
                        setPublishCover('');
                        setReport(null);
                      }}
                    >
                      Publish…
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td className="py-6 text-gray-500" colSpan={5}>
                  No quests yet. Click “New quest” to create one.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {/* Validation/Publish panel */}
        {activeQuestId && (report || !items.find((i) => i.id === activeQuestId)?.published_at) && (
          <div className="mt-4 rounded border p-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Quest tools</h3>
              <button
                className="text-sm text-gray-600"
                onClick={() => {
                  setActiveQuestId(null);
                  setReport(null);
                }}
              >
                Close
              </button>
            </div>

            {report && (
              <div className="mt-2">
                <div className="mb-2">
                  <span className="mr-4">
                    Errors: <b>{report.errors}</b>
                  </span>
                  <span>
                    Warnings: <b>{report.warnings}</b>
                  </span>
                </div>
                <div className="max-h-64 overflow-auto border rounded">
                  <table className="min-w-full text-sm">
                    <thead className="text-left">
                      <tr>
                        <th className="p-2">Level</th>
                        <th className="p-2">Code</th>
                        <th className="p-2">Message</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.items.map((it, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="p-2">{it.level}</td>
                          <td className="p-2">{it.code}</td>
                          <td className="p-2">{it.message}</td>
                        </tr>
                      ))}
                      {report.items.length === 0 && (
                        <tr>
                          <td className="p-2 text-gray-500" colSpan={3}>
                            No issues
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {!items.find((i) => i.id === activeQuestId)?.published_at && (
              <div className="mt-3">
                <div className="mb-2 text-sm text-gray-600">Publish settings</div>
                <div className="flex flex-wrap items-center gap-2">
                  <select
                    className="border rounded px-2 py-1"
                    value={publishAccess}
                    onChange={(e) =>
                      setPublishAccess(
                        e.target.value as 'premium_only' | 'everyone' | 'early_access',
                      )
                    }
                  >
                    <option value="everyone">everyone</option>
                    <option value="premium_only">premium_only</option>
                    <option value="early_access">early_access</option>
                  </select>
                  <input
                    className="border rounded px-2 py-1 w-96"
                    placeholder="Cover URL (optional)"
                    value={publishCover}
                    onChange={(e) => setPublishCover(e.target.value)}
                  />
                  <button
                    className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-50"
                    disabled={publishing || (report?.errors ?? 0) > 0}
                    onClick={() => activeQuestId && onPublish(activeQuestId)}
                    title={
                      (report?.errors ?? 0) > 0
                        ? 'Fix validation errors before publishing'
                        : 'Publish quest'
                    }
                  >
                    {publishing ? 'Publishing…' : 'Publish'}
                  </button>
                  {!report && (
                    <button
                      className="px-3 py-1 rounded border"
                      onClick={() => activeQuestId && onValidate(activeQuestId)}
                    >
                      Run validation
                    </button>
                  )}
                  <button
                    className="px-3 py-1 rounded border"
                    onClick={async () => {
                      if (!activeQuestId) return;
                      await autofixQuest(activeQuestId, ['ensure_entry', 'deduplicate_nodes']);
                      const r = await validateQuest(activeQuestId);
                      setReport(mapValidateResult(r));
                    }}
                  >
                    Autofix (basic)
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </>
    );
  })();

  function mapValidateResult(r: ValidateResult): ValidationReport {
    const errors = Array.isArray(r.errors) ? r.errors : [];
    const warnings = Array.isArray(r.warnings) ? r.warnings : [];
    return {
      errors: errors.length,
      warnings: warnings.length,
      items: [
        ...errors.map((m) => ({ level: 'error', code: '', message: String(m) })),
        ...warnings.map((m) => ({ level: 'warning', code: '', message: String(m) })),
      ],
    };
  }

  return (
    <PageLayout title="Quests" subtitle="Управление квестами">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={onNewQuest}>
          New quest
        </button>
        <input
          className="border rounded px-2 py-1"
          placeholder="Search by title/desc…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={draftOnly}
            onChange={(e) => setDraftOnly(e.target.checked)}
          />
          Drafts only
        </label>
        <select
          className="border rounded px-2 py-1"
          value={lenFilter}
          onChange={(e) => setLenFilter(e.target.value as '' | 'short' | 'long')}
        >
          <option value="">length: any</option>
          <option value="short">short</option>
          <option value="long">long</option>
        </select>
        <input
          type="datetime-local"
          className="border rounded px-2 py-1"
          value={createdFrom}
          onChange={(e) => setCreatedFrom(e.target.value)}
        />
        <input
          type="datetime-local"
          className="border rounded px-2 py-1"
          value={createdTo}
          onChange={(e) => setCreatedTo(e.target.value)}
        />
        <button className="px-3 py-1 rounded border" onClick={onApplyFilters}>
          Apply
        </button>
      </div>
      {content}
    </PageLayout>
  );
}
