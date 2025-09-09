import Pill from '../../components/Pill';

export interface JobRow {
  id: string;
  name: string;
  status: string;
  started_at: string;
  finished_at?: string | null;
  log_url?: string | null;
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

interface JobsTableProps {
  jobs: JobRow[];
  variant: 'ops' | 'summary';
  onRetry?: (id: string) => void | Promise<void>;
  className?: string;
}

export function JobsTable({ jobs, variant, onRetry, className = '' }: JobsTableProps) {
  return (
    <table className={`min-w-full text-sm ${className}`.trim()}>
      <thead>
        <tr className="border-b">
          <th className="p-2 text-left">Name</th>
          <th className="p-2 text-left">Status</th>
          {variant === 'summary' ? (
            <th className="p-2 text-left">Duration</th>
          ) : (
            <>
              <th className="p-2 text-left">Started</th>
              <th className="p-2 text-left">Finished</th>
              <th className="p-2 text-left">Actions</th>
            </>
          )}
        </tr>
      </thead>
      <tbody>
        {jobs.map((job) => (
          <tr key={job.id} className="border-b">
            <td className="p-2">{job.name}</td>
            <td className="p-2 align-middle">
              <Pill variant={statusVariant(job.status)}>{job.status}</Pill>
            </td>
            {variant === 'summary' ? (
              <td className="p-2">{formatDuration(job.started_at, job.finished_at)}</td>
            ) : (
              <>
                <td className="p-2">{new Date(job.started_at).toLocaleString()}</td>
                <td className="p-2">
                  {job.finished_at ? new Date(job.finished_at).toLocaleString() : '-'}
                </td>
                <td className="p-2 space-x-2">
                  <button
                    className="px-2 py-1 bg-amber-600 text-white rounded"
                    onClick={async () => {
                      if (onRetry) await onRetry(job.id);
                    }}
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
              </>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
