import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { createQuest, createDraft } from "../api/questEditor";
import PageLayout from "./_shared/PageLayout";

interface QuestItem {
  id: string;
  slug: string;
  title: string;
  is_draft: boolean;
  created_at: string;
  published_at?: string | null;
}

export default function QuestsList() {
  const nav = useNavigate();
  const [items, setItems] = useState<QuestItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<QuestItem[]>("/admin/quests");
      setItems((res.data as any) || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onNewQuest = async () => {
    // Создаём черновой квест с дефолтным заголовком без диалогов
    try {
      const defaultTitle = "New quest";
      const id = await createQuest(defaultTitle);
      if (!id || typeof id !== "string") {
        console.error("createQuest returned invalid id:", id);
        alert("Failed to create quest: invalid server response (id is empty).");
        return;
      }
      const ver = await createDraft(id);
      if (!ver || typeof ver !== "string") {
        console.error("createDraft returned invalid versionId:", ver);
        alert("Failed to create draft: invalid server response (versionId is empty).");
        return;
      }
      // Обновим список квестов и сразу откроем редактор
      await load();
      nav(`/quests/version/${ver}`);
    } catch (e) {
      console.error("New quest flow failed:", e);
      const msg = e instanceof Error ? e.message : String(e);
      // Браузерный NetworkError означает, что API не достигнуто (базовый URL/порт, CORS, прокси)
      alert(`Failed to create quest: ${msg}`);
    }
  };

  const onNewDraft = async (id: string) => {
    try {
      const ver = await createDraft(id);
      if (!ver || typeof ver !== "string") {
        console.error("createDraft returned invalid versionId:", ver);
        alert("Failed to create draft: invalid server response (versionId is empty).");
        return;
      }
      nav(`/quests/version/${ver}`);
    } catch (e) {
      console.error("Create draft failed:", e);
      alert(`Failed to create draft: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const content = (() => {
    if (loading) return <div className="text-sm text-gray-500">Loading...</div>;
    if (error) return <div className="text-sm text-red-600">{error}</div>;
    return (
      <table className="min-w-full text-sm">
        <thead className="text-left">
          <tr>
            <th className="py-2 pr-4">Title</th>
            <th className="py-2 pr-4">Slug</th>
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
              <td className="py-2 pr-4">{new Date(q.created_at).toLocaleString()}</td>
              <td className="py-2 pr-4">{q.published_at ? `Published ${new Date(q.published_at).toLocaleDateString()}` : "Draft"}</td>
              <td className="py-2 pr-4">
                <button className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 mr-2" onClick={() => onNewDraft(q.id)}>New draft</button>
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr><td className="py-6 text-gray-500" colSpan={4}>No quests yet. Click “New quest” to create one.</td></tr>
          )}
        </tbody>
      </table>
    );
  })();

  return (
    <PageLayout title="Quests" subtitle="Управление квестами">
      <div className="mb-3">
        <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={onNewQuest}>New quest</button>
      </div>
      {content}
    </PageLayout>
  );
}
