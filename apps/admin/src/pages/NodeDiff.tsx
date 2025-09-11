import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { getNode } from '../api/nodes';
import type { OutputData } from '../types/editorjs';

function diffObjects(a: unknown, b: unknown, prefix = ''): string[] {
  let out: string[] = [];
  const keys = new Set([...Object.keys((a as object) || {}), ...Object.keys((b as object) || {})]);
  for (const k of keys) {
    const path = prefix ? `${prefix}.${k}` : k;
    const av = a && typeof a === 'object' ? (a as Record<string, unknown>)[k] : undefined;
    const bv = b && typeof b === 'object' ? (b as Record<string, unknown>)[k] : undefined;
    if (av && bv && typeof av === 'object' && typeof bv === 'object') {
      out = out.concat(diffObjects(av, bv, path));
    } else if (JSON.stringify(av) !== JSON.stringify(bv)) {
      out.push(`${path}: ${JSON.stringify(av)} → ${JSON.stringify(bv)}`);
    }
  }
  return out;
}

function getString(obj: unknown, key: string, fallback = ''): string {
  if (obj && typeof obj === 'object' && key in (obj as Record<string, unknown>)) {
    const v = (obj as Record<string, unknown>)[key];
    return typeof v === 'string' ? v : fallback;
  }
  return fallback;
}

export default function NodeDiff() {
  const { id } = useParams<{ id: string }>();
  const [remote, setRemote] = useState<Record<string, unknown> | null>(null);
  const [local, setLocal] = useState<Record<string, unknown> | null>(null);

  const nodeId = Number(id);

  useEffect(() => {
    if (!Number.isInteger(nodeId)) return;
    (async () => {
      const node = await getNode(nodeId);
      const localRaw = localStorage.getItem(`node-draft-${nodeId}`);
      const localData = localRaw ? JSON.parse(localRaw) : null;
      const remoteData: Record<string, unknown> = {
        title: node.title ?? '',
        summary: getString(node, 'summary', ''),
        tags: node.tags ?? [],
        contentData: (node as unknown as Record<string, unknown>).content ?? ({} as OutputData),
      };
      setLocal(localData);
      setRemote(remoteData);
    })();
  }, [nodeId]);

  if (!Number.isInteger(nodeId)) {
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
      <button
        type="button"
        className="inline-block mt-4 px-2 py-1 border rounded"
        onClick={() => window.history.back()}
      >
        Back
      </button>
    </div>
  );
}
