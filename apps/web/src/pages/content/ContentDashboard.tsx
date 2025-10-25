import React from 'react';
import { ContentLayout } from './ContentLayout';
import { PageViews } from './PageViews';
import { TopTags } from './Tops/TopTags';
import { Edits } from './Tops/Edits';
import { Searches } from './Tops/Searches';
import { FeaturedEditors } from './FeaturedEditors';
import { apiGet } from '@shared/api/client';
import type { PageHeroMetric } from '@ui/patterns/PageHero';
import type { KPIs } from './PageViews/Statistics';

type ContentStats = KPIs;

export default function ContentDashboard() {
  const [stats, setStats] = React.useState<ContentStats | null>(null);

  React.useEffect(() => {
    void (async () => {
      try {
        const data = await apiGet<(Partial<ContentStats> & { links_per_object?: number })>('/v1/content/stats');
        if (!data) return;
        const legacyLinks = typeof data.links_per_object === 'number' ? data.links_per_object : undefined;
        setStats({
          nodes: Number(data.nodes ?? 0),
          quests: Number(data.quests ?? 0),
          worlds: Number(data.worlds ?? 0),
          published: Number(data.published ?? 0),
          drafts: Number(data.drafts ?? 0),
          linksPerObject: Number(data.linksPerObject ?? legacyLinks ?? 0),
        });
      } catch (err) {
        console.warn('Failed to load content stats', err);
      }
    })();
  }, []);

  const heroMetrics: PageHeroMetric[] = [
    {
      id: 'dashboard-drafts',
      label: 'Drafts',
      value: stats ? stats.drafts.toLocaleString('ru-RU') : '—',
    },
    {
      id: 'dashboard-published',
      label: 'Published',
      value: stats ? stats.published.toLocaleString('ru-RU') : '—',
    },
    {
      id: 'dashboard-links',
      label: 'Links per object',
      value: stats
        ? stats.linksPerObject.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        : '—',
    },
  ];

  return (
    <ContentLayout
      title="Content intelligence"
      description="Track how stories, tags, and relations evolve across Flavour Trip and spot where momentum drops."
      metrics={heroMetrics}
    >
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <PageViews stats={stats} />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <TopTags />
            <Edits />
            <Searches />
          </div>
        </div>
        <div className="lg:col-span-1">
          <FeaturedEditors />
        </div>
      </div>
    </ContentLayout>
  );
}
