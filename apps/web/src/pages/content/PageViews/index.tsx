import { Card } from '@ui';
import { Statistics, KPIs } from './Statistics';
import { ViewChart } from './ViewChart';

type PageViewsProps = {
  stats: KPIs | null;
};

export function PageViews({ stats }: PageViewsProps) {
  return (
    <Card className="pb-4 overflow-hidden">
      <div className="flex min-w-0 items-center justify-between px-4 pt-3 sm:px-5">
        <h2 className="text-sm-plus font-medium tracking-wide text-gray-800 dark:text-dark-100">Audience & Publishing</h2>
      </div>

      <div className="mt-3 grid grid-cols-12 gap-4">
        <Statistics stats={stats} />
        <ViewChart />
      </div>
    </Card>
  );
}