import { apiDelete, apiPost } from '../client';
import type { NodeLifecycleStatus } from '../../types/nodes';
import { pickString } from './utils';

const NODES_ENDPOINT = '/v1/admin/nodes';
const NODES_BULK_ENDPOINT = '/v1/admin/nodes/bulk/status';

type RequestOptions = {
  signal?: AbortSignal;
};

function normalizeNodeId(value: string): string {
  return value.trim();
}

export async function restoreNode(nodeId: string, options: RequestOptions = {}): Promise<void> {
  const normalized = normalizeNodeId(nodeId);
  if (!normalized) {
    throw new Error('node_id_missing');
  }
  await apiPost(`${NODES_ENDPOINT}/${encodeURIComponent(normalized)}/restore`, {}, { signal: options.signal });
}

export async function deleteNode(nodeId: string, options: RequestOptions = {}): Promise<void> {
  const normalized = normalizeNodeId(nodeId);
  if (!normalized) {
    throw new Error('node_id_missing');
  }
  await apiDelete(`${NODES_ENDPOINT}/${encodeURIComponent(normalized)}`, { signal: options.signal });
}

export type BulkUpdateNodesStatusPayload = {
  ids: string[];
  status: NodeLifecycleStatus;
  publish_at?: string;
  unpublish_at?: string;
};

function sanitizeIds(ids: string[]): string[] {
  const result: string[] = [];
  for (const value of ids) {
    const normalized = pickString(value);
    if (normalized) {
      result.push(normalized);
    }
  }
  return Array.from(new Set(result));
}

function normalizeScheduleValue(value: string | undefined): string | undefined {
  const normalized = value?.trim();
  return normalized && normalized.length ? normalized : undefined;
}

export async function bulkUpdateNodesStatus(
  payload: BulkUpdateNodesStatusPayload,
  options: RequestOptions = {},
): Promise<void> {
  const ids = sanitizeIds(payload.ids);
  if (!ids.length) {
    throw new Error('nodes_bulk_ids_missing');
  }
  if (!payload.status) {
    throw new Error('nodes_bulk_status_missing');
  }
  const body: Record<string, unknown> = {
    ids,
    status: payload.status,
  };
  const publishAt = normalizeScheduleValue(payload.publish_at);
  if (publishAt) {
    body.publish_at = publishAt;
  }
  const unpublishAt = normalizeScheduleValue(payload.unpublish_at);
  if (unpublishAt) {
    body.unpublish_at = unpublishAt;
  }
  await apiPost(NODES_BULK_ENDPOINT, body, { signal: options.signal });
}

export const nodesMutationsApi = {
  restoreNode,
  deleteNode,
  bulkUpdateNodesStatus,
};

