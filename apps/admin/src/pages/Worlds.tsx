import { useEffect, useState } from "react";

import { api } from "../api/client";

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
  const [worlds, setWorlds] = useState<WorldTemplate[]>([]);
  const [selectedWorld, setSelectedWorld] = useState<string>("");
  const [characters, setCharacters] = useState<Character[]>([]);

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

  const loadWorlds = async () => {
    try {
      const res = await api.get<WorldTemplate[]>("/admin/ai/quests/worlds");
      setWorlds(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCharacters = async (wid: string) => {
    if (!wid) {
      setCharacters([]);
      return;
    }
    try {
      const res = await api.get<Character[]>(
        `/admin/ai/quests/worlds/${encodeURIComponent(wid)}/characters`,
      );
      setCharacters(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadWorlds();
  }, []);
  useEffect(() => {
    loadCharacters(selectedWorld);
  }, [selectedWorld]);

  const createWorld = async () => {
    if (!newWorld.title.trim()) return alert("Введите название мира");
    try {
      await api.post("/admin/ai/quests/worlds", {
        title: newWorld.title,
        locale: newWorld.locale || null,
        description: newWorld.description || null,
        meta: null,
      });
      setNewWorld({ title: "", locale: "", description: "" });
      await loadWorlds();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const removeWorld = async (id: string) => {
    if (!confirm("Удалить мир со всеми персонажами?")) return;
    try {
      await api.request(`/admin/ai/quests/worlds/${encodeURIComponent(id)}`, {
        method: "DELETE",
      });
      if (id === selectedWorld) {
        setSelectedWorld("");
        setCharacters([]);
      }
      await loadWorlds();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const addCharacter = async () => {
    if (!selectedWorld) return alert("Сначала выберите мир");
    if (!newChar.name.trim()) return alert("Имя персонажа обязательно");
    try {
      await api.post(
        `/admin/ai/quests/worlds/${encodeURIComponent(selectedWorld)}/characters`,
        {
          name: newChar.name,
          role: newChar.role || null,
          description: newChar.description || null,
          traits: null,
        },
      );
      setNewChar({ name: "", role: "", description: "" });
      await loadCharacters(selectedWorld);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const removeCharacter = async (id: string) => {
    if (!confirm("Удалить персонажа?")) return;
    try {
      await api.request(
        `/admin/ai/quests/characters/${encodeURIComponent(id)}`,
        { method: "DELETE" },
      );
      await loadCharacters(selectedWorld);
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
