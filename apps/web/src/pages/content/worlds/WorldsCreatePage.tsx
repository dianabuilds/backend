import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ContentLayout } from "../ContentLayout";
import { Card, Input as TInput, Textarea, Button, Badge, Select } from "@ui";
import { apiGet, apiPost, apiPatch } from "../../../shared/api/client";

const localeOptions = [
  { value: "ru-RU", label: "Русский" },
  { value: "en-US", label: "English" },
] as const;
type LocaleValue = (typeof localeOptions)[number]["value"];

const defaultLocale = localeOptions[0].value;

function normalizeLocale(raw?: string | null): LocaleValue {
  if (!raw) return defaultLocale;
  const lower = String(raw).toLowerCase();
  const directMatch = localeOptions.find((option) => option.value.toLowerCase() === lower);
  if (directMatch) return directMatch.value;
  const prefixMatch = localeOptions.find((option) => option.value.split('-')[0].toLowerCase() === lower);
  return prefixMatch ? prefixMatch.value : defaultLocale;
}

function useWorldForm(worldId: string | null) {
  const mode: "create" | "edit" = worldId ? "edit" : "create";
  const navigate = useNavigate();
  const [title, setTitle] = React.useState("");
  const [locale, setLocale] = React.useState<LocaleValue>(defaultLocale);
  const [description, setDescription] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [info, setInfo] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (mode === "edit" && worldId) {
      (async () => {
        try {
          const data = await apiGet(`/v1/admin/worlds/${encodeURIComponent(worldId)}`);
          setTitle(String(data?.title || ""));
          setLocale(normalizeLocale(data?.locale));
          setDescription(String(data?.description || ""));
        } catch (e: any) {
          setError(String(e?.message || e));
        }
      })();
    }
  }, [mode, worldId]);

  async function submit() {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const payload: Record<string, string | undefined> = {
        title: title.trim() || undefined,
        locale: locale.trim() || undefined,
        description: description.trim() || undefined,
      };
      if (!payload.title) throw new Error("Введите название мира");

      if (mode === "edit" && worldId) {
        await apiPatch(`/v1/admin/worlds/${encodeURIComponent(worldId)}`, payload);
        navigate("/quests/worlds");
      } else {
        const created = await apiPost(`/v1/admin/worlds`, payload);
        setInfo(`Мир создан (id ${created?.id ?? "—"})`);
        setTitle("");
        setDescription("");
      }
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }

  return {
    mode,
    title,
    setTitle,
    locale,
    setLocale,
    description,
    setDescription,
    busy,
    error,
    info,
    submit,
    navigate,
  };
}

export default function WorldsCreatePage() {
  const [params] = useSearchParams();
  const worldId = params.get("id");
  const form = useWorldForm(worldId);
  const { mode, title, setTitle, locale, setLocale, description, setDescription, busy, error, info, submit, navigate } = form;

  const previewBody = description.trim() || "Добавьте описание, чтобы объяснить атмосферу, ключевые конфликты и важные локации мира.";

  const localeLabel = React.useMemo(() => {
    const match = localeOptions.find((option) => option.value === locale);
    return match ? match.label : locale || defaultLocale;
  }, [locale]);

  return (
    <ContentLayout
      context="quests"
      title={mode === "edit" ? "Редактирование мира" : "Создание мира"}
      description="Фиксируйте лор мира — локаль, краткую аннотацию и подсказки для авторов квестов и AI."
      actions={<Button variant="outlined" onClick={() => navigate("/quests/worlds")}>Назад к мирам</Button>}
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Card className="space-y-6 rounded-3xl bg-white/95 p-6 shadow-xl ring-1 ring-gray-100/80 backdrop-blur-md dark:bg-dark-800/85 dark:ring-dark-500/50 dark:shadow-[0_35px_60px_-35px_rgba(2,6,23,0.75)]">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-dark-50">Основная информация</h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-dark-200">
              Локаль и название используются в дашбордах и AI-подсказках. Описание помогает авторам быстро включиться в контекст мира.
            </p>
          </div>
          {error && <div className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}
          {info && <div className="rounded border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{info}</div>}

          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label="Локаль"
              value={locale}
              onChange={(event: React.ChangeEvent<HTMLSelectElement>) => setLocale(event.target.value as LocaleValue)}
            >
              {localeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
            <TInput
              label="Название"
              placeholder="Flavour Trip Universe"
              value={title}
              onChange={(event: any) => setTitle(event.target.value)}
              className="sm:col-span-2"
            />
            <Textarea
              label="Описание"
              placeholder="Ключевые элементы мира, атмосферу, конфликт, вспомогательные подсказки для авторов"
              value={description}
              onChange={(event: any) => setDescription(event.target.value)}
              className="sm:col-span-2"
              rows={8}
            />
          </div>

          <div className="flex gap-2">
            <Button className="min-w-[140px]" disabled={busy} onClick={submit}>
              {busy ? "Сохранение…" : mode === "edit" ? "Сохранить" : "Создать"}
            </Button>
            {mode === "edit" && worldId && <Badge color="neutral">ID {worldId}</Badge>}
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="space-y-3 p-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-800 dark:text-dark-100">Карточка мира</h3>
              <p className="text-xs text-gray-500 dark:text-dark-300">Так мир будет выглядеть в списке и подборках.</p>
            </div>
            <div className="rounded-3xl border border-gray-200 bg-gradient-to-br from-white via-white to-primary-50/60 p-6 shadow-inner dark:border-dark-600 dark:from-dark-700 dark:via-dark-700 dark:to-dark-800">
              <span className="text-xs uppercase tracking-wide text-primary-600">{localeLabel}</span>
              <h4 className="mt-1 text-xl font-semibold text-gray-900 dark:text-dark-50">{title || "Новый мир"}</h4>
              <p className="mt-3 text-sm text-gray-700 dark:text-dark-200">{previewBody}</p>
            </div>
          </Card>

          <Card className="space-y-2 p-6 text-sm text-gray-600 dark:text-dark-200">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-dark-100">Подсказки</h3>
            <ul className="list-disc space-y-1 pl-5">
              <li>Фиксируйте ключевые локации, фракции и NPC — это помогает передавать контекст между командами.</li>
              <li>Опишите ограничения или «тон», чтобы генеративные сценарии оставались в рамках.</li>
              <li>Добавьте ссылки на связанные документы или Miro, если мир создаётся совместно с другими командами.</li>
            </ul>
          </Card>
        </div>
      </div>
    </ContentLayout>
  );
}

