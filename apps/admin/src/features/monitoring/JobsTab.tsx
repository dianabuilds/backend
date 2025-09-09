import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { api } from '../../api/client';
import Pill from '../../components/Pill';
import { type JobRow,JobsTable } from './JobsTable';

type Job = JobRow;

interface QueueStats {
  pending: number;
  active: number;
}

interface Queues {
  [name: string]: QueueStats;
}

// status formatting and duration handled inside JobsTable

export default function JobsTab() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [queues, setQueues] = useState<Queues>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [recentRes, queuesRes] = await Promise.all([
        api.get<Job[]>('/admin/jobs/recent'),
        api.get<Queues>('/admin/jobs/queues'),
      ]);
      setJobs(recentRes.data || []);
      setQueues(queuesRes.data || {});
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const restartFailed = async () => {
    try {
      await api.post('/admin/jobs/restart_failed', {});
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">Jobs</h2>
        <div className="ml-auto flex gap-2">
          <button onClick={restartFailed} className="px-3 py-1 rounded border">
            Restart failed
          </button>
          <Link to="/ops/jobs" className="px-3 py-1 rounded border bg-blue-600 text-white">
            Open Ops
          </Link>
        </div>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <>
          {Object.keys(queues).length > 0 && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(queues).map(([name, stats]) => (
                <Pill key={name} variant="warn">
                  {name}: {stats.pending}/{stats.active}
                </Pill>
              ))}
            </div>
          )}
          <JobsTable jobs={jobs} variant="summary" />
        </>
      )}
    </div>
  );
}
