import * as React from 'react';

import { Badge, Button, Skeleton, Surface } from '@ui';

import {
  formatDateTime,
  resolveRiskLevel,
  riskBadgeProps,
  statusToBadgeTone,
} from '../normalizers';
import type { ModerationUserSummary } from '../types';

const SKELETON_ROWS = Array.from({ length: 4 });

type UsersCardsMobileProps = {
  items: ModerationUserSummary[];
  loading: boolean;
  onOpenUser: (user: ModerationUserSummary) => void;
  emptyContent?: React.ReactNode;
};

export function UsersCardsMobile({ items, loading, onOpenUser, emptyContent }: UsersCardsMobileProps): JSX.Element {
  return (
    <div className="grid gap-3 px-5 pb-5 md:hidden" data-testid="moderation-users-cards" data-analytics="moderation:users:cards">
      {loading
        ? SKELETON_ROWS.map((_, index) => (
            <Surface key={`card-skeleton-${index}`} variant="soft" className="space-y-3 p-4">
              <Skeleton className="h-4 w-40 rounded-full" />
              <Skeleton className="h-3 w-24 rounded-full" />
              <Skeleton className="h-3 w-full rounded-full" />
            </Surface>
          ))
        : items.map((user) => {
            const risk = resolveRiskLevel(user);
            const riskProps = riskBadgeProps(risk);
            return (
              <Surface
                key={`card-${user.id}`}
                variant="soft"
                className="space-y-4 p-4"
                onClick={() => onOpenUser(user)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">{user.username}</div>
                    <div className="text-xs text-gray-500 dark:text-dark-300">{user.email ?? 'N/A'}</div>
                    <div className="mt-1 text-[11px] text-gray-400">ID: {user.id}</div>
                  </div>
                  <Badge color={statusToBadgeTone(user.status)} variant="soft" className="capitalize">
                    {user.status}
                  </Badge>
                </div>
                <div className="flex flex-wrap gap-2">
                  {user.roles.length
                    ? user.roles.map((role) => (
                        <Badge key={role} color="info" variant="soft" className="capitalize">
                          {role}
                        </Badge>
                      ))
                    : <span className="text-xs text-gray-400">N/A</span>}
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs text-gray-500 dark:text-dark-200">
                  <div>
                    <div className="font-semibold text-gray-600 dark:text-dark-50">Complaints</div>
                    <div>{user.complaints_count}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-600 dark:text-dark-50">Sanctions</div>
                    <div>{user.sanction_count}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-600 dark:text-dark-50">Registered</div>
                    <div>{formatDateTime(user.registered_at)}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-600 dark:text-dark-50">Last seen</div>
                    <div>{formatDateTime(user.last_seen_at)}</div>
                  </div>
                </div>
                <div className="flex items-center justify-between pt-1">
                  <Badge color={riskProps.color} variant="soft">
                    {riskProps.label} risk
                  </Badge>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpenUser(user);
                    }}
                  >
                    Manage
                  </Button>
                </div>
              </Surface>
            );
          })}

      {!loading && !items.length && emptyContent ? emptyContent : null}
    </div>
  );
}
