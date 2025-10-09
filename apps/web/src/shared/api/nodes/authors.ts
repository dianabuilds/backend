import { apiGet } from '../client';
import type { NodeUserOption } from '../../types/nodes';
import { ensureArray, isObjectRecord, pickNullableString, pickString } from './utils';

type RequestOptions = {
  signal?: AbortSignal;
};

type SearchOptions = RequestOptions & {
  limit?: number;
};

const USERS_ENDPOINT = '/v1/users';
const USERS_SEARCH_ENDPOINT = '/v1/users/search';

function normalizeUserOption(value: unknown): NodeUserOption | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  if (!id) {
    return null;
  }
  const username = pickNullableString(value.username) ?? id;
  return {
    id,
    username,
  };
}

export async function searchNodeAuthors(query: string, options: SearchOptions = {}): Promise<NodeUserOption[]> {
  const trimmed = query.trim();
  if (!trimmed) {
    return [];
  }
  const params = new URLSearchParams({ q: trimmed });
  if (options.limit) {
    params.set('limit', String(options.limit));
  }
  const response = await apiGet<unknown[]>(`${USERS_SEARCH_ENDPOINT}?${params.toString()}`, {
    signal: options.signal,
  });
  return ensureArray(response, normalizeUserOption);
}

export async function fetchNodeAuthor(userId: string, options: RequestOptions = {}): Promise<NodeUserOption | null> {
  const trimmed = userId.trim();
  if (!trimmed) {
    throw new Error('node_author_id_missing');
  }
  const response = await apiGet<unknown>(`${USERS_ENDPOINT}/${encodeURIComponent(trimmed)}`, {
    signal: options.signal,
  });
  if (!isObjectRecord(response)) {
    return null;
  }
  const id = pickString(response.id) ?? trimmed;
  const username = pickNullableString(response.username) ?? id;
  return { id, username };
}

export const nodesAuthorsApi = {
  searchNodeAuthors,
  fetchNodeAuthor,
};

