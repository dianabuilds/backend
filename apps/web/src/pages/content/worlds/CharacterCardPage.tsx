import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ContentLayout } from "../ContentLayout";
import { Card, Input as TInput, Textarea, Button, Badge } from "@ui";
import { apiGet, apiPost, apiPatch } from "@shared/api/client";

type Mode = "create" | "edit";

type CharacterPayload = {
  name?: string;
  role?: string;
  description?: string;
};

type CharacterResponse = {
  id?: string | number;
  character_id?: string | number;
} & CharacterPayload;

export default function CharacterCardPage() {
  const [params] = useSearchParams();
  const charId = params.get("id");
  const worldId = params.get("world_id");
  const mode: Mode = charId ? "edit" : "create";
  const navigate = useNavigate();

  const [name, setName] = React.useState("");
  const [role, setRole] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (mode === "edit" && charId) {
      (async () => {
        try {
          const data = await apiGet<CharacterResponse>(`/v1/admin/worlds/characters/${encodeURIComponent(charId)}`);
          setName(String(data?.name || ""));
          setRole(String(data?.role || ""));
          setDescription(String(data?.description || ""));
        } catch (e: any) {
          setError(String(e?.message || e));
        }
      })();
    }
  }, [mode, charId]);

  const previewDescription = description.trim() || "Опишите мотивацию и отношение персонажа к игроку.";

  async function handleSubmit() {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      if (!name.trim()) {
        throw new Error("Укажите имя персонажа");
      }
      const payload: CharacterPayload = {
        name: name.trim(),
        role: role.trim() || undefined,
        description: description.trim() || undefined,
      };

      if (mode === "edit" && charId) {
        await apiPatch(`/v1/admin/worlds/characters/${encodeURIComponent(charId)}`, payload);
        navigate("/quests/worlds");
      } else {
        if (!worldId) throw new Error("world_id обязателен");
        const created = await apiPost<CharacterResponse>(`/v1/admin/worlds/${encodeURIComponent(worldId)}/characters`, payload);
        const createdId = created?.id ?? created?.character_id;
        setInfo(createdId ? `Персонаж создан (id ${createdId})` : 'Персонаж создан');
        setName("");
        setRole("");
        setDescription("");
      }
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <ContentLayout
      context="quests"
      title={mode === "edit" ? "Редактирование персонажа" : "Новый персонаж"}
      description="Создайте карточку NPC, чтобы авторам и AI было проще использовать его в сюжетах."
      actions={<Button variant="outlined" onClick={() => navigate("/quests/worlds")}>Назад к мирам</Button>}
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Card className="space-y-6 rounded-3xl bg-white/95 p-6 shadow-xl ring-1 ring-gray-100/80 backdrop-blur-md dark:bg-dark-800/85 dark:ring-dark-500/50 dark:shadow-[0_35px_60px_-35px_rgba(2,6,23,0.75)]">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-dark-50">Данные персонажа</h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-dark-200">
              Фиксируйте имя, роль и заметки — они помогают авторам понимать контекст NPC и связь с мирами.
            </p>
          </div>

          {mode === "create" && !worldId && (
            <div className="rounded border border-amber-400 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              Чтобы создать персонажа, перейдите из списка миров или укажите параметр <code>world_id</code> в адресной строке.
            </div>
          )}

          {error && <div className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}
          {info && <div className="rounded border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{info}</div>}

          <div className="grid gap-4 sm:grid-cols-2">
            {mode === "create" && (
              <TInput label="ID мира" placeholder="world_id" value={worldId || ""} readOnly />
            )}
            <TInput label="Имя" placeholder="NPC name" value={name} onChange={(event: any) => setName(event.target.value)} className="sm:col-span-2" />
            <TInput label="Роль" placeholder="Наставник, торговец, соперник" value={role} onChange={(event: any) => setRole(event.target.value)} className="sm:col-span-2" />
            <Textarea label="Описание" rows={6} value={description} onChange={(event: any) => setDescription(event.target.value)} className="sm:col-span-2" />
          </div>

          <div className="flex gap-2">
            <Button className="min-w-[140px]" disabled={busy || (mode === "create" && !worldId)} onClick={handleSubmit}>
              {busy ? "Сохранение…" : mode === "edit" ? "Сохранить" : "Создать"}
            </Button>
            {mode === "edit" && charId && <Badge color="neutral">ID {charId}</Badge>}
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="space-y-3 p-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-800 dark:text-dark-100">Превью карточки</h3>
              <p className="text-xs text-gray-500 dark:text-dark-300">Так персонаж выглядит в списках и деталях мира.</p>
            </div>
            <div className="rounded-3xl border border-gray-200 bg-gradient-to-br from-white via-white to-primary-50/60 p-6 shadow-inner dark:border-dark-600 dark:from-dark-700 dark:via-dark-700 dark:to-dark-800">
              <div className="text-lg font-semibold text-gray-900 dark:text-dark-50">{name || "Имя персонажа"}</div>
              <div className="text-sm text-primary-600 dark:text-primary-300">{role.trim() || "Роль не указана"}</div>
              <p className="mt-3 text-sm text-gray-600 dark:text-dark-200">{previewDescription}</p>
            </div>
          </Card>

          <Card className="space-y-2 p-6 text-sm text-gray-600 dark:text-dark-200">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-dark-100">Советы</h3>
            <ul className="list-disc space-y-1 pl-5">
              <li>Уточните мотивацию и конфликт, чтобы генеративные сюжеты были консистентны.</li>
              <li>Привяжите персонажа к группам или мирам — это улучшит навигацию (функция скоро появится).</li>
              <li>Используйте описание, чтобы зафиксировать голос персонажа, ключевые реплики или сленг.</li>
            </ul>
          </Card>
        </div>
      </div>
    </ContentLayout>
  );
}


