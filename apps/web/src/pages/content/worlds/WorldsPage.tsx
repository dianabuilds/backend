import React from "react";
import { useNavigate } from "react-router-dom";
import { ContentLayout } from "../ContentLayout";
import { Card, Button, Spinner, Skeleton, Badge, Tabs, Input, PieChart } from "@ui";
import { apiGet, apiDelete } from "../../../shared/api/client";

type World = {
  id: string;
  title: string;
  locale?: string;
  description?: string;
};

type Character = {
  id: string;
  name: string;
  role?: string;
  description?: string;
};

type DetailTab = "summary" | "characters" | "schematics";

export default function WorldsPage() {
  const navigate = useNavigate();
  const [worlds, setWorlds] = React.useState<World[]>([]);
  const [selectedId, setSelectedId] = React.useState<string>("");
  const [characters, setCharacters] = React.useState<Character[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [loadingCharacters, setLoadingCharacters] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [search, setSearch] = React.useState("");
  const [detailTab, setDetailTab] = React.useState<DetailTab>("summary");

  const stats = React.useMemo(() => {
    const withDescription = worlds.reduce((acc, world) => acc + (world.description?.trim() ? 1 : 0), 0);
    const locales = new Set(
      worlds
        .map((world) => world.locale?.trim())
        .filter((locale): locale is string => Boolean(locale && locale.length > 0)),
    );
    return {
      total: worlds.length,
      withDescription,
      locales: locales.size,
    };
  }, [worlds]);

  const filteredWorlds = React.useMemo(() => {
    if (!search.trim()) {
      return worlds;
    }
    const query = search.trim().toLowerCase();
    return worlds.filter((world) => {
      const title = (world.title || "").toLowerCase();
      const description = (world.description || "").toLowerCase();
      const locale = (world.locale || "").toLowerCase();
      return title.includes(query) || description.includes(query) || locale.includes(query);
    });
  }, [worlds, search]);

  const activeWorld = React.useMemo(
    () => filteredWorlds.find((world) => world.id === selectedId) ?? null,
    [filteredWorlds, selectedId],
  );

  const detailTabs = React.useMemo(
    () => [
      { key: "summary", label: "Обзор" },
      { key: "characters", label: `Персонажи (${characters.length})` },
      { key: "schematics", label: "Схемы" },
    ],
    [characters.length],
  );

  const loadWorlds = React.useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await apiGet<World[]>("/v1/admin/worlds");
      const normalized = Array.isArray(data) ? data : [];
      setWorlds(normalized);
      setSelectedId((previous) => {
        if (previous && normalized.some((world) => world.id === previous)) {
          return previous;
        }
        return normalized[0]?.id ?? "";
      });
      if (normalized.length === 0) {
        setCharacters([]);
      }
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadCharacters = React.useCallback(async (worldId: string) => {
    if (!worldId) {
      setCharacters([]);
      return;
    }
    setError(null);
    setLoadingCharacters(true);
    try {
      const data = await apiGet<Character[]>(`/v1/admin/worlds/${encodeURIComponent(worldId)}/characters`);
      setCharacters(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(String(e?.message || e));
      setCharacters([]);
    } finally {
      setLoadingCharacters(false);
    }
  }, []);

  React.useEffect(() => {
    void loadWorlds();
  }, [loadWorlds]);

  React.useEffect(() => {
    if (filteredWorlds.length === 0) {
      if (selectedId) {
        setSelectedId("");
      }
      return;
    }
    const hasSelected = filteredWorlds.some((world) => world.id === selectedId);
    if (!hasSelected) {
      setSelectedId(filteredWorlds[0].id);
    }
  }, [filteredWorlds, selectedId]);

  React.useEffect(() => {
    if (selectedId) {
      setDetailTab("summary");
      void loadCharacters(selectedId);
    } else {
      setCharacters([]);
    }
  }, [selectedId, loadCharacters]);

  const charactersByRole = React.useMemo(() => {
    if (characters.length === 0) {
      return [] as Array<[string, number]>;
    }
    const map = new Map<string, number>();
    characters.forEach((character) => {
      const key = character.role?.trim() || "Без роли";
      map.set(key, (map.get(key) ?? 0) + 1);
    });
    return Array.from(map.entries());
  }, [characters]);

  const charactersWithNotes = React.useMemo(
    () => characters.filter((character) => Boolean(character.description?.trim())).length,
    [characters],
  );

  function handleSelectWorld(worldId: string) {
    setSelectedId(worldId);
  }

  function handleDuplicate(world: World) {
    navigate(`/quests/worlds/new?duplicate=${encodeURIComponent(world.id)}`);
  }

  async function handleDelete(world: World) {
    if (!window.confirm(`Удалить мир «${world.title || "Без названия"}»?`)) {
      return;
    }
    try {
      await apiDelete(`/v1/admin/worlds/${encodeURIComponent(world.id)}`);
      await loadWorlds();
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  }

  return (
    <ContentLayout
      context="quests"
      title="Работа с мирами"
      description="Компактный центр управления мирами: поиск, описание, персонажи и визуальные схемы связей."
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" onClick={() => navigate("/quests/worlds/new")}>Новый мир</Button>
          <Button size="sm" variant="outlined" color="neutral" disabled={!selectedId} onClick={() => selectedId && navigate(`/quests/worlds/new?duplicate=${encodeURIComponent(selectedId)}`)}>
            Дублировать текущий
          </Button>
          <Button size="sm" variant="outlined" color="neutral" onClick={() => void loadWorlds()}>
            Обновить
          </Button>
        </div>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[300px_minmax(0,1fr)]">
        <div className="space-y-4">
          <Card className="space-y-4 p-5">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Навигация</h3>
              <p className="mt-1 text-xs text-gray-500 dark:text-dark-200">Быстрые переходы внутри карточки мира.</p>
            </div>
            {activeWorld ? (
              <div className="flex flex-col gap-2">
                {detailTabs.map((tab) => {
                  const active = tab.key === detailTab;
                  return (
                    <button
                      key={tab.key}
                      type="button"
                      onClick={() => setDetailTab(tab.key as DetailTab)}
                      className={`rounded-md px-3 py-2 text-left text-sm transition ${
                        active
                          ? "bg-primary-600 text-white shadow-sm"
                          : "bg-white/70 text-gray-600 hover:bg-gray-100 dark:bg-dark-700/70 dark:text-dark-100 dark:hover:bg-dark-650"
                      }`}
                    >
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-dark-200">Выберите мир, чтобы увидеть навигацию по разделам.</p>
            )}
            <Button size="sm" variant="outlined" className="w-full" onClick={() => navigate("/quests/worlds/new")}>Создать новый мир</Button>
          </Card>

          <Card className="space-y-4 p-5">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Каталог миров</h3>
              <p className="mt-1 text-xs text-gray-500 dark:text-dark-200">Поиск и быстрый выбор существующих миров.</p>
            </div>
            <Input value={search} placeholder="Найти по названию, описанию или локали" onChange={(event: React.ChangeEvent<HTMLInputElement>) => setSearch(event.target.value)} />
            <div className="custom-scrollbar max-h-[440px] space-y-2 overflow-y-auto pr-1">
              {loading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((item) => (
                    <div key={item} className="space-y-2 rounded-lg border border-gray-200 p-3 dark:border-dark-600">
                      <Skeleton className="h-4 w-2/3 rounded" />
                      <Skeleton className="h-3 w-full rounded" />
                    </div>
                  ))}
                </div>
              ) : filteredWorlds.length === 0 ? (
                <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-500 dark:border-dark-600 dark:bg-dark-700/40 dark:text-dark-200">
                  Нет миров, удовлетворяющих запросу. Попробуйте изменить фильтр или создайте новый мир.
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredWorlds.map((world) => {
                    const isActive = world.id === selectedId;
                    return (
                      <button
                        key={world.id}
                        type="button"
                        onClick={() => handleSelectWorld(world.id)}
                        className={`w-full rounded-lg border px-3 py-3 text-left transition ${
                          isActive
                            ? "border-primary-500 bg-primary-50/80 shadow-sm dark:border-primary-500/70 dark:bg-primary-500/20"
                            : "border-gray-200 bg-white hover:border-primary-300 hover:bg-primary-50/40 dark:border-dark-600 dark:bg-dark-700/60 dark:hover:border-primary-500/50"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="line-clamp-1 text-sm font-semibold text-gray-900 dark:text-dark-50">
                            {world.title || "Без названия"}
                          </span>
                          <Badge color="neutral" variant="outline">{world.locale || "—"}</Badge>
                        </div>
                        <p className="mt-1 line-clamp-2 text-xs text-gray-500 dark:text-dark-200">
                          {world.description || "Описание пока не добавлено."}
                        </p>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </Card>

          <Card className="space-y-4 p-5">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Статистика пространства</h3>
              <p className="mt-1 text-xs text-gray-500 dark:text-dark-200">Обновляется при каждом запросе списка.</p>
            </div>
            <div className="space-y-3 text-sm text-gray-700 dark:text-dark-100">
              <div className="flex items-center justify-between gap-3">
                <span>Всего миров</span>
                <span className="font-semibold">{stats.total}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>С описанием</span>
                <span className="font-semibold">{stats.withDescription}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span>Уникальных локалей</span>
                <span className="font-semibold">{stats.locales}</span>
              </div>
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
              {error}
            </div>
          )}

          {activeWorld ? (
            <>
              <Card className="space-y-4 p-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="space-y-2">
                    <span className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-300">Активный мир</span>
                    <h2 className="text-2xl font-semibold text-gray-900 dark:text-dark-50">{activeWorld.title || "Без названия"}</h2>
                    <div className="flex flex-wrap gap-2">
                      <Badge color="primary">{activeWorld.locale || "—"}</Badge>
                      <Badge color="neutral" variant="outline">ID {activeWorld.id}</Badge>
                      <Badge color="info" variant="soft">{characters.length} персонажей</Badge>
                      <Badge color="success" variant="soft">{charactersWithNotes} с заметками</Badge>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" variant="outlined" onClick={() => navigate(`/quests/worlds/new?id=${encodeURIComponent(activeWorld.id)}`)}>
                      Редактировать
                    </Button>
                    <Button size="sm" variant="outlined" onClick={() => handleDuplicate(activeWorld)}>
                      Дублировать
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      color="neutral"
                      className="text-rose-600 hover:bg-rose-50 hover:text-rose-700 dark:text-rose-300 dark:hover:bg-rose-500/20"
                      onClick={() => handleDelete(activeWorld)}
                    >
                      Удалить
                    </Button>
                  </div>
                </div>
                <div className="grid gap-3 text-sm text-gray-600 dark:text-dark-200 md:grid-cols-2">
                  <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-dark-600 dark:bg-dark-700/60">
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Кратко</h3>
                    <p className="mt-2 leading-relaxed">
                      {activeWorld.description || "Добавьте описание, чтобы команда понимала атмосферу и ключевые конфликты мира."}
                    </p>
                  </div>
                  <div className="rounded-lg border border-primary-200 bg-primary-50/80 p-4 text-primary-800 dark:border-primary-600/50 dark:bg-primary-950/40 dark:text-primary-200">
                    <h3 className="text-xs font-semibold uppercase tracking-wide">Следующие шаги</h3>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                      <li>Синхронизируйте мир с актуальными квестами и указателями.</li>
                      <li>Соберите ключевые NPC и привяжите их через карточки персонажей.</li>
                      <li>Поделитесь ссылкой с авторами — навигация в левой колонке поможет им быстрее разобраться.</li>
                    </ul>
                  </div>
                </div>
              </Card>

              <Tabs items={detailTabs} value={detailTab} onChange={(key) => setDetailTab(key as DetailTab)} className="pt-2" />

              {detailTab === "summary" && (
                <Card className="space-y-4 p-6">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Сводка мира</h3>
                    <p className="mt-1 text-sm text-gray-600 dark:text-dark-200">
                      Опорные факты, заметки и источники, которые помогают авторам быстро включиться в работу.
                    </p>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-lg border border-gray-200 bg-white p-4 text-sm leading-relaxed dark:border-dark-600 dark:bg-dark-700/60 dark:text-dark-100">
                      <h4 className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-300">Описание</h4>
                      <p className="mt-2">
                        {activeWorld.description || "Описание пока не заполнено. Добавьте основные фракции, атмосферу и ограничения по тону."}
                      </p>
                    </div>
                    <div className="rounded-lg border border-dashed border-primary-200 bg-primary-50/50 p-4 text-sm text-primary-800 dark:border-primary-600/60 dark:bg-primary-950/30 dark:text-primary-100">
                      <h4 className="text-xs uppercase tracking-wide">Материалы</h4>
                      <ul className="mt-2 space-y-1">
                        <li>🧭 Схема мира: разместите ссылку на Miro или документацию.</li>
                        <li>🎭 Документ NPC: таблица персонажей с ролями и голосами.</li>
                        <li>⚙️ Контролируемые триггеры: флаги, которые должны оставаться синхронными между квестами.</li>
                      </ul>
                    </div>
                  </div>
                </Card>
              )}

              {detailTab === "characters" && (
                <Card className="space-y-4 p-6">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Персонажи мира</h3>
                      <p className="text-sm text-gray-600 dark:text-dark-200">
                        Держите NPC связаными с миром, чтобы сценаристы видели контекст.
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outlined" onClick={() => navigate(`/quests/characters/new?world_id=${encodeURIComponent(activeWorld.id)}`)}>
                        Добавить персонажа
                      </Button>
                      <Button size="sm" variant="ghost" color="neutral" onClick={() => void loadCharacters(activeWorld.id)}>
                        Обновить
                      </Button>
                    </div>
                  </div>

                  {loadingCharacters ? (
                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-dark-200">
                      <Spinner size="sm" /> Загружаем персонажей…
                    </div>
                  ) : characters.length === 0 ? (
                    <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-sm text-gray-500 dark:border-dark-500 dark:bg-dark-700/50 dark:text-dark-200">
                      Пока нет связанных персонажей. Добавьте их, чтобы схемы и список ролей работали корректно.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {characters.map((character) => (
                        <Card key={character.id} className="p-4 shadow-sm dark:bg-dark-700">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div className="space-y-2">
                              <div className="flex items-center gap-2">
                                <h4 className="text-base font-semibold text-gray-900 dark:text-dark-50">{character.name}</h4>
                                {character.role && <Badge color="primary">{character.role}</Badge>}
                              </div>
                              <p className="text-sm text-gray-600 dark:text-dark-200">
                                {character.description || "Добавьте заметку, чтобы пояснить роль и связь с сюжетом."}
                              </p>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <Button
                                size="sm"
                                variant="outlined"
                                onClick={() =>
                                  navigate(
                                    `/quests/characters/edit?id=${encodeURIComponent(character.id)}&world_id=${encodeURIComponent(activeWorld.id)}`,
                                  )
                                }
                              >
                                Редактировать
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                color="neutral"
                                onClick={() => navigate(`/quests/worlds?remove_character=${encodeURIComponent(character.id)}`)}
                              >
                                Отвязать
                              </Button>
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  )}
                </Card>
              )}

              {detailTab === "schematics" && (
                <Card className="space-y-6 p-6">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Схемы и визуализации</h3>
                    <p className="mt-1 text-sm text-gray-600 dark:text-dark-200">
                      Быстрый взгляд на роли и связи. Дополните данными, чтобы визуализации оставались актуальными.
                    </p>
                  </div>

                  {charactersByRole.length > 0 ? (
                    <div className="grid gap-6 lg:grid-cols-2">
                      <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-dark-600 dark:bg-dark-700/60">
                        <h4 className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-300">Распределение ролей</h4>
                        <PieChart
                          series={charactersByRole.map(([, count]) => count)}
                          height={260}
                          options={{
                            labels: charactersByRole.map(([role]) => role),
                            colors: ["#6366F1", "#22C55E", "#F97316", "#A855F7", "#3B82F6", "#EC4899", "#14B8A6", "#FACC15"],
                          }}
                        />
                      </div>

                      <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-dark-600 dark:bg-dark-700/60">
                        <h4 className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-300">Связи мира</h4>
                        <RelationshipDiagram world={activeWorld} characters={characters} />
                        {characters.length > 8 && (
                          <p className="mt-2 text-center text-xs text-gray-500 dark:text-dark-300">
                            Показаны первые 8 персонажей. Остальные остаются в списке.
                          </p>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-sm text-gray-500 dark:border-dark-500 dark:bg-dark-700/50 dark:text-dark-200">
                      Добавьте хотя бы одного персонажа, чтобы построить диаграмму связей и распределение ролей.
                    </div>
                  )}
                </Card>
              )}
            </>
          ) : loading ? (
            <Card className="p-6">
              <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-dark-200">
                <Spinner size="sm" /> Загружаем миры…
              </div>
            </Card>
          ) : (
            <Card className="p-8 text-center text-sm text-gray-500 dark:text-dark-200">
              Нет выбранного мира. Используйте список слева, чтобы начать работу, или создайте новый мир.
            </Card>
          )}
        </div>
      </div>
    </ContentLayout>
  );
}

type RelationshipDiagramProps = {
  world: World;
  characters: Character[];
};

function RelationshipDiagram({ world, characters }: RelationshipDiagramProps) {
  const nodes = React.useMemo(() => characters.slice(0, 8), [characters]);

  if (nodes.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-primary-200 bg-primary-50/40 p-6 text-center text-sm text-primary-700 dark:border-primary-600/50 dark:bg-primary-950/30 dark:text-primary-200">
        Добавьте персонажей, чтобы визуализировать связи.
      </div>
    );
  }

  const radius = 38;

  return (
    <div className="relative mx-auto h-60 w-full max-w-md">
      <svg
        className="absolute inset-0 z-0 text-primary-200 dark:text-primary-900/50"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {nodes.map((node, index) => {
          const angle = (index / nodes.length) * Math.PI * 2;
          const x = 50 + Math.cos(angle) * radius;
          const y = 50 + Math.sin(angle) * radius;
          return <line key={node.id} x1="50" y1="50" x2={x} y2={y} stroke="currentColor" strokeWidth="0.7" strokeDasharray="2 2" />;
        })}
      </svg>
      {nodes.map((character, index) => {
        const angle = (index / nodes.length) * Math.PI * 2;
        const x = 50 + Math.cos(angle) * radius;
        const y = 50 + Math.sin(angle) * radius;
        return (
          <div
            key={character.id}
            className="absolute z-10 flex w-28 -translate-x-1/2 -translate-y-1/2 flex-col items-center rounded-lg border border-gray-200 bg-white p-2 text-center shadow-sm dark:border-dark-500 dark:bg-dark-700"
            style={{ left: `${x}%`, top: `${y}%` }}
          >
            <span className="line-clamp-2 text-xs font-semibold text-gray-800 dark:text-dark-50">{character.name}</span>
            <span className="mt-1 text-[10px] uppercase tracking-wide text-primary-600 dark:text-primary-300">
              {character.role || "Без роли"}
            </span>
          </div>
        );
      })}
      <div className="absolute left-1/2 top-1/2 z-20 flex h-24 w-24 -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full border border-primary-300 bg-primary-50 text-center text-xs font-medium text-primary-700 shadow-inner dark:border-primary-600/50 dark:bg-primary-900/40 dark:text-primary-200">
        <span className="text-[10px] uppercase tracking-[0.2em]">Мир</span>
        <span className="mt-1 line-clamp-2 text-sm font-semibold leading-tight">{world.title || "Без названия"}</span>
      </div>
    </div>
  );
}
