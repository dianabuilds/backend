import React from 'react';
import { ContentLayout } from '../ContentLayout';
import { Card } from '../../../shared/ui';
import { apiGet } from '../../../shared/api/client';
import type { KPIs } from '../PageViews/Statistics';

type ContentStats = KPIs;

export default function QuestsOverviewPage() {
  const [stats, setStats] = React.useState<ContentStats | null>(null);

  React.useEffect(() => {
    void (async () => {
      try {
        const data = await apiGet<Partial<ContentStats>>('/v1/content/stats');
        if (data) {
          setStats({
            nodes: Number(data.nodes ?? 0),
            quests: Number(data.quests ?? 0),
            worlds: Number(data.worlds ?? 0),
            published: Number(data.published ?? 0),
            drafts: Number(data.drafts ?? 0),
            linksPerObject: Number(data.linksPerObject ?? data.links_per_object ?? 0),
          });
        }
      } catch (err) {
        console.warn('Failed to load content stats', err);
      }
    })();
  }, []);

  const headerStats = [
    { label: 'Quests', value: stats ? stats.quests.toLocaleString() : '-' },
    { label: 'World templates', value: stats ? stats.worlds.toLocaleString() : '-' },
    { label: 'Published quests', value: stats ? stats.published.toLocaleString() : '-' },
  ];

  return (
    <ContentLayout
      context="quests"
      title="Quest operations"
      description="Align quest authoring, validation, and AI assistance in one place. Compare manual pipelines with generated storylines as we roll out new tooling."
      stats={headerStats}
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="space-y-4 p-6">
          <div>
            <h2 className="text-base font-semibold text-gray-800 dark:text-dark-50">Pipeline health</h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-dark-200">
              Separate dashboards for authored versus generated quests will appear here. Until then keep an eye on world coverage and review backlogs manually.
            </p>
          </div>
          <div className="rounded-2xl border border-dashed border-primary-200 bg-primary-50 p-4 text-sm text-primary-800 dark:border-primary-700/60 dark:bg-primary-950/30 dark:text-primary-200">
            Soon you will compare AI-assisted drafts with human-authored quests and promote the best ideas straight into production.
          </div>
        </Card>
        <Card className="space-y-4 p-6">
          <div>
            <h2 className="text-base font-semibold text-gray-800 dark:text-dark-50">Next integrations</h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-dark-200">
              Worlds, tags, and progression logic belong to this workspace. Use it to organise narrative beats per world and to align with live-ops requirements.
            </p>
          </div>
          <ul className="space-y-3 text-sm text-gray-700 dark:text-dark-100">
            <li>• Curate world templates that AI generation can reuse.</li>
            <li>• Sync quest tags with live events to improve discovery.</li>
            <li>• Validate progression rules before shipping updates.</li>
          </ul>
        </Card>
      </div>
    </ContentLayout>
  );
}