import * as React from 'react';

import { Badge, Button, Skeleton, Table } from '@ui';
import { ChevronRightIcon, PencilSquareIcon } from '@heroicons/react/24/outline';

import {
  formatDateTime,
  formatRelativeTime,
  resolveRiskLevel,
  riskBadgeProps,
  statusToBadgeTone,
} from '../normalizers';
import type { ModerationUserSummary, SortKey, SortOrder, SortState } from '../types';

const SKELETON_ROWS = Array.from({ length: 6 });

type UsersTableProps = {
  items: ModerationUserSummary[];
  loading: boolean;
  sort: SortState;
  onSort: (key: SortKey) => void;
  onOpenUser: (user: ModerationUserSummary) => void;
};

export function UsersTable({ items, loading, sort, onSort, onOpenUser }: UsersTableProps): JSX.Element {
  return (
    <div className="hidden md:block">
      <div className="custom-scrollbar overflow-x-auto" data-testid="moderation-users-table-wrapper">
        <Table.Table
          className="min-w-[1100px] text-left"
          zebra
          hover
          data-testid="moderation-users-table"
          data-analytics="moderation:users:table"
        >
          <Table.THead className="sticky top-0 z-10 bg-white/95 backdrop-blur dark:bg-dark-800/90">
            <Table.TR>
              <Table.TH className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500">User</Table.TH>
              <Table.TH className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Roles</Table.TH>
              <Table.TH className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Status</Table.TH>
              <Table.TH className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500">Risk</Table.TH>
              <Table.TH className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                <SortButton label="Complaints" active={sort.key === 'complaints_count'} order={sort.order} onClick={() => onSort('complaints_count')} />
              </Table.TH>
              <Table.TH className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                <SortButton label="Sanctions" active={sort.key === 'sanction_count'} order={sort.order} onClick={() => onSort('sanction_count')} />
              </Table.TH>
              <Table.TH className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                <SortButton label="Registered" active={sort.key === 'registered_at'} order={sort.order} onClick={() => onSort('registered_at')} />
              </Table.TH>
              <Table.TH className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                <SortButton label="Last seen" active={sort.key === 'last_seen_at'} order={sort.order} onClick={() => onSort('last_seen_at')} />
              </Table.TH>
              <Table.TH className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500 text-right">Actions</Table.TH>
              <Table.TH className="w-10 px-3 py-3" aria-hidden="true" />
            </Table.TR>
          </Table.THead>
          <Table.TBody>
            {loading
              ? SKELETON_ROWS.map((_, index) => (
                  <Table.TR key={`skeleton-${index}`} className="animate-pulse">
                    <Table.TD className="px-5 py-4" colSpan={10}>
                      <div className="flex items-center gap-4">
                        <Skeleton className="h-4 w-40 rounded-full" />
                        <Skeleton className="h-3 w-24 rounded-full" />
                        <Skeleton className="h-3 w-32 rounded-full" />
                      </div>
                    </Table.TD>
                  </Table.TR>
                ))
              : items.map((user) => {
                  const risk = resolveRiskLevel(user);
                  const riskProps = riskBadgeProps(risk);
                  return (
                    <Table.TR
                      key={user.id}
                      className="group cursor-pointer transition hover:bg-primary-50/40 dark:hover:bg-dark-700/40"
                      onClick={() => onOpenUser(user)}
                      data-testid={`moderation-users-row-${user.id}`}
                      data-analytics="moderation:users:row"
                    >
                      <Table.TD className="px-5 py-4">
                        <div className="space-y-1">
                          <div className="font-medium text-gray-900 dark:text-white">{user.username}</div>
                          <div className="text-xs text-gray-500 dark:text-dark-300">{user.email ?? 'N/A'}</div>
                          <div className="text-[11px] text-gray-400 dark:text-dark-400">ID: {user.id}</div>
                        </div>
                      </Table.TD>
                      <Table.TD className="px-5 py-4">
                        <div className="flex flex-wrap gap-2">
                          {user.roles.length
                            ? user.roles.map((role) => (
                                <Badge key={role} color="info" variant="soft" className="capitalize">
                                  {role}
                                </Badge>
                              ))
                            : <span className="text-xs text-gray-400">N/A</span>}
                        </div>
                      </Table.TD>
                      <Table.TD className="px-5 py-4">
                        <Badge color={statusToBadgeTone(user.status)} variant="soft" className="capitalize">
                          {user.status}
                        </Badge>
                      </Table.TD>
                      <Table.TD className="px-5 py-4">
                        <Badge color={riskProps.color} variant="soft">
                          {riskProps.label}
                        </Badge>
                      </Table.TD>
                      <Table.TD className="px-5 py-4">
                        <span className="text-sm text-gray-700 dark:text-dark-100">{user.complaints_count}</span>
                      </Table.TD>
                      <Table.TD className="px-5 py-4">
                        <span className="text-sm text-gray-700 dark:text-dark-100">{user.sanction_count}</span>
                      </Table.TD>
                      <Table.TD className="px-5 py-4">
                        <div className="text-sm text-gray-600 dark:text-dark-200">{formatDateTime(user.registered_at)}</div>
                      </Table.TD>
                      <Table.TD className="px-5 py-4">
                        <div className="text-sm text-gray-600 dark:text-dark-200" title={formatRelativeTime(user.last_seen_at)}>
                          {formatDateTime(user.last_seen_at)}
                        </div>
                      </Table.TD>
                      <Table.TD className="px-5 py-4 text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(event) => {
                            event.stopPropagation();
                            onOpenUser(user);
                          }}
                          data-testid={`moderation-users-row-${user.id}-actions`}
                        >
                          <PencilSquareIcon className="mr-1 size-4" aria-hidden="true" />
                          Open
                        </Button>
                      </Table.TD>
                      <Table.TD className="px-3 py-4 text-right">
                        <ChevronRightIcon className="size-4 text-gray-300 transition group-hover:text-primary-500" aria-hidden="true" />
                      </Table.TD>
                    </Table.TR>
                  );
                })}
          </Table.TBody>
        </Table.Table>
      </div>
    </div>
  );
}

type SortButtonProps = {
  label: string;
  active: boolean;
  order: SortOrder;
  onClick: () => void;
};

function SortButton({ label, active, order, onClick }: SortButtonProps): JSX.Element {
  return (
    <button
      type="button"
      className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-gray-500 transition hover:text-primary-600"
      onClick={onClick}
    >
      {label}
      <SortMarker active={active} order={order} />
    </button>
  );
}

type SortMarkerProps = {
  active: boolean;
  order: SortOrder;
};

function SortMarker({ active, order }: SortMarkerProps): JSX.Element {
  return <span className={`ml-1 text-[10px] transition ${active ? 'opacity-90' : 'opacity-30'}`}>{order === 'asc' ? '^' : 'v'}</span>;
}
