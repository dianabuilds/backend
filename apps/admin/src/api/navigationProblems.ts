import { api } from './client';

export interface NavigationProblem {
  node_id: string;
  slug: string;
  title: string | null;
  views: number;
  transitions: number;
  ctr: number;
  dead_end: boolean;
  cycle: boolean;
}

export async function listNavigationProblems(): Promise<NavigationProblem[]> {
  const res = await api.get<NavigationProblem[]>("/admin/navigation/problems");
  return res.data ?? [];
}
