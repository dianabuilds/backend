export interface ListResponse<T> {
  items: T[];
}

export interface Page<T> extends ListResponse<T> {
  page: number;
  size: number;
  total: number;
}

export interface Workspace {
  id: string;
  name: string;
  role?: string;
  type: "personal" | "team" | "global";
}
