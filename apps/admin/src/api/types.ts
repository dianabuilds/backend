export interface ListResponse<T> {
  items: T[];
}

export interface Page<T> extends ListResponse<T> {
  page: number;
  size: number;
  total: number;
}
