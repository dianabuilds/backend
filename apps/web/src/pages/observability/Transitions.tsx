import React from 'react';
import { ApexChart, Card, Spinner, Table, TablePagination } from '@ui';
import { apiGet } from '../../shared/api/client';

type Row = {
  tenant_id: string;
  mode: string;
  avg_latency_ms: number;
  no_route_ratio: number;
  fallback_ratio: number;
  count: number;
};

export default function ObservabilityTransitions() {
  const [rows, setRows] = React.useState<Row[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);

  React.useEffect(() => {
    let mounted = true;
    apiGet<Row[]>('/v1/admin/telemetry/transitions/summary')
      .then((d) => mounted && setRows(d))
      .catch((e) => mounted && setError(String(e)))
      .catch(() => void 0);
    return () => {
      mounted = false;
    };
  }, []);

  React.useEffect(() => {
    setPage(1);
  }, [rows?.length]);

  const dataRows = rows ?? [];
  const totalRows = dataRows.length;
  const start = (page - 1) * pageSize;
  const paginatedRows = dataRows.slice(start, start + pageSize);
  const hasNext = page * pageSize < totalRows;
  const cats = dataRows.map((r) => `${r.tenant_id}/${r.mode}`);

  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!rows) return <div className="p-6"><Spinner /></div>;

  return (
    <div className="p-6 space-y-6">
      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Avg latency by tenant/mode</div>
          <ApexChart
            type="bar"
            series={[{ name: 'avg_ms', data: dataRows.map((r) => Math.round(r.avg_latency_ms || 0)) }]}
            options={{ xaxis: { categories: cats, labels: { rotate: -45 } } }}
            height={360}
          />
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">No-route / fallback ratios</div>
          <ApexChart
            type="bar"
            series={[
              { name: 'no_route_%', data: dataRows.map((r) => Math.round((r.no_route_ratio || 0) * 100)) },
              { name: 'fallback_%', data: dataRows.map((r) => Math.round((r.fallback_ratio || 0) * 100)) },
            ]}
            options={{ xaxis: { categories: cats, labels: { rotate: -45 } }, legend: { show: true } }}
            height={360}
          />
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <Table.Table>
            <Table.THead>
              <Table.TR>
                <Table.TH>Tenant/Mode</Table.TH>
                <Table.TH>Avg ms</Table.TH>
                <Table.TH>No-route %</Table.TH>
                <Table.TH>Fallback %</Table.TH>
                <Table.TH>Count</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {paginatedRows.map((r, index) => (
                <Table.TR key={`${r.tenant_id}-${r.mode}-${index}`}>
                  <Table.TD className="font-mono text-xs">{r.tenant_id}/{r.mode}</Table.TD>
                  <Table.TD>{Math.round(r.avg_latency_ms || 0)}</Table.TD>
                  <Table.TD>{((r.no_route_ratio || 0) * 100).toFixed(2)}%</Table.TD>
                  <Table.TD>{((r.fallback_ratio || 0) * 100).toFixed(2)}%</Table.TD>
                  <Table.TD>{r.count || 0}</Table.TD>
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
