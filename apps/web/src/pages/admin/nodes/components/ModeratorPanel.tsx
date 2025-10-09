import React from 'react';

import { Badge, Button, Card, Switch, useToast } from '@ui';

import { useConfirmDialog } from '@shared/hooks/useConfirmDialog';
import { extractErrorMessage } from '@shared/utils/errors';
import { disableAdminComments, lockAdminComments } from '../api';
import type { AdminNodeEngagementCommentSummary, AdminNodeEngagementSummary } from '../types';

type ModeratorPanelProps = {
  nodeId: string;
  summary: AdminNodeEngagementSummary | null;
  refreshing?: boolean;
  onRefresh?: () => Promise<void> | void;
};

export function ModeratorPanel({ nodeId, summary, refreshing, onRefresh }: ModeratorPanelProps) {
  const { pushToast } = useToast();
  const { confirm, confirmationElement } = useConfirmDialog();

  const [lockBusy, setLockBusy] = React.useState(false);
  const [disableBusy, setDisableBusy] = React.useState(false);

  const commentMeta: AdminNodeEngagementCommentSummary | null = summary?.comments ?? null;
  const locked = Boolean(commentMeta?.locked);
  const disabled = Boolean(commentMeta?.disabled);
  const bansCount = Number.isFinite(commentMeta?.bans_count) ? Number(commentMeta?.bans_count) : 0;

  const handleRefresh = React.useCallback(async () => {
    if (!onRefresh) return;
    await onRefresh();
  }, [onRefresh]);

  const handleToggleLock = React.useCallback(
    async (next: boolean) => {
      const proceed = await confirm({
        title: next ? 'Lock comments?' : 'Unlock comments?',
        description: next
          ? 'New comments will be blocked until you unlock the thread.'
          : 'Visitors will be able to post new messages again.',
        confirmLabel: next ? 'Lock' : 'Unlock',
        cancelLabel: 'Cancel',
      });
      if (!proceed) return;

      setLockBusy(true);
      try {
        await lockAdminComments(nodeId, { locked: next, reason: next ? 'Locked via admin UI' : undefined });
        pushToast({ intent: 'success', description: next ? 'Comments locked for this node.' : 'Comments unlocked.' });
        await handleRefresh();
      } catch (err) {
        pushToast({ intent: 'error', description: extractErrorMessage(err) });
      } finally {
        setLockBusy(false);
      }
    },
    [confirm, handleRefresh, nodeId, pushToast],
  );

  const handleToggleDisable = React.useCallback(
    async (next: boolean) => {
      const proceed = await confirm({
        title: next ? 'Disable comments?' : 'Enable comments?',
        description: next
          ? 'Existing comments stay visible, but the reply form disappears for visitors.'
          : 'The reply form becomes visible and users can post again.',
        confirmLabel: next ? 'Disable' : 'Enable',
        cancelLabel: 'Cancel',
      });
      if (!proceed) return;

      setDisableBusy(true);
      try {
        await disableAdminComments(nodeId, { disabled: next, reason: next ? 'Disabled via admin UI' : undefined });
        pushToast({ intent: 'success', description: next ? 'Comments disabled.' : 'Comments enabled.' });
        await handleRefresh();
      } catch (err) {
        pushToast({ intent: 'error', description: extractErrorMessage(err) });
      } finally {
        setDisableBusy(false);
      }
    },
    [confirm, handleRefresh, nodeId, pushToast],
  );

  return (
    <>
      <Card className="space-y-6 p-6 rounded-3xl border border-emerald-100/70 bg-gradient-to-br from-emerald-50/70 via-white to-white dark:border-dark-600 dark:from-dark-700/40 dark:via-dark-800 dark:to-dark-900">
        <div className="flex flex-col gap-4">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">Moderator panel</h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-300">
                Control comment availability and inspect moderation context.
              </p>
            </div>
            <Button
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              data-testid="moderator-refresh"
              data-analytics="admin.comments.refresh.summary"
            >
              {refreshing ? 'Refreshing...' : 'Refresh node state'}
            </Button>
          </div>
          <div className="flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-300">
            <Badge color={bansCount ? 'warning' : 'neutral'} variant="soft">
              Active bans: {bansCount}
            </Badge>
            {commentMeta?.disabled ? (
              <span className="rounded-full bg-rose-100 px-2 py-0.5 text-rose-700 dark:bg-rose-500/20 dark:text-rose-200">
                Comments disabled
              </span>
            ) : null}
            {commentMeta?.locked ? (
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-700 dark:bg-amber-500/20 dark:text-amber-200">
                Locked for review
              </span>
            ) : null}
          </div>
        </div>

        <div className="space-y-5">
          <div className="rounded-lg border border-neutral-200 p-4 dark:border-dark-600">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="font-medium text-neutral-900 dark:text-neutral-100">Lock comments</div>
                <div className="text-xs text-neutral-500 dark:text-neutral-400">
                  Prevents new comments while moderators investigate.
                </div>
              </div>
              <Switch
                checked={locked}
                disabled={lockBusy}
                data-testid="moderator-lock-toggle"
                data-analytics="admin.comments.lock"
                onChange={(event) => handleToggleLock(event.currentTarget.checked)}
              />
            </div>
          </div>

          <div className="rounded-lg border border-neutral-200 p-4 dark:border-dark-600">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="font-medium text-neutral-900 dark:text-neutral-100">Disable comments</div>
                <div className="text-xs text-neutral-500 dark:text-neutral-400">
                  Hides the reply form entirely for this node.
                </div>
              </div>
              <Switch
                checked={disabled}
                disabled={disableBusy}
                data-testid="moderator-disable-toggle"
                data-analytics="admin.comments.disable"
                onChange={(event) => handleToggleDisable(event.currentTarget.checked)}
              />
            </div>
          </div>

          <div className="space-y-3 rounded-lg border border-neutral-200 p-4 text-sm text-neutral-600 dark:border-dark-600 dark:text-neutral-200">
            <div className="font-medium text-neutral-800 dark:text-neutral-100">Current state</div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-neutral-500 dark:text-neutral-400">Locked by</span>
              <span>{commentMeta?.locked_by ?? 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-neutral-500 dark:text-neutral-400">Locked at</span>
              <span>{commentMeta?.locked_at ?? 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-neutral-500 dark:text-neutral-400">Last comment</span>
              <span>{commentMeta?.last_comment_created_at ?? 'N/A'}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-neutral-500 dark:text-neutral-400">Bans in effect</span>
              <Badge color={bansCount ? 'warning' : 'neutral'} variant="soft">
                {bansCount}
              </Badge>
            </div>
          </div>

          <div className="rounded-md bg-neutral-50 p-4 text-xs text-neutral-600 dark:bg-dark-700/40 dark:text-dark-100">
            Review the full moderation handbook in the bans section for policy details.
          </div>
        </div>
      </Card>

      {confirmationElement}
    </>
  );
}
