import { api } from './client';

export interface SearchTopItem {
  query: string;
  count: number;
  results: number;
}

export async function getSearchTop(): Promise<SearchTopItem[]> {
  const res = await api.get<SearchTopItem[]>('/admin/search/top');
  return res.data ?? [];
}
