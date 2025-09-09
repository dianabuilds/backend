export interface ListResponse<T> {
  items: T[];
}

export interface Page<T> extends ListResponse<T> {
  page: number;
  size: number;
  total: number;
}

export interface Account {
  id: string;
  name: string;
  slug: string;
  role?: string;
  type: 'personal' | 'team' | 'global';
}
