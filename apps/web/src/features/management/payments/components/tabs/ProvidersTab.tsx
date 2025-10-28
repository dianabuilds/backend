import React from 'react';
import {
  Badge,
  Button,
  Card,
  Drawer,
  Input,
  Pagination,
  Select,
  Table,
  Textarea,
  useToast,
} from '@ui';
import { CheckCircle2, AlertTriangle, Coins, Timer } from '@icons';

import type {
  BillingContract,
  BillingKpi,
  BillingProvider,
  BillingProviderPayload,
} from '@shared/types/management';

import {
  ProviderFormState,
  DEFAULT_PROVIDER_FORM,
  providerToForm,
  parseStructuredList,
  parseStructuredTokens,
  toListString,
  centsToUsd,
} from '../helpers';

const PAGE_SIZE = 10;

type ProvidersTabProps = {
  loading: boolean;
  kpi: BillingKpi;
  providers: BillingProvider[];
  contracts: BillingContract[];
  onSave: (payload: BillingProviderPayload) => Promise<void>;
  onDelete: (slug: string) => Promise<void>;
};

export function ProvidersTab({
  loading,
  kpi,
  providers,
  contracts,
  onSave,
  onDelete,
}: ProvidersTabProps): React.ReactElement {
  const { pushToast } = useToast();

  const [page, setPage] = React.useState(1);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<ProviderFormState | null>(null);
  const [expanded, setExpanded] = React.useState<Record<string, boolean>>({});

  const buildPayload = React.useCallback(
    (
      form: ProviderFormState,
      options: { silent?: boolean } = {},
    ): BillingProviderPayload | null => {
      const { silent = false } = options;
      const slug = form.slug.trim();
      if (!slug) {
        if (!silent) {
          pushToast({ intent: 'error', description: 'Slug обязателен' });
        }
        return null;
      }

      const priority = Number.parseInt(form.priority.trim(), 10);
      const networks = parseStructuredList(form.networks);
      const tokens = parseStructuredTokens(form.supportedTokens);
      const defaultNetwork = form.defaultNetwork.trim();
      let extraConfig: Record<string, unknown> | undefined;

      if (form.extraConfig.trim()) {
        try {
          const parsed = JSON.parse(form.extraConfig);
          if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
            throw new Error('Дополнительные настройки должны быть JSON-объектом');
          }
          extraConfig = parsed as Record<string, unknown>;
        } catch (err) {
          if (!silent) {
            pushToast({
              intent: 'error',
              description:
                err instanceof Error
                  ? err.message
                  : 'Некорректный JSON в дополнительных настройках',
            });
          }
          return null;
        }
      }

      return {
        slug,
        type: form.type.trim() || 'custom',
        enabled: form.enabled,
        priority: Number.isFinite(priority) ? priority : 100,
        contract_slug: form.contractSlug.trim() || undefined,
        networks: networks ?? undefined,
        supported_tokens: tokens ?? undefined,
        default_network: defaultNetwork || undefined,
        config: extraConfig,
      };
    },
    [pushToast],
  );

  const handleCreate = () => {
    setEditing({ ...DEFAULT_PROVIDER_FORM });
    setDrawerOpen(true);
  };

  const handleEdit = (provider: BillingProvider) => {
    setEditing(providerToForm(provider));
    setDrawerOpen(true);
  };

  const handleSave = async () => {
    if (!editing) return;
    const payload = buildPayload(editing);
    if (!payload) return;
    try {
      await onSave(payload);
      pushToast({ intent: 'success', description: 'Провайдер сохранён' });
      setDrawerOpen(false);
    } catch (err) {
      pushToast({
        intent: 'error',
        description:
          err instanceof Error ? err.message : 'Не удалось сохранить провайдера',
      });
    }
  };

  const handleQuickLink = async (
    provider: BillingProvider,
    contractSlug: string,
  ) => {
    const form = providerToForm(provider);
    form.contractSlug = contractSlug;
    const payload = buildPayload(form, { silent: true });
    if (!payload) return;
    try {
      await onSave(payload);
    } catch (err) {
      pushToast({
        intent: 'error',
        description:
          err instanceof Error ? err.message : 'Не удалось обновить привязку',
      });
    }
  };

  const handleDelete = async (slug: string) => {
    try {
      await onDelete(slug);
      pushToast({ intent: 'info', description: 'Провайдер удалён' });
    } catch (err) {
      pushToast({
        intent: 'error',
        description:
          err instanceof Error ? err.message : 'Не удалось удалить провайдера',
      });
    }
  };

  const providerPage = React.useMemo(() => {
    const total = Math.max(1, Math.ceil(providers.length / PAGE_SIZE));
    const current = Math.min(Math.max(1, page), total);
    const start = (current - 1) * PAGE_SIZE;
    return {
      total,
      page: current,
      items: providers.slice(start, start + PAGE_SIZE),
    };
  }, [page, providers]);

  const kpiCards = React.useMemo(
    () => [
      {
        key: 'success',
        icon: <CheckCircle2 className="h-5 w-5" />,
        label: 'Успешные',
        value: kpi.success?.toLocaleString(),
        tone: 'bg-emerald-50 text-emerald-700',
      },
      {
        key: 'errors',
        icon: <AlertTriangle className="h-5 w-5" />,
        label: 'Ошибки',
        value: kpi.errors?.toLocaleString(),
        tone: 'bg-rose-50 text-rose-700',
      },
      {
        key: 'volume',
        icon: <Coins className="h-5 w-5" />,
        label: 'Объём (USD)',
        value: centsToUsd(kpi.volume_cents),
        tone: 'bg-sky-50 text-sky-700',
      },
      {
        key: 'pending',
        icon: <Timer className="h-5 w-5" />,
        label: 'В ожидании',
        value: kpi.pending?.toLocaleString(),
        tone: 'bg-violet-50 text-violet-700',
      },
    ],
    [kpi],
  );

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpiCards.map((card) => (
          <Card key={card.key} className="p-5 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3">
              <div
                className={['rounded-full', 'p-3', card.tone, 'flex', 'items-center', 'justify-center'].join(' ')}
              >
                {card.icon}
              </div>
              <div>
                <div className="text-xs uppercase tracking-wide text-gray-500">
                  {card.label}
                </div>
                <div className="mt-1 text-xl font-semibold text-gray-900">
                  {card.value}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      <Card className="p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Провайдеры</h2>
            <p className="text-sm text-gray-500">Управление шлюзами, сетями и маршрутизацией.</p>
          </div>
          <Button size="sm" onClick={handleCreate} disabled={loading}>
            Новый провайдер
          </Button>
        </div>

        <Table.Table zebra>
          <Table.THead>
            <Table.TR>
              <Table.TH>Slug</Table.TH>
              <Table.TH>Тип</Table.TH>
              <Table.TH>Статус</Table.TH>
              <Table.TH>Приоритет</Table.TH>
              <Table.TH>Default network</Table.TH>
              <Table.TH>Networks</Table.TH>
              <Table.TH>Tokens</Table.TH>
              <Table.TH>Контракт</Table.TH>
              <Table.TH>Действия</Table.TH>
            </Table.TR>
          </Table.THead>
          <Table.TBody>
            {providerPage.items.map((provider) => {
              const contractSlug =
                provider.contract_slug ??
                (typeof provider.config?.linked_contract === 'string'
                  ? provider.config?.linked_contract
                  : '');
              const defaultNetwork =
                provider.default_network ??
                (typeof provider.config?.default_network === 'string'
                  ? provider.config?.default_network
                  : '');
              const networksDisplay = toListString(
                provider.networks ?? provider.config?.networks,
              );
              const tokensDisplay = toListString(
                provider.supported_tokens ?? provider.config?.supported_tokens,
              );
              const isExpanded = Boolean(expanded[provider.slug]);

              return (
                <React.Fragment key={provider.slug}>
                  <Table.TR>
                    <Table.TD className="font-mono">{provider.slug}</Table.TD>
                    <Table.TD>{provider.type}</Table.TD>
                    <Table.TD>
                      <Badge color={provider.enabled ? 'success' : 'neutral'}>
                        {provider.enabled ? 'вкл' : 'выкл'}
                      </Badge>
                    </Table.TD>
                    <Table.TD>{provider.priority}</Table.TD>
                    <Table.TD>{defaultNetwork || '—'}</Table.TD>
                    <Table.TD>{networksDisplay || '—'}</Table.TD>
                    <Table.TD>{tokensDisplay || '—'}</Table.TD>
                    <Table.TD>
                      <Select
                        value={contractSlug || ''}
                        onChange={(event) =>
                          void handleQuickLink(provider, event.target.value)
                        }
                      >
                        <option value="">—</option>
                        {contracts.map((contract) => (
                          <option key={contract.slug} value={contract.slug}>
                            {contract.title || contract.slug}
                          </option>
                        ))}
                      </Select>
                    </Table.TD>
                    <Table.TD>
                      <div className="flex items-center gap-2">
                        <Button
                          size="xs"
                          variant="ghost"
                          onClick={() => handleEdit(provider)}
                        >
                          Редактировать
                        </Button>
                        <Button
                          size="xs"
                          variant="ghost"
                          color="error"
                          onClick={() => void handleDelete(provider.slug)}
                        >
                          Удалить
                        </Button>
                        <Button
                          size="xs"
                          variant="ghost"
                          onClick={() =>
                            setExpanded((prev) => ({
                              ...prev,
                              [provider.slug]: !prev[provider.slug],
                            }))
                          }
                        >
                          {isExpanded ? 'Скрыть' : 'Показать'}
                        </Button>
                      </div>
                    </Table.TD>
                  </Table.TR>
                  <Table.TR>
                    <Table.TD colSpan={9}>
                      <div
                        className={
                          isExpanded
                            ? 'overflow-hidden transition-all max-h-[320px]'
                            : 'overflow-hidden transition-all max-h-0'
                        }
                      >
                        <Card className="mt-2 bg-gray-50 p-4 text-xs">
                          <div className="grid gap-2 md:grid-cols-2">
                            <div>
                              <div className="font-semibold text-gray-700">
                                Сводка
                              </div>
                              <div className="mt-1 text-gray-600">
                                <div>Slug: {provider.slug}</div>
                                <div>Тип: {provider.type}</div>
                                <div>Контракт: {contractSlug || 'не привязан'}</div>
                              </div>
                            </div>
                            <div>
                              <div className="font-semibold text-gray-700">
                                Конфигурация
                              </div>
                              <pre className="mt-1 max-h-48 overflow-auto rounded bg-white/80 p-3">
                                {JSON.stringify(provider.config || {}, null, 2)}
                              </pre>
                            </div>
                          </div>
                        </Card>
                      </div>
                    </Table.TD>
                  </Table.TR>
                </React.Fragment>
              );
            })}
          </Table.TBody>
        </Table.Table>

        <div className="mt-4 flex justify-end">
          <Pagination
            page={providerPage.page}
            total={providerPage.total}
            onChange={setPage}
          />
        </div>
      </Card>

      <Drawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title={editing?.slug ? 'Провайдер' : 'Новый провайдер'}
        widthClass="w-[720px]"
        footer={
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-gray-500">
              Значения нормализуются перед сохранением.
            </span>
            <div className="flex items-center gap-2">
              <Button variant="ghost" onClick={() => setDrawerOpen(false)}>
                Отмена
              </Button>
              <Button onClick={() => void handleSave()}>Сохранить</Button>
            </div>
          </div>
        }
      >
        {editing ? (
          <div className="space-y-4 px-4 py-5">
            <div className="grid gap-3 md:grid-cols-2">
              <Input
                label="Slug"
                value={editing.slug}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev ? { ...prev, slug: event.target.value } : prev,
                  )
                }
                required
              />
              <Input
                label="Тип"
                value={editing.type}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev ? { ...prev, type: event.target.value } : prev,
                  )
                }
              />
              <Input
                label="Приоритет"
                type="number"
                value={editing.priority}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev ? { ...prev, priority: event.target.value } : prev,
                  )
                }
              />
              <Select
                label="Статус"
                value={editing.enabled ? 'true' : 'false'}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev
                      ? { ...prev, enabled: event.target.value !== 'false' }
                      : prev,
                  )
                }
              >
                <option value="true">enabled</option>
                <option value="false">disabled</option>
              </Select>
              <Input
                label="Contract slug"
                value={editing.contractSlug}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev
                      ? { ...prev, contractSlug: event.target.value }
                      : prev,
                  )
                }
              />
              <Input
                label="Default network"
                value={editing.defaultNetwork}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev
                      ? { ...prev, defaultNetwork: event.target.value }
                      : prev,
                  )
                }
              />
            </div>
            <Textarea
              label="Networks (JSON или CSV)"
              rows={4}
              value={editing.networks}
              onChange={(event) =>
                setEditing((prev) =>
                  prev ? { ...prev, networks: event.target.value } : prev,
                )
              }
            />
            <Textarea
              label="Supported tokens (JSON или CSV)"
              rows={3}
              value={editing.supportedTokens}
              onChange={(event) =>
                setEditing((prev) =>
                  prev ? { ...prev, supportedTokens: event.target.value } : prev,
                )
              }
            />
            <Textarea
              label="Доп. конфигурация (JSON)"
              rows={6}
              placeholder={`{
  "webhook_secret": "..."
}`}
              value={editing.extraConfig}
              onChange={(event) =>
                setEditing((prev) =>
                  prev ? { ...prev, extraConfig: event.target.value } : prev,
                )
              }
            />
            <Card className="bg-gray-50 p-4 text-xs">
              <div className="font-semibold text-gray-700">
                Предварительный просмотр payload
              </div>
              <pre className="mt-2 max-h-64 overflow-auto rounded bg-white/70 p-3">
                {buildPayload(editing, { silent: true })
                  ? JSON.stringify(buildPayload(editing, { silent: true }), null, 2)
                  : 'Заполните форму для предпросмотра итогового payload.'}
              </pre>
            </Card>
          </div>
        ) : null}
      </Drawer>
    </div>
  );
}
