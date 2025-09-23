import React from 'react';
import { Card, Spinner, Table, TablePagination } from '@ui';
import { apiGet } from '../../shared/api/client';

type HandlerRow = { event: string; handler: string; success: number; failure: number; total: number; avg_ms: number };
type EventsSummary = { per_tenant: Record<string, Record<string, number>>; handlers: HandlerRow[] };

export default function ObservabilityEvents() {
  const [data, setData] = React.useState<EventsSummary | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  React.useEffect(() => {
    let mounted = true;
    apiGet<EventsSummary>('/v1/admin/telemetry/events/summary')
      .then((d) => mounted && setData(d))
      .catch((e) => mounted && setError(String(e)))
      .catch(() => void 0);
    return () => {
      mounted = false;
    };
  }, []);

  React.useEffect(() => {
    setPage(1);
  }, [data?.handlers?.length]);

  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!data) return <div className="p-6"><Spinner /></div>;

  const handlers = (data.handlers || []).slice().sort((a, b) => (b.failure || 0) - (a.failure || 0));
  const totalRows = handlers.length;
  const start = (page - 1) * pageSize;
  const paginatedRows = handlers.slice(start, start + pageSize);
  const hasNext = page * pageSize < totalRows;

  return (
    <div className="p-6 space-y-6">
      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Event handlers</div>
          <Table.Table>
            <Table.THead>
              <Table.TR>
                <Table.TH>Event</Table.TH>
                <Table.TH>Handler</Table.TH>
                <Table.TH>Success</Table.TH>
                <Table.TH>Failure</Table.TH>
                <Table.TH>Avg ms</Table.TH>
                <Table.TH>Total</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {paginatedRows.map((r, i) => (
                <Table.TR key={i}>
                  <Table.TD className="font-mono text-xs">{r.event}</Table.TD>
                  <Table.TD>{r.handler}</Table.TD>
                  <Table.TD>{r.success}</Table.TD>
                  <Table.TD className={r.failure ? 'text-red-600' : ''}>{r.failure}</Table.TD>
                  <Table.TD>{Math.round(r.avg_ms || 0)}</Table.TD>
                  <Table.TD>{r.total}</Table.TD>
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
