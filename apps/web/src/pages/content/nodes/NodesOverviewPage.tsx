import React from 'react';
import { ContentLayout } from '../ContentLayout';
import { Card } from "@ui";
import { apiGet } from '../../../shared/api/client';
import type { KPIs } from '../PageViews/Statistics';

type ContentStats = KPIs;

export default function NodesOverviewPage() {
  const [stats, setStats] = React.useState<ContentStats | null>(null);

  React.useEffect(() => {
    void (async () => {
      try {
        const data = await apiGet<(Partial<ContentStats> & { links_per_object?: number })>('/v1/content/stats');
        if (data) {
          const legacyLinks = typeof data.links_per_object === 'number' ? data.links_per_object : undefined;
          setStats({
            nodes: Number(data.nodes ?? 0),
            quests: Number(data.quests ?? 0),
            worlds: Number(data.worlds ?? 0),
            published: Number(data.published ?? 0),
            drafts: Number(data.drafts ?? 0),
            linksPerObject: Number(data.linksPerObject ?? legacyLinks ?? 0),
          });
        }
      } catch (err) {
        console.warn('Failed to load content stats', err);
      }
    })();
  }, []);

  const headerStats = [
    { label: 'Nodes', value: stats ? stats.nodes.toLocaleString() : '-' },
    { label: 'Draft nodes', value: stats ? stats.drafts.toLocaleString() : '-' },
    {
      label: 'Avg links per node',
      value: stats ? stats.linksPerObject.toFixed(2) : '-',
    },
  ];

  return (
    <ContentLayout
      context="nodes"
      title="Nodes intelligence"
      description="Monitor growth of the narrative graph, surface bottlenecks, and keep relations healthy across every node."
      stats={headerStats}
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="space-y-4 p-6">
          <div>
            <h2 className="text-base font-semibold text-gray-800 dark:text-dark-50">Graph cadence</h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-dark-200">
              Track how many nodes are published versus still in drafting. Use this view to balance the pipeline and decide where more authoring support is required.
            </p>
          </div>
          <div className="rounded-2xl border border-dashed border-primary-200 bg-primary-50 p-4 text-sm text-primary-800 dark:border-primary-700/60 dark:bg-primary-950/30 dark:text-primary-200">
            Node-specific trend charts will live here next � retention by world hops, broken edges, and high-friction relations.
          </div>
        </Card>
        <Card className="space-y-4 p-6">
          <div>
            <h2 className="text-base font-semibold text-gray-800 dark:text-dark-50">Operational checklist</h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-dark-200">
              Keep the library tidy by reviewing relations and tagging hygiene. The quick wins section below highlights where editors should spend their time each week.
            </p>
          </div>
          <ul className="space-y-3 text-sm text-gray-700 dark:text-dark-100">
            <li>� Audit relation strategies with the tuning panel.</li>
            <li>� Refresh outdated tags so discovery continues to improve.</li>
            <li>� Warm up drafts that have been inactive for more than 14 days.</li>
          </ul>
        </Card>
      </div>
    </ContentLayout>
  );
}