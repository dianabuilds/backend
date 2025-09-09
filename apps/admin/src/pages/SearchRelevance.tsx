import { useEffect, useState } from 'react';

import type { RelevancePayload } from '../api/searchSettings';
import { applyRelevance, dryRunRelevance, getRelevance } from '../api/searchSettings';
import { promptDialog } from '../shared/ui';
import PageLayout from './_shared/PageLayout';

export default function SearchRelevance() {
  const [payload, setPayload] = useState<RelevancePayload>({
    weights: { title: 3, body: 1, tags: 1.5, author: 0.5 },
    boosts: { freshness: { half_life_days: 14 }, popularity: { weight: 1 } },
    query: {
      fuzziness: 'AUTO',
      min_should_match: '2<75%',
      phrase_slop: 0,
      tie_breaker: undefined,
    },
  });
  const [sample, setSample] = useState<string>('photo, quest, tags');
  const [diff, setDiff] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [version, setVersion] = useState<number>(1);

  useEffect(() => {
    (async () => {
      try {
        const r = await getRelevance();
        setPayload(r.payload);
        setVersion(r.version);
      } catch {
        // ignore
      }
    })();
  }, []);

  const onPreview = async () => {
    setLoading(true);
    try {
      const res = await dryRunRelevance(
        payload,
        sample
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      );
      const txt = res.diff
        .map(
          (d) =>
            `• ${d.query}\n  before: [${d.topBefore.join(', ')}]\n  after:  [${d.topAfter.join(', ')}]`,
        )
        .join('\n');
      setDiff(txt || 'No diff (MVP stub)');
    } finally {
      setLoading(false);
    }
  };

  const onApply = async () => {
    const comment = (await promptDialog('Comment for audit (optional):')) || undefined;
    const res = await applyRelevance(payload, comment);
    setVersion(res.version);
    alert('Applied');
  };

  return (
    <PageLayout title="Search settings — Relevance" subtitle={`Active version: ${version}`}>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <div className="rounded border p-3 mb-4">
            <h2 className="font-semibold mb-2">Weights</h2>
            {(['title', 'body', 'tags', 'author'] as const).map((k) => (
              <div key={k} className="flex items-center gap-2 mb-2">
                <label className="w-32">{k}</label>
                <input
                  type="number"
                  step="0.1"
                  className="border rounded px-2 py-1 w-32"
                  value={payload.weights[k]}
                  onChange={(e) =>
                    setPayload({
                      ...payload,
                      weights: {
                        ...payload.weights,
                        [k]: Number(e.target.value),
                      },
                    })
                  }
                />
              </div>
            ))}
          </div>

          <div className="rounded border p-3 mb-4">
            <h2 className="font-semibold mb-2">Query params</h2>
            <div className="flex items-center gap-2 mb-2">
              <label className="w-32">fuzziness</label>
              <input
                className="border rounded px-2 py-1 w-48"
                value={payload.query.fuzziness}
                onChange={(e) =>
                  setPayload({
                    ...payload,
                    query: { ...payload.query, fuzziness: e.target.value },
                  })
                }
              />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <label className="w-32">min_should_match</label>
              <input
                className="border rounded px-2 py-1 w-48"
                value={payload.query.min_should_match}
                onChange={(e) =>
                  setPayload({
                    ...payload,
                    query: {
                      ...payload.query,
                      min_should_match: e.target.value,
                    },
                  })
                }
              />
            </div>
            <div className="flex items-center gap-2 mb-2">
              <label className="w-32">phrase_slop</label>
              <input
                type="number"
                className="border rounded px-2 py-1 w-32"
                value={payload.query.phrase_slop}
                onChange={(e) =>
                  setPayload({
                    ...payload,
                    query: {
                      ...payload.query,
                      phrase_slop: Number(e.target.value),
                    },
                  })
                }
              />
            </div>
          </div>

          <div className="flex gap-2">
            <button
              className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
              onClick={onPreview}
              disabled={loading}
            >
              Preview
            </button>
            <button
              className="px-3 py-1 rounded bg-green-600 text-white"
              onClick={onApply}
              disabled={loading}
            >
              Apply
            </button>
          </div>
        </div>

        <div>
          <div className="rounded border p-3">
            <h2 className="font-semibold mb-2">Sample queries</h2>
            <textarea
              className="w-full h-32 border rounded px-2 py-1"
              value={sample}
              onChange={(e) => setSample(e.target.value)}
            />
            <h2 className="font-semibold mt-4 mb-2">Preview diff</h2>
            <pre
              className="text-xs bg-gray-50 dark:bg-gray-900 p-2 rounded overflow-auto"
              style={{ minHeight: 160 }}
            >
              {diff || '—'}
            </pre>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
