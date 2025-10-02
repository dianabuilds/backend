import React from 'react';
import { useParams } from 'react-router-dom';
import { apiGet } from '../../shared/api/client';
import { sanitizeHtml } from '../../shared/utils/sanitize';

type NodePublic = {
  id: number;
  slug: string;
  title?: string | null;
  content?: string | null;
  cover_url?: string | null;
  tags?: string[];
  is_public?: boolean;
};

export default function NodePublicPage() {
  const { slug } = useParams();
  const [data, setData] = React.useState<NodePublic | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const sanitizedContent = React.useMemo(() => sanitizeHtml(data?.content ?? ''), [data?.content]);

  React.useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await apiGet(`/v1/nodes/slug/${encodeURIComponent(String(slug || ''))}`);
        if (!cancelled) setData(res);
      } catch (err: any) {
        if (!cancelled) setError(String(err?.message || 'Not found or private'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (slug) load();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (loading) return <div className="mx-auto max-w-3xl p-6 text-gray-600">Loading...</div>;
  if (error) return <div className="mx-auto max-w-3xl p-6 text-red-600">{error}</div>;
  if (!data) return null;

  const title = data.title || `Node ${data.slug}`;

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="mb-3 text-2xl font-semibold text-gray-900">{title}</h1>
      {data.cover_url && (
        <div className="mb-4">
          {/* eslint-disable-next-line jsx-a11y/img-redundant-alt */}
          <img src={data.cover_url} alt="Cover" className="mx-auto max-h-[420px] rounded" />
        </div>
      )}
      {Array.isArray(data.tags) && data.tags.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {data.tags.map((t) => (
            <span key={t} className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
              #{t}
            </span>
          ))}
        </div>
      )}
      {data.content && (
        <article className="prose max-w-none dark:prose-invert">
          <div dangerouslySetInnerHTML={{ __html: sanitizedContent }} />
        </article>
      )}
    </div>
  );
}

