import { useEffect, useState } from 'react';

import { api } from '../../api/client';
import Pill from '../../components/Pill';
import { Card, CardContent } from '../../components/ui/card';
import RateLimitRulesEditor from './RateLimitRulesEditor';
import Recent429Table from './Recent429Table';

interface RateRules {
  enabled: boolean;
  rules: Record<string, string>;
}
interface RecentHit {
  path: string;
  ip: string;
  rule: string;
  ts: string;
}

type Recent429 = RecentHit[];

export default function RateLimitsTab() {
  const [rules, setRules] = useState<RateRules | null>(null);
  const [recent, setRecent] = useState<Recent429 | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [r, h] = await Promise.all([
        api.get<RateRules>('/admin/ratelimit/rules'),
        api.get<Recent429>('/admin/ratelimit/recent429'),
      ]);
      setRules(r.data || null);
      setDraft(
        ((r.data as { rules?: Record<string, string> } | null)?.rules || {}) as Record<
          string,
          string
        >,
      );
      setRecent(h.data || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const saveRule = async (key: string) => {
    setSaving((s) => ({ ...s, [key]: true }));
    try {
      await api.patch('/admin/ratelimit/rules', { key, rule: draft[key] });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving((s) => ({ ...s, [key]: false }));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const entries = Object.entries(draft);

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">Rate limits</h2>
            {rules && (
              <Pill variant={rules.enabled ? 'ok' : 'warn'} className="text-sm">
                {rules.enabled ? 'Enabled' : 'Disabled'}
              </Pill>
            )}
          </div>
          {loading && <p>Loading...</p>}
          {error && <p className="text-red-600">{error}</p>}
          {rules && (
            <RateLimitRulesEditor
              entries={entries}
              onChange={(k, v) => setDraft((d) => ({ ...d, [k]: v }))}
              onSave={saveRule}
              saving={saving}
            />
          )}
        </CardContent>
      </Card>
      {recent && (
        <Card>
          <CardContent>
            <h3 className="font-semibold mb-2">Recent 429</h3>
            <Recent429Table items={recent} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
