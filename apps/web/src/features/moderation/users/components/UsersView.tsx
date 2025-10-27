import * as React from 'react';
import { Surface, TablePagination, useToast } from '@ui';
import { useNavigate } from 'react-router-dom';

import { UsersHeader } from './UsersHeader';
import { UsersFilters } from './UsersFilters';
import { UsersTable } from './UsersTable';
import { UsersCardsMobile } from './UsersCardsMobile';
import { UsersEmptyState } from './UsersEmptyState';
import { UsersError } from './UsersError';
import { UserDrawer } from './UserDrawer';
import { DEFAULT_FILTERS, DEFAULT_SORT, PAGE_SIZE_OPTIONS } from '../constants';
import {
  formatRelativeTime,
  resolveRiskLevel,
} from '../normalizers';
import type {
  DrawerTabKey,
  FilterState,
  ModerationRole,
  ModerationUserDetail,
  ModerationUserSummary,
  SortKey,
  SortState,
} from '../types';
import { useModerationUsersDirectory } from '../hooks/useModerationUsersDirectory';
import {
  createModerationUserNote,
  createModerationUserSanction,
  updateModerationUserRoles,
} from '@shared/api/moderation/users';
import { extractErrorMessage } from '@shared/utils/errors';

const DEFAULT_METRICS = {
  total: 0,
  active: 0,
  sanctioned: 0,
  highRisk: 0,
  complaints: 0,
};

function computeMetrics(users: ModerationUserSummary[]) {
  if (!users.length) {
    return DEFAULT_METRICS;
  }
  let active = 0;
  let sanctioned = 0;
  let highRisk = 0;
  let complaints = 0;
  users.forEach((user) => {
    if ((user.status ?? '').toLowerCase() === 'active') {
      active += 1;
    }
    if (user.sanction_count > 0) {
      sanctioned += 1;
    }
    if (resolveRiskLevel(user) === 'high') {
      highRisk += 1;
    }
    complaints += user.complaints_count ?? 0;
  });
  return {
    total: users.length,
    active,
    sanctioned,
    highRisk,
    complaints,
  };
}

function sortUsers(items: ModerationUserSummary[], sort: SortState): ModerationUserSummary[] {
  const sorted = [...items];
  sorted.sort((a, b) => {
    const orderFactor = sort.order === 'asc' ? 1 : -1;
    switch (sort.key) {
      case 'registered_at': {
        const aTime = a.registered_at ? new Date(a.registered_at).getTime() : 0;
        const bTime = b.registered_at ? new Date(b.registered_at).getTime() : 0;
        return (aTime - bTime) * orderFactor;
      }
      case 'last_seen_at': {
        const aTime = a.last_seen_at ? new Date(a.last_seen_at).getTime() : 0;
        const bTime = b.last_seen_at ? new Date(b.last_seen_at).getTime() : 0;
        return (aTime - bTime) * orderFactor;
      }
      case 'complaints_count':
        return (a.complaints_count - b.complaints_count) * orderFactor;
      case 'sanction_count':
        return (a.sanction_count - b.sanction_count) * orderFactor;
      default:
        return 0;
    }
  });
  return sorted;
}

