import React from 'react';
import { ApexChart, Badge, Card, Select, Spinner, Table } from '@ui';
import { apiGet } from '@shared/api/client';

export default function PaymentsMonitoring() {
  const [contracts, setContracts] = React.useState<any[]>([]);
  const [selected, setSelected] = React.useState<string>('');
  const [days, setDays] = React.useState<number>(30);
  const [methodsTS, setMethodsTS] = React.useState<any[]>([]);
  const [volumeTS, setVolumeTS] = React.useState<any[]>([]);
  const [events, setEvents] = React.useState<any[]>([]);
  const [daysWindow, setDaysWindow] = React.useState<number>(30);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const c = await apiGet<{ items: any[] }>('/v1/billing/admin/contracts');
      setContracts(c?.items || []);
      const q = selected ? `?id_or_slug=${encodeURIComponent(selected)}&days=${days}` : `?days=${days}`;
      const m = await apiGet<{ methods: any[]; volume: any[] }>(`/v1/billing/admin/contracts/metrics_ts${q}`);
      setMethodsTS(m?.methods || []);
      setVolumeTS(m?.volume || []);
      const ev = await apiGet<{ items: any[] }>(selected ? `/v1/billing/admin/contracts/${encodeURIComponent(selected)}/events?limit=1000` : '/v1/billing/admin/contracts/events?limit=1000');
      setEvents(ev?.items || []);
    } catch {}
    setLoading(false);
  }, [selected, days]);

  React.useEffect(() => { void load(); }, [load]);

  // Prepare series for charts
  const daysList = Array.from(new Set(methodsTS.map((r) => r.day))).sort();
  const methods = Array.from(new Set(methodsTS.map((r) => r.method)));
  const seriesMethods = methods.map((name) => ({ name, data: daysList.map((d) => (methodsTS.find((r) => r.day === d && r.method === name)?.calls || 0)) }));

  const volDays = Array.from(new Set(volumeTS.map((r) => r.day))).sort();
  const tokens = Array.from(new Set(volumeTS.map((r) => r.token)));
  const seriesVolume = tokens.map((name) => ({ name, data: volDays.map((d) => Number(volumeTS.find((r) => r.day === d && r.token === name)?.total || 0)) }));

  // Chain watchlist style summary derived from events + contracts
  const contractsById = React.useMemo(() => Object.fromEntries(contracts.map((c: any) => [c.id, c])), [contracts]);
  const chainSummary = React.useMemo(() => {
    const totals: Record<string, number> = {};
    const now = Date.now();
    const since = now - daysWindow * 86400000;
    for (const e of events) {
      const c = contractsById[e.contract_id as string];
      if (!c) continue;
      const t = new Date(e.created_at || Date.now()).getTime();
      if (isNaN(t) || t < since) continue;
      const ch = c.chain || 'other';
      const amt = Number(e.amount || 0);
      totals[ch] = (totals[ch] || 0) + (isFinite(amt) ? amt : 0);
    }
    return Object.keys(totals)
      .map((k) => ({ chain: k, total: totals[k] }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 4);
  }, [events, contractsById, daysWindow]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Select value={selected} onChange={(e: any) => setSelected(e.target.value)}>
          <option value="">Все контракты</option>
          {contracts.map((c) => <option key={c.id} value={c.id}>{c.title || c.slug}</option>)}
        </Select>
        <Select value={String(days)} onChange={(e: any) => setDays(parseInt(e.target.value || '30', 10))}>
          <option value="7">7 дней</option>
          <option value="30">30 дней</option>
          <option value="90">90 дней</option>
        </Select>
        <Select value={String(daysWindow)} onChange={(e: any) => setDaysWindow(parseInt(e.target.value || '30', 10))}>
          <option value="7">Watchlist: 7 дней</option>
          <option value="30">Watchlist: 30 дней</option>
          <option value="90">Watchlist: 90 дней</option>
        </Select>
      </div>

      {loading ? <Spinner /> : (
        <>
          {chainSummary.length > 0 && (
            <Card>
              <div className="p-4">
                <div className="mb-2 text-sm text-gray-500">Суммы по блокчейнам (watchlist)</div>
                <div className="grid grid-cols-4 gap-3">
                  {chainSummary.map((c) => (
                    <Card key={c.chain}>
                      <div className="p-3">
                        <div className="flex items-center justify-between">
                          <div className="text-xs text-gray-500">{(c.chain || '').toUpperCase()}</div>
                          <Badge color={c.chain === 'ethereum' ? 'info' : c.chain === 'polygon' ? 'primary' : c.chain === 'bsc' ? 'warning' : 'neutral'}>{(c.chain || '').toUpperCase()}</Badge>
                        </div>
                        <div className="mt-1 text-lg font-semibold">{c.total.toFixed(2)}</div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </Card>
          )}
          <Card>
            <div className="p-4">
              <div className="mb-2 text-sm text-gray-500">Вызовы методов по дням</div>
              <ApexChart type="line" series={seriesMethods} options={{ xaxis: { categories: daysList } }} height={320} />
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <div className="mb-2 text-sm text-gray-500">Объём транзакций по дням</div>
              <ApexChart type="bar" series={seriesVolume} options={{ xaxis: { categories: volDays } }} height={320} />
            </div>
          </Card>

          <Card>
            <div className="p-4">
              <div className="mb-2 text-sm text-gray-500">Последние события</div>
              <Table.Table>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Время</Table.TH>
                    <Table.TH>Event</Table.TH>
                    <Table.TH>Method</Table.TH>
                    <Table.TH>Status</Table.TH>
                    <Table.TH>Tx</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {(events || []).map((e, i) => (
                    <Table.TR key={i}>
                      <Table.TD>{e.created_at || ''}</Table.TD>
                      <Table.TD>{e.event || ''}</Table.TD>
                      <Table.TD>{e.method || ''}</Table.TD>
                      <Table.TD>{e.status || ''}</Table.TD>
                      <Table.TD>{e.tx_hash || ''}</Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
