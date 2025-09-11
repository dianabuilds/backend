// @ts-nocheck
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { useAccount } from '../../../account/AccountContext';
import { getNode } from '../../../api/nodes';
import type { Doc } from '../components/AdminNodePreview';
import AdminNodePreview from '../components/AdminNodePreview';

export default function NodePreview() {
  const { type = 'article', id = '' } = useParams<{ type?: string; id?: string }>();
  const { accountId } = useAccount();
  const [doc, setDoc] = useState<Doc | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const n = await getNode(accountId || '', id);
        const content = (n as unknown as { content?: unknown }).content;
        const blocks =
          content &&
          typeof content === 'object' &&
          Array.isArray((content as { blocks?: unknown }).blocks)
            ? ((content as { blocks?: unknown }).blocks as Doc['blocks'])
            : [];
        setDoc({
          title: n.title || '',
          cover: n.coverUrl || undefined,
          tags: n.tags || [],
          reactions: n.reactions || {},
          blocks,
        });
      } catch {
        setError('Failed to load node');
      } finally {
        setLoading(false);
      }
    })();
  }, [accountId, type, id]);
  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;
  if (!doc) return <div>No data</div>;

  return <AdminNodePreview doc={doc} />;
}
