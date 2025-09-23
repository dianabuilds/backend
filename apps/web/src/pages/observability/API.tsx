import React from 'react';
import { ApexChart, Card, Table, Spinner, TablePagination } from '@ui';
import { apiGet } from '../../shared/api/client';

type HttpSummary = { paths: Array<{ method: string; path: string; requests_total: number; error5xx_ratio: number; avg_duration_ms: number }> };

export default function ObservabilityAPI() {
  const [data, setData] = React.useState<HttpSummary | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);

  React.useEffect(() => {
    let mounted = true;
    apiGet<HttpSummary>('/v1/admin/telemetry/http/summary')
      .then((d) => mounted && setData(d))
      .catch((e) => mounted && setError(String(e)))
      .catch(() => void 0);
    return () => {
      mounted = false;
    };
  }, []);

  React.useEffect(() => {
    setPage(1);
  }, [data?.paths?.length]);

  const rows = React.useMemo(() => data?.paths || [], [data]);
  const totalRows = rows.length;
  const paginatedRows = React.useMemo(() => {
    const start = (page - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }, [rows, page, pageSize]);
  const hasNext = page * pageSize < totalRows;
  const top = rows.slice(0, 12);

  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!data) return <div className="p-6"><Spinner /></div>;


  return (
    <div className="p-6 space-y-6">
      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Top endpoints by avg latency</div>
          <ApexChart
            type="bar"
            series={[{ name: 'avg_ms', data: top.map((r) => ({ x: `${r.method} ${r.path}`, y: Math.round(r.avg_duration_ms || 0) })) }]}
            options={{ xaxis: { type: 'category', labels: { rotate: -45 } } }}
            height={360}
          />
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Endpoints snapshot</div>
          <Table.Table>
            <Table.THead>
              <Table.TR>
                <Table.TH>Method</Table.TH>
                <Table.TH>Path</Table.TH>
                <Table.TH>Avg ms</Table.TH>
                <Table.TH>5xx %</Table.TH>
                <Table.TH>Req total</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {paginatedRows.map((r, i) => (
                <Table.TR key={i}>
                  <Table.TD>{r.method}</Table.TD>
                  <Table.TD className="font-mono text-xs">{r.path}</Table.TD>
                  <Table.TD>{Math.round(r.avg_duration_ms || 0)}</Table.TD>
                  <Table.TD>{((r.error5xx_ratio || 0) * 100).toFixed(2)}%</Table.TD>
                  <Table.TD>{Math.round(r.requests_total || 0)}</Table.TD>
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






