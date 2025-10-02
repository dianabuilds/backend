import * as React from 'react';

import { Badge, Button, Drawer, Input, Select, Skeleton, Surface, Switch, Tabs, Textarea } from '@ui';
import {
  ArrowPathIcon,
  BoltIcon,
  PencilSquareIcon,
  ShieldExclamationIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';

import { DRAWER_TABS, ROLE_FILTERS, SANCTION_TYPES } from '../constants';
import {
  formatDateTime,
  resolvePreferredRole,
  resolveRiskLevel,
  riskBadgeProps,
  statusToBadgeTone,
  toTitleCase,
} from '../normalizers';
import type {
  DrawerTabKey,
  ModerationRole,
  ModerationUserDetail,
  ModerationUserSummary,
} from '../types';
import type { DetailStatus } from '../hooks/useModerationUsers';

type SanctionFormState = { type: string; reason: string; durationHours: string };
type NoteFormState = { text: string; pinned: boolean };

const createDefaultSanctionForm = (): SanctionFormState => ({ type: SANCTION_TYPES[0], reason: '', durationHours: '' });
const createDefaultNoteForm = (): NoteFormState => ({ text: '', pinned: false });

type UserDrawerProps = {
  open: boolean;
  tab: DrawerTabKey;
  onTabChange: (tab: DrawerTabKey) => void;
  onClose: () => void;
  userSummary: ModerationUserSummary | null;
  userDetail: ModerationUserDetail | null;
  detailStatus: DetailStatus;
  onRefreshDetail: (userId: string, opts?: { silent?: boolean }) => Promise<ModerationUserDetail | null>;
  onSaveRoles: (userId: string, role: ModerationRole) => Promise<void>;
  onIssueSanction: (
    userId: string,
    payload: { type: string; reason?: string; durationHours?: number }
  ) => Promise<void>;
  onCreateNote: (
    userId: string,
    payload: { text: string; pinned: boolean }
  ) => Promise<void>;
  resetDetailStatus: () => void;
};

export function UserDrawer({
  open,
  tab,
  onTabChange,
  onClose,
  userSummary,
  userDetail,
  detailStatus,
  onRefreshDetail,
  onSaveRoles,
  onIssueSanction,
  onCreateNote,
  resetDetailStatus,
}: UserDrawerProps): JSX.Element {
  const user = userDetail ?? userSummary;

  const [selectedRole, setSelectedRole] = React.useState<ModerationRole>('user');
  const [sanctionForm, setSanctionForm] = React.useState<SanctionFormState>(() => createDefaultSanctionForm());
  const [noteForm, setNoteForm] = React.useState<NoteFormState>(() => createDefaultNoteForm());
  const [rolesSubmitting, setRolesSubmitting] = React.useState(false);
  const [sanctionSubmitting, setSanctionSubmitting] = React.useState(false);
  const [noteSubmitting, setNoteSubmitting] = React.useState(false);

  const detailRolesKey = React.useMemo(() => (userDetail ? userDetail.roles.join('|') : null), [userDetail]);

  React.useEffect(() => {
    if (!open) {
      setSelectedRole('user');
      setSanctionForm(createDefaultSanctionForm());
      setNoteForm(createDefaultNoteForm());
      setRolesSubmitting(false);
      setSanctionSubmitting(false);
      setNoteSubmitting(false);
      return;
    }
    if (user) {
      setSelectedRole(resolvePreferredRole(user.roles));
      setSanctionForm(createDefaultSanctionForm());
      setNoteForm(createDefaultNoteForm());
      resetDetailStatus();
    }
  }, [open, user, resetDetailStatus]);

  React.useEffect(() => {
    if (open && userDetail) {
      setSelectedRole(resolvePreferredRole(userDetail.roles));
    }
  }, [open, detailRolesKey, userDetail]);

  const drawerRisk = user ? resolveRiskLevel(user) : 'unknown';

  const handleSaveRoles = React.useCallback(async () => {
    if (!user) return;
    resetDetailStatus();
    setRolesSubmitting(true);
    try {
      await onSaveRoles(user.id, selectedRole);
      onTabChange('overview');
    } finally {
      setRolesSubmitting(false);
    }
  }, [user, selectedRole, onSaveRoles, onTabChange, resetDetailStatus]);

  const handleIssueSanction = React.useCallback(async () => {
    if (!user) return;
    resetDetailStatus();
    setSanctionSubmitting(true);
    try {
      const payload: { type: string; reason?: string; durationHours?: number } = { type: sanctionForm.type };
      const reason = sanctionForm.reason.trim();
      if (reason) payload.reason = reason;
      const duration = Number(sanctionForm.durationHours);
      if (!Number.isNaN(duration) && sanctionForm.durationHours) {
        payload.durationHours = duration;
      }
      await onIssueSanction(user.id, payload);
      setSanctionForm(createDefaultSanctionForm());
      onTabChange('overview');
    } finally {
      setSanctionSubmitting(false);
    }
  }, [user, sanctionForm, onIssueSanction, onTabChange, resetDetailStatus]);

  const handleCreateNote = React.useCallback(async () => {
    if (!user || !noteForm.text.trim()) return;
    resetDetailStatus();
    setNoteSubmitting(true);
    try {
      await onCreateNote(user.id, { text: noteForm.text.trim(), pinned: noteForm.pinned });
      setNoteForm(createDefaultNoteForm());
      onTabChange('notes');
    } finally {
      setNoteSubmitting(false);
    }
  }, [user, noteForm, onCreateNote, onTabChange, resetDetailStatus]);

  const footer = React.useMemo(() => {
    if (!user) return null;
    if (tab === 'overview') {
      return (
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" onClick={() => onTabChange('roles')}>
            Update roles
          </Button>
          <Button size="sm" variant="outlined" onClick={() => onTabChange('sanctions')}>
            Issue sanction
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onTabChange('notes')}>
            Add note
          </Button>
        </div>
      );
    }
    if (tab === 'roles') {
      return (
        <div className="flex items-center gap-3">
          <Button size="sm" onClick={handleSaveRoles} disabled={rolesSubmitting} data-testid="moderation-users-drawer-save-roles">
            {rolesSubmitting ? 'Saving...' : 'Save changes'}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onTabChange('overview')}>
            Cancel
          </Button>
        </div>
      );
    }
    if (tab === 'sanctions') {
      return (
        <div className="flex items-center gap-3">
          <Button size="sm" onClick={handleIssueSanction} disabled={sanctionSubmitting} data-testid="moderation-users-drawer-apply-sanction">
            {sanctionSubmitting ? 'Applying...' : 'Apply sanction'}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onTabChange('overview')}>
            Cancel
          </Button>
        </div>
      );
    }
    if (tab === 'notes') {
      return (
        <div className="flex items-center gap-3">
          <Button
            size="sm"
            onClick={handleCreateNote}
            disabled={noteSubmitting || !noteForm.text.trim()}
            data-testid="moderation-users-drawer-save-note"
          >
            {noteSubmitting ? 'Saving...' : 'Save note'}
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onTabChange('overview')}>
            Cancel
          </Button>
        </div>
      );
    }
    if (tab === 'activity' && user) {
      return (
        <Button size="sm" variant="ghost" onClick={() => void onRefreshDetail(user.id, { silent: true })}>
          <ArrowPathIcon className="size-4" aria-hidden="true" /> Refresh activity
        </Button>
      );
    }
    return null;
  }, [user, tab, onTabChange, handleSaveRoles, rolesSubmitting, handleIssueSanction, sanctionSubmitting, handleCreateNote, noteSubmitting, noteForm.text, onRefreshDetail]);

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={user ? `User - ${user.username}` : 'User detail'}
      footer={footer}
      widthClass="w-full max-w-[760px]"
    >
      <div className="flex h-full flex-col" data-testid="moderation-users-drawer">
        <Tabs items={DRAWER_TABS} value={tab} onChange={(key) => onTabChange(key as DrawerTabKey)} className="px-6 pt-4" />
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {user ? (
            <>
              {tab === 'overview' ? (
                <div className="space-y-5" data-testid="moderation-users-drawer-overview">
                  <Surface variant="soft" className="space-y-4 p-5">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="space-y-1">
                        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">User</div>
                        <div className="text-lg font-semibold text-gray-900 dark:text-white">{user.username}</div>
                        <div className="text-sm text-gray-500 dark:text-dark-200/80">{user.email ?? 'N/A'}</div>
                        <div className="text-xs text-gray-400 dark:text-dark-400">ID: {user.id}</div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge color={statusToBadgeTone(user.status)} variant="soft" className="capitalize">
                          {user.status}
                        </Badge>
                        <Badge color={riskBadgeProps(drawerRisk).color} variant="outline">
                          {riskBadgeProps(drawerRisk).label} risk
                        </Badge>
                        {user.roles.map((role) => (
                          <Badge key={role} color="info" variant="outline" className="capitalize">
                            {role}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="grid gap-4 text-sm text-gray-600 dark:text-dark-200 sm:grid-cols-2">
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Registered</div>
                        <div>{formatDateTime(user.registered_at)}</div>
                      </div>
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Last seen</div>
                        <div>{formatDateTime(user.last_seen_at)}</div>
                      </div>
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Complaints</div>
                        <div>{user.complaints_count}</div>
                      </div>
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Sanctions</div>
                        <div>{user.sanction_count}</div>
                      </div>
                    </div>
                  </Surface>

                  {detailStatus.loading ? (
                    <Surface variant="soft" className="space-y-3 p-5">
                      <Skeleton className="h-4 w-48 rounded-full" />
                      <Skeleton className="h-3 w-full rounded-full" />
                      <Skeleton className="h-3 w-3/4 rounded-full" />
                    </Surface>
                  ) : null}

                  {detailStatus.error ? (
                    <Surface
                      variant="soft"
                      className="space-y-3 border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700"
                      data-testid="moderation-users-drawer-error"
                    >
                      <div className="font-semibold">{detailStatus.error}</div>
                      <Button size="sm" variant="ghost" onClick={() => onRefreshDetail(user.id)}>
                        Retry
                      </Button>
                    </Surface>
                  ) : null}

                  {userDetail ? (
                    <div className="space-y-5">
                      {userDetail.active_sanctions.length ? (
                        <Surface variant="soft" className="space-y-3 p-5">
                          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
                            <ShieldExclamationIcon className="size-4" aria-hidden="true" /> Active sanctions
                          </div>
                          <div className="space-y-3 text-sm text-gray-600 dark:text-dark-200">
                            {userDetail.active_sanctions.map((sanction) => (
                              <div key={sanction.id} className="rounded-2xl border border-white/40 bg-white/60 p-4 dark:border-dark-600/60 dark:bg-dark-800/40">
                                <div className="flex items-center justify-between">
                                  <div className="font-semibold capitalize text-gray-800 dark:text-dark-50">{toTitleCase(sanction.type)}</div>
                                  <Badge color={statusToBadgeTone(sanction.status)} variant="soft" className="capitalize text-xs">
                                    {sanction.status}
                                  </Badge>
                                </div>
                                <div className="mt-2 space-y-1 text-xs text-gray-500 dark:text-dark-300">
                                  <div>{sanction.reason ?? 'N/A'}</div>
                                  <div>
                                    {formatDateTime(sanction.issued_at)}
                                    {sanction.ends_at ? ` -> ${formatDateTime(sanction.ends_at)}` : ''}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </Surface>
                      ) : null}

                      {userDetail.notes.length ? (
                        <Surface variant="soft" className="space-y-3 p-5">
                          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
                            <PencilSquareIcon className="size-4" aria-hidden="true" /> Moderator notes
                          </div>
                          <div className="space-y-3 text-sm text-gray-600 dark:text-dark-200">
                            {userDetail.notes.map((note) => (
                              <div key={note.id} className="rounded-2xl border border-white/40 bg-white/70 p-4 dark:border-dark-600/40 dark:bg-dark-800/40">
                                <div className="flex items-center justify-between">
                                  <div className="font-semibold text-gray-800 dark:text-dark-50">{note.author_name ?? 'Moderator'}</div>
                                  <div className="text-xs text-gray-400">{formatDateTime(note.created_at)}</div>
                                </div>
                                <div className="mt-2 whitespace-pre-wrap text-sm text-gray-600 dark:text-dark-200">{note.text}</div>
                                {note.pinned ? (
                                  <Badge color="warning" variant="soft" className="mt-2 text-[10px] uppercase">
                                    Pinned
                                  </Badge>
                                ) : null}
                              </div>
                            ))}
                          </div>
                        </Surface>
                      ) : null}

                      {userDetail.cases && userDetail.cases.length ? (
                        <Surface variant="soft" className="space-y-3 p-5">
                          <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
                            <BoltIcon className="size-4" aria-hidden="true" /> Related cases
                          </div>
                          <div className="space-y-3 text-xs text-gray-500 dark:text-dark-300">
                            {userDetail.cases.map((caseItem) => (
                              <div key={caseItem.id} className="rounded-2xl border border-white/30 bg-white/60 p-4 dark:border-dark-600/40 dark:bg-dark-800/40">
                                <div className="flex items-center justify-between text-sm">
                                  <span className="font-semibold text-gray-800 dark:text-dark-50">Case {caseItem.id ?? 'N/A'}</span>
                                  <Badge color={statusToBadgeTone(caseItem.status)} variant="soft" className="capitalize text-xs">
                                    {caseItem.status ?? 'open'}
                                  </Badge>
                                </div>
                                <div className="mt-1 text-xs text-gray-500 dark:text-dark-300">
                                  {toTitleCase(caseItem.type ?? 'moderation')} | {caseItem.priority ?? 'normal'} | {formatDateTime(caseItem.opened_at)}
                                </div>
                              </div>
                            ))}
                          </div>
                        </Surface>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ) : null}

              {tab === 'roles' ? (
                <div className="space-y-4" data-testid="moderation-users-drawer-roles">
                  <p className="text-sm text-gray-600 dark:text-dark-200">
                    Choose the highest role that should remain after update. Lower-level roles will be revoked automatically.
                  </p>
                  <div className="grid gap-3">
                    {ROLE_FILTERS.filter((option) => option.value !== 'any').map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setSelectedRole(option.value as ModerationRole)}
                        className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/60 ${
                          selectedRole === option.value
                            ? 'border-primary-500 bg-primary-50/80 text-primary-700 shadow-[0_10px_35px_-28px_rgba(79,70,229,0.6)] dark:border-primary-400/70 dark:bg-primary-400/10 dark:text-primary-100'
                            : 'border-white/40 bg-white/70 text-gray-700 hover:border-primary-400 hover:bg-primary-50/40 dark:border-dark-600/40 dark:bg-dark-800/40 dark:text-dark-100'
                        }`}
                      >
                        <span>
                          <span className="text-sm font-semibold capitalize">{option.label}</span>
                          <span className="mt-1 block text-xs text-gray-500 dark:text-dark-300">{option.description}</span>
                        </span>
                        <span
                          className={`inline-flex size-4 items-center justify-center rounded-full border ${
                            selectedRole === option.value ? 'border-primary-600 bg-primary-600' : 'border-gray-300 bg-white'
                          }`}
                          aria-hidden="true"
                        >
                          {selectedRole === option.value ? <span className="size-2 rounded-full bg-white" /> : null}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}

              {tab === 'sanctions' ? (
                <div className="space-y-4" data-testid="moderation-users-drawer-sanctions">
                  <Select
                    label="Sanction type"
                    value={sanctionForm.type}
                    onChange={(event) => setSanctionForm((prev) => ({ ...prev, type: event.target.value }))}
                  >
                    {SANCTION_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {toTitleCase(type)}
                      </option>
                    ))}
                  </Select>
                  <Textarea
                    label="Reason"
                    value={sanctionForm.reason}
                    onChange={(event) => setSanctionForm((prev) => ({ ...prev, reason: event.target.value }))}
                    minLength={3}
                    rows={5}
                    placeholder="Describe why this sanction is applied"
                  />
                  <Input
                    label="Duration (hours)"
                    value={sanctionForm.durationHours}
                    onChange={(event) => setSanctionForm((prev) => ({ ...prev, durationHours: event.target.value }))}
                    placeholder="24"
                  />
                </div>
              ) : null}

              {tab === 'notes' ? (
                <div className="space-y-4" data-testid="moderation-users-drawer-notes">
                  <Textarea
                    label="Moderator note"
                    value={noteForm.text}
                    onChange={(event) => setNoteForm((prev) => ({ ...prev, text: event.target.value }))}
                    rows={6}
                    placeholder="Share context for the moderation team"
                  />
                  <Switch
                    label="Pin note"
                    checked={noteForm.pinned}
                    onChange={() => setNoteForm((prev) => ({ ...prev, pinned: !prev.pinned }))}
                  />
                  {userDetail && userDetail.notes.length ? (
                    <Surface variant="soft" className="space-y-3 p-4">
                      <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Existing notes</div>
                      <div className="space-y-3 text-sm text-gray-600 dark:text-dark-200">
                        {userDetail.notes.map((note) => (
                          <div key={note.id} className="rounded-2xl border border-white/40 bg-white/60 p-3 dark:border-dark-600/40 dark:bg-dark-800/40">
                            <div className="flex items-center justify-between text-xs text-gray-400">
                              <span>{note.author_name ?? 'Moderator'}</span>
                              <span>{formatDateTime(note.created_at)}</span>
                            </div>
                            <div className="mt-2 whitespace-pre-wrap text-sm text-gray-700 dark:text-dark-100">{note.text}</div>
                            {note.pinned ? (
                              <Badge color="warning" variant="soft" className="mt-2 text-[10px] uppercase">
                                Pinned
                              </Badge>
                            ) : null}
                          </div>
                        ))}
                      </div>
                    </Surface>
                  ) : null}
                </div>
              ) : null}

              {tab === 'activity' ? (
                <div className="space-y-4" data-testid="moderation-users-drawer-activity">
                  <Surface variant="soft" className="space-y-3 p-4">
                    <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Tickets</div>
                    {userDetail?.tickets?.length ? (
                      <div className="space-y-3 text-sm text-gray-600 dark:text-dark-200">
                        {userDetail.tickets.map((ticket) => (
                          <div key={ticket.id} className="rounded-2xl border border-white/40 bg-white/60 p-3 dark:border-dark-600/40 dark:bg-dark-800/40">
                            <div className="flex items-center justify-between">
                              <div className="font-medium text-gray-800 dark:text-dark-50">{ticket.title ?? ticket.id}</div>
                              <Badge color={statusToBadgeTone(ticket.status)} variant="soft" className="capitalize text-xs">
                                {ticket.status ?? 'open'}
                              </Badge>
                            </div>
                            <div className="mt-1 text-xs text-gray-500 dark:text-dark-300">
                              Priority: {ticket.priority ?? 'normal'} | {formatDateTime(ticket.created_at)}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-gray-400">No tickets yet.</div>
                    )}
                  </Surface>

                  <Surface variant="soft" className="space-y-3 p-4">
                    <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Reports</div>
                    {userDetail?.reports?.length ? (
                      <div className="space-y-3 text-sm text-gray-600 dark:text-dark-200">
                        {userDetail.reports.map((report) => (
                          <div key={report.id} className="rounded-2xl border border-white/40 bg-white/60 p-3 dark:border-dark-600/40 dark:bg-dark-800/40">
                            <div className="flex items-center justify-between">
                              <div className="font-medium text-gray-800 dark:text-dark-50">{toTitleCase(report.category ?? 'Report')}</div>
                              <Badge color={statusToBadgeTone(report.status)} variant="soft" className="capitalize text-xs">
                                {report.status ?? 'new'}
                              </Badge>
                            </div>
                            <div className="mt-1 text-xs text-gray-500 dark:text-dark-300">
                              {formatDateTime(report.created_at)} | Reporter: {report.reporter_id ?? 'N/A'}
                            </div>
                            <div className="mt-2 text-xs text-gray-600 dark:text-dark-200">{report.text ?? 'N/A'}</div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-gray-400">No reports logged.</div>
                    )}
                  </Surface>
                </div>
              ) : null}
            </>
          ) : (
            <Surface variant="soft" className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center text-sm text-gray-500">
              <UsersIcon className="size-8 text-gray-300" aria-hidden="true" />
              Select a user to open the moderation drawer.
            </Surface>
          )}
        </div>
      </div>
    </Drawer>
  );
}
