import widgets from './widgets.json';
import { useAuth } from '../../auth/AuthContext';
import { Card } from '../../components/ui/card';
import ModerationQueueWidget from './ModerationQueueWidget';
import DraftIssuesWidget from './DraftIssuesWidget';
import BackgroundJobsWidget from './BackgroundJobsWidget';
import ProblematicTransitionsWidget from './ProblematicTransitionsWidget';

const componentMap: Record<string, any> = {
  moderation: ModerationQueueWidget,
  drafts: DraftIssuesWidget,
  jobs: BackgroundJobsWidget,
  problems: ProblematicTransitionsWidget,
};

export default function Dashboard() {
  const { user } = useAuth();
  const role = user?.role ?? '';
  const allowed = widgets.filter((w) => {
    if (role === 'admin') return true;
    if (role === 'moderator')
      return w.type === 'moderation' || w.type === 'drafts';
    if (role === 'support') return w.type === 'jobs';
    return false;
  });
  const widgetComponents = allowed
    .map((w) => {
      const Comp = componentMap[w.type];
      return Comp ? (
        <Comp
          key={w.type}
          query={w.query}
          refreshInterval={w.refreshInterval}
        />
      ) : null;
    })
    .filter(Boolean);
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="sticky top-0 z-20 bg-white border-b px-6 py-3 flex justify-between items-center">
        <h1 className="font-bold text-xl">Dashboard</h1>
        <div className="flex gap-2">
          <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-700">System OK</span>
          <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">Global</span>
          <span className="px-2 py-1 text-xs rounded bg-purple-100 text-purple-700">active</span>
        </div>
      </header>
      <main className="p-6 space-y-6">
        <div className="grid grid-cols-5 gap-4">
          <Card className="p-4">
            <h2 className="text-sm font-medium text-gray-500">Active users (24h)</h2>
            <p className="text-2xl font-bold">0</p>
          </Card>
          <Card className="p-4">
            <h2 className="text-sm font-medium text-gray-500">Incidents (24h)</h2>
            <p className="text-2xl font-bold text-red-600">0</p>
          </Card>
          <Card className="p-4">
            <h2 className="text-sm font-medium text-gray-500">Active premium</h2>
            <p className="text-2xl font-bold">1</p>
            <span className="text-xs text-green-600">+0% vs last week</span>
          </Card>
          <Card className="p-4">
            <h2 className="text-sm font-medium text-gray-500">New nodes (7d)</h2>
            <p className="text-2xl font-bold">0</p>
          </Card>
          <Card className="p-4">
            <h2 className="text-sm font-medium text-gray-500">Dead-end %</h2>
            <p className="text-2xl font-bold text-yellow-600">0%</p>
          </Card>
        </div>
        <div className="grid grid-cols-2 gap-6">
          {widgetComponents}
        </div>
        <div className="grid grid-cols-3 gap-6">
          <Card>
            <div className="p-4 space-y-2">
              <h2 className="font-semibold">Payments</h2>
              <ul className="text-sm space-y-1">
                <li>User X — Premium+ — $14.99</li>
                <li>User Y — Premium — $9.99</li>
              </ul>
            </div>
          </Card>
          <Card>
            <div className="p-4 space-y-2">
              <h2 className="font-semibold">Top searches</h2>
              <ul className="text-sm space-y-1">
                <li>“коты” — 12 results</li>
                <li>“утка” — 0 results ⚠️</li>
              </ul>
            </div>
          </Card>
          <Card>
            <div className="p-4 space-y-2">
              <h2 className="font-semibold">Feature flags</h2>
              <ul className="text-sm space-y-1">
                <li>New Compass UI — on</li>
                <li>Echo v2 — off</li>
              </ul>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
