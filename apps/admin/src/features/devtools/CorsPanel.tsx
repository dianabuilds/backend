import { useEffect, useState } from 'react';

import { api } from '../../api/client';

interface CorsPolicy {
  allow_origins?: string[];
  allow_origin_regex?: string;
  allow_credentials: boolean;
  allow_methods: string[];
  allow_headers: string[];
  expose_headers: string[];
  max_age: number;
}

export default function CorsPanel() {
  const [policy, setPolicy] = useState<CorsPolicy | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.get<CorsPolicy>('/admin/ops/cors-policy');
        setPolicy(res.data || null);
      } catch (e) {
        setError((e as Error)?.message || 'Failed to load');
      }
    };
    load();
  }, []);

  const origin = typeof window !== 'undefined' ? window.location.origin : '';

  let mismatch = false;
  if (policy) {
    if (Array.isArray(policy.allow_origins) && policy.allow_origins.length > 0) {
      mismatch = !policy.allow_origins.includes(origin);
    } else if (policy.allow_origin_regex) {
      try {
        mismatch = !new RegExp(policy.allow_origin_regex).test(origin);
      } catch {
        mismatch = true;
      }
    }
  }

  return (
    <div className="rounded border p-3">
      <h3 className="font-semibold mb-2">CORS Policy</h3>
      <div className="mb-2">
        <span className="text-gray-600">Current origin: </span>
        <span className="font-mono">{origin}</span>
      </div>
      {error && <div className="mb-2 text-red-600">{error}</div>}
      {policy ? (
        <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded mb-2 overflow-x-auto">
          {JSON.stringify(policy, null, 2)}
        </pre>
      ) : (
        !error && <div className="mb-2 text-sm text-gray-500">Loading...</div>
      )}
      {mismatch && (
        <div className="text-sm text-red-600">
          Warning: current origin is not allowed by the server CORS policy
        </div>
      )}
    </div>
  );
}
