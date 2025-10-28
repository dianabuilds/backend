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
import {
  CheckCircle2,
  Coins,
  CreditCard,
  Timer,
} from '@icons';

import type {
  BillingContract,
  BillingContractEvent,
  BillingContractPayload,
} from '@shared/types/management';

import {
  formatDate,
  getContractStats,
  getTxStatusMeta,
  txExplorerUrl,
} from '../helpers';

const PAGE_SIZE = 10;

type ContractsTabProps = {
  contracts: BillingContract[];
  contractEvents: BillingContractEvent[];
  onSave: (payload: BillingContractPayload) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onLoadEvents: (params: {
    contractIdOrSlug?: string;
    limit?: number;
    signal?: AbortSignal;
  }) => Promise<BillingContractEvent[]>;
};

type EditableBillingContract = BillingContract & {
  abi_text?: string | null;
};

export function ContractsTab({
  contracts,
  contractEvents,
  onSave,
  onDelete,
  onLoadEvents,
}: ContractsTabProps): React.ReactElement {
  const { pushToast } = useToast();

  const [page, setPage] = React.useState(1);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<EditableBillingContract | null>(null);
  const [selectedContract, setSelectedContract] = React.useState<BillingContract | null>(null);
  const [events, setEvents] = React.useState<BillingContractEvent[]>([]);
  const [eventsLimit, setEventsLimit] = React.useState(25);
  const [eventsLoading, setEventsLoading] = React.useState(false);

  const stats = React.useMemo(() => getContractStats(contracts), [contracts]);

  const contractsPage = React.useMemo(() => {
    const total = Math.max(1, Math.ceil(contracts.length / PAGE_SIZE));
    const current = Math.min(Math.max(1, page), total);
    const start = (current - 1) * PAGE_SIZE;
    return {
      total,
      page: current,
      items: contracts.slice(start, start + PAGE_SIZE),
    };
  }, [contracts, page]);

  React.useEffect(() => {
    if (!selectedContract) {
      setEvents(contractEvents.slice(0, eventsLimit));
      return;
    }
    const controller = new AbortController();
    setEventsLoading(true);
    void onLoadEvents({
      contractIdOrSlug: selectedContract.slug || selectedContract.id,
      limit: eventsLimit,
      signal: controller.signal,
    })
      .then((result) => setEvents(result))
      .finally(() => setEventsLoading(false));
    return () => controller.abort();
  }, [contractEvents, eventsLimit, onLoadEvents, selectedContract]);

  const openNewContract = () => {
    setEditing({
      id: '',
      slug: '',
      title: '',
      chain: '',
      address: '',
      type: 'ERC-20',
      enabled: true,
      testnet: false,
      methods: { list: [], roles: [] },
      status: 'active',
      abi_present: false,
      webhook_url: '',
      abi_text: '',
    });
    setDrawerOpen(true);
  };

  const editContract = (contract: BillingContract) => {
    setEditing({
      ...contract,
      methods: contract.methods
        ? { ...contract.methods }
        : { list: [], roles: [] },
      abi_text: '',
    });
    setDrawerOpen(true);
  };

  const saveContract = async () => {
    if (!editing) return;
    const payload: BillingContractPayload = { ...editing };
    if (typeof payload.abi_text === 'string' && payload.abi_text.trim().length) {
      try {
        payload.abi = JSON.parse(payload.abi_text);
      } catch {
        payload.abi = undefined;
      }
    }
    delete payload.abi_text;

    try {
      await onSave(payload);
      pushToast({ intent: 'success', description: 'Контракт сохранён' });
      setDrawerOpen(false);
    } catch (err) {
      pushToast({
        intent: 'error',
        description:
          err instanceof Error ? err.message : 'Не удалось сохранить контракт',
      });
    }
  };

  const deleteContract = async (id: string) => {
    try {
      await onDelete(id);
      pushToast({ intent: 'info', description: 'Контракт удалён' });
    } catch (err) {
      pushToast({
        intent: 'error',
        description:
          err instanceof Error ? err.message : 'Не удалось удалить контракт',
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <CreditCard className="h-5 w-5 text-primary-500" />
            <div>
              <div className="text-xs text-gray-500">Всего контрактов</div>
              <div className="text-lg font-semibold text-gray-900">{stats.total}</div>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            <div>
              <div className="text-xs text-gray-500">Активных</div>
              <div className="text-lg font-semibold text-gray-900">{stats.enabled}</div>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Timer className="h-5 w-5 text-sky-500" />
            <div>
              <div className="text-xs text-gray-500">Testnet</div>
              <div className="text-lg font-semibold text-gray-900">{stats.testnet}</div>
            </div>
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <Coins className="h-5 w-5 text-violet-500" />
            <div>
              <div className="text-xs text-gray-500">Mainnet</div>
              <div className="text-lg font-semibold text-gray-900">{stats.mainnet}</div>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Контракты</h2>
            <p className="text-sm text-gray-500">Список контрактов и их статусы.</p>
          </div>
          <Button size="sm" onClick={openNewContract}>
            Новый контракт
          </Button>
        </div>

        <Table.Table>
          <Table.THead>
            <Table.TR>
              <Table.TH>Название</Table.TH>
              <Table.TH>Сеть</Table.TH>
              <Table.TH>Адрес</Table.TH>
              <Table.TH>Тип</Table.TH>
              <Table.TH>Статус</Table.TH>
              <Table.TH>Действия</Table.TH>
            </Table.TR>
          </Table.THead>
          <Table.TBody>
            {contractsPage.items.map((contract) => (
              <Table.TR key={contract.id}>
                <Table.TD>{contract.title || contract.slug}</Table.TD>
                <Table.TD>
                  <Badge color={contract.testnet ? 'neutral' : 'primary'}>
                    {contract.chain || '—'}
                    {contract.testnet ? ' test' : ''}
                  </Badge>
                </Table.TD>
                <Table.TD className="font-mono text-xs">{contract.address || '—'}</Table.TD>
                <Table.TD>{contract.type || 'custom'}</Table.TD>
                <Table.TD>
                  <Badge color={contract.enabled ? 'success' : 'neutral'}>
                    {contract.status || (contract.enabled ? 'active' : 'inactive')}
                  </Badge>
                </Table.TD>
                <Table.TD>
                  <div className="flex items-center gap-2">
                    <Button
                      size="xs"
                      variant="ghost"
                      onClick={() => setSelectedContract(contract)}
                    >
                      События
                    </Button>
                    <Button
                      size="xs"
                      variant="ghost"
                      onClick={() => editContract(contract)}
                    >
                      Редактировать
                    </Button>
                    <Button
                      size="xs"
                      variant="ghost"
                      color="error"
                      onClick={() => void deleteContract(contract.id)}
                    >
                      Удалить
                    </Button>
                  </div>
                </Table.TD>
              </Table.TR>
            ))}
          </Table.TBody>
        </Table.Table>

        <div className="mt-4 flex justify-end">
          <Pagination
            page={contractsPage.page}
            total={contractsPage.total}
            onChange={setPage}
          />
        </div>
      </Card>

      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Таймлайн событий</h3>
            <p className="text-xs text-gray-500">
              Последние события выбранного контракта или общий список.
            </p>
          </div>
          {selectedContract ? (
            <div className="text-xs text-gray-500">
              Выбран: {selectedContract.title || selectedContract.slug}
            </div>
          ) : null}
        </div>
        <Table.Table>
          <Table.THead>
            <Table.TR>
              <Table.TH>Время</Table.TH>
              <Table.TH>Контракт</Table.TH>
              <Table.TH>Event</Table.TH>
              <Table.TH>Status</Table.TH>
              <Table.TH>Tx</Table.TH>
            </Table.TR>
          </Table.THead>
          <Table.TBody>
            {(selectedContract ? events : contractEvents).map((event, index) => {
              const contract =
                contracts.find(
                  (item) =>
                    item.id === event.contract_id ||
                    item.slug === event.contract_id,
                ) || selectedContract;
              const statusMeta = getTxStatusMeta(event.status);
              const explorer = txExplorerUrl(contract?.chain, event.tx_hash || '');
              return (
                <Table.TR key={(event.id || 'evt') + '-' + index}>
                  <Table.TD>{formatDate(event.created_at)}</Table.TD>
                  <Table.TD>{contract ? contract.title || contract.slug : event.contract_id}</Table.TD>
                  <Table.TD>{event.event || '—'}</Table.TD>
                  <Table.TD>
                    <Badge color={statusMeta.color}>{statusMeta.label}</Badge>
                  </Table.TD>
                  <Table.TD>
                    {explorer ? (
                      <a
                        className="text-primary-600 hover:underline"
                        href={explorer}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {(event.tx_hash || '').slice(0, 10)}…
                      </a>
                    ) : (
                      event.tx_hash || '—'
                    )}
                  </Table.TD>
                </Table.TR>
              );
            })}
          </Table.TBody>
        </Table.Table>
        <div className="flex items-center justify-between gap-2">
          {selectedContract ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelectedContract(null)}
            >
              Показать все события
            </Button>
          ) : <span />}
          <Button
            size="sm"
            variant="ghost"
            disabled={eventsLoading}
            onClick={() => setEventsLimit((prev) => prev + 25)}
          >
            {eventsLoading ? 'Загрузка…' : 'Загрузить ещё'}
          </Button>
        </div>
      </Card>

      <Drawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title={editing?.title || 'Контракт'}
        widthClass="w-[720px]"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setDrawerOpen(false)}>
              Отмена
            </Button>
            <Button onClick={() => void saveContract()}>Сохранить</Button>
          </div>
        }
      >
        {editing ? (
          <div className="space-y-3 px-4 py-5 text-sm">
            <div className="grid gap-3 md:grid-cols-2">
              <Input
                label="Название"
                value={editing.title || ''}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev ? { ...prev, title: event.target.value } : prev,
                  )
                }
              />
              <Input
                label="Slug"
                value={editing.slug || ''}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev ? { ...prev, slug: event.target.value } : prev,
                  )
                }
              />
              <Select
                label="Сеть"
                value={editing.chain || ''}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev ? { ...prev, chain: event.target.value } : prev,
                  )
                }
              >
                <option value="">—</option>
                <option value="ethereum">Ethereum</option>
                <option value="polygon">Polygon</option>
                <option value="bsc">BSC</option>
                <option value="ton">TON</option>
              </Select>
              <Select
                label="Тип"
                value={editing.type || ''}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev ? { ...prev, type: event.target.value } : prev,
                  )
                }
              >
                <option value="ERC-20">ERC-20</option>
                <option value="ERC-721">ERC-721</option>
                <option value="ERC-1155">ERC-1155</option>
                <option value="custom">custom</option>
              </Select>
              <Input
                label="Адрес"
                value={editing.address || ''}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev ? { ...prev, address: event.target.value } : prev,
                  )
                }
              />
              <Input
                label="Webhook URL"
                value={editing.webhook_url || ''}
                onChange={(event) =>
                  setEditing((prev) =>
                    prev ? { ...prev, webhook_url: event.target.value } : prev,
                  )
                }
              />
            </div>
            <Textarea
              label="ABI JSON"
              rows={6}
              value={(editing as EditableBillingContract).abi_text || ''}
              onChange={(event) =>
                setEditing((prev) =>
                  prev
                    ? { ...prev, abi_text: event.target.value }
                    : prev,
                )
              }
            />
            <Input
              label="Методы (через запятую)"
              value={(editing.methods?.list || []).join(', ')}
              onChange={(event) =>
                setEditing((prev) =>
                  prev
                    ? {
                        ...prev,
                        methods: {
                          ...((prev.methods as Record<string, unknown>) || {}),
                          list: event.target.value
                            .split(',')
                            .map((item) => item.trim())
                            .filter(Boolean),
                        },
                      }
                    : prev,
                )
              }
            />
            <Input
              label="Роли (через запятую)"
              value={(editing.methods?.roles || []).join(', ')}
              onChange={(event) =>
                setEditing((prev) =>
                  prev
                    ? {
                        ...prev,
                        methods: {
                          ...((prev.methods as Record<string, unknown>) || {}),
                          roles: event.target.value
                            .split(',')
                            .map((item) => item.trim())
                            .filter(Boolean),
                        },
                      }
                    : prev,
                )
              }
            />
            <Input
              label="Статус"
              value={editing.status || ''}
              onChange={(event) =>
                setEditing((prev) =>
                  prev ? { ...prev, status: event.target.value } : prev,
                )
              }
            />
          </div>
        ) : null}
      </Drawer>
    </div>
  );
}
