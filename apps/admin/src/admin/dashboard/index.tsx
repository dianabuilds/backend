import widgets from './widgets.json';
import { useAuth } from '../../auth/AuthContext';
import ModerationQueueWidget from './ModerationQueueWidget';
import DraftIssuesWidget from './DraftIssuesWidget';
import BackgroundJobsWidget from './BackgroundJobsWidget';

const componentMap: Record<string, any> = {
  moderation: ModerationQueueWidget,
  drafts: DraftIssuesWidget,
  jobs: BackgroundJobsWidget,
};

export default function Dashboard() {
  const { user } = useAuth();
  const role = user?.role ?? '';
  const allowed = widgets.filter((w) => {
    if (role === 'admin') return true;
    if (role === 'moderator') return w.type === 'moderation' || w.type === 'drafts';
    if (role === 'support') return w.type === 'jobs';
    return false;
  });
  return (
    <div className="space-y-6">
      {allowed.map((w) => {
        const Comp = componentMap[w.type];
        return Comp ? (
          <Comp
            key={w.type}
            query={w.query}
            refreshInterval={w.refreshInterval}
          />
        ) : null;
      })}
    </div>
  );
}
