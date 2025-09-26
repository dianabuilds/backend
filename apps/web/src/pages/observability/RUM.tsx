import React from 'react';
import { Card, Spinner, Table, TablePagination } from '@ui';
import { apiGet } from '../../shared/api/client';

type RumSummary = {
  window: number;
  counts: Record<string, number>;
  login_attempt_avg_ms: number | null;
  navigation_avg: {
    ttfb_ms: number | null;
    dom_content_loaded_ms: number | null;
    load_event_ms: number | null;
  };
};

export default function ObservabilityRUM() {
  const [summary, setSummary] = React.useState<RumSummary | null>(null);
  const [events, setEvents] = React.useState<any[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const [countsPage, setCountsPage] = React.useState(1);
  const [countsPageSize, setCountsPageSize] = React.useState(10);
  const [eventPage, setEventPage] = React.useState(1);
  const [eventPageSize, setEventPageSize] = React.useState(20);

  const countsLength = React.useMemo(() => Object.keys(summary?.counts ?? {}).length, [summary]);
  const eventsLength = events?.length ?? 0;

  React.useEffect(() => {
    let mounted = true;
    apiGet<RumSummary>('/v1/admin/telemetry/rum/summary')
      .then((d) => mounted && setSummary(d))
      .catch((e) => mounted && setError(String(e)))
      .catch(() => void 0);
    apiGet<any[]>('/v1/admin/telemetry/rum?limit=100')
      .then((d) => mounted && setEvents(d))
      .catch(() => void 0);
    return () => {
      mounted = false;
    };
  }, []);

  React.useEffect(() => {
    setCountsPage(1);
  }, [countsLength]);

  React.useEffect(() => {
    setEventPage(1);
  }, [eventsLength]);

  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!summary) return <div className="p-6"><Spinner /></div>;

  const nav = summary.navigation_avg || {};
  const counts = Object.entries(summary.counts || {}).map(([event, count]) => ({ event, count: count as number }));
  const countsTotal = counts.length;
  const countsStart = (countsPage - 1) * countsPageSize;
  const countsRows = counts.slice(countsStart, countsStart + countsPageSize);
  const countsHasNext = countsPage * countsPageSize < countsTotal;

  const eventList = events ?? [];
  const eventTotal = eventList.length;
  const eventStart = (eventPage - 1) * eventPageSize;
  const eventRows = eventList.slice(eventStart, eventStart + eventPageSize);
  const eventsHasNext = eventPage * eventPageSize < eventTotal;

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="p-4">
            <div className="text-sm text-gray-500">Login avg ms</div>
            <div className="text-2xl font-semibold">{summary.login_attempt_avg_ms ?? '-'}</div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="text-sm text-gray-500">TTFB avg</div>
            <div className="text-2xl font-semibold">{nav.ttfb_ms ?? '-'}</div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="text-sm text-gray-500">Load avg</div>
            <div className="text-2xl font-semibold">{nav.load_event_ms ?? '-'}</div>
          </div>
        </Card>
      </div>

      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Event counts</div>
          <Table.Table>
            <Table.THead>
              <Table.TR>
                <Table.TH>Event</Table.TH>
                <Table.TH>Count</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {countsRows.map((row) => (
                <Table.TR key={row.event}>
                  <Table.TD>{row.event}</Table.TD>
                  <Table.TD>{row.count}</Table.TD>
                </Table.TR>
              ))}
            </Table.TBody>
          </Table.Table>
          <TablePagination
            page={countsPage}
            pageSize={countsPageSize}
            currentCount={countsRows.length}
            totalItems={countsTotal}
            hasNext={countsHasNext}
            onPageChange={setCountsPage}
            onPageSizeChange={(value) => { setCountsPageSize(value); setCountsPage(1); }}
            pageSizeOptions={[10, 20, 50, 100]}
          />
        </div>
      </Card>

      <Card>
        <div className="p-4">
          <div className="mb-2 text-sm text-gray-500">Recent events</div>
          {!events ? (
            <Spinner />
          ) : (
            <>
              <Table.Table>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Ts</Table.TH>
                    <Table.TH>Event</Table.TH>
                    <Table.TH>URL</Table.TH>
                    <Table.TH>Data</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {eventRows.map((event, index) => (
                    <Table.TR key={index}>
                      <Table.TD className="font-mono text-xs">{event.ts}</Table.TD>
                      <Table.TD>{event.event}</Table.TD>
                      <Table.TD className="font-mono text-xs">{event.url}</Table.TD>
                      <Table.TD className="font-mono text-xs break-all">{JSON.stringify(event.data || {})}</Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
              <TablePagination
                page={eventPage}
                pageSize={eventPageSize}
                currentCount={eventRows.length}
                totalItems={eventTotal}
                hasNext={eventsHasNext}
                onPageChange={setEventPage}
                onPageSizeChange={(value) => { setEventPageSize(value); setEventPage(1); }}
              />
            </>
          )}
        </div>
      </Card>
    </div>
  );
}
