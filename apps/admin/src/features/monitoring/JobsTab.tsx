import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { api } from '../../api/client';
import Pill from '../../components/Pill';

interface Job {
  id: string;
  name: string;
  status: string;
  started_at: string;
  finished_at?: string | null;
}

interface QueueStats {
  pending: number;
  active: number;
}

interface Queues {
  [name: string]: QueueStats;
}

function statusVariant(status: string): 'ok' | 'warn' | 'danger' {
  switch (status) {
    case 'success':
      return 'ok';
    case 'failed':
      return 'danger';
    default:
      return 'warn';
  }
}

function formatDuration(start: string, finish?: string | null): string {
  const startMs = new Date(start).getTime();
  const endMs = finish ? new Date(finish).getTime() : Date.now();
  const ms = Math.max(0, endMs - startMs);
  return `${(ms / 1000).toFixed(1)}s`;
}

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
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="p-2 text-left">Name</th>
                <th className="p-2 text-left">Status</th>
                <th className="p-2 text-left">Duration</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id} className="border-b">
                  <td className="p-2">{job.name}</td>
                  <td className="p-2 align-middle">
                    <Pill variant={statusVariant(job.status)}>{job.status}</Pill>
                  </td>
                  <td className="p-2">{formatDuration(job.started_at, job.finished_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
