import React from 'react';
import { Badge, Button, Card, Select, Spinner, Textarea } from '@ui';
import type { Model } from '../types';
import { Send } from '@icons';

type PlaygroundSectionProps = {
  models: Model[];
  selectedModel: string;
  onSelectModel: (id: string) => void;
  prompt: string;
  onChangePrompt: (value: string) => void;
  onUseTemplate: () => void;
  onRun: () => void;
  busy: boolean;
  latency: number | null;
  result: string | null;
  error: string | null;
};

export function PlaygroundSection({
  models,
  selectedModel,
  onSelectModel,
  prompt,
  onChangePrompt,
  onUseTemplate,
  onRun,
  busy,
  latency,
  result,
  error,
}: PlaygroundSectionProps) {
  const current = React.useMemo(() => models.find((item) => item.id === selectedModel) || null, [models, selectedModel]);

  return (
    <Card
      skin="none"
      className="rounded-2xl border border-white/50 bg-white/70 px-0 py-0 shadow-lg shadow-indigo-100/40 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/70 dark:shadow-none"
    >
      <div className="space-y-6 p-6 lg:p-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">Playground</div>
            <p className="mt-1 max-w-xl text-xs text-slate-500 dark:text-slate-400">
              Быстрый тест выбранной модели. Для продакшена используйте клиентские SDK – этот инструмент только для проверки конфигурации.
            </p>
          </div>
          <Badge color="neutral" variant="soft" className="text-[11px] uppercase tracking-wide">
            не логируется
          </Badge>
        </div>

        <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div>
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Модель</div>
            <Select
              value={selectedModel}
              onChange={(e: any) => onSelectModel(e.target.value)}
              className="mt-1 h-11 w-full rounded-full border-transparent bg-white/80 px-4 text-sm shadow-inner focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:bg-slate-900/60"
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.provider_slug}:{model.name}
                </option>
              ))}
            </Select>
            {current ? (
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500 dark:text-slate-400">
                <span>
                  Провайдер: <span className="font-medium text-slate-700 dark:text-slate-200">{current.provider_slug}</span>
                </span>
                {current.version ? (
                  <span>
                    Версия: <span className="font-medium text-slate-700 dark:text-slate-200">{current.version}</span>
                  </span>
                ) : null}
              </div>
            ) : null}
          </div>
          <div className="flex flex-col gap-2 md:items-end">
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Шаблон подсказки</div>
            <Button size="sm" variant="ghost" color="neutral" className="rounded-full px-4" onClick={onUseTemplate}>
              Заполнить примером
            </Button>
          </div>
        </div>

        <Textarea
          placeholder="Введите prompt для теста модели"
          value={prompt}
          onChange={(e) => onChangePrompt(e.target.value)}
          rows={6}
          className="rounded-2xl border border-white/60 bg-white/80 p-4 text-sm text-slate-800 shadow-inner focus:border-primary-300 focus:ring-2 focus:ring-primary-200 dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-100"
        />

        <div className="flex flex-wrap items-center gap-3">
          <Button
            onClick={onRun}
            disabled={!prompt.trim() || busy}
            className="rounded-full px-5"
          >
            {busy ? (
              <span className="flex items-center gap-2">
                <Spinner size="sm" />
                Отправляем...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Send className="h-4 w-4" />
                Выполнить запрос
              </span>
            )}
          </Button>
          {latency != null ? <span className="text-xs text-slate-500 dark:text-slate-400">Latency: {latency} мс</span> : null}
        </div>

        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50/80 p-4 text-xs text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/40 dark:text-rose-200">
            {error}
          </div>
        ) : null}

        {result ? (
          <pre className="max-h-96 overflow-auto rounded-2xl border border-white/60 bg-slate-900/90 p-4 text-xs text-slate-100 shadow-inner">
            {result}
          </pre>
        ) : null}
      </div>
    </Card>
  );
}
