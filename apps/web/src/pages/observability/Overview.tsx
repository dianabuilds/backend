import React from 'react';
import { ApexChart, Card, Spinner } from '@ui';
import { ObservabilityLayout } from './ObservabilityLayout';
import { apiGet } from '../../shared/api/client';

type Summary = {
  llm: any;
  workers: any;
  events: { per_tenant: Record<string, Record<string, number>>; handlers: any[] };
  transitions: Array<any>;
  ux: any;
  rum: any;
};

export default function ObservabilityOverview() {
  const [data, setData] = React.useState<Summary | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let mounted = true;
    apiGet<Summary>('/v1/admin/telemetry/summary')
      .then((d) => mounted && setData(d))
      .catch((e) => mounted && setError(String(e)))
      .catch(() => void 0);
    return () => {
      mounted = false;
    };
  }, []);

  if (error) {
    return (
      <ObservabilityLayout>
        <Card className="p-6 text-error">{error}</Card>
      </ObservabilityLayout>
    );
  }
  if (!data) {
    return (
      <ObservabilityLayout>
        <div className="flex justify-center p-6">
          <Spinner />
        </div>
      </ObservabilityLayout>
    );
  }

  const llmCalls = (data.llm?.calls || []) as Array<any>;
  const llmTotalCalls = llmCalls.filter((r) => r.type === 'calls').reduce((a, b) => a + (b.count || 0), 0);
  const llmTotalErrors = llmCalls.filter((r) => r.type === 'errors').reduce((a, b) => a + (b.count || 0), 0);

  const workerJobs = data.workers?.jobs || {};
  const workerCompleted = workerJobs.completed || 0;
  const workerFailed = workerJobs.failed || 0;

  const transitions = (data.transitions || []) as Array<any>;
  const noRouteAvg = transitions.length ? transitions.reduce((a, b) => a + (b.no_route_ratio || 0), 0) / transitions.length : 0;
  const transitAvg = transitions.length ? transitions.reduce((a, b) => a + (b.avg_latency_ms || 0), 0) / transitions.length : 0;

  const rumNav = data.rum?.navigation_avg || {};

  const stats = [
    { label: 'LLM calls', value: llmTotalCalls || '--', hint: `${llmTotalErrors} errors` },
    { label: 'Worker jobs', value: workerCompleted || '--', hint: `${workerFailed} failed` },
    { label: 'Avg transition', value: `${Math.round(transitAvg)} ms`, hint: `No-route ${(noRouteAvg * 100).toFixed(1)}%` },
  ];

  return (
    <ObservabilityLayout stats={stats}>
      <div className="grid gap-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <div className="p-4">
              <div className="text-sm text-gray-500">LLM calls</div>
              <div className="text-2xl font-semibold">{llmTotalCalls}</div>
              <div className="text-xs text-error">errors: {llmTotalErrors}</div>
            </div>
          </Card>
          <Card>
            <div className="p-4">
              <div className="text-sm text-gray-500">Worker completed</div>
              <div className="text-2xl font-semibold">{workerCompleted}</div>
              <div className="text-xs text-error">failed: {workerFailed}</div>
            </div>
          </Card>
          <Card>
            <div className="p-4">
              <div className="text-sm text-gray-500">Transitions avg</div>
              <div className="text-2xl font-semibold">{Math.round(transitAvg)} ms</div>
              <div className="text-xs text-amber-600">no-route: {(noRouteAvg * 100).toFixed(2)}%</div>
            </div>
          </Card>
          <Card>
            <div className="p-4">
              <div className="text-sm text-gray-500">RUM navigation avg</div>
              <div className="text-xs">TTFB: {rumNav.ttfb_ms ?? '--'} ms</div>
              <div className="text-xs">DCL: {rumNav.dom_content_loaded_ms ?? '--'} ms</div>
              <div className="text-xs">Load: {rumNav.load_event_ms ?? '--'} ms</div>
            </div>
          </Card>
        </div>

        <Card>
          <div className="p-4">
            <div className="mb-2 text-sm text-gray-500">LLM avg latency by provider</div>
            <ApexChart
              type="bar"
              series={[
                {
                  name: 'avg_ms',
                  data: (data.llm?.latency_avg_ms || [])
                    .map((r: any) => ({ x: `${r.provider}:${r.model}`, y: Math.round(r.avg_ms || 0) }))
                    .slice(0, 12),
                },
              ]}
              options={{ xaxis: { type: 'category', labels: { rotate: -45 } }, yaxis: { labels: { formatter: (v) => `${Math.round(v)} ms` } } }}
              height={320}
            />
          </div>
        </Card>
      </div>
    </ObservabilityLayout>
  );
}
