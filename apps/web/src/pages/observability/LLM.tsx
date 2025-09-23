import React from 'react';
import { ApexChart, Card, Spinner, Table, TablePagination } from '@ui';
import { apiGet } from '../../shared/api/client';

type LLMSummary = { calls: Array<any>; latency_avg_ms: Array<any>; tokens_total: Array<any>; cost_usd_total: Array<any> };

export default function ObservabilityLLM() {
  const [data, setData] = React.useState<LLMSummary | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);

  React.useEffect(() => {
    let mounted = true;
    apiGet<LLMSummary>('/v1/admin/telemetry/llm/summary')
      .then((d) => mounted && setData(d))
      .catch((e) => mounted && setError(String(e)))
      .catch(() => void 0);
    return () => {
      mounted = false;
    };
  }, []);

  React.useEffect(() => {
    setPage(1);
  }, [data?.calls?.length, data?.tokens_total?.length]);


  const calls = data?.calls ?? [];
  const errors = calls.filter((c: any) => c.type === 'errors');
  const ok = calls.filter((c: any) => c.type === 'calls');
  const groupKey = (r: any) => `${r.provider}:${r.model}`;
  const providers = Array.from(new Set(ok.map(groupKey)));
  const okSeries = providers.map((k) => ok.filter((r: any) => groupKey(r) === k).reduce((a: number, b: any) => a + (b.count || 0), 0));
  const errSeries = providers.map((k) => errors.filter((r: any) => groupKey(r) === k).reduce((a: number, b: any) => a + (b.count || 0), 0));
  const tokensTotal = data?.tokens_total ?? [];
  const costTotals = data?.cost_usd_total ?? [];
  const latencies = data?.latency_avg_ms ?? [];
  const tableRows = providers.map((k) => {
    const [provider, model] = k.split(':');
    const promptTok = tokensTotal.filter((r: any) => r.provider === provider && r.model === model && r.type === 'prompt').reduce((a: number, b: any) => a + (b.total || 0), 0);
    const complTok = tokensTotal.filter((r: any) => r.provider === provider && r.model === model && r.type === 'completion').reduce((a: number, b: any) => a + (b.total || 0), 0);
    const usd = costTotals.filter((r: any) => r.provider === provider && r.model === model).reduce((a: number, b: any) => a + (b.total_usd || 0), 0);
    return { key: k, provider, model, promptTok, complTok, usd };
  });
  const totalRows = tableRows.length;
  const paginatedRows = React.useMemo(() => {
    const start = (page - 1) * pageSize;
    return tableRows.slice(start, start + pageSize);
  }, [tableRows, page, pageSize]);
  const hasNext = page * pageSize < totalRows;
  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!data) return <div className="p-6"><Spinner /></div>;


  return (
    <div className="p-6 space-y-6">
      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">LLM calls/errors by provider:model</div>
          <ApexChart
            type="bar"
            series={[
              { name: 'calls', data: providers.map((_, i) => okSeries[i]) },
              { name: 'errors', data: providers.map((_, i) => errSeries[i]) },
            ]}
            options={{ xaxis: { categories: providers, labels: { rotate: -45 } }, legend: { show: true } }}
            height={360}
          />
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Avg latency by provider:model</div>
          <ApexChart
            type="bar"
            series={[
              {
                name: 'avg_ms',
                data: latencies.map((r: any) => ({ x: `${r.provider}:${r.model}`, y: Math.round(r.avg_ms || 0) })),
              },
            ]}
            options={{ xaxis: { type: 'category', labels: { rotate: -45 } } }}
            height={360}
          />
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Tokens & Cost</div>
          <Table.Table>
            <Table.THead>
              <Table.TR>
                <Table.TH>Provider</Table.TH>
                <Table.TH>Model</Table.TH>
                <Table.TH>Prompt tok</Table.TH>
                <Table.TH>Compl tok</Table.TH>
                <Table.TH>USD total</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {paginatedRows.map((row) => (
                <Table.TR key={row.key}>
                  <Table.TD>{row.provider}</Table.TD>
                  <Table.TD>{row.model}</Table.TD>
                  <Table.TD>{row.promptTok}</Table.TD>
                  <Table.TD>{row.complTok}</Table.TD>
                  <Table.TD>${row.usd.toFixed(4)}</Table.TD>
                </Table.TR>
              ))}
            </Table.TBody>
          </Table.Table>
          <TablePagination
            page={page}
            pageSize={pageSize}
            currentCount={paginatedRows.length}
            totalItems={totalRows}
            hasNext={hasNext}
            onPageChange={setPage}
            onPageSizeChange={(value) => { setPageSize(value); setPage(1); }}
          />
        </div>
      </Card>
    </div>
  );
}






