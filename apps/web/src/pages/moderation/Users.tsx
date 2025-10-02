import * as React from 'react';
import { useSearchParams } from 'react-router-dom';
import { Surface, TablePagination } from '@ui';

import { apiPost } from '../../shared/api/client';
import { extractErrorMessage } from '../../shared/utils/errors';

import { UsersCardsMobile } from './users/components/UsersCardsMobile';
import { UserDrawer } from './users/components/UserDrawer';
import { UsersEmptyState } from './users/components/UsersEmptyState';
import { UsersError } from './users/components/UsersError';
import { UsersFilters } from './users/components/UsersFilters';
import { UsersHeader } from './users/components/UsersHeader';
import { UsersTable } from './users/components/UsersTable';
import { DEFAULT_FILTERS, DEFAULT_SORT, PAGE_SIZE_OPTIONS } from './users/constants';
import {
  capitalizeRole,
  formatRelativeTime,
  resolveRiskLevel,
} from './users/normalizers';
import type {
  DrawerTabKey,
  FilterState,
  ModerationRole,
  ModerationUserDetail,
  ModerationUserSummary,
  SortKey,
  SortState,
} from './users/types';
import { useModerationUsers } from './users/hooks/useModerationUsers';

export default function ModerationUsers(): JSX.Element {
  const [searchParams, setSearchParams] = useSearchParams();

  const [filters, setFilters] = React.useState<FilterState>(DEFAULT_FILTERS);
  const [search, setSearch] = React.useState('');
  const [advancedOpen, setAdvancedOpen] = React.useState(false);
  const [sort, setSort] = React.useState<SortState>(DEFAULT_SORT);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [drawerTab, setDrawerTab] = React.useState<DrawerTabKey>('overview');
  const [activeUserSummary, setActiveUserSummary] = React.useState<ModerationUserSummary | null>(null);
  const [activeUserDetail, setActiveUserDetail] = React.useState<ModerationUserDetail | null>(null);

  const lastFocusRef = React.useRef<string | null>(null);
  const [lastLoadedAt, setLastLoadedAt] = React.useState<string>(() => new Date().toISOString());

  const {
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
  } = useModerationUsers({ filters, search });

  React.useEffect(() => {
    if (!listState.loading) {
      setLastLoadedAt(new Date().toISOString());
    }
  }, [listState.loading, listState.items]);

  const lastRefreshLabel = formatRelativeTime(lastLoadedAt);

  const advancedActiveCount = React.useMemo(() => {
    let count = 0;
    if (filters.risk !== 'any') count += 1;
    if (filters.registrationFrom) count += 1;
    if (filters.registrationTo) count += 1;
    return count;
  }, [filters]);

  const handleFilterChange = React.useCallback((patch: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...patch }));
  }, []);

  const resetFilters = React.useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setSearch('');
    setAdvancedOpen(false);
  }, []);

  const handleSort = React.useCallback((key: SortKey) => {
    setSort((prev) => {
      if (prev.key === key) {
        return { key, order: prev.order === 'asc' ? 'desc' : 'asc' };
      }
      return { key, order: 'desc' };
    });
  }, []);

  const locallyFiltered = React.useMemo(() => {
    const needle = debouncedSearch.toLowerCase();
    return listState.items.filter((user) => {
      if (filters.status !== 'all' && user.status.toLowerCase() !== filters.status) return false;
      if (filters.role !== 'any' && !user.roles.map((role) => role.toLowerCase()).includes(filters.role)) return false;
      if (filters.registrationFrom && user.registered_at && user.registered_at < `${filters.registrationFrom}T00:00:00`) return false;
      if (filters.registrationTo && user.registered_at && user.registered_at > `${filters.registrationTo}T23:59:59`) return false;
      if (filters.risk !== 'any' && resolveRiskLevel(user) !== filters.risk) return false;
      if (!needle) return true;
      const haystack = [user.username, user.email ?? '', user.id, ...user.roles].map((value) => value.toLowerCase());
      return haystack.some((entry) => entry.includes(needle));
    });
  }, [debouncedSearch, filters, listState.items]);

  const sortedItems = React.useMemo(() => {
    const items = [...locallyFiltered];
    items.sort((a, b) => {
      let result = 0;
      switch (sort.key) {
        case 'registered_at': {
          const aTime = a.registered_at ? new Date(a.registered_at).getTime() : 0;
          const bTime = b.registered_at ? new Date(b.registered_at).getTime() : 0;
          result = aTime - bTime;
          break;
        }
        case 'last_seen_at': {
          const aTime = a.last_seen_at ? new Date(a.last_seen_at).getTime() : 0;
          const bTime = b.last_seen_at ? new Date(b.last_seen_at).getTime() : 0;
          result = aTime - bTime;
          break;
        }
        case 'complaints_count':
          result = a.complaints_count - b.complaints_count;
          break;
        case 'sanction_count':
          result = a.sanction_count - b.sanction_count;
          break;
        default:
          result = 0;
      }
      return sort.order === 'asc' ? result : -result;
    });
    return items;
  }, [locallyFiltered, sort]);

  const metrics = React.useMemo(() => {
    const total = sortedItems.length;
    const active = sortedItems.filter((user) => user.status.toLowerCase() === 'active').length;
    const sanctioned = sortedItems.filter((user) => user.sanction_count > 0).length;
    const highRisk = sortedItems.filter((user) => resolveRiskLevel(user) === 'high').length;
    const complaints = sortedItems.reduce(
      (sum, user) => sum + (Number.isFinite(user.complaints_count) ? user.complaints_count : 0),
      0,
    );
    return {
      total,
      active,
      sanctioned,
      highRisk,
      complaints,
    };
  }, [sortedItems]);

  const showEmptyState = !listState.loading && sortedItems.length === 0;

  const fetchAndSetDetail = React.useCallback(
    async (userId: string, opts: { silent?: boolean } = {}) => {
      const detail = await loadUserDetail(userId, opts);
      if (detail) {
        setActiveUserDetail(detail);
        setActiveUserSummary(detail);
      }
      return detail;
    },
    [loadUserDetail],
  );

  const handleOpenDrawer = React.useCallback(
    (user: ModerationUserSummary, nextTab: DrawerTabKey = 'overview') => {
      setActiveUserSummary(user);
      const cached = getCachedDetail(user.id);
      setActiveUserDetail(cached ?? null);
      setDrawerTab(nextTab);
      setDrawerOpen(true);
      resetDetailStatus();
      setDetailError(null);
      void fetchAndSetDetail(user.id);
    },
    [fetchAndSetDetail, getCachedDetail, resetDetailStatus, setDetailError],
  );

  const handleCloseDrawer = React.useCallback(() => {
    setDrawerOpen(false);
    setDrawerTab('overview');
    setActiveUserSummary(null);
    setActiveUserDetail(null);
    resetDetailStatus();
    setDetailError(null);
    if (searchParams.has('focus')) {
      const next = new URLSearchParams(searchParams);
      next.delete('focus');
      setSearchParams(next, { replace: true });
    }
  }, [resetDetailStatus, setDetailError, searchParams, setSearchParams]);

  React.useEffect(() => {
    const focusId = searchParams.get('focus');
    if (!focusId) {
      lastFocusRef.current = null;
      return;
    }
    if (lastFocusRef.current === focusId) return;
    const existing = listState.items.find((item) => item.id === focusId);
    if (existing) {
      lastFocusRef.current = focusId;
      handleOpenDrawer(existing, 'overview');
      return;
    }
    lastFocusRef.current = focusId;
    const placeholder: ModerationUserSummary = {
      id: focusId,
      username: focusId,
      email: null,
      roles: [],
      status: 'active',
      registered_at: null,
      last_seen_at: null,
      complaints_count: 0,
      notes_count: 0,
      sanction_count: 0,
      active_sanctions: [],
      last_sanction: null,
      meta: {},
    };
    setActiveUserSummary(placeholder);
    setActiveUserDetail(null);
    setDrawerTab('overview');
    setDrawerOpen(true);
    resetDetailStatus();
    setDetailError(null);
    void fetchAndSetDetail(focusId);
  }, [searchParams, listState.items, handleOpenDrawer, fetchAndSetDetail, resetDetailStatus, setDetailError]);

  const handleSaveRoles = React.useCallback(
    async (userId: string, targetRole: ModerationRole) => {
      const reference =
        activeUserDetail?.id === userId
          ? activeUserDetail
          : activeUserSummary?.id === userId
          ? activeUserSummary
          : null;
      const currentRoles = reference ? reference.roles.map((role) => role.toLowerCase() as ModerationRole) : [];
      const validRoles: ModerationRole[] = ['admin', 'moderator', 'support', 'user'];
      const add = currentRoles.includes(targetRole) ? [] : [targetRole];
      const remove = validRoles.filter((role) => role !== targetRole && currentRoles.includes(role));
      if (targetRole === 'user' && !add.includes('user')) add.push('user');

      try {
        setDetailError(null);
        await apiPost(`/api/moderation/users/${encodeURIComponent(userId)}/roles`, {
          add: add.map(capitalizeRole),
          remove: remove.map(capitalizeRole),
        });
        await refresh();
        await fetchAndSetDetail(userId, { silent: true });
      } catch (error) {
        setDetailError(extractErrorMessage(error, 'Failed to update roles'));
      }
    },
    [activeUserDetail, activeUserSummary, refresh, fetchAndSetDetail, setDetailError],
  );

  const handleIssueSanction = React.useCallback(
    async (
      userId: string,
      payload: { type: string; reason?: string; durationHours?: number },
    ) => {
      try {
        setDetailError(null);
        const request: Record<string, unknown> = { type: payload.type };
        const reason = payload.reason?.trim();
        if (reason) request.reason = reason;
        if (typeof payload.durationHours === 'number') {
          request.duration_hours = payload.durationHours;
        }
        await apiPost(`/api/moderation/users/${encodeURIComponent(userId)}/sanctions`, request);
        await refresh();
        await fetchAndSetDetail(userId, { silent: true });
      } catch (error) {
        setDetailError(extractErrorMessage(error, 'Failed to issue sanction'));
      }
    },
    [refresh, fetchAndSetDetail, setDetailError],
  );

  const handleCreateNote = React.useCallback(
    async (userId: string, payload: { text: string; pinned: boolean }) => {
      try {
        setDetailError(null);
        await apiPost(`/api/moderation/users/${encodeURIComponent(userId)}/notes`, {
          text: payload.text.trim(),
          pinned: payload.pinned,
        });
        await fetchAndSetDetail(userId, { silent: true });
      } catch (error) {
        setDetailError(extractErrorMessage(error, 'Failed to save note'));
      }
    },
    [fetchAndSetDetail, setDetailError],
  );

  const handleCreateCase = React.useCallback(() => {
    // TODO: integrate with moderation case creation flow
  }, []);

  const mobileEmptyContent = !listState.loading && showEmptyState ? (
    <UsersEmptyState variant="mobile" onResetFilters={resetFilters} />
  ) : null;

  return (
    <div className="space-y-8" data-testid="moderation-users-page" data-analytics="moderation:users:page">
      <UsersHeader metrics={metrics} lastRefreshLabel={lastRefreshLabel} onRefresh={refresh} onCreateCase={handleCreateCase} />

      <UsersFilters
        filters={filters}
        search={search}
        advancedOpen={advancedOpen}
        advancedActiveCount={advancedActiveCount}
        onFilterChange={handleFilterChange}
        onSearchChange={setSearch}
        onToggleAdvanced={() => setAdvancedOpen((prev) => !prev)}
        onReset={resetFilters}
      />

      {listState.error ? <UsersError message={listState.error} onRetry={refresh} /> : null}

      <Surface variant="frosted" className="space-y-5" data-testid="moderation-users-table-surface">
        <div className="flex flex-col gap-2 px-5 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">User directory</h2>
            <p className="text-sm text-gray-500 dark:text-dark-200/80">
              Filter, sort, and drill into moderation insights for every member.
            </p>
          </div>
          <div className="text-xs text-gray-400 dark:text-dark-300">
            {sortedItems.length.toLocaleString('ru-RU')} results on this page | Page {page}
          </div>
        </div>

        <UsersTable items={sortedItems} loading={listState.loading} sort={sort} onSort={handleSort} onOpenUser={handleOpenDrawer} />

        <UsersCardsMobile items={sortedItems} loading={listState.loading} onOpenUser={handleOpenDrawer} emptyContent={mobileEmptyContent} />

        {!listState.loading && showEmptyState ? (
          <div className="hidden px-5 pb-6 md:block">
            <UsersEmptyState variant="desktop" onResetFilters={resetFilters} onRefresh={refresh} />
          </div>
        ) : null}

        <div className="px-5 pb-5">
          <TablePagination
            page={page}
            pageSize={pageSize}
            currentCount={sortedItems.length}
            totalItems={listState.totalItems}
            hasNext={Boolean(listState.nextCursor)}
            onPageChange={handlePageChange}
            onPageSizeChange={setPageSize}
            pageSizeOptions={PAGE_SIZE_OPTIONS}
            summaryPrefix="Showing"
            data-testid="moderation-users-pagination"
          />
        </div>
      </Surface>

      <UserDrawer
        open={drawerOpen}
        tab={drawerTab}
        onTabChange={setDrawerTab}
        onClose={handleCloseDrawer}
        userSummary={activeUserSummary}
        userDetail={activeUserDetail}
        detailStatus={detailStatus}
        onRefreshDetail={fetchAndSetDetail}
        onSaveRoles={handleSaveRoles}
        onIssueSanction={handleIssueSanction}
        onCreateNote={handleCreateNote}
        resetDetailStatus={resetDetailStatus}
      />
    </div>
  );
}


