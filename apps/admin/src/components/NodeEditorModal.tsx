import { memo, useEffect, useMemo } from 'react';

import type { NodeCreate } from '../openapi';
import EditorJSEmbed from './EditorJSEmbed';
import ImageDropzone from './ImageDropzone';
import TagInput from './TagInput';

export interface NodeEditorData extends Partial<NodeCreate> {
  id?: number;
  subtitle?: string;
  content: unknown;
}

interface Props {
  open: boolean;
  node: NodeEditorData | null;
  onChange: (patch: Partial<NodeEditorData>) => void;
  onClose: () => void;
  onCommit: (action: 'save' | 'next') => void;
}

function NodeEditorModalImpl({ open, node, onChange, onClose, onCommit }: Props) {
  // Hooks must be called unconditionally; guard inside effects and render
  const heading = useMemo(
    () => (node?.title?.trim() ? 'Редактировать пещеру' : 'Создать пещеру'),
    [node?.title],
  );

  // Autosave draft to localStorage
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

  // Hotkeys: Ctrl+Enter save; Ctrl+Shift+Enter save+next
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!open) return;
      if (e.key === 'Enter' && e.ctrlKey && e.shiftKey) {
        e.preventDefault();
        onCommit('next');
      } else if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        onCommit('save');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onCommit]);

  if (!open || !node) return null;

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
                  value={node.subtitle || ''}
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
                <ImageDropzone
                  value={node.coverUrl || null}
                  onChange={(url) => onChange({ coverUrl: url })}
                  height={160}
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
                  checked={!!node.allowFeedback}
                  onChange={(e) => onChange({ allowFeedback: e.target.checked })}
                />
                <span>Разрешить комментарии</span>
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!node.premiumOnly}
                  onChange={(e) => onChange({ premiumOnly: e.target.checked })}
                />
                <span>Только для премиум</span>
              </label>
            </div>
          </section>

          {/* Контент */}
          <section className="rounded border p-4">
            <h3 className="font-semibold mb-3">Контент</h3>
            <EditorJSEmbed
              key={node.id}
              value={node.content}
              onChange={(data) => onChange({ content: data })}
              className="border rounded"
              minHeight={480}
              placeholder="Напишите описание, легенду или сценарий пещеры…"
            />
          </section>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t flex items-center justify-end gap-3">
          <button className="px-4 py-1.5 rounded border" onClick={onClose}>
            Отмена
          </button>
          <button
            className="px-4 py-1.5 rounded bg-blue-600 text-white"
            onClick={() => onCommit('save')}
          >
            Сохранить
          </button>
          <button
            className="px-4 py-1.5 rounded bg-blue-700 text-white"
            title="Ctrl+Shift+Enter"
            onClick={() => onCommit('next')}
          >
            Сохранить и создать следующую
          </button>
        </div>
      </div>
    </div>
  );
}

const NodeEditorModal = memo(NodeEditorModalImpl);
export default NodeEditorModal;
