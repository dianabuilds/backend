import { memo, useEffect, useMemo } from "react";
import EditorJSEmbed from "./EditorJSEmbed";
import MediaPicker from "./MediaPicker";
import TagInput from "./TagInput";

export interface NodeEditorData {
  id: string;
  title: string;
  subtitle?: string;
  cover_url?: string | null;
  tags?: string[];
  allow_comments?: boolean;
  is_premium_only?: boolean;
  contentData: any;
}

interface Props {
  open: boolean;
  node: NodeEditorData | null;
  onChange: (patch: Partial<NodeEditorData>) => void;
  onClose: () => void;
  onCommit: (action: "save" | "next") => void;
  busy?: boolean;
}

function NodeEditorModalImpl({ open, node, onChange, onClose, onCommit, busy = false }: Props) {
  if (!open || !node) return null;

  const heading = useMemo(() => (node.title?.trim() ? "Редактировать пещеру" : "Создать пещеру"), [node.title]);

  // Сохраняем актуальное содержимое редактора перед коммитом
  const handleCommit = async (action: "save" | "next") => {
    try {
      const saveFn: (() => Promise<any>) | undefined = (handleCommit as any)._save;
      if (typeof saveFn === "function") {
        const data = await saveFn();
        if (data) onChange({ contentData: data });
      }
    } catch {
      // игнорируем — лучше сохранить с последней известной версией
    }
    onCommit(action);
  };

  // Автосохранение черновика в localStorage
  useEffect(() => {
    if (!open || !node) return;
    const key = `qe:nodeDraft:${node.id}`;
    const payload = { ts: Date.now(), data: node };
    try {
      localStorage.setItem(key, JSON.stringify(payload));
    } catch {
      // ignore quota
    }
  }, [open, node]);

  // Хоткеи: Ctrl+Enter — сохранить; Ctrl+Shift+Enter — сохранить и создать следующую
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!open) return;
      if (e.key === "Enter" && e.ctrlKey && e.shiftKey) {
        e.preventDefault();
        onCommit("next");
      } else if (e.key === "Enter" && e.ctrlKey) {
        e.preventDefault();
        onCommit("save");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCommit]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-[95vw] md:max-w-7xl max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="px-5 py-3 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold">{heading}</h2>
          <button className="px-2 py-1 text-sm rounded border" onClick={onClose}>
            Закрыть
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-auto flex-1 space-y-5">
          {/* Основная информация */}
          <section className="rounded border p-4">
            <h3 className="font-semibold mb-3">Основная информация</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <input
                  className="w-full text-2xl font-bold mb-2 outline-none border-b pb-2 bg-transparent"
                  placeholder="Название"
                  value={node.title}
                  onChange={(e) => onChange({ title: e.target.value })}
                />
                <input
                  className="w-full text-base mb-2 outline-none border-b pb-2 bg-transparent"
                  placeholder="Подзаголовок (опционально)"
                  value={node.subtitle || ""}
                  onChange={(e) => onChange({ subtitle: e.target.value })}
                />
                <TagInput
                  value={node.tags || []}
                  onChange={(tags) => onChange({ tags })}
                  placeholder="Добавьте теги и нажмите Enter"
                />
              </div>

              {/* Медиа */}
              <div>
                <h4 className="font-semibold mb-2">Изображение</h4>
                <MediaPicker
                  value={node.cover_url || null}
                  onChange={(url) => onChange({ cover_url: url })}
                  height={160}
                  className="w-[120px]"
                />
              </div>
            </div>
          </section>

          {/* Настройки */}
          <section className="rounded border p-4">
            <h3 className="font-semibold mb-3">Настройки</h3>
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!node.allow_comments}
                  onChange={(e) => onChange({ allow_comments: e.target.checked })}
                />
                <span>💬 Разрешить комментарии</span>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!node.is_premium_only}
                  onChange={(e) => onChange({ is_premium_only: e.target.checked })}
                />
                <span>⭐ Только для премиум</span>
              </label>
            </div>
          </section>

          {/* Контент */}
          <section className="rounded border p-4">
            <h3 className="font-semibold mb-3">Контент</h3>
            <EditorJSEmbed
              key={node.id}
              value={node.contentData}
              onChange={(data) => onChange({ contentData: data })}
              onReady={({ save }) => {
                // Сохраняем функцию save для использования при коммите
                (window as any).__ed_save__ = save; // для отладки
                // сохраняем на экземпляре компонента через ref
                (handleCommit as any)._save = save;
              }}
              className="border rounded"
              minHeight={480}
              placeholder="Напишите описание, легенду или сценарий пещеры…"
            />
          </section>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t flex items-center justify-end gap-3">
          <button className="px-4 py-1.5 rounded border" onClick={onClose} disabled={busy}>
            Отмена
          </button>
          <button
            className="px-4 py-1.5 rounded bg-blue-600 text-white disabled:opacity-50"
            onClick={() => handleCommit("save")}
            disabled={busy}
          >
            {busy ? "Сохранение…" : "Сохранить"}
          </button>
          <button
            className="px-4 py-1.5 rounded bg-blue-700 text-white disabled:opacity-50"
            title="Ctrl+Shift+Enter"
            onClick={() => handleCommit("next")}
            disabled={busy}
          >
            {busy ? "Сохранение…" : "Сохранить и создать следующую"}
          </button>
        </div>
      </div>
    </div>
  );
}

const NodeEditorModal = memo(NodeEditorModalImpl);
export default NodeEditorModal;
