import React from 'react';
import { Badge, Button, Card, Dialog, Input, Skeleton, Table, useToast } from '@ui';

import { useConfirmDialog } from '@shared/hooks/useConfirmDialog';
import { extractErrorMessage } from '@shared/utils/errors';
import {
  createAdminCommentBan,
  deleteAdminCommentBan,
  fetchAdminCommentBans,
} from '../api';
import type { AdminNodeCommentBan, AdminNodeEngagementCommentSummary } from '../types';

type BansPanelProps = {
  nodeId: string;
  commentSummary: AdminNodeEngagementCommentSummary | null | undefined;
  onChange?: () => void;
};

type BanFormState = {
  target_user_id: string;
  reason: string;
};

const initialForm: BanFormState = {
  target_user_id: '',
  reason: '',
};

function normalizeUuid(value: string): string {
  const trimmed = value.trim();
  return trimmed.toLowerCase();
}

function isUuid(value: string): boolean {
  const normalized = normalizeUuid(value);
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(normalized);
}

function BansLoadingSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" rounded />
      <Skeleton className="h-10 w-full" rounded />
      <Skeleton className="h-10 w-3/4" rounded />
    </div>
  );
}

export function BansPanel({ nodeId, commentSummary, onChange }: BansPanelProps) {
  const { pushToast } = useToast();
  const { confirm, confirmationElement } = useConfirmDialog();
  const [items, setItems] = React.useState<AdminNodeCommentBan[]>([]);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = React.useState<boolean>(false);
  const [form, setForm] = React.useState<BanFormState>(initialForm);
  const [submitting, setSubmitting] = React.useState<boolean>(false);
  const userIdInputRef = React.useRef<HTMLInputElement | null>(null);

  React.useEffect(() => {
    if (dialogOpen && userIdInputRef.current) {
      userIdInputRef.current.focus();
    }
  }, [dialogOpen]);

  const loadBans = React.useCallback(async () => {
    if (!nodeId) return;
    setLoading(true);
    try {
      const data = await fetchAdminCommentBans(nodeId);
      setItems(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [nodeId]);

  React.useEffect(() => {
    loadBans();
  }, [loadBans]);

  const handleOpenDialog = React.useCallback(() => {
    setForm(initialForm);
    setDialogOpen(true);
  }, []);

  const handleCloseDialog = React.useCallback(() => {
    if (submitting) return;
    setDialogOpen(false);
  }, [submitting]);

  const handleChangeField = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }, []);

  const canSubmit = React.useMemo(() => isUuid(form.target_user_id), [form.target_user_id]);

  const handleSubmit = React.useCallback(async () => {
    if (!canSubmit || submitting) return;
    setSubmitting(true);
    try {
      await createAdminCommentBan(nodeId, {
        target_user_id: normalizeUuid(form.target_user_id),
        reason: form.reason.trim() || undefined,
      });
      pushToast({ intent: 'success', description: 'User has been banned from commenting.' });
      setDialogOpen(false);
      setForm(initialForm);
      await loadBans();
      onChange?.();
    } catch (err) {
      pushToast({ intent: 'error', description: extractErrorMessage(err) });
    } finally {
      setSubmitting(false);
    }
  }, [canSubmit, form.reason, form.target_user_id, loadBans, nodeId, onChange, pushToast, submitting]);

  const handleRemove = React.useCallback(
    async (ban: AdminNodeCommentBan) => {
      const approved = await confirm({
        title: 'Remove ban?',
        description: `Allow ${ban.target_user_id} to post comments again?`,
        confirmLabel: 'Remove ban',
        cancelLabel: 'Cancel',
      });
      if (!approved) return;
      try {
        await deleteAdminCommentBan(nodeId, ban.target_user_id);
        pushToast({ intent: 'success', description: `Ban removed for ${ban.target_user_id}.` });
        await loadBans();
        onChange?.();
      } catch (err) {
        pushToast({ intent: 'error', description: extractErrorMessage(err) });
      }
    },
    [confirm, loadBans, nodeId, onChange, pushToast],
  );

  const bansCount = commentSummary?.bans_count ?? items.length;

  return (
    <>
      <Card
        id="bans"
        className="space-y-6 p-6 rounded-3xl border border-rose-100/70 bg-gradient-to-br from-rose-50/70 via-white to-white dark:border-dark-600 dark:from-dark-700/40 dark:via-dark-800 dark:to-dark-900"
        data-testid="comment-bans-panel"
        data-analytics="admin.comments.bans"
      >
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">Comment bans</h3>
            <p className="text-sm text-neutral-600 dark:text-neutral-300">
              Track restricted users and adjust ban status.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Badge color={bansCount ? 'warning' : 'neutral'} variant="soft" data-testid="comment-bans-count">
              Active bans: {bansCount}
            </Badge>
            <Button
              size="sm"
              variant="ghost"
              color="neutral"
              onClick={loadBans}
              disabled={loading}
              data-testid="comment-bans-refresh"
              data-analytics="admin.comments.bans.refresh"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </Button>
            <Button
              size="sm"
              onClick={handleOpenDialog}
              data-testid="comment-bans-add"
              data-analytics="admin.comments.bans.add"
            >
              Add ban
            </Button>
          </div>
        </div>

        {error ? (
          <Card className="border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/60 dark:bg-rose-900/30 dark:text-rose-200">
            {error}
          </Card>
        ) : loading && !items.length ? (
          <BansLoadingSkeleton />
        ) : items.length === 0 ? (
          <Card className="border border-dashed border-neutral-300 bg-neutral-50 p-6 text-center text-sm text-neutral-500 dark:border-dark-500 dark:bg-dark-700/40 dark:text-dark-100" data-testid="comment-bans-empty">
            No active bans configured for this node.
          </Card>
        ) : (
          <div className="overflow-x-auto">
            <Table.Table className="min-w-full text-sm">
              <Table.THead>
                <Table.TR>
                  <Table.TH>User ID</Table.TH>
                  <Table.TH>Reason</Table.TH>
                  <Table.TH>Set by</Table.TH>
                  <Table.TH>Created at</Table.TH>
                  <Table.TH className="text-right">Actions</Table.TH>
                </Table.TR>
              </Table.THead>
              <Table.TBody>
                {items.map((ban) => (
                  <Table.TR key={ban.target_user_id}>
                    <Table.TD className="font-mono text-xs text-neutral-700 dark:text-neutral-100">{ban.target_user_id}</Table.TD>
                    <Table.TD>{ban.reason || '—'}</Table.TD>
                    <Table.TD className="text-xs text-neutral-500">{ban.set_by}</Table.TD>
                    <Table.TD className="text-xs text-neutral-500">{ban.created_at || '—'}</Table.TD>
                    <Table.TD className="text-right">
                      <Button
                        size="xs"
                        variant="ghost"
                        color="error"
                        onClick={() => handleRemove(ban)}
                        data-testid={`comment-bans-remove-${ban.target_user_id}`}
                        data-analytics="admin.comments.bans.remove"
                      >
                        Remove
                      </Button>
                    </Table.TD>
                  </Table.TR>
                ))}
              </Table.TBody>
            </Table.Table>
          </div>
        )}

        <div className="rounded-md bg-neutral-50 p-4 text-xs text-neutral-600 dark:bg-dark-700/40 dark:text-dark-100">
          Bans remove posting ability immediately. Review moderation policy in{' '}
          <a
            href="/docs/api/node-engagement-admin.md"
            target="_blank"
            rel="noreferrer"
            className="text-primary-600 hover:underline dark:text-primary-300"
          >
            the moderation handbook
          </a>
          .
        </div>
      </Card>

      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        title="Add comment ban"
        footer={
          <>
            <Button
              variant="ghost"
              color="neutral"
              onClick={handleCloseDialog}
              disabled={submitting}
              data-testid="comment-bans-cancel"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!canSubmit || submitting}
              data-testid="comment-bans-submit"
            >
              {submitting ? 'Saving...' : 'Save ban'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label htmlFor="ban-user-id" className="text-sm font-medium text-neutral-800 dark:text-neutral-200">
              User ID
            </label>
            <Input
              id="ban-user-id"
              name="target_user_id"
              value={form.target_user_id}
              onChange={handleChangeField}
              placeholder="uuid"
              ref={userIdInputRef}
              data-testid="comment-bans-user-input"
            />
            {!canSubmit && form.target_user_id.trim() && (
              <p className="mt-1 text-xs text-rose-600">Enter a valid UUID.</p>
            )}
          </div>
          <div>
            <label htmlFor="ban-reason" className="text-sm font-medium text-neutral-800 dark:text-neutral-200">
              Reason (optional)
            </label>
            <Input
              id="ban-reason"
              name="reason"
              value={form.reason}
              onChange={handleChangeField}
              placeholder="spam, abuse..."
              data-testid="comment-bans-reason-input"
            />
          </div>
        </div>
      </Dialog>

      {confirmationElement}
    </>
  );
}

export default BansPanel;
