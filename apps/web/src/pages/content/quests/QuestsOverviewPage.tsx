import React from "react";
import { Link } from "react-router-dom";
import { ContentLayout } from "../ContentLayout";
import { Card, MetricCard, Button, Badge } from "@ui";
import { apiGet } from "@shared/api/client";
import type { KPIs } from "../PageViews/Statistics";

type ContentStats = KPIs & {
  approvalQueue?: number;
  draftsPerWorld?: number;
  aiDrafts?: number;
};

const initialStats: ContentStats = {
  nodes: 0,
  quests: 0,
  worlds: 0,
  published: 0,
  drafts: 0,
  linksPerObject: 0,
  approvalQueue: 0,
  draftsPerWorld: 0,
  aiDrafts: 0,
};

export default function QuestsOverviewPage() {
  const [stats, setStats] = React.useState<ContentStats>(initialStats);

  React.useEffect(() => {
    void (async () => {
      try {
        const data = await apiGet<Partial<ContentStats> & { links_per_object?: number }>("/v1/content/stats");
        if (data) {
          setStats((prev) => ({
            ...prev,
            nodes: Number(data.nodes ?? prev.nodes),
            quests: Number(data.quests ?? prev.quests),
            worlds: Number(data.worlds ?? prev.worlds),
            published: Number(data.published ?? prev.published),
            drafts: Number(data.drafts ?? prev.drafts),
            linksPerObject: Number(data.linksPerObject ?? data.links_per_object ?? prev.linksPerObject),
            approvalQueue: Number(data.approvalQueue ?? prev.approvalQueue ?? 0),
            draftsPerWorld: Number(data.draftsPerWorld ?? prev.draftsPerWorld ?? 0),
            aiDrafts: Number(data.aiDrafts ?? prev.aiDrafts ?? 0),
          }));
        }
      } catch (error) {
        console.warn("Failed to load quest overview stats", error);
      }
    })();
  }, []);

  const headerStats = [
    { label: "Quests", value: stats.quests.toLocaleString() },
    { label: "World templates", value: stats.worlds.toLocaleString() },
    { label: "Published", value: stats.published.toLocaleString() },
  ];

  return (
    <ContentLayout
      context="quests"
      title="Quest operations"
      description="Follow the health of the quest pipeline, balance manual and AI-assisted creation, and see where to focus next."
      stats={headerStats}
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <Link to="/quests/new">
            <Button>New quest</Button>
          </Link>
          <Link to="/quests/worlds">
            <Button variant="outlined">Manage worlds</Button>
          </Link>
        </div>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-6">
          <Card className="grid gap-4 p-6 lg:grid-cols-3">
            <MetricCard label="Drafts waiting review" value={stats.approvalQueue?.toLocaleString() ?? "0"} trendLabel="Currently in backlog" />
            <MetricCard label="Drafts per world" value={stats.draftsPerWorld?.toFixed(1) ?? "0.0"} trendLabel="Average" />
            <MetricCard label="AI generated" value={stats.aiDrafts?.toLocaleString() ?? "0"} trendLabel="Ready for curation" />
          </Card>

          <Card className="space-y-4 p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold text-gray-900 dark:text-dark-50">Pipeline snapshot</h2>
                <p className="text-sm text-gray-600 dark:text-dark-200">
                  Track authored quests, world coverage, and next actions for the content team. Use these tiles as quick entry points into detailed views.
                </p>
              </div>
              <Button variant="outlined" size="sm" onClick={() => window.location.reload()}>Refresh</Button>
            </div>

            <div className="grid gap-3 lg:grid-cols-2">
              <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-dark-600 dark:bg-dark-700/70">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">World topology</h3>
                    <p className="text-xs text-gray-500 dark:text-dark-300">{stats.linksPerObject?.toFixed(2) ?? "0.00"} links per object</p>
                  </div>
                  <Badge color="primary">Graph</Badge>
                </div>
                <p className="mt-3 text-sm text-gray-600 dark:text-dark-200">Balance worlds with well-connected quest entries and those still missing coverage.</p>
                <div className="mt-4 flex gap-2">
                  <Link to="/quests/worlds">
                    <Button size="sm">View worlds</Button>
                  </Link>
                  <Link to="/quests/library">
                    <Button variant="outlined" size="sm">Quest library</Button>
                  </Link>
                </div>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-dark-600 dark:bg-dark-700/70">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Review queue</h3>
                    <p className="text-xs text-gray-500 dark:text-dark-300">{stats.drafts.toLocaleString()} drafts total</p>
                  </div>
                  <Badge color="neutral">Ops</Badge>
                </div>
                <p className="mt-3 text-sm text-gray-600 dark:text-dark-200">Сheck queued drafts, assign reviewers, or fast-track ready content into production.</p>
                <div className="mt-4 flex gap-2">
                  <Link to="/content/drafts">
                    <Button size="sm">Open drafts</Button>
                  </Link>
                  <Link to="/tools/import-export?scope=quests">
                    <Button variant="outlined" size="sm">Import / Export</Button>
                  </Link>
                </div>
              </div>
            </div>
          </Card>

          <Card className="grid gap-6 p-6 lg:grid-cols-2">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Next best actions</h3>
              <ul className="mt-3 space-y-2 text-sm text-gray-600 dark:text-dark-200">
                <li>• Закройте квесты, дожидающиеся финального ревью.</li>
                <li>• Подготовьте описания миров к предстоящему AI-генератору сценариев.</li>
                <li>• Сверьте соответствие тегов квестов текущим лайв-ивентам.</li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Recently updated worlds</h3>
              <p className="mt-3 text-sm text-gray-600 dark:text-dark-200">Когда новые миры появляются в системе, добавляйте ключевых NPC и отмечайте связи с квестами, чтобы быстрее запускать сюжетные арки.</p>
              <Link to="/quests/worlds">
                <Button variant="outlined" className="mt-3">Go to worlds</Button>
              </Link>
            </div>
          </Card>
        </div>

        <Card className="space-y-4 p-6">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-dark-50">AI Studio preview</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200">Experiment with AI-assisted drafts and promote the best ideas into the backlog.</p>
            </div>
            <Link to="/quests/ai-studio">
              <Button variant="outlined" size="sm">Open studio</Button>
            </Link>
          </div>
          <div className="rounded-2xl border border-dashed border-primary-200 bg-primary-50/70 p-4 text-sm text-primary-800 dark:border-primary-700 dark:bg-primary-950/40 dark:text-primary-200">
            В ближайших релизах AI Studio позволит сравнить генерируемые истории с ручными драфтами и отправлять лучшие варианты в продакшн.
          </div>
          <div className="space-y-3 text-sm text-gray-600 dark:text-dark-200">
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-dark-600 dark:bg-dark-700/70">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Sync with notifications</h4>
              <p className="mt-2">Настраивайте кампании, чтобы анонсировать запуски квестов и миров. Связывайте теги с событиями.</p>
              <Link to="/notifications">
                <Button variant="outlined" size="sm" className="mt-3">Notification hub</Button>
              </Link>
            </div>
          </div>
        </Card>
      </div>
    </ContentLayout>
  );
}
