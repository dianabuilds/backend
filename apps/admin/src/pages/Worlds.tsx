import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { confirmWithEnv } from "../utils/env";

import { client } from "../shared/api/client";
import { queryKeys } from "../shared/api/queryKeys";

type WorldTemplate = {
  id: string;
  title: string;
  locale?: string | null;
  description?: string | null;
};
type Character = {
  id: string;
  world_id: string;
  name: string;
  role?: string | null;
  description?: string | null;
};

export default function WorldsPage() {
  const qc = useQueryClient();
  const [selectedWorld, setSelectedWorld] = useState<string>("");

  const [newWorld, setNewWorld] = useState<{
    title: string;
    locale: string;
    description: string;
  }>({ title: "", locale: "", description: "" });
  const [newChar, setNewChar] = useState<{
    name: string;
    role: string;
    description: string;
  }>({ name: "", role: "", description: "" });

  const { data: worlds = [] } = useQuery({
    queryKey: queryKeys.worlds,
    queryFn: () =>
      client.get<WorldTemplate[]>("/admin/ai/quests/worlds").then((d) => d || []),
  });
  const { data: characters = [] } = useQuery({
    queryKey: queryKeys.worldCharacters(selectedWorld),
    queryFn: () =>
      client
        .get<Character[]>(
          `/admin/ai/quests/worlds/${encodeURIComponent(selectedWorld)}/characters`,
        )
        .then((d) => d || []),
    enabled: !!selectedWorld,
  });

  const createWorldMutation = useMutation({
    mutationFn: (payload: {
      title: string;
      locale: string;
      description: string;
    }) =>
      client.post(`/admin/ai/quests/worlds`, {
        title: payload.title,
        locale: payload.locale || null,
        description: payload.description || null,
        meta: null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.worlds });
    },
  });

  const removeWorldMutation = useMutation({
    mutationFn: (id: string) =>
      client.del(`/admin/ai/quests/worlds/${encodeURIComponent(id)}`),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: queryKeys.worlds });
      qc.removeQueries({ queryKey: queryKeys.worldCharacters(id) });
    },
  });

  const addCharacterMutation = useMutation({
    mutationFn: (payload: {
      name: string;
      role: string;
      description: string;
    }) =>
      client.post(
        `/admin/ai/quests/worlds/${encodeURIComponent(selectedWorld)}/characters`,
        {
          name: payload.name,
          role: payload.role || null,
          description: payload.description || null,
          traits: null,
        },
      ),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: queryKeys.worldCharacters(selectedWorld),
      });
    },
  });

  const removeCharacterMutation = useMutation({
    mutationFn: (id: string) =>
      client.del(`/admin/ai/quests/characters/${encodeURIComponent(id)}`),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: queryKeys.worldCharacters(selectedWorld),
      });
    },
  });

  const createWorld = async () => {
    if (!newWorld.title.trim()) return alert("Введите название мира");
    try {
      await createWorldMutation.mutateAsync(newWorld);
      setNewWorld({ title: "", locale: "", description: "" });
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const removeWorld = async (id: string) => {
    if (!(await confirmWithEnv("Удалить мир со всеми персонажами?"))) return;
    try {
      await removeWorldMutation.mutateAsync(id);
      if (id === selectedWorld) setSelectedWorld("");
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const addCharacter = async () => {
    if (!selectedWorld) return alert("Сначала выберите мир");
    if (!newChar.name.trim()) return alert("Имя персонажа обязательно");
    try {
      await addCharacterMutation.mutateAsync(newChar);
      setNewChar({ name: "", role: "", description: "" });
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const removeCharacter = async (id: string) => {
    if (!(await confirmWithEnv("Удалить персонажа?"))) return;
    try {
      await removeCharacterMutation.mutateAsync(id);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Worlds & Characters</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="rounded border p-3">
          <h3 className="font-semibold mb-2">Миры</h3>
          <div className="flex flex-col gap-2 mb-3">
            <input
              className="border rounded px-2 py-1"
              placeholder="Название"
              value={newWorld.title}
              onChange={(e) =>
                setNewWorld((s) => ({ ...s, title: e.target.value }))
              }
            />
            <input
              className="border rounded px-2 py-1"
              placeholder="Локаль (ru-RU / en-US)"
              value={newWorld.locale}
              onChange={(e) =>
                setNewWorld((s) => ({ ...s, locale: e.target.value }))
              }
            />
            <textarea
              className="border rounded px-2 py-1"
              placeholder="Описание"
              value={newWorld.description}
              onChange={(e) =>
                setNewWorld((s) => ({ ...s, description: e.target.value }))
              }
            />
            <button
              className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
              onClick={createWorld}
            >
              Добавить мир
            </button>
          </div>
          <div className="max-h-80 overflow-auto divide-y">
            {worlds.map((w) => (
              <div
                key={w.id}
                className="py-2 flex items-center justify-between gap-2"
              >
                <button
                  className={`text-left flex-1 ${selectedWorld === w.id ? "font-semibold" : ""}`}
                  onClick={() => setSelectedWorld(w.id)}
                >
                  {w.title}
                  {w.locale ? ` · ${w.locale}` : ""}
                </button>
                <button
                  className="px-2 py-1 rounded border"
                  onClick={() => removeWorld(w.id)}
                >
                  Удалить
                </button>
              </div>
            ))}
            {worlds.length === 0 && (
              <div className="text-sm text-gray-500">Пока нет миров</div>
            )}
          </div>
        </div>

        <div className="rounded border p-3 lg:col-span-2">
          <h3 className="font-semibold mb-2">
            Персонажи {selectedWorld ? "" : "(выберите мир)"}
          </h3>
          {selectedWorld && (
            <>
              <div className="flex flex-col gap-2 mb-3">
                <input
                  className="border rounded px-2 py-1"
                  placeholder="Имя"
                  value={newChar.name}
                  onChange={(e) =>
                    setNewChar((s) => ({ ...s, name: e.target.value }))
                  }
                />
                <input
                  className="border rounded px-2 py-1"
                  placeholder="Роль"
                  value={newChar.role}
                  onChange={(e) =>
                    setNewChar((s) => ({ ...s, role: e.target.value }))
                  }
                />
                <textarea
                  className="border rounded px-2 py-1"
                  placeholder="Описание"
                  value={newChar.description}
                  onChange={(e) =>
                    setNewChar((s) => ({ ...s, description: e.target.value }))
                  }
                />
                <button
                  className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
                  onClick={addCharacter}
                >
                  Добавить персонажа
                </button>
              </div>
              <div className="max-h-96 overflow-auto divide-y">
                {characters.map((c) => (
                  <div
                    key={c.id}
                    className="py-2 flex items-center justify-between gap-2"
                  >
                    <div className="flex-1">
                      <div className="font-medium">
                        {c.name}
                        {c.role ? ` · ${c.role}` : ""}
                      </div>
                      {c.description && (
                        <div className="text-xs text-gray-600">
                          {c.description}
                        </div>
                      )}
                    </div>
                    <button
                      className="px-2 py-1 rounded border"
                      onClick={() => removeCharacter(c.id)}
                    >
                      Удалить
                    </button>
                  </div>
                ))}
                {characters.length === 0 && (
                  <div className="text-sm text-gray-500">
                    Пока нет персонажей
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
