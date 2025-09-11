import type { AdminTransitionOut } from '../openapi';
import { api } from './client';

export type Transition = AdminTransitionOut & {
  priority?: number | null;
  disabled?: boolean | null;
  updated_at?: string | null;
  [k: string]: unknown;
};

export type TransitionListParams = {
  from_slug?: string;
  to_slug?: string;
  limit?: number;
  offset?: number;
  // "any" | "enabled" | "disabled"
  status?: 'any' | 'enabled' | 'disabled';
};

export async function listTransitions(params: TransitionListParams = {}): Promise<Transition[]> {
  const q = new URLSearchParams();
  if (params.from_slug) q.set('from_slug', params.from_slug);
  if (params.to_slug) q.set('to_slug', params.to_slug);
  if (typeof params.limit === 'number') q.set('limit', String(params.limit));
  if (typeof params.offset === 'number') q.set('offset', String(params.offset));
  if (params.status && params.status !== 'any') q.set('status', params.status);
  const res = await api.get<Transition[]>(
    `/admin/transitions${q.toString() ? `?${q.toString()}` : ''}`,
  );
  return res.data ?? [];
}

export type CreateTransitionBody = {
  from_slug: string;
  to_slug: string;
  label?: string;
  weight?: number;
  priority?: number;
  disabled?: boolean;

  [k: string]: unknown;
};

export async function createTransition(body: CreateTransitionBody): Promise<Transition> {
  const res = await api.post<CreateTransitionBody, Transition>('/admin/transitions', body);
  return res.data!;
}

export type UpdateTransitionBody = Partial<Omit<CreateTransitionBody, 'from_slug' | 'to_slug'>> & {
  // возможно, у бэкенда другие поля для обновления — оставим запас
  [k: string]: unknown;
};

export async function updateTransition(id: string, body: UpdateTransitionBody): Promise<void> {
  await api.patch(`/admin/transitions/${encodeURIComponent(id)}`, body);
}

// Клиентские bulk-хелперы поверх одиночных запросов

export async function bulkUpdate(ids: string[], patch: UpdateTransitionBody): Promise<void> {
  for (const id of ids) {
    await updateTransition(id, patch);
  }
}

export interface SimulateTransitionsBody {
  start: string;
  mode?: string;
  seed?: number;
  history?: string[];
  preview_mode?: string;
}

export interface TransitionTraceItem {
  policy?: string | null;
  candidates: string[];
  filters: string[];
  scores: Record<string, unknown>;
  chosen?: string | null;
}

export interface SimulateTransitionsResponse {
  next?: string | null;
  reason?: string | null;
  trace?: TransitionTraceItem[];
  metrics?: Record<string, unknown>;
}

// Removed unused helpers: deleteTransition, bulkDelete, simulateTransitions
