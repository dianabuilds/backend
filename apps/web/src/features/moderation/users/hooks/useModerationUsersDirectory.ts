import * as React from 'react';

import {
  fetchModerationUserDetail,
  fetchModerationUsers,
} from '@shared/api/moderation';
import type { FetchModerationUsersParams } from '@shared/api/moderation/users';
import { extractErrorMessage } from '@shared/utils/errors';
import type { FilterState, ListState, ModerationUserDetail } from '../types';
import { useDebounce } from './useDebounce';

const INITIAL_LIST_STATE: ListState = {
  items: [],
  loading: false,
  error: null,
  nextCursor: null,
  totalItems: undefined,
  meta: {},
};

export type DetailStatus = {
  loading: boolean;
  error: string | null;
};

export type UseModerationUsersDirectoryParams = {
  filters: FilterState;
  search: string;
  initialPageSize?: number;
};

export type UseModerationUsersDirectoryResult = {
  listState: ListState;
  page: number;
  pageSize: number;
  setPageSize: (size: number) => void;
  handlePageChange: (page: number) => void;
  refresh: () => void;
  loadUserDetail: (userId: string, opts?: { silent?: boolean }) => Promise<ModerationUserDetail | null>;
  detailStatus: DetailStatus;
  resetDetailStatus: () => void;
  setDetailError: (message: string | null) => void;
  getCachedDetail: (userId: string) => ModerationUserDetail | null;
  debouncedSearch: string;
};

function buildFetchParams(
  base: FetchModerationUsersParams,
  overrides: Partial<FetchModerationUsersParams> = {},
): FetchModerationUsersParams {
  return {
    ...base,
    ...overrides,
  };
}

export function useModerationUsersDirectory({
  filters,
  search,
  initialPageSize = 25,
}: UseModerationUsersDirectoryParams): UseModerationUsersDirectoryResult {
  const debouncedSearch = useDebounce(search.trim());

  const [listState, setListState] = React.useState<ListState>(INITIAL_LIST_STATE);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSizeState] = React.useState(initialPageSize);
  const [cursor, setCursor] = React.useState<string | null>(null);
  const [detailStatus, setDetailStatus] = React.useState<DetailStatus>({ loading: false, error: null });

  const listAbortRef = React.useRef<AbortController | null>(null);
  const detailAbortRef = React.useRef<AbortController | null>(null);
  const prevCursorsRef = React.useRef<string[]>([]);
  const detailCacheRef = React.useRef<Map<string, ModerationUserDetail>>(new Map());

  const baseParams = React.useMemo<FetchModerationUsersParams>(
    () => ({
      limit: pageSize,
      cursor,
      status: filters.status,
      role: filters.role,
      registrationFrom: filters.registrationFrom || null,
      registrationTo: filters.registrationTo || null,
      search: debouncedSearch || null,
    }),
    [cursor, debouncedSearch, filters.registrationFrom, filters.registrationTo, filters.role, filters.status, pageSize],
  );

  const loadUsers = React.useCallback(
    async (targetCursor: string | null) => {
      listAbortRef.current?.abort();
      const controller = new AbortController();
      listAbortRef.current = controller;
      setListState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const params = buildFetchParams(baseParams, { cursor: targetCursor });
        const result = await fetchModerationUsers({ ...params, signal: controller.signal });

        setListState({
          items: result.items,
          loading: false,
          error: null,
          nextCursor: result.nextCursor ?? null,
          totalItems: result.total,
          meta: result.meta ?? {},
        });
      } catch (err) {
        if (controller.signal.aborted) return;
        const message = extractErrorMessage(err, 'Failed to load moderation users');
        setListState((prev) => ({ ...prev, loading: false, error: message }));
      }
    },
    [baseParams],
  );

  React.useEffect(() => {
    prevCursorsRef.current = [];
    setPage(1);
    setCursor(null);
  }, [debouncedSearch, filters.registrationFrom, filters.registrationTo, filters.risk, filters.role, filters.status, pageSize]);

  React.useEffect(() => {
    void loadUsers(cursor);
    return () => {
      listAbortRef.current?.abort();
    };
  }, [cursor, loadUsers]);

  React.useEffect(
    () => () => {
      listAbortRef.current?.abort();
      detailAbortRef.current?.abort();
    },
    [],
  );

  const loadUserDetail = React.useCallback(
    async (userId: string, opts: { silent?: boolean } = {}) => {
      detailAbortRef.current?.abort();
      const controller = new AbortController();
      detailAbortRef.current = controller;

      if (opts.silent) {
        setDetailStatus((prev) => ({ ...prev, error: null }));
      } else {
        setDetailStatus({ loading: true, error: null });
      }

      try {
        const detail = await fetchModerationUserDetail(userId, { signal: controller.signal });
        detailCacheRef.current.set(detail.id, detail);
        setDetailStatus({ loading: false, error: null });
        setListState((prev) => ({
          ...prev,
          items: prev.items.map((item) => (item.id === detail.id ? detail : item)),
        }));
        return detail;
      } catch (err) {
        if (controller.signal.aborted) return null;
        const message = extractErrorMessage(err, 'Failed to load user detail');
        setDetailStatus({ loading: false, error: message });
        return null;
      }
    },
    [],
  );

  const handlePageChange = React.useCallback(
    (targetPage: number) => {
      setDetailStatus((prev) => (prev.loading ? { ...prev, loading: false } : prev));
      if (targetPage === page) return;
      if (targetPage > page) {
        if (!listState.nextCursor) return;
        prevCursorsRef.current = [...prevCursorsRef.current, cursor ?? ''];
        setPage(targetPage);
        setCursor(listState.nextCursor);
        return;
      }
      const history = prevCursorsRef.current;
      const prevCursor = history[history.length - 1] ?? '';
      prevCursorsRef.current = history.slice(0, -1);
      setPage(targetPage);
      setCursor(prevCursor || null);
    },
    [cursor, listState.nextCursor, page],
  );

  const refresh = React.useCallback(() => {
    void loadUsers(cursor);
  }, [cursor, loadUsers]);

  const setPageSize = React.useCallback((size: number) => {
    setPageSizeState(size);
  }, []);

  const resetDetailStatus = React.useCallback(() => {
    setDetailStatus({ loading: false, error: null });
  }, []);

  const setDetailError = React.useCallback((message: string | null) => {
    setDetailStatus({ loading: false, error: message });
  }, []);

  const getCachedDetail = React.useCallback(
    (userId: string) => detailCacheRef.current.get(userId) ?? null,
    [],
  );

  return {
    listState,
    page,
    pageSize,
    setPageSize,
    handlePageChange,
    refresh,
    loadUserDetail,
    detailStatus,
    resetDetailStatus,
    setDetailError,
    getCachedDetail,
    debouncedSearch,
  };
}
