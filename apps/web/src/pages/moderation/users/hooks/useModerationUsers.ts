import * as React from 'react';

import { apiGet } from '../../../../shared/api/client';
import { extractErrorMessage } from '../../../../shared/utils/errors';
import {
  normalizeUserDetail,
  normalizeUserSummary,
} from '../normalizers';
import type {
  FilterState,
  ListState,
  ModerationUserDetail,
  ModerationUsersResponse,
} from '../types';
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

export type UseModerationUsersParams = {
  filters: FilterState;
  search: string;
  initialPageSize?: number;
};

export type UseModerationUsersResult = {
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

export function useModerationUsers({
  filters,
  search,
  initialPageSize = 25,
}: UseModerationUsersParams): UseModerationUsersResult {
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

  const loadUsers = React.useCallback(
    async (targetCursor: string | null) => {
      listAbortRef.current?.abort();
      const controller = new AbortController();
      listAbortRef.current = controller;
      setListState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        const params = new URLSearchParams();
        params.set('limit', String(pageSize));
        if (targetCursor) params.set('cursor', targetCursor);
        if (filters.status !== 'all') params.set('status', filters.status);
        if (filters.role !== 'any') params.set('role', filters.role);
        if (filters.registrationFrom) params.set('registered_from', filters.registrationFrom);
        if (filters.registrationTo) params.set('registered_to', filters.registrationTo);
        if (debouncedSearch) params.set('q', debouncedSearch);

        const response = await apiGet<ModerationUsersResponse>(`/api/moderation/users?${params.toString()}`, {
          signal: controller.signal,
        });

        const rawItems: Array<Record<string, unknown>> = Array.isArray(response?.items) ? response?.items ?? [] : [];
        const normalized = rawItems.map((item) => normalizeUserSummary(item));

        setListState({
          items: normalized,
          loading: false,
          error: null,
          nextCursor: response?.next_cursor ?? null,
          totalItems: typeof response?.total === 'number' ? response.total : undefined,
          meta: response?.meta ?? {},
        });
      } catch (err) {
        if (controller.signal.aborted) return;
        const message = extractErrorMessage(err, 'Failed to load moderation users');
        setListState((prev) => ({ ...prev, loading: false, error: message }));
      }
    },
    [debouncedSearch, filters.registrationFrom, filters.registrationTo, filters.role, filters.status, pageSize],
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
        const detailRaw = await apiGet<Record<string, unknown>>(`/api/moderation/users/${encodeURIComponent(userId)}`, {
          signal: controller.signal,
        });
        const detail = normalizeUserDetail(detailRaw ?? {});
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
