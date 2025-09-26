import React from 'react';
import { ApexChart, Card, Spinner, Table, TablePagination } from '@ui';
import { apiGet } from '../../shared/api/client';

type WorkersSummary = { jobs: Record<string, number>; job_avg_ms: number; tokens: { prompt: number; completion: number }; cost_usd_total: number; stages: Record<string, { count: number; avg_ms: number }> };

export default function ObservabilityWorkers() {
  const [data, setData] = React.useState<WorkersSummary | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);

  const stagesLength = React.useMemo(() => Object.keys(data?.stages ?? {}).length, [data]);

  React.useEffect(() => {
    let mounted = true;
    apiGet<WorkersSummary>('/v1/admin/telemetry/workers/summary')
      .then((d) => mounted && setData(d))
      .catch((e) => mounted && setError(String(e)))
      .catch(() => void 0);
    return () => {
      mounted = false;
    };
  }, []);

  React.useEffect(() => {
    setPage(1);
  }, [stagesLength]);

  const stages = React.useMemo(() => data?.stages ?? {}, [data]);
  const stageRows = React.useMemo(() => Object.entries(stages).map(([stage, v]) => ({ stage, ...(v as any) })), [stages]);
  const totalRows = stageRows.length;
  const paginatedRows = React.useMemo(() => {
    const start = (page - 1) * pageSize;
    return stageRows.slice(start, start + pageSize);
  }, [stageRows, page, pageSize]);
  const hasNext = page * pageSize < totalRows;

  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!data) return <div className="p-6"><Spinner /></div>;

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card><div className="p-4"><div className="text-sm text-gray-500">Started</div><div className="text-2xl font-semibold">{data.jobs?.started || 0}</div></div></Card>
        <Card><div className="p-4"><div className="text-sm text-gray-500">Completed</div><div className="text-2xl font-semibold">{data.jobs?.completed || 0}</div></div></Card>
        <Card><div className="p-4"><div className="text-sm text-gray-500">Failed</div><div className="text-2xl font-semibold">{data.jobs?.failed || 0}</div></div></Card>
        <Card><div className="p-4"><div className="text-sm text-gray-500">Avg duration</div><div className="text-2xl font-semibold">{Math.round(data.job_avg_ms || 0)} ms</div></div></Card>
      </div>

      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Stage avg duration</div>
          <ApexChart type="bar" series={[{ name: 'avg_ms', data: stageRows.map((r) => ({ x: r.stage, y: Math.round(r.avg_ms || 0) })) }]} options={{ xaxis: { type: 'category', labels: { rotate: -45 } } }} height={360} />
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Stages table</div>
          <Table.Table>
            <Table.THead>
              <Table.TR>
                <Table.TH>Stage</Table.TH>
                <Table.TH>Count</Table.TH>
                <Table.TH>Avg ms</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {paginatedRows.map((r) => (
                <Table.TR key={r.stage}>
                  <Table.TD>{r.stage}</Table.TD>
                  <Table.TD>{r.count}</Table.TD>
                  <Table.TD>{Math.round(r.avg_ms || 0)}</Table.TD>
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


