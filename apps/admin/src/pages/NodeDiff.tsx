/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { getNode } from '../api/nodes';
import type { OutputData } from '../types/editorjs';
import { useAccount } from '../account/AccountContext';

function diffObjects(a: any, b: any, prefix = ''): string[] {
  let out: string[] = [];
  const keys = new Set([...Object.keys(a || {}), ...Object.keys(b || {})]);
  for (const k of keys) {
    const path = prefix ? `${prefix}.${k}` : k;
    const av = a ? a[k] : undefined;
    const bv = b ? b[k] : undefined;
    if (av && bv && typeof av === 'object' && typeof bv === 'object') {
      out = out.concat(diffObjects(av, bv, path));
    } else if (JSON.stringify(av) !== JSON.stringify(bv)) {
      out.push(`${path}: ${JSON.stringify(av)} → ${JSON.stringify(bv)}`);
    }
  }
  return out;
}

export default function NodeDiff() {
  const { id } = useParams<{ id: string }>();
  const { accountId } = useAccount();
  const [remote, setRemote] = useState<any | null>(null);
  const [local, setLocal] = useState<any | null>(null);

  const nodeId = Number(id);

  useEffect(() => {
    if (!Number.isInteger(nodeId) || !accountId) return;
    (async () => {
      const node = await getNode(accountId, nodeId);
      const localRaw = localStorage.getItem(`node-draft-${nodeId}`);
      const localData = localRaw ? JSON.parse(localRaw) : null;
      const remoteData = {
        title: node.title ?? '',
        summary: (node as any).summary ?? '',
        tags: node.tags ?? [],
        contentData: (node.content as OutputData) || {},
      };
      setLocal(localData);
      setRemote(remoteData);
    })();
  }, [nodeId, accountId]);

  if (!Number.isInteger(nodeId) || !accountId) {
    return <div className="p-4">Invalid id</div>;
  }

  if (!remote || !local) {
    return <div className="p-4">Loading…</div>;
  }

  const diffs = diffObjects(local, remote);

  return (
    <div className="p-4">
      <h1 className="text-lg font-bold mb-4">Node diff</h1>
      {diffs.length === 0 ? (
        <div>No differences</div>
      ) : (
        <ul className="list-disc pl-5 text-sm space-y-1">
          {diffs.map((d, i) => (
            <li key={i}>{d}</li>
          ))}
        </ul>
      )}
      <Link to={-1 as any} className="inline-block mt-4 px-2 py-1 border rounded">
        Back
      </Link>
    </div>
  );
}
