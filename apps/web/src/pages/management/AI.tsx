import React from 'react';
import { AlertTriangle, FileCode2, Gauge, Link2 } from '@icons';
import { Button, Card, PageHeader, Spinner, Tabs } from '@ui';
import { apiDelete, apiPost } from '../../shared/api/client';
import { useAuth } from '../../shared/auth';
import { FallbacksSection } from './ai/components/FallbacksSection';
import { ModelDrawer } from './ai/components/ModelDrawer';
import { ModelsSection } from './ai/components/ModelsSection';
import { PlaygroundSection } from './ai/components/PlaygroundSection';
import { ProviderDrawer } from './ai/components/ProviderDrawer';
import { ProvidersSection } from './ai/components/ProvidersSection';
import { UsageSection } from './ai/components/UsageSection';
import { useAiManagement } from './ai/hooks/useAiManagement';
import { buildUsageRows, groupFallbacksByPrimary, groupFallbacksBySecondary } from './ai/utils';
import type { Model, ModelFormState, Provider, ProviderFormState } from './ai/types';

const TAB_ITEMS = [
  { key: 'overview', label: 'Обзор' },
  { key: 'models', label: 'Модели' },
  { key: 'providers', label: 'Провайдеры' },
  { key: 'fallbacks', label: 'Fallback' },
  { key: 'playground', label: 'Playground' },
] as const;

type TabKey = (typeof TAB_ITEMS)[number]['key'];

