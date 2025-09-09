import { useEffect, useState } from 'react';

import { api } from '../api/client';
import { type JobRow,JobsTable } from '../features/monitoring/JobsTable';

type Job = JobRow;

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<{ jobs?: Job[] }>('/admin/ops/jobs');
      setJobs((res.data?.jobs as Job[]) || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Background jobs</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <JobsTable
          jobs={jobs}
          variant="ops"
          onRetry={async (id) => {
            await api.post(`/admin/ops/jobs/${id}/retry`);
            await load();
          }}
        />
      )}
    </div>
  );
}
