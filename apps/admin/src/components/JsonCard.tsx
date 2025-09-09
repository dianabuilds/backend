import { useState } from 'react';

interface JsonCardProps {
  data: unknown;
  className?: string;
}

export default function JsonCard({ data, className }: JsonCardProps) {
  const [showRaw, setShowRaw] = useState(false);

  if (showRaw) {
    return (
      <div className={className}>
        <button
          onClick={() => setShowRaw(false)}
          className="mb-2 text-xs text-blue-600 hover:underline"
        >
          Hide raw JSON
        </button>
        <pre className="max-h-64 overflow-auto whitespace-pre-wrap text-xs bg-gray-50 p-2 rounded">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  }

  if (!data || typeof data !== 'object') {
    return <div className={className}>-</div>;
  }

  return (
    <div className={className}>
      <table className="min-w-full text-xs">
        <tbody>
          {Object.entries(data as Record<string, unknown>).map(([k, v]) => (
            <tr key={k} className="border-t">
              <td className="px-2 py-1 font-medium">{k}</td>
              <td className="px-2 py-1 break-all">
                {typeof v === 'object' ? JSON.stringify(v) : String(v)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button
        onClick={() => setShowRaw(true)}
        className="mt-2 text-xs text-blue-600 hover:underline"
      >
        Show raw JSON
      </button>
    </div>
  );
}