export default function ManagementAI() {
  const { user } = useAuth();
  const {
    models,
    providers,
    fallbacks,
    metrics,
    loading,
    refreshing,
    error,
    loadAll,
  } = useAiManagement();

  const [activeTab, setActiveTab] = React.useState<TabKey>('overview');

  const roles = React.useMemo(() => {
    const result = new Set<string>();
    if (user?.role) result.add(String(user.role).toLowerCase());
    (user?.roles || []).forEach((role) => result.add(String(role).toLowerCase()));
    return Array.from(result);
  }, [user]);

  const hasProviderAccess = React.useMemo(
    () => roles.some((role) => role === 'admin' || role === 'support' || role.includes('platform_admin') || role.includes('platform-admin')),
    [roles],
  );

  const usageRows = React.useMemo(() => buildUsageRows(metrics), [metrics]);
  const fallbackByPrimary = React.useMemo(() => groupFallbacksByPrimary(fallbacks), [fallbacks]);
  const fallbackBySecondary = React.useMemo(() => groupFallbacksBySecondary(fallbacks), [fallbacks]);

  const activeModels = React.useMemo(() => models.filter((m) => (m.status || 'active') !== 'disabled'), [models]);
  const totalActiveModels = activeModels.length;
  const fallbackCount = fallbacks.length;
  const totalErrors = usageRows.reduce((acc, row) => acc + row.errors, 0);
  const totalCalls = usageRows.reduce((acc, row) => acc + row.calls, 0);
  const enabledProviders = providers.filter((p) => p.enabled !== false).length;
  const avgLatency = React.useMemo(() => {
    const latencies = metrics?.latency_avg_ms || [];
    if (!latencies.length) return null;
    const sum = latencies.reduce((acc, row) => acc + (row.avg_ms || 0), 0);
    return Math.round(sum / latencies.length);
  }, [metrics]);

  const [modelDrawerOpen, setModelDrawerOpen] = React.useState(false);
  const [modelForm, setModelForm] = React.useState<ModelFormState | null>(null);
  const [modelSaving, setModelSaving] = React.useState(false);
  const [busyModelId, setBusyModelId] = React.useState<string | null>(null);

  const [providerDrawerOpen, setProviderDrawerOpen] = React.useState(false);
  const [providerForm, setProviderForm] = React.useState<ProviderFormState | null>(null);
  const [providerSaving, setProviderSaving] = React.useState(false);
  const [busyProviderSlug, setBusyProviderSlug] = React.useState<string | null>(null);

  const [fallbackDraft, setFallbackDraft] = React.useState({ primary: '', fallback: '', mode: 'on_error', priority: 100 });
  const [fallbackSaving, setFallbackSaving] = React.useState(false);
  const [fallbackRemoving, setFallbackRemoving] = React.useState<string | null>(null);

  const [playgroundPrompt, setPlaygroundPrompt] = React.useState('');
  const [playgroundModel, setPlaygroundModel] = React.useState('');
  const [playgroundResult, setPlaygroundResult] = React.useState<string | null>(null);
  const [playgroundBusy, setPlaygroundBusy] = React.useState(false);
  const [playgroundLatency, setPlaygroundLatency] = React.useState<number | null>(null);
  const [playgroundError, setPlaygroundError] = React.useState<string | null>(null);

  React.useEffect(() => {
    setPlaygroundModel((prev) => {
      if (!models.length) return '';
      if (prev && models.some((m) => m.id === prev)) return prev;
      return models[0].id;
    });
    setFallbackDraft((prev) => {
      const hasPrimary = prev.primary && models.some((m) => m.name === prev.primary);
      const hasFallback = prev.fallback && models.some((m) => m.name === prev.fallback);
      return {
        ...prev,
        primary: hasPrimary ? prev.primary : '',
        fallback: hasFallback ? prev.fallback : '',
      };
    });
  }, [models]);

  const summaryCards = React.useMemo(
    () => [
      {
        title: 'Активные LLM',
        value: totalActiveModels,
        hint: models.length ? `из ${models.length}` : 'нет моделей',
        icon: FileCode2,
        tone: 'bg-violet-50 text-violet-700',
      },
      {
        title: 'Fallback-правила',
        value: fallbackCount,
        hint: fallbackCount ? 'активные правила' : 'не настроены',
        icon: Link2,
        tone: 'bg-sky-50 text-sky-700',
      },
      {
        title: 'Ошибки LLM',
        value: totalErrors,
        hint: totalCalls ? `из ${totalCalls}` : 'нет данных',
        icon: AlertTriangle,
        tone: 'bg-rose-50 text-rose-700',
      },
      {
        title: 'Средняя латентность',
        value: avgLatency != null ? `${avgLatency} мс` : '—',
        hint: `провайдеров: ${enabledProviders}`,
        icon: Gauge,
        tone: 'bg-emerald-50 text-emerald-700',
      },
    ],
    [totalActiveModels, models.length, fallbackCount, totalErrors, totalCalls, avgLatency, enabledProviders],
  );

  const startCreateModel = React.useCallback(() => {
    setModelForm(createEmptyModelForm(providers));
    setModelDrawerOpen(true);
  }, [providers]);

  const startEditModel = React.useCallback((model: Model) => {
    setModelForm(createFormFromModel(model));
    setModelDrawerOpen(true);
  }, []);

  const openProviderDrawer = React.useCallback((provider?: Provider) => {
    if (!hasProviderAccess) return;
    if (provider) {
      setProviderForm({
        slug: provider.slug,
        title: provider.title ?? '',
        enabled: provider.enabled !== false,
        base_url: provider.base_url ?? '',
        timeout_sec: provider.timeout_sec ?? null,
        retries: provider.extras?.retries ?? null,
        api_key: '',
        originalSlug: provider.slug,
      });
    } else {
      setProviderForm({
        slug: '',
        title: '',
        enabled: true,
        base_url: '',
        timeout_sec: 30,
        retries: 0,
        api_key: '',
      });
    }
    setProviderDrawerOpen(true);
  }, [hasProviderAccess]);

  const handleSubmitModel = React.useCallback(
    async (form: ModelFormState) => {
      setModelSaving(true);
      try {
        await apiPost('/v1/ai/admin/models', {
          id: form.id || undefined,
          name: form.name.trim(),
          provider_slug: form.provider_slug.trim(),
          version: form.version?.trim() || undefined,
          status: form.status || 'active',
          is_default: !!form.is_default,
          params: {
            limits: {
              daily_tokens: form.params.limits?.daily_tokens ?? undefined,
              monthly_tokens: form.params.limits?.monthly_tokens ?? undefined,
            },
            usage: {
              content: !!form.params.usage?.content,
              quests: !!form.params.usage?.quests,
              moderation: !!form.params.usage?.moderation,
            },
            fallback_priority: form.params.fallback_priority ?? undefined,
            mode: form.params.mode ?? undefined,
          },
        });
        setModelDrawerOpen(false);
        setModelForm(null);
        await loadAll({ silent: true });
      } finally {
        setModelSaving(false);
      }
    },
    [loadAll],
  );

  const handleToggleModel = React.useCallback(
    async (model: Model) => {
      setBusyModelId(model.id);
      try {
        const current = (model.status || 'active') !== 'disabled';
        const status = current ? 'disabled' : 'active';
        await apiPost('/v1/ai/admin/models', {
          id: model.id,
          name: model.name,
          provider_slug: model.provider_slug,
          version: model.version || undefined,
          status,
          params: model.params || {},
        });
        await loadAll({ silent: true });
      } finally {
        setBusyModelId(null);
      }
    },
    [loadAll],
  );

  const handleDeleteModel = React.useCallback(
    async (model: Model) => {
      if (!model?.id) return;
      setBusyModelId(model.id);
      try {
        await apiDelete(`/v1/ai/admin/models/${encodeURIComponent(model.id)}`);
        await loadAll({ silent: true });
      } finally {
        setBusyModelId(null);
      }
    },
    [loadAll],
  );

  const handleSaveProvider = React.useCallback(
    async (form: ProviderFormState) => {
      if (!hasProviderAccess) return;
      setProviderSaving(true);
      try {
        await apiPost('/v1/ai/admin/providers', {
          slug: form.slug.trim(),
          title: form.title?.trim() || undefined,
          enabled: form.enabled,
          base_url: form.base_url?.trim() || undefined,
          timeout_sec: form.timeout_sec ?? undefined,
          api_key: form.api_key?.trim() || undefined,
          extras: form.retries != null ? { retries: form.retries } : undefined,
        });
        setProviderDrawerOpen(false);
        setProviderForm(null);
        await loadAll({ silent: true });
      } finally {
        setProviderSaving(false);
      }
    },
    [hasProviderAccess, loadAll],
  );

  const handleToggleProvider = React.useCallback(
    async (provider: Provider) => {
      if (!hasProviderAccess) return;
      setBusyProviderSlug(provider.slug);
      try {
        const current = provider.enabled !== false;
        await apiPost('/v1/ai/admin/providers', {
          slug: provider.slug,
          title: provider.title ?? undefined,
          enabled: !current,
          base_url: provider.base_url ?? undefined,
          timeout_sec: provider.timeout_sec ?? undefined,
          extras: provider.extras ?? undefined,
        });
        await loadAll({ silent: true });
      } finally {
        setBusyProviderSlug(null);
      }
    },
    [hasProviderAccess, loadAll],
  );

  const handleCreateFallback = React.useCallback(async () => {
    if (!fallbackDraft.primary || !fallbackDraft.fallback || fallbackDraft.primary === fallbackDraft.fallback) return;
    setFallbackSaving(true);
    try {
      await apiPost('/v1/ai/admin/fallbacks', {
        primary_model: fallbackDraft.primary,
        fallback_model: fallbackDraft.fallback,
        mode: fallbackDraft.mode,
        priority: fallbackDraft.priority,
      });
      setFallbackDraft((prev) => ({ ...prev, fallback: '' }));
      await loadAll({ silent: true });
    } finally {
      setFallbackSaving(false);
    }
  }, [fallbackDraft, loadAll]);

  const handleRemoveFallback = React.useCallback(
    async (id: string) => {
      setFallbackRemoving(id);
      try {
        await apiDelete(`/v1/ai/admin/fallbacks/${encodeURIComponent(id)}`);
        await loadAll({ silent: true });
      } finally {
        setFallbackRemoving(null);
      }
    },
    [loadAll],
  );

  const handlePlayground = React.useCallback(async () => {
    if (!playgroundPrompt.trim()) return;
    setPlaygroundBusy(true);
    setPlaygroundResult(null);
    setPlaygroundError(null);
    const started = performance.now();
    try {
      const selected = models.find((m) => m.id === playgroundModel);
      const response = await apiPost<{ result?: string }>('/v1/ai/admin/playground', {
        prompt: playgroundPrompt,
        model: selected?.name || undefined,
        model_id: selected?.id || undefined,
        provider: selected?.provider_slug || undefined,
      });
      setPlaygroundResult(String(response?.result ?? ''));
    } catch (err: any) {
      setPlaygroundError(String(err?.message || err || 'Не удалось выполнить запрос'));
    } finally {
      setPlaygroundLatency(Math.round(performance.now() - started));
      setPlaygroundBusy(false);
    }
  }, [models, playgroundModel, playgroundPrompt]);

  const handleUseTemplate = React.useCallback(() => {
    setPlaygroundPrompt((prev) => prev || 'Ты — ассистент Caves. Ответь, что админ-панель готова к обновлению.');
  }, []);

  return (
    <div className='p-6 space-y-6'>
      <PageHeader
        title='AI & LLM — управление моделями'
        description='Выберите активные модели, настройте fallback-политику и провайдеров. Изменения применяются мгновенно — проверяйте значения перед сохранением.'
        stats={summaryCards.map((item) => ({ label: item.title, value: item.value, hint: item.hint }))}
        actions={
          <div className='flex flex-wrap items-center gap-3'>
            <Button variant='outlined' color='neutral' onClick={() => void loadAll({ silent: true })} disabled={refreshing}>
              {refreshing ? (
                <span className='flex items-center gap-2'>
                  <Spinner size='sm' />
                  Обновляем...
                </span>
              ) : (
                'Обновить'
              )}
            </Button>
            <Button onClick={startCreateModel}>Добавить модель</Button>
          </div>
        }
      />

      {loading ? (
        <Card>
          <div className='flex items-center gap-3 p-6 text-sm text-gray-500'>
            <Spinner />
            <span>Загружаем конфигурацию AI...</span>
          </div>
        </Card>
      ) : (
        <>
          {error ? (
            <Card>
              <div className='p-4 text-sm text-rose-600'>{error}</div>
            </Card>
          ) : null}

          <div className='space-y-4'>
            <Tabs
              items={TAB_ITEMS.map((tab) => ({ key: tab.key, label: tab.label }))}
              value={activeTab}
              onChange={(key) => setActiveTab(key as TabKey)}
            />

            {activeTab === 'overview' ? (
              <div className='space-y-6'>
                <div className='grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4'>
                  {summaryCards.map((card) => {
                    const Icon = card.icon;
                    return (
                      <Card key={card.title}>
                        <div className={`p-6 lg:p-8 flex items-start gap-4 rounded-md ${card.tone}`}>
                          <div className='rounded-full bg-white/70 p-2'>
                            <Icon className='h-5 w-5' />
                          </div>
                          <div>
                            <div className='text-xs text-gray-600'>{card.title}</div>
                            <div className='text-2xl font-semibold tracking-tight'>{card.value}</div>
                            <div className='text-xs text-gray-500'>{card.hint}</div>
                          </div>
                        </div>
                      </Card>
                    );
                  })}
                </div>

                <UsageSection usageRows={usageRows} />
              </div>
            ) : null}

            {activeTab === 'models' ? (
              <ModelsSection
                models={models}
                providers={providers}
                usageRows={usageRows}
                fallbackByPrimary={fallbackByPrimary}
                fallbackBySecondary={fallbackBySecondary}
                busyModelId={busyModelId}
                onCreateModel={startCreateModel}
                onEditModel={startEditModel}
                onToggleModel={(model) => void handleToggleModel(model)}
                onDeleteModel={(model) => void handleDeleteModel(model)}
              />
            ) : null}

            {activeTab === 'providers' ? (
              <ProvidersSection
                providers={providers}
                hasProviderAccess={hasProviderAccess}
                busyProviderSlug={busyProviderSlug}
                onToggleProvider={(provider) => void handleToggleProvider(provider)}
                onOpenProvider={(provider) => openProviderDrawer(provider)}
              />
            ) : null}

            {activeTab === 'fallbacks' ? (
              <FallbacksSection
                models={models}
                fallbacks={fallbacks}
                draft={fallbackDraft}
                onDraftChange={setFallbackDraft}
                onCreateFallback={() => void handleCreateFallback()}
                onRemoveFallback={(id) => void handleRemoveFallback(id)}
                saving={fallbackSaving}
                removingId={fallbackRemoving}
              />
            ) : null}

            {activeTab === 'playground' ? (
              <PlaygroundSection
                models={models}
                selectedModel={playgroundModel}
                onSelectModel={setPlaygroundModel}
                prompt={playgroundPrompt}
                onChangePrompt={setPlaygroundPrompt}
                onUseTemplate={handleUseTemplate}
                onRun={() => void handlePlayground()}
                busy={playgroundBusy}
                latency={playgroundLatency}
                result={playgroundResult}
                error={playgroundError}
              />
            ) : null}
          </div>
        </>
      )}

      <ModelDrawer
        open={modelDrawerOpen}
        model={modelForm}
        providers={providers}
        saving={modelSaving}
        onClose={() => {
          setModelDrawerOpen(false);
          setModelForm(null);
        }}
        onSubmit={(form) => void handleSubmitModel(form)}
        onCreateProvider={hasProviderAccess ? () => openProviderDrawer() : undefined}
        hasProviderAccess={hasProviderAccess}
      />

      <ProviderDrawer
        open={providerDrawerOpen}
        provider={providerForm}
        saving={providerSaving}
        hasAccess={hasProviderAccess}
        onClose={() => {
          setProviderDrawerOpen(false);
          setProviderForm(null);
        }}
        onSubmit={(form) => void handleSaveProvider(form)}
      />
    </div>
  );
}

function createEmptyModelForm(providers: Provider[]): ModelFormState {
  return {
    name: '',
    provider_slug: providers[0]?.slug || '',
    version: '',
    status: 'active',
    is_default: false,
    params: {
      limits: {},
      usage: {},
      fallback_priority: 100,
    },
  };
}

function createFormFromModel(model: Model): ModelFormState {
  return {
    id: model.id,
    name: model.name,
    provider_slug: model.provider_slug,
    version: model.version ?? '',
    status: model.status ?? 'active',
    is_default: !!model.is_default,
    params: {
      limits: {
        daily_tokens: model.params?.limits?.daily_tokens ?? null,
        monthly_tokens: model.params?.limits?.monthly_tokens ?? null,
      },
      usage: {
        content: !!model.params?.usage?.content,
        quests: !!model.params?.usage?.quests,
        moderation: !!model.params?.usage?.moderation,
      },
      fallback_priority: model.params?.fallback_priority ?? null,
      mode: model.params?.mode ?? null,
    },
  };
}
