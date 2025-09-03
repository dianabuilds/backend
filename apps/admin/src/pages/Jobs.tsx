import { useEffect, useState } from "react";
import { api } from "../api/client";
import Pill from "../components/Pill";

interface Job {
  id: string;
  name: string;
  status: string;
  log_url?: string | null;
  started_at: string;
  finished_at?: string | null;
}

function statusVariant(status: string): "ok" | "warn" | "danger" {
  switch (status) {
    case "success":
      return "ok";
    case "failed":
      return "danger";
    default:
      return "warn";
  }
}

export default function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/admin/jobs/recent");
      setJobs(res.data as Job[]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Background jobs</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Name</th>
              <th className="p-2 text-left">Status</th>
              <th className="p-2 text-left">Started</th>
              <th className="p-2 text-left">Finished</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id} className="border-b">
                <td className="p-2">{job.name}</td>
                <td className="p-2 align-middle">
                  <Pill variant={statusVariant(job.status)}>{job.status}</Pill>
                </td>
                <td className="p-2">
                  {new Date(job.started_at).toLocaleString()}
                </td>
                <td className="p-2">
                  {job.finished_at
                    ? new Date(job.finished_at).toLocaleString()
                    : "-"}
                </td>
                <td className="p-2 space-x-2">
                  <button
                    className="px-2 py-1 bg-amber-600 text-white rounded"
                    onClick={() => alert("Not implemented")}
                  >
                    Перезапустить
                  </button>
                  {job.log_url && (
                    <a
                      href={job.log_url}
                      target="_blank"
                      rel="noopener"
                      className="px-2 py-1 bg-sky-600 text-white rounded"
                    >
                      Открыть лог
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
