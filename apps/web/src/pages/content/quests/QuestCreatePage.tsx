import React from 'react';
import { ContentLayout } from '../ContentLayout';
import { Card, Input as TInput, Textarea, Switch, Button, TagInput } from '@ui';
import { apiPost } from '../../../shared/api/client';

export default function QuestCreatePage() {
  const [title, setTitle] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [tags, setTags] = React.useState<string[]>([]);
  const [isPublic, setIsPublic] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [created, setCreated] = React.useState<{ id: string; slug?: string } | null>(null);

  async function createQuest() {
    setBusy(true); setError(null); setCreated(null);
    try {
      const payload = {
        title: title.trim(),
        description: description.trim() || undefined,
        tags,
        is_public: isPublic,
      };
      if (!payload.title) throw new Error('Укажите название');
      const res = await apiPost('/v1/quests', payload);
      setCreated(res);
      setTitle(''); setDescription(''); setTags(''); setIsPublic(false);
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally { setBusy(false); }
  }

  return (
    <ContentLayout context="quests">
      <Card className="p-4">
        <h2 className="mb-3 text-base font-semibold">Создать квест</h2>
        {error && <div className="mb-2 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}
        <div className="space-y-3">
          <TInput label="Название" placeholder="Введите название" value={title} onChange={(e: any) => setTitle(e.target.value)} />
          <Textarea label="Описание" placeholder="Краткое описание" value={description} onChange={(e: any) => setDescription(e.target.value)} />
          <TagInput label="Теги" placeholder="story, ai, demo" value={tags} onChange={setTags} />
          <div className="flex items-center gap-3">
            <Switch checked={isPublic} onChange={(e: any) => setIsPublic(e.currentTarget.checked)} />
            <span className="text-sm">Опубликовать</span>
          </div>
          <div>
            <Button disabled={busy || !title.trim()} onClick={createQuest}>{busy ? 'Сохранение…' : 'Создать'}</Button>
          </div>
          {created && (
            <div className="text-sm text-gray-700">Создано: id={created.id}{created.slug ? `, slug=${created.slug}` : ''}</div>
          )}
        </div>
      </Card>
    </ContentLayout>
  );
}
