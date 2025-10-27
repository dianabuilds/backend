import * as React from "react";

import { fetchAuditEvents, fetchAuditUsers } from "@shared/api";
import type {
  ManagementAuditEvent,
  ManagementAuditFacets,
  ManagementAuditResponse,
  ManagementAuditTaxonomy,
  ManagementAuditUser
} from "@shared/types/management";
import { usePaginatedQuery } from "@shared/hooks/usePaginatedQuery";
import { extractErrorMessage } from "@shared/utils/errors";

export type ManagementAuditFilters = {
  search: string;
  module: string;
  action: string;
  resourceType: string;
  result: string;
  actorId: string;
  dateFrom: string;
  dateTo: string;
};

export const DEFAULT_MANAGEMENT_AUDIT_FILTERS: ManagementAuditFilters = {
  search: '',
  module: '',
  action: '',
  resourceType: '',
  result: '',
  actorId: '',
  dateFrom: '',
  dateTo: '',
};

export type UseManagementAuditOptions = {
  initialPageSize?: number;
};

export type UseManagementAuditResult = {
  events: ManagementAuditEvent[];
  page: number;
  setPage: (page: number) => void;
  pageSize: number;
  setPageSize: (size: number) => void;
  hasNext: boolean;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  facets: ManagementAuditFacets | undefined;
  taxonomy: ManagementAuditTaxonomy | undefined;
  totalItems: number | undefined;
};

export function useManagementAudit(
  filters: ManagementAuditFilters,
  { initialPageSize = 10 }: UseManagementAuditOptions = {},
): UseManagementAuditResult {
  const filtersKey = React.useMemo(
    () => JSON.stringify(filters),
    [filters],
  );
  const [response, setResponse] = React.useState<ManagementAuditResponse | null>(null);
  const [totalItems, setTotalItems] = React.useState<number | undefined>(undefined);

  const query = usePaginatedQuery<ManagementAuditEvent, ManagementAuditResponse>({
    initialPageSize,
    debounceMs: 250,
    dependencies: [filtersKey],
    fetcher: async ({ page, pageSize, signal }) => {

      return await fetchAuditEvents({
        page,
        pageSize,
        search: filters.search,
        module: filters.module,
        action: filters.action,
        resourceType: filters.resourceType,
        result: filters.result,
        actorId: filters.actorId,
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
        signal,
      });
    },
    mapResponse: (payload, { page, pageSize }) => {
      setResponse(payload ?? null);
      const items = Array.isArray(payload?.items) ? payload.items : [];
      const hasMore = Boolean(payload?.has_more);
      const computedTotal = hasMore ? undefined : (page - 1) * pageSize + items.length;
      setTotalItems(computedTotal);
      return {
        items,
        hasNext: hasMore,
        total: computedTotal,
      };
    },
    onError: (error) => {
      setResponse(null);
      setTotalItems(undefined);
      return extractErrorMessage(error, 'Не удалось загрузить аудит');
    },
  });

  return {
    events: query.items,
    page: query.page,
    setPage: query.setPage,
    pageSize: query.pageSize,
    setPageSize: query.setPageSize,
    hasNext: query.hasNext,
    loading: query.loading,
    error: query.error,
    refresh: query.refresh,
    facets: response?.facets,
    taxonomy: response?.taxonomy,
    totalItems,
  };
}

export type UseManagementAuditUsersResult = {
  options: ManagementAuditUser[];
  loading: boolean;
  error: string | null;
};

export function useManagementAuditUsers(search: string): UseManagementAuditUsersResult {
  const [options, setOptions] = React.useState<ManagementAuditUser[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const trimmed = search.trim();
    if (!trimmed) {
      setOptions([]);
      setLoading(false);
      setError(null);
      return;
    }
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError(null);
    void fetchAuditUsers(trimmed, { signal: controller.signal })
      .then((result) => {
        if (!active) return;
        setOptions(result);
      })
      .catch((err) => {
        if (!active) return;
        setOptions([]);
        setError(extractErrorMessage(err, 'Не удалось загрузить пользователей'));
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [search]);

  return { options, loading, error };
}