export default function ModerationUsersView(): React.ReactElement {
  const { pushToast } = useToast();
  const navigate = useNavigate();

  const [filters, setFilters] = React.useState<FilterState>(DEFAULT_FILTERS);
  const [search, setSearch] = React.useState('');
  const [advancedOpen, setAdvancedOpen] = React.useState(false);
  const [sort, setSort] = React.useState<SortState>(DEFAULT_SORT);

  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [drawerTab, setDrawerTab] = React.useState<DrawerTabKey>('overview');
  const [activeUserSummary, setActiveUserSummary] = React.useState<ModerationUserSummary | null>(null);
  const [activeUserDetail, setActiveUserDetail] = React.useState<ModerationUserDetail | null>(null);

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
  } = useModerationUsersDirectory({ filters, search });

  const [lastLoadedAt, setLastLoadedAt] = React.useState<string>(() => new Date().toISOString());

  React.useEffect(() => {
    if (!listState.loading && !listState.error) {
      setLastLoadedAt(new Date().toISOString());
    }
  }, [listState.error, listState.items, listState.loading]);

  const filteredByRisk = React.useMemo(() => {
    if (filters.risk === 'any') {
      return listState.items;
    }
    return listState.items.filter((user) => resolveRiskLevel(user) === filters.risk);
  }, [filters.risk, listState.items]);

  const sortedItems = React.useMemo(() => sortUsers(filteredByRisk, sort), [filteredByRisk, sort]);

  const metrics = React.useMemo(() => computeMetrics(sortedItems), [sortedItems]);

  const advancedActiveCount = React.useMemo(() => {
    let count = 0;
    if (filters.risk !== 'any') count += 1;
    if (filters.registrationFrom) count += 1;
    if (filters.registrationTo) count += 1;
    return count;
  }, [filters]);

  const lastRefreshLabel = lastLoadedAt ? `Updated ${formatRelativeTime(lastLoadedAt)}` : 'Waiting for data';

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

  const setPage = React.useCallback((nextPage: number) => {
    handlePageChange(nextPage);
  }, [handlePageChange]);

  const fetchAndSetDetail = React.useCallback(
    async (userId: string, opts: { silent?: boolean } = {}) => {
      const detail = await loadUserDetail(userId, opts);
      if (detail) {
        setActiveUserDetail(detail);
      }
      return detail;
    },
    [loadUserDetail],
  );

  const handleOpenDrawer = React.useCallback(
    async (user: ModerationUserSummary) => {
      setActiveUserSummary(user);
      setDrawerTab('overview');
      setDrawerOpen(true);
      const cached = getCachedDetail(user.id);
      if (cached) {
        setActiveUserDetail(cached);
        await fetchAndSetDetail(user.id, { silent: true });
      } else {
        setActiveUserDetail(null);
        await fetchAndSetDetail(user.id, { silent: false });
      }
    },
    [fetchAndSetDetail, getCachedDetail],
  );

  const handleCloseDrawer = React.useCallback(() => {
    setDrawerOpen(false);
    setActiveUserSummary(null);
    setActiveUserDetail(null);
    resetDetailStatus();
  }, [resetDetailStatus]);

  const handleSaveRoles = React.useCallback(
    async (userId: string, nextRole: ModerationRole) => {
      try {
        setDetailError(null);
        const currentRoles = activeUserDetail?.roles ?? activeUserSummary?.roles ?? [];
        const add: string[] = currentRoles.includes(nextRole) ? [] : [nextRole];
        const remove = currentRoles.filter((role) => role !== nextRole);
        await updateModerationUserRoles(userId, { add, remove });
        pushToast({ intent: 'success', description: 'Roles updated.' });
        await refresh();
        await fetchAndSetDetail(userId, { silent: true });
      } catch (error) {
        setDetailError(extractErrorMessage(error, 'Failed to update roles'));
      }
    },
    [activeUserDetail?.roles, activeUserSummary?.roles, fetchAndSetDetail, pushToast, refresh, setDetailError],
  );

  const handleIssueSanction = React.useCallback(
    async (
      userId: string,
      payload: { type: string; reason?: string; durationHours?: number },
    ) => {
      try {
        setDetailError(null);
        await createModerationUserSanction(userId, {
          type: payload.type,
          reason: payload.reason?.trim() || undefined,
          duration_hours:
            typeof payload.durationHours === 'number' && !Number.isNaN(payload.durationHours)
              ? payload.durationHours
              : undefined,
        });
        pushToast({ intent: 'success', description: 'Sanction issued.' });
        await refresh();
        await fetchAndSetDetail(userId, { silent: true });
      } catch (error) {
        setDetailError(extractErrorMessage(error, 'Failed to issue sanction'));
      }
    },
    [fetchAndSetDetail, pushToast, refresh, setDetailError],
  );

  const handleCreateNote = React.useCallback(
    async (userId: string, payload: { text: string; pinned: boolean }) => {
      try {
        const text = payload.text.trim();
        if (!text) {
          setDetailError('Note text is required.');
          return;
        }
        setDetailError(null);
        await createModerationUserNote(userId, {
          text,
          pinned: payload.pinned,
        });
        pushToast({ intent: 'success', description: 'Note added.' });
        await fetchAndSetDetail(userId, { silent: true });
      } catch (error) {
        setDetailError(extractErrorMessage(error, 'Failed to create note'));
      }
    },
    [fetchAndSetDetail, pushToast, setDetailError],
  );

  const handleCreateCase = React.useCallback(() => {
    navigate('/moderation/cases');
  }, [navigate]);

  const showEmptyState = !listState.loading && sortedItems.length === 0;
  const mobileEmptyContent = showEmptyState ? (
    <UsersEmptyState variant="mobile" onResetFilters={resetFilters} />
  ) : null;

  return (
    <div className="space-y-8" data-testid="moderation-users-page">
      <UsersHeader
        metrics={metrics}
        lastRefreshLabel={lastRefreshLabel}
        loading={listState.loading}
        hasError={Boolean(listState.error)}
        onRefresh={refresh}
        onCreateCase={handleCreateCase}
      />

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

      <Surface variant="frosted" className="space-y-6" data-testid="moderation-users-surface">
        <UsersTable
          items={sortedItems}
          loading={listState.loading}
          sort={sort}
          onSort={handleSort}
          onOpenUser={handleOpenDrawer}
        />

        <UsersCardsMobile
          items={sortedItems}
          loading={listState.loading}
          onOpenUser={handleOpenDrawer}
          emptyContent={mobileEmptyContent}
        />

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
            onPageChange={setPage}
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
