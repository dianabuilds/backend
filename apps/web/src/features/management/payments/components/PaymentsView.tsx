import React from 'react';
import { ApexChart, Badge, Button, Card, Drawer, Input, Pagination, Select, Table, Textarea, Tabs, Accordion, Collapse, useToast } from '@ui';
import { useManagementPayments } from '../hooks';
import type { BillingContract, BillingContractPayload, BillingCryptoConfig, BillingProvider, BillingProviderPayload } from '@shared/types/management';
import { CheckCircle2, AlertTriangle, Coins, Timer, CreditCard } from '@icons';

type EditableBillingProvider = BillingProvider & {
  config: Record<string, unknown>;
};

type EditableBillingContract = BillingContract & {
  abi_text?: string | null;
};

export default function ManagementPayments() {
  const {
    error: dataError,
    kpi,
    providers,
    transactions,
    contracts,
    contractEvents,
    cryptoConfig,
    clearError: clearDataError,
    saveProvider: persistProvider,
    deleteProvider: removeProvider,
    saveContract: persistContract,
    deleteContract: removeContract,
    updateCryptoConfig: persistCryptoConfig,
  } = useManagementPayments();
  const { pushToast } = useToast();

  const [activeTab, setActiveTab] = React.useState<'providers' | 'contracts'>('providers');
  const [provPage, setProvPage] = React.useState(1);
  const provPageSize = 10;
  const [provDrawer, setProvDrawer] = React.useState(false);
  const [provEditing, setProvEditing] = React.useState<EditableBillingProvider | null>(null);
  const [provExpanded, setProvExpanded] = React.useState<Record<string, boolean>>({});

  const [txFilter, setTxFilter] = React.useState<'all' | 'ok' | 'err'>('all');
  const [txPage, setTxPage] = React.useState(1);
  const txPageSize = 10;

  const [ctrPage, setCtrPage] = React.useState(1);
  const ctrPageSize = 10;
  const [ctrDrawer, setCtrDrawer] = React.useState(false);
  const [ctrEditing, setCtrEditing] = React.useState<EditableBillingContract | null>(null);
  const [daysWindow, setDaysWindow] = React.useState<number>(30);

  const [cryptoCfg, setCryptoCfg] = React.useState<BillingCryptoConfig>(cryptoConfig);

  React.useEffect(() => {
    setCryptoCfg(cryptoConfig);
  }, [cryptoConfig]);

  React.useEffect(() => {
    if (!dataError) return;
    pushToast({ intent: 'error', description: dataError });
    clearDataError();
  }, [clearDataError, dataError, pushToast]);


  const chainLabel = (c?: string | null) => (c ? c.toUpperCase() : '');
  const chainColor = (c?: string | null): any => (c === 'ethereum' ? 'info' : c === 'polygon' ? 'primary' : c === 'bsc' ? 'warning' : 'neutral');
  const statusColor = (s?: string | null): any => {
    const v = (s || '').toLowerCase();
    if (['succeeded', 'success', 'captured', 'active'].includes(v)) return 'success';
    if (['pending', 'test', 'processing'].includes(v)) return 'warning';
    if (['failed', 'error', 'declined'].includes(v)) return 'error';
    return 'neutral';
  };

  const filteredTx = React.useMemo(() => {
    const isOk = (s?: string | null) => /captured|succeeded|success/i.test(String(s || ''));
    const isErr = (s?: string | null) => /failed|error|declined/i.test(String(s || ''));
    if (txFilter === 'ok') return transactions.filter((t) => isOk(t.status));
    if (txFilter === 'err') return transactions.filter((t) => isErr(t.status));
    return transactions;
  }, [transactions, txFilter]);

  const paginate = <T,>(arr: T[], page: number, size: number) => {
    const total = Math.max(1, Math.ceil(arr.length / size));
    const p = Math.min(Math.max(1, page), total);
    const start = (p - 1) * size;
    return { total, page: p, items: arr.slice(start, start + size) };
  };

  // Provider actions
  const openNewProvider = () => {
    setProvEditing({
      slug: '',
      type: 'custom',
      enabled: true,
      priority: 100,
      config: {},
    });
    setProvDrawer(true);
  };

  const editProvider = (provider: BillingProvider) => {
    setProvEditing({
      ...provider,
      config: provider.config ? { ...provider.config } : {},
    });
    setProvDrawer(true);
  };

  const saveProvider = async () => {
    if (!provEditing || !provEditing.slug) return;
    const rawConfig = (provEditing.config ?? {}) as Record<string, unknown>;
    const { linked_contract, ...restConfig } = rawConfig;
    const payload: BillingProviderPayload = {
      slug: provEditing.slug,
      type: provEditing.type || 'custom',
      enabled: Boolean(provEditing.enabled),
      priority: Number.isFinite(provEditing.priority) ? Number(provEditing.priority) : 100,
      config: restConfig,
      contract_slug: typeof linked_contract === 'string' && linked_contract ? linked_contract : undefined,
    };
    await persistProvider(payload);
    setProvDrawer(false);
  };

  const deleteProvider = async (slug: string) => {
    await removeProvider(slug);
  };

  // Contract actions
  const openNewContract = () => {
    setCtrEditing({
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
    setCtrDrawer(true);
  };

  const editContract = (contract: BillingContract) => {
    setCtrEditing({
      ...contract,
      methods: contract.methods ? { ...contract.methods } : { list: [], roles: [] },
      abi_text: '',
    });
    setCtrDrawer(true);
  };

  const saveContract = async () => {
    if (!ctrEditing) return;
    const payload: BillingContractPayload = { ...ctrEditing };
    if (typeof payload.abi_text === 'string' && payload.abi_text.trim().length) {
      try {
        payload.abi = JSON.parse(payload.abi_text);
      } catch {
        payload.abi = undefined;
      }
    }
    delete payload.abi_text;
    await persistContract(payload);
    setCtrDrawer(false);
  };

  const deleteContract = async (id: string) => {
    await removeContract(id);
  };
  const contractsById = React.useMemo(() => Object.fromEntries(contracts.map((c) => [c.id, c])), [contracts]);
  const txExplorer = (chain?: string, tx?: string) => {
    if (!tx) return '';
    switch (chain) {
      case 'ethereum': return `https://etherscan.io/tx/${tx}`;
      case 'polygon': return `https://polygonscan.com/tx/${tx}`;
      case 'bsc': return `https://bscscan.com/tx/${tx}`;
      default: return '';
    }
  };

  const provPageData = paginate(providers, provPage, provPageSize);
  const txPageData = paginate(filteredTx, txPage, txPageSize);
  const ctrPageData = paginate(contracts, ctrPage, ctrPageSize);

  const chainSummary = React.useMemo(() => {
    const totals: Record<string, number> = {};
    const series: Record<string, { x: number; y: number }[]> = {};
    const now = Date.now();
    const since = now - daysWindow * 86400000;
    for (const e of contractEvents) {
      const c = contractsById[e.contract_id as string];
      if (!c) continue;
      const t = new Date(e.created_at || Date.now()).getTime();
      if (isNaN(t) || t < since) continue;
      const ch = c.chain || 'other';
      const amt = Number(e.amount || 0);
      totals[ch] = (totals[ch] || 0) + (isFinite(amt) ? amt : 0);
      if (!series[ch]) series[ch] = [];
      series[ch].push({ x: t, y: isFinite(amt) ? amt : 0 });
    }
    const items = Object.keys(totals).map((ch) => ({ chain: ch, total: totals[ch], data: (series[ch] || []).sort((a, b) => a.x - b.x) }));
    items.sort((a, b) => (b.total - a.total));
    return items.slice(0, 4);
  }, [contractEvents, contractsById, daysWindow]);

  return (
    <div className="p-6 space-y-6">
      {/* KPI row styled per Tailux banking-2 */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <Card>
          <div className="p-6 lg:p-8 bg-emerald-50 rounded-md flex items-center gap-4">
            <div className="rounded-full bg-emerald-100 text-emerald-700 p-2"><CheckCircle2 className="h-5 w-5" /></div>
            <div>
              <div className="text-xs text-gray-600" title="Количество успешных транзакций">Успешные</div>
              <div className="text-2xl font-semibold tracking-tight">{kpi.success || 0}</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6 lg:p-8 bg-rose-50 rounded-md flex items-center gap-4">
            <div className="rounded-full bg-rose-100 text-rose-700 p-2"><AlertTriangle className="h-5 w-5" /></div>
            <div>
              <div className="text-xs text-gray-600" title="Количество ошибок оплат">Ошибки</div>
              <div className="text-2xl font-semibold tracking-tight">{kpi.errors || 0}</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6 lg:p-8 bg-sky-50 rounded-md flex items-center gap-4">
            <div className="rounded-full bg-sky-100 text-sky-700 p-2"><Coins className="h-5 w-5" /></div>
            <div>
              <div className="text-xs text-gray-600" title="Общий объём (валюта из записей)">Объём ($)</div>
              <div className="text-2xl font-semibold tracking-tight">${((kpi.volume_cents || 0) / 100).toFixed(2)}</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6 lg:p-8 bg-violet-50 rounded-md flex items-center gap-4">
            <div className="rounded-full bg-violet-100 text-violet-700 p-2"><Timer className="h-5 w-5" /></div>
            <div>
              <div className="text-xs text-gray-600" title="Среднее время подтверждения">Подтверждение</div>
              <div className="text-2xl font-semibold tracking-tight">{Math.round(kpi.avg_confirm_ms || 0)} ms</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Watchlist row */}
      {chainSummary.length > 0 && (
        <Card>
          <div className="p-6 lg:p-8">
            <div className="mb-2 flex items-center justify-between">
              <div className="text-sm text-gray-500">Суммы по блокчейнам (за {daysWindow} дн.)</div>
              <Select value={String(daysWindow)} onChange={(e: any) => setDaysWindow(parseInt(e.target.value || '30', 10))}>
                <option value="7">7 дн.</option>
                <option value="30">30 дн.</option>
                <option value="90">90 дн.</option>
              </Select>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
              {chainSummary.map((it) => (
                <Card key={it.chain}>
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-gray-500">{chainLabel(it.chain)}</div>
                      <Badge color={chainColor(it.chain)}>{chainLabel(it.chain)}</Badge>
                    </div>
                    <div className="mt-1 text-lg font-semibold">{it.total.toFixed(2)}</div>
                    <div className="mt-2">
                      <ApexChart type="line" height={60} series={[{ name: 'sum', data: it.data.map((p) => ({ x: new Date(p.x).toISOString(), y: p.y })) }]} options={{ chart: { sparkline: { enabled: true } }, stroke: { width: 2 }, tooltip: { enabled: false }, xaxis: { type: 'datetime', labels: { show: false } }, yaxis: { show: false } }} />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Tabs + action */}
      <div className="space-y-3">
        <Tabs
          items={[{ key: 'providers', label: 'Провайдеры' }, { key: 'contracts', label: 'Контракты' }]}
          value={activeTab}
          onChange={(key) => setActiveTab(key as 'providers' | 'contracts')}
        />
        <div className="flex justify-end">
          {activeTab === 'providers' ? (
            <Button onClick={openNewProvider} className="flex items-center gap-2"><CreditCard className="h-4 w-4" /> Добавить провайдера</Button>
          ) : (
            <Button onClick={openNewContract}>Добавить контракт</Button>
          )}
        </div>
      </div>

      {/* Providers tab */}
      {activeTab === 'providers' && (
        <>
          <Card>
            <div className="p-6 lg:p-8">
              <div className="mb-2 text-sm text-gray-500">Провайдеры шлюзов</div>
              <Table.Table zebra>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Slug</Table.TH>
                    <Table.TH>Тип</Table.TH>
                    <Table.TH>Сеть</Table.TH>
                    <Table.TH>Валюты</Table.TH>
                    <Table.TH>Статус</Table.TH>
                    <Table.TH>Приоритет</Table.TH>
                    <Table.TH>Контракт</Table.TH>
                    <Table.TH>Действия</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {provPageData.items.map((it) => (
                    <React.Fragment key={it.slug}>
                      <Table.TR>
                        <Table.TD className="font-mono">{it.slug}</Table.TD>
                        <Table.TD>{it.type}</Table.TD>
                        <Table.TD><Badge color={it.enabled ? 'success' : 'neutral'}>{it.enabled ? 'вкл' : 'выкл'}</Badge></Table.TD>
                        <Table.TD>{it.priority}</Table.TD>
                        <Table.TD>
                          <Select
                            value={it.config?.linked_contract || ''}
                            onChange={async (e: any) => {
                              const lc = e.target.value;
                              const cfg = { ...(it.config || {}), linked_contract: lc || undefined } as Record<string, unknown>;
                              const payload: BillingProviderPayload = {
                                slug: it.slug,
                                type: it.type,
                                enabled: it.enabled,
                                priority: it.priority,
                                config: cfg,
                                contract_slug: lc || undefined,
                              };
                              await persistProvider(payload);
                            }}
                          >
                            <option value="">—</option>
                            {contracts.map((c) => <option key={c.slug} value={c.slug}>{c.title || c.slug}</option>)}
                          </Select>
                        </Table.TD>
                        <Table.TD>
                          <div className="flex items-center gap-2">
                            <Button onClick={() => editProvider(it)}>Редактировать</Button>
                            <Button onClick={() => deleteProvider(it.slug)}>Удалить</Button>
                            <Button onClick={() => setProvExpanded((s) => ({ ...s, [it.slug]: !s[it.slug] }))}>{provExpanded[it.slug] ? 'Скрыть' : 'Показать'}</Button>
                          </div>
                        </Table.TD>
                      </Table.TR>
                      <Table.TR>
                        <Table.TD colSpan={8}>
                          <Collapse open={provExpanded[it.slug]}>
                            <pre className="mt-2 rounded bg-gray-50 p-3 text-xs overflow-auto">{JSON.stringify(it.config || {}, null, 2)}</pre>
                          </Collapse>
                        </Table.TD>
                      </Table.TR>
                    </React.Fragment>
                  ))}
                </Table.TBody>
              </Table.Table>
              <div className="mt-3 flex justify-end">
                <Pagination page={provPageData.page} total={provPageData.total} onChange={setProvPage} />
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6 lg:p-8">
              <div className="mb-3 flex items-center gap-2">
                <div className="text-sm text-gray-500">Транзакции</div>
                <div className="flex gap-1">
                  <Button onClick={() => { setTxFilter('all'); setTxPage(1); }} disabled={txFilter === 'all'}>Все</Button>
                  <Button onClick={() => { setTxFilter('ok'); setTxPage(1); }} disabled={txFilter === 'ok'}>Успешные</Button>
                  <Button onClick={() => { setTxFilter('err'); setTxPage(1); }} disabled={txFilter === 'err'}>Ошибки</Button>
                </div>
              </div>
              <Table.Table>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Время</Table.TH>
                    <Table.TH>Пользователь</Table.TH>
                    <Table.TH>Провайдер</Table.TH>
                    <Table.TH>Статус</Table.TH>
                    <Table.TH>Сумма</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {txPageData.items.map((r, i) => (
                    <Table.TR key={i}>
                      <Table.TD>{r.created_at || ''}</Table.TD>
                      <Table.TD className="font-mono text-xs">{r.user_id || '-'}</Table.TD>
                      <Table.TD>{r.gateway_slug || '-'}</Table.TD>
                      <Table.TD><Badge color={statusColor(r.status)}>{r.status || '-'}</Badge></Table.TD>
                      <Table.TD>{r.currency || 'USD'} {typeof r.gross_cents === 'number' ? (r.gross_cents / 100).toFixed(2) : '-'}</Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
              <div className="mt-3 flex justify-end">
                <Pagination page={txPageData.page} total={txPageData.total} onChange={setTxPage} />
              </div>
            </div>
          </Card>
        </>
      )}

      {/* Contracts tab */}
      {activeTab === 'contracts' && (
        <>
          <Card>
            <div className="p-4">
              <div className="mb-2 text-sm text-gray-500">Контракты</div>
              <Table.Table>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Вкл</Table.TH>
                    <Table.TH>Название</Table.TH>
                    <Table.TH>Сеть</Table.TH>
                    <Table.TH>Адрес</Table.TH>
                    <Table.TH>Тип</Table.TH>
                    <Table.TH>ABI</Table.TH>
                    <Table.TH>Методы</Table.TH>
                    <Table.TH>Статус</Table.TH>
                    <Table.TH>Действия</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {ctrPageData.items.map((c) => (
                    <Table.TR key={c.id}>
                      <Table.TD><Badge color={c.enabled ? 'success' : 'neutral'}>{c.enabled ? 'on' : 'off'}</Badge></Table.TD>
                      <Table.TD>{c.title || c.slug}</Table.TD>
                      <Table.TD><Badge color={chainColor(c.chain)}>{chainLabel(c.chain)}{c.testnet ? ' test' : ''}</Badge></Table.TD>
                      <Table.TD className="font-mono text-xs">{c.address}</Table.TD>
                      <Table.TD>{c.type}</Table.TD>
                      <Table.TD>{c.abi_present ? 'да' : '—'}</Table.TD>
                      <Table.TD>{Array.isArray(c.methods?.list) ? (c.methods.list as any[]).join(', ') : '-'}</Table.TD>
                      <Table.TD><Badge color={statusColor(c.status)}>{c.status || '-'}</Badge></Table.TD>
                      <Table.TD>
                        <div className="flex gap-2">
                          <Button onClick={() => editContract(c)}>Редактировать</Button>
                          <Button onClick={() => deleteContract(c.id!)}>Удалить</Button>
                        </div>
                      </Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
              <div className="mt-3 flex justify-end">
                <Pagination page={ctrPageData.page} total={ctrPageData.total} onChange={setCtrPage} />
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <div className="mb-2 text-sm text-gray-500">Последние события контрактов</div>
              <Table.Table>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Время</Table.TH>
                    <Table.TH>Контракт</Table.TH>
                    <Table.TH>Event</Table.TH>
                    <Table.TH>Method</Table.TH>
                    <Table.TH>Status</Table.TH>
                    <Table.TH>Tx</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {(contractEvents || []).map((e, i) => {
                    const c = contractsById[e.contract_id as string];
                    const url = txExplorer(c?.chain ?? undefined, e.tx_hash ?? undefined);
                    return (
                      <Table.TR key={i}>
                        <Table.TD>{e.created_at || ''}</Table.TD>
                        <Table.TD>{c ? (c.title || c.slug) : e.contract_id}</Table.TD>
                        <Table.TD>{e.event || ''}</Table.TD>
                        <Table.TD>{e.method || ''}</Table.TD>
                        <Table.TD><Badge color={statusColor(e.status)}>{e.status || ''}</Badge></Table.TD>
                        <Table.TD>
                          {url ? <a className="text-primary-600 hover:underline" href={url} target="_blank" rel="noreferrer">{(e.tx_hash || '').slice(0, 10)}…</a> : (e.tx_hash || '')}
                        </Table.TD>
                      </Table.TR>
                    );
                  })}
                </Table.TBody>
              </Table.Table>
            </div>
          </Card>
        </>
      )}

      {/* Crypto settings (Accordion) */}
      <Accordion title="Глобальные настройки крипты">
        <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Textarea placeholder="RPC endpoints (JSON)" value={JSON.stringify(cryptoCfg.rpc_endpoints || {}, null, 2)} onChange={(e) => setCryptoCfg((s: any) => ({ ...(s || {}), rpc_endpoints: safeParseJSON(e.target.value, s?.rpc_endpoints || {}) }))} />
          <Textarea placeholder="Fallback networks (JSON)" value={JSON.stringify(cryptoCfg.fallback_networks || {}, null, 2)} onChange={(e) => setCryptoCfg((s: any) => ({ ...(s || {}), fallback_networks: safeParseJSON(e.target.value, s?.fallback_networks || {}) }))} />
          <Input placeholder="Retries" value={String(cryptoCfg.retries ?? '')} onChange={(e) => setCryptoCfg((s: any) => ({ ...(s || {}), retries: parseInt(e.target.value || '0', 10) }))} />
          <Input placeholder="Gas price cap" value={String(cryptoCfg.gas_price_cap ?? '')} onChange={(e) => setCryptoCfg((s: any) => ({ ...(s || {}), gas_price_cap: parseFloat(e.target.value || '0') }))} />
          <div className="lg:col-span-2 flex justify-end">
            <Button
              onClick={async () => {
                await persistCryptoConfig(cryptoCfg);
              }}
            >
              Сохранить
            </Button>
          </div>
        </div>
      </Accordion>

      {/* Provider Drawer */}
      <Drawer
        open={provDrawer}
        onClose={() => setProvDrawer(false)}
        title="Провайдер"
        footer={<Button onClick={saveProvider} disabled={!provEditing?.slug}>Сохранить</Button>}
        widthClass="w-[720px]"
      >
        <div className="p-4 grid grid-cols-2 gap-2">
          <Input placeholder="slug" value={provEditing?.slug || ''} onChange={(e) => setProvEditing((s) => ({ ...(s as any), slug: e.target.value }))} />
          <Input placeholder="type" value={provEditing?.type || ''} onChange={(e) => setProvEditing((s) => ({ ...(s as any), type: e.target.value }))} />
          <Input placeholder="priority" type="number" value={String(provEditing?.priority ?? 100)} onChange={(e) => setProvEditing((s) => ({ ...(s as any), priority: parseInt(e.target.value || '0', 10) }))} />
          <Select value={String(provEditing?.enabled ? 'true' : 'false')} onChange={(e: any) => setProvEditing((s) => ({ ...(s as any), enabled: e.target.value !== 'false' }))}>
            <option value="true">enabled</option>
            <option value="false">disabled</option>
          </Select>
          <Select value={provEditing?.config?.linked_contract || ''} onChange={(e: any) => setProvEditing((s) => ({ ...(s as any), config: { ...((s as any)?.config || {}), linked_contract: e.target.value || undefined } }))}>
            <option value="">— contract —</option>
            {contracts.map((c) => <option key={c.slug} value={c.slug}>{c.title || c.slug}</option>)}
          </Select>
          <div />
          <div className="col-span-2">
            <Textarea placeholder="config JSON" value={JSON.stringify(provEditing?.config || {}, null, 2)} onChange={(e) => setProvEditing((s) => ({ ...(s as any), config: safeParseJSON(e.target.value, (s as any)?.config || {}) }))} />
          </div>
        </div>
      </Drawer>

      {/* Contract Drawer */}
      <Drawer
        open={ctrDrawer}
        onClose={() => setCtrDrawer(false)}
        title="Контракт"
        footer={<Button onClick={saveContract} disabled={!ctrEditing?.title && !ctrEditing?.slug}>Сохранить</Button>}
        widthClass="w-[720px]"
      >
        <div className="p-4 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <Input placeholder="Название" value={ctrEditing?.title || ''} onChange={(e) => setCtrEditing((s: any) => ({ ...(s || {}), title: e.target.value }))} />
            <Input placeholder="Slug (опц.)" value={ctrEditing?.slug || ''} onChange={(e) => setCtrEditing((s: any) => ({ ...(s || {}), slug: e.target.value }))} />
            <Select value={ctrEditing?.chain || ''} onChange={(e: any) => setCtrEditing((s: any) => ({ ...(s || {}), chain: e.target.value }))}>
              <option value="">Сеть</option>
              <option value="ethereum">Ethereum</option>
              <option value="polygon">Polygon</option>
              <option value="bsc">BSC</option>
              <option value="ton">TON</option>
            </Select>
            <Input placeholder="Адрес (0x...)" value={ctrEditing?.address || ''} onChange={(e) => setCtrEditing((s: any) => ({ ...(s || {}), address: e.target.value }))} />
            <Select value={ctrEditing?.type || ''} onChange={(e: any) => setCtrEditing((s: any) => ({ ...(s || {}), type: e.target.value }))}>
              <option value="">Тип</option>
              <option value="ERC-20">ERC-20</option>
              <option value="ERC-721">ERC-721</option>
              <option value="ERC-1155">ERC-1155</option>
              <option value="custom">custom</option>
            </Select>
            <Input placeholder="Webhook URL (опц.)" value={ctrEditing?.webhook_url || ''} onChange={(e) => setCtrEditing((s: any) => ({ ...(s || {}), webhook_url: e.target.value }))} />
          </div>
          <Textarea placeholder="ABI JSON (вставьте сюда)" value={(ctrEditing as any)?.abi_text || ''} onChange={(e) => setCtrEditing((s: any) => ({ ...(s || {}), abi_text: e.target.value }))} />
          <div className="grid grid-cols-3 gap-2">
            <Input placeholder="методы (pay,mint,withdraw)" value={(ctrEditing?.methods?.list || []).join(', ')} onChange={(e) => setCtrEditing((s: any) => ({ ...(s || {}), methods: { ...((s?.methods || {})), list: e.target.value.split(',').map((x) => x.trim()).filter(Boolean) } }))} />
            <Input placeholder="статус (active/test/error)" value={ctrEditing?.status || 'active'} onChange={(e) => setCtrEditing((s: any) => ({ ...(s || {}), status: e.target.value }))} />
            <Input placeholder="roles (admin,ops)" value={(ctrEditing?.methods?.roles || []).join(', ')} onChange={(e) => setCtrEditing((s: any) => ({ ...(s || {}), methods: { ...((s?.methods || {})), roles: e.target.value.split(',').map((x) => x.trim()).filter(Boolean) } }))} />
          </div>
        </div>
      </Drawer>
    </div>
  );
}

function safeParseJSON(s: string, fallback: any) {
  try { return JSON.parse(s); } catch { return fallback; }
}











