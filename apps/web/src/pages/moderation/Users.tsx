import React from 'react';
import { Card, Spinner, Drawer, Input, Select, Textarea, Switch, Button, TablePagination, Badge, Accordion } from '@ui';
import { apiGet, apiPost } from '../../shared/api/client';

interface User {
  id: string;
  username: string;
  email?: string | null;
  roles: string[];
  status: string;
  registered_at?: string | null;
  last_seen_at?: string | null;
  complaints_count?: number;
  notes_count?: number;
  sanction_count?: number;
}

type DrawerMode = 'detail' | 'roles' | 'sanction' | 'note';
type DrawerState = { mode: DrawerMode; user: User } | null;

type UserDetail = Record<string, any> | null;

type SanctionRecord = {
  id?: string;
  type?: string;
  status?: string;
  reason?: string;
  issued_at?: string;
  expires_at?: string;
  actor?: string;
};

type NoteRecord = {
  id?: string;
  text?: string;
  author?: string;
  created_at?: string;
  pinned?: boolean;
};

type CaseRecord = {
  id?: string;
  type?: string;
  status?: string;
  priority?: string;
  opened_at?: string;
};

function toTitleCase(value: string): string {
  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(' ');
}

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString();
}

function relativeTime(value?: string | null): string {
  if (!value) return '—';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  const diffMs = Date.now() - dt.getTime();
  const diffMin = Math.round(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return dt.toLocaleDateString();
}

function ensureArray<T = Record<string, any>>(value: any): T[] {
  if (Array.isArray(value)) return value as T[];
  return [];
}

function statusToBadgeColor(status?: string): 'success' | 'error' | 'warning' | 'neutral' | 'info' {
  if (!status) return 'neutral';
  const normalized = status.toLowerCase();
  if (normalized === 'active' || normalized === 'ok') return 'success';
  if (normalized === 'banned' || normalized === 'blocked') return 'error';
  if (normalized === 'pending' || normalized === 'review') return 'warning';
  return 'neutral';
}

export default function ModerationUsers() {
  const [items, setItems] = React.useState<User[]>([]);
  const [selectedDetail, setSelectedDetail] = React.useState<UserDetail>(null);
  const [detailLoading, setDetailLoading] = React.useState(false);
  const [detailError, setDetailError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [q, setQ] = React.useState('');
  const [status, setStatus] = React.useState('');
  const [role, setRole] = React.useState('');
  const [filterRole, setFilterRole] = React.useState<'all' | 'user' | 'editor' | 'moderator' | 'admin'>('all');
  const [filterStatus, setFilterStatus] = React.useState<'all' | 'active' | 'banned'>('all');

  const [drawer, setDrawer] = React.useState<DrawerState>(null);
  const [selectedRole, setSelectedRole] = React.useState<'user' | 'editor' | 'moderator' | 'admin'>('user');
  const [sanctionType, setSanctionType] = React.useState('ban');
  const [sanctionReason, setSanctionReason] = React.useState('');
  const [sanctionHours, setSanctionHours] = React.useState<string>('');
  const [noteText, setNoteText] = React.useState('');
  const [notePinned, setNotePinned] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [totalItems, setTotalItems] = React.useState<number | undefined>(undefined);

  const resetPagination = React.useCallback(() => {
    setPage(1);
    setHasNext(false);
    setTotalItems(undefined);
  }, []);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = Math.max(0, (page - 1) * pageSize);
      const params: string[] = [`limit=${pageSize}`, `offset=${offset}`];
      if (q) params.push(`q=${encodeURIComponent(q)}`);
      if (status) params.push(`status=${encodeURIComponent(status)}`);
      if (role) params.push(`role=${encodeURIComponent(role)}`);
      const res = await apiGet<{ items?: User[]; total?: number }>(`/api/moderation/users?${params.join('&')}`);
      const fetched = Array.isArray(res?.items) ? res.items : [];
      setItems(fetched);
      const total = typeof res?.total === 'number' ? Number(res.total) : undefined;
      setTotalItems(total);
      if (total != null) {
        setHasNext(page * pageSize < total);
      } else {
        setHasNext(fetched.length === pageSize);
      }
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
      setHasNext(false);
      setTotalItems(undefined);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, q, status, role]);

  React.useEffect(() => {
    const t = setTimeout(() => {
      void load();
    }, 200);
    return () => clearTimeout(t);
  }, [load]);

  const loadDetails = React.useCallback(async (user: User) => {
    setDetailLoading(true);
    setDetailError(null);
    try {
      const detail = await apiGet(`/api/moderation/users/${encodeURIComponent(user.id)}`);
      setSelectedDetail(detail);
    } catch (e: any) {
      setDetailError(String(e?.message || e || 'Failed to load user detail'));
      setSelectedDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const openDetailDrawer = React.useCallback(
    (user: User, opts: { reload?: boolean } = {}) => {
      setDrawer({ mode: 'detail', user });
      if (opts.reload !== false) {
        setSelectedDetail(null);
        void loadDetails(user);
      }
    },
    [loadDetails],
  );

  const openRolesDrawer = React.useCallback((user: User) => {
    setDrawer({ mode: 'roles', user });
    const roles = (user.roles || []).map((r) => String(r).toLowerCase());
    const highest = roles.includes('admin')
      ? 'admin'
      : roles.includes('moderator')
        ? 'moderator'
        : roles.includes('editor')
          ? 'editor'
          : 'user';
    setSelectedRole(highest as any);
  }, []);

  const openSanctionDrawer = React.useCallback((user: User, type: string) => {
    setDrawer({ mode: 'sanction', user });
    setSanctionType(type);
    setSanctionReason('');
    setSanctionHours('');
  }, []);

  const openNoteDrawer = React.useCallback((user: User) => {
    setDrawer({ mode: 'note', user });
    setNoteText('');
    setNotePinned(false);
  }, []);

  const closeDrawer = React.useCallback(() => {
    setDrawer(null);
    setSelectedDetail(null);
    setDetailError(null);
    setDetailLoading(false);
    setSelectedRole('user');
    setSanctionType('ban');
    setSanctionReason('');
    setSanctionHours('');
    setNoteText('');
    setNotePinned(false);
  }, []);

  const total = items.length;
  const admins = items.filter((u) => (u.roles || []).map((r) => String(r).toLowerCase()).includes('admin')).length;
  const moderators = items.filter((u) => (u.roles || []).map((r) => String(r).toLowerCase()).includes('moderator')).length;
  const editors = items.filter((u) => (u.roles || []).map((r) => String(r).toLowerCase()).includes('editor')).length;
  const banned = items.filter((u) => String(u.status).toLowerCase() === 'banned').length;
  const active = items.filter((u) => String(u.status).toLowerCase() === 'active').length;

  const filteredItems = items.filter((u) => {
    const rs = (u.roles || []).map((r) => String(r).toLowerCase());
    const st = String(u.status || '').toLowerCase();
    if (filterRole !== 'all' && !rs.includes(filterRole)) return false;
    if (filterStatus !== 'all' && st !== filterStatus) return false;
    return true;
  });

  const drawerMode = drawer?.mode ?? null;
  const drawerUser = drawer?.user ?? null;

  const goBackToDetail = React.useCallback(
    (reload = false) => {
      if (!drawerUser) {
        closeDrawer();
        return;
      }
      openDetailDrawer(drawerUser, { reload });
    },
    [drawerUser, closeDrawer, openDetailDrawer],
  );

  let drawerTitle = '';
  let drawerBody: React.ReactNode = null;
  let drawerFooter: React.ReactNode = null;

  if (drawerMode === 'detail' && drawerUser) {
    const detail = selectedDetail ?? {};
    const sanctions = ensureArray<SanctionRecord>(detail.sanctions ?? detail.recent_sanctions);
    const notes = ensureArray<NoteRecord>(detail.notes ?? detail.recent_notes);
    const cases = ensureArray<CaseRecord>(detail.cases ?? detail.open_cases ?? detail.pending_cases);

    drawerTitle = `User: ${drawerUser.username || drawerUser.id || ''}`;
    drawerBody = (
      <div className="space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Identifier</div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">{drawerUser.username || drawerUser.id}</div>
            <div className="text-sm text-gray-500">{drawerUser.email || '—'}</div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge color={statusToBadgeColor(drawerUser.status)} variant="soft" className="capitalize">
              {drawerUser.status || 'unknown'}
            </Badge>
            {(drawerUser.roles || []).map((r) => (
              <Badge key={r} color="info" variant="outline" className="capitalize">
                {r}
              </Badge>
            ))}
          </div>
        </div>

        <dl className="grid gap-x-6 gap-y-4 text-sm text-gray-600 dark:text-dark-200 sm:grid-cols-2">
          <div className="space-y-1">
            <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">User ID</dt>
            <dd className="font-mono text-xs break-all text-gray-700 dark:text-dark-100">{drawerUser.id}</dd>
          </div>
          <div className="space-y-1">
            <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Registered</dt>
            <dd>{formatDate(drawerUser.registered_at)}</dd>
          </div>
          <div className="space-y-1">
            <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Last seen</dt>
            <dd>{relativeTime(drawerUser.last_seen_at)}</dd>
          </div>
          <div className="space-y-1">
            <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Complaints</dt>
            <dd>{drawerUser.complaints_count ?? detail.complaints_count ?? 0}</dd>
          </div>
          <div className="space-y-1">
            <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Notes</dt>
            <dd>{drawerUser.notes_count ?? detail.notes_count ?? 0}</dd>
          </div>
          <div className="space-y-1">
            <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Sanctions</dt>
            <dd>{drawerUser.sanction_count ?? detail.sanction_count ?? sanctions.length}</dd>
          </div>
        </dl>

        {detailLoading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Spinner size="sm" />
            <span>Loading detail…</span>
          </div>
        ) : null}
        {detailError ? (
          <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {detailError}
          </div>
        ) : null}

        {!detailLoading && !detailError ? (
          <div className="space-y-4">
            {sanctions.length > 0 ? (
              <Card skin="shadow" className="p-4">
                <div className="text-sm font-semibold text-gray-700">Recent sanctions</div>
                <div className="mt-3 space-y-3">
                  {sanctions.slice(0, 5).map((sanction, index) => (
                    <div key={sanction.id ?? index} className="text-xs text-gray-600 dark:text-dark-200">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold uppercase tracking-wide text-gray-500">
                          {toTitleCase(String(sanction.type ?? 'sanction'))}
                        </span>
                        <Badge color={statusToBadgeColor(sanction.status)} variant="soft" className="capitalize">
                          {sanction.status ?? 'active'}
                        </Badge>
                      </div>
                      <div className="mt-1 flex flex-wrap items-center gap-2 text-gray-500">
                        <span>{sanction.reason || '—'}</span>
                        <span className="text-gray-300">|</span>
                        <span>
                          {formatDate(sanction.issued_at)}
                          {sanction.expires_at ? ` > ${formatDate(sanction.expires_at)}` : ''}
                        </span>
                      </div>
                      {sanction.actor ? (
                        <div className="text-[11px] text-gray-400">by {sanction.actor}</div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </Card>
            ) : null}

            {notes.length > 0 ? (
              <Card skin="shadow" className="p-4">
                <div className="text-sm font-semibold text-gray-700">Moderator notes</div>
                <div className="mt-3 space-y-3">
                  {notes.slice(0, 5).map((note, index) => (
                    <div key={note.id ?? index} className="rounded border border-gray-200 p-3 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-gray-700 dark:text-dark-100">{note.author || 'moderator'}</span>
                        <span className="text-[11px] text-gray-400">{formatDate(note.created_at)}</span>
                      </div>
                      <div className="mt-1 whitespace-pre-wrap text-gray-600 dark:text-dark-200">{note.text || '—'}</div>
                      {note.pinned ? <Badge color="warning" variant="soft" className="mt-2 uppercase">Pinned</Badge> : null}
                    </div>
                  ))}
                </div>
              </Card>
            ) : null}

            {cases.length > 0 ? (
              <Card skin="shadow" className="p-4">
                <div className="text-sm font-semibold text-gray-700">Open cases</div>
                <div className="mt-3 space-y-3">
                  {cases.slice(0, 5).map((caseItem, index) => (
                    <div key={caseItem.id ?? index} className="flex flex-col gap-1 text-xs text-gray-600 dark:text-dark-200">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-gray-700 dark:text-dark-100">Case #{caseItem.id ?? index + 1}</span>
                        <Badge color={statusToBadgeColor(caseItem.status)} variant="soft" className="capitalize">
                          {caseItem.status ?? 'open'}
                        </Badge>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-gray-400">
                        <span>{toTitleCase(String(caseItem.type ?? 'moderation'))}</span>
                        {caseItem.priority ? (
                          <>
                            <span className="text-gray-300">|</span>
                            <span>Priority: {caseItem.priority}</span>
                          </>
                        ) : null}
                        {caseItem.opened_at ? (
                          <>
                            <span className="text-gray-300">|</span>
                            <span>{relativeTime(caseItem.opened_at)}</span>
                          </>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            ) : null}

            <Accordion title="Raw payload" defaultOpen={false} className="border-gray-200">
              <div className="max-h-80 overflow-auto px-4 py-3 text-xs text-gray-600 dark:text-dark-200">
                <pre>{JSON.stringify(detail, null, 2)}</pre>
              </div>
            </Accordion>
          </div>
        ) : null}
      </div>
    );
    drawerFooter = (
      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={() => openSanctionDrawer(drawerUser, 'warning')}>Issue warning</Button>
        <Button onClick={() => openSanctionDrawer(drawerUser, 'ban')} className="bg-red-600 text-white hover:bg-red-700">
          Ban
        </Button>
        <Button onClick={() => openRolesDrawer(drawerUser)} variant="outlined">
          Edit role
        </Button>
        <Button onClick={() => openNoteDrawer(drawerUser)} variant="ghost">
          Add note
        </Button>
        <Button size="sm" variant="ghost" onClick={() => void loadDetails(drawerUser)}>
          Refresh detail
        </Button>
      </div>
    );
  } else if (drawerMode === 'roles' && drawerUser) {
    drawerTitle = `Edit role: ${drawerUser.username || drawerUser.id || ''}`;
    const handleSave = async () => {
      const current = (drawerUser.roles || []).map((r) => String(r).toLowerCase());
      const target = selectedRole;
      const all = ['user', 'editor', 'moderator', 'admin'];
      const add = current.includes(target) ? [] : [target];
      const remove = all.filter((r) => r !== target && current.includes(r));
      if (target === 'user' && !add.includes('user')) add.push('user');
      try {
        await apiPost(`/api/moderation/users/${encodeURIComponent(drawerUser.id)}/roles`, {
          add: add.map((r) => r[0].toUpperCase() + r.slice(1)),
          remove: remove.map((r) => r[0].toUpperCase() + r.slice(1)),
        });
        await load();
        openDetailDrawer(drawerUser);
      } catch (e: any) {
        setError(String(e?.message || e || 'error'));
      }
    };
    drawerBody = (
      <div className="p-4 space-y-4">
        <button className="text-xs text-gray-500 hover:text-primary-600" onClick={() => goBackToDetail(false)}>{'< Back to user'}</button>
        <fieldset className="space-y-2">
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-sm">Admin</span>
            <input type="radio" name="role" checked={selectedRole === 'admin'} onChange={() => setSelectedRole('admin')} />
          </label>
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-sm">Moderator</span>
            <input type="radio" name="role" checked={selectedRole === 'moderator'} onChange={() => setSelectedRole('moderator')} />
          </label>
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-sm">Editor</span>
            <input type="radio" name="role" checked={selectedRole === 'editor'} onChange={() => setSelectedRole('editor')} />
          </label>
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-sm">User</span>
            <input type="radio" name="role" checked={selectedRole === 'user'} onChange={() => setSelectedRole('user')} />
          </label>
        </fieldset>
      </div>
    );
    drawerFooter = (
      <div className="flex items-center gap-2">
        <Button onClick={handleSave}>Save</Button>
        <Button variant="ghost" onClick={() => goBackToDetail(false)}>Cancel</Button>
      </div>
    );
  } else if (drawerMode === 'sanction' && drawerUser) {
    drawerTitle = `Issue sanction: ${drawerUser.username || drawerUser.id || ''}`;
    const handleIssue = async () => {
      const payload: any = { type: sanctionType, reason: sanctionReason };
      const hours = parseFloat(sanctionHours || '');
      if (!Number.isNaN(hours)) payload.duration_hours = hours;
      try {
        await apiPost(`/api/moderation/users/${encodeURIComponent(drawerUser.id)}/sanctions`, payload);
        await load();
        openDetailDrawer(drawerUser);
      } catch (e: any) {
        setError(String(e?.message || e || 'error'));
      }
    };
    drawerBody = (
      <div className="p-4 space-y-3">
        <button className="text-xs text-gray-500 hover:text-primary-600" onClick={() => goBackToDetail(false)}>{'< Back to user'}</button>
        <div>
          <div className="mb-1 text-xs text-gray-500">Type</div>
          <Select value={sanctionType} onChange={(e: any) => setSanctionType(e.target.value)}>
            <option value="ban">ban</option>
            <option value="mute">mute</option>
            <option value="limit">limit</option>
            <option value="shadowban">shadowban</option>
            <option value="warning">warning</option>
          </Select>
        </div>
        <div>
          <div className="mb-1 text-xs text-gray-500">Reason</div>
          <Textarea value={sanctionReason} onChange={(e) => setSanctionReason(e.target.value)} placeholder="Reason" />
        </div>
        <div>
          <div className="mb-1 text-xs text-gray-500">Duration (hours, optional)</div>
          <Input value={sanctionHours} onChange={(e) => setSanctionHours(e.target.value)} placeholder="e.g. 24" />
        </div>
      </div>
    );
    drawerFooter = (
      <div className="flex items-center gap-2">
        <Button onClick={handleIssue}>Issue</Button>
        <Button variant="ghost" onClick={() => goBackToDetail(false)}>Cancel</Button>
      </div>
    );
  } else if (drawerMode === 'note' && drawerUser) {
    drawerTitle = `Add moderator note: ${drawerUser.username || drawerUser.id || ''}`;
    const handleSave = async () => {
      try {
        await apiPost(`/api/moderation/users/${encodeURIComponent(drawerUser.id)}/notes`, { text: noteText, pinned: notePinned });
        await load();
        openDetailDrawer(drawerUser);
      } catch (e: any) {
        setError(String(e?.message || e || 'error'));
      }
    };
    drawerBody = (
      <div className="p-4 space-y-3">
        <button className="text-xs text-gray-500 hover:text-primary-600" onClick={() => goBackToDetail(false)}>{'< Back to user'}</button>
        <div>
          <div className="mb-1 text-xs text-gray-500">Text</div>
          <Textarea value={noteText} onChange={(e) => setNoteText(e.target.value)} placeholder="Note text" />
        </div>
        <div className="flex items-center justify-between">
          <div className="text-sm">Pinned</div>
          <Switch checked={notePinned} onChange={() => setNotePinned((s) => !s)} />
        </div>
      </div>
    );
    drawerFooter = (
      <div className="flex items-center gap-2">
        <Button onClick={handleSave}>Save</Button>
        <Button variant="ghost" onClick={() => goBackToDetail(false)}>Cancel</Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-6">
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Total</div><div className="text-lg font-semibold">{total}</div></Card>
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Admins</div><div className="text-lg font-semibold">{admins}</div></Card>
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Moderators</div><div className="text-lg font-semibold">{moderators}</div></Card>
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Editors</div><div className="text-lg font-semibold">{editors}</div></Card>
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Active</div><div className="text-lg font-semibold">{active}</div></Card>
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Banned</div><div className="text-lg font-semibold">{banned}</div></Card>
      </div>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Users</h1>
        <div className="flex items-center gap-2">
          {loading && <Spinner size="sm" />}
          <Button variant="outlined" onClick={() => void load()}>Refresh</Button>
        </div>
      </div>
      <Card skin="shadow" className="p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
          <input className="form-input h-9 w-64" placeholder="Search username or email" value={q} onChange={(e) => {
            setQ(e.target.value);
            resetPagination();
          }} />
          <select className="form-select h-9 w-40" value={filterStatus} onChange={(e) => {
            const value = e.target.value as any;
            setFilterStatus(value);
            setStatus(value === 'all' ? '' : value);
            resetPagination();
          }}>
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="banned">Banned</option>
          </select>
          <select className="form-select h-9 w-40" value={filterRole} onChange={(e) => {
            const value = e.target.value as any;
            setFilterRole(value);
            setRole(value === 'all' ? '' : value);
            resetPagination();
          }}>
            <option value="all">All roles</option>
            <option value="admin">Admin</option>
            <option value="moderator">Moderator</option>
            <option value="editor">Editor</option>
            <option value="user">User</option>
          </select>
        </div>
        {error && <div className="mb-2 text-sm text-red-600">{error}</div>}
        <div className="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-500">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-dark-700/40">
              <tr>
                <th className="py-2 px-3">ID</th>
                <th className="py-2 px-3">Username</th>
                <th className="py-2 px-3">Email</th>
                <th className="py-2 px-3">Roles</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Last seen</th>
                <th className="py-2 px-3">Complaints</th>
                <th className="py-2 px-3">Notes</th>
                <th className="py-2 px-3">Sanctions</th>
                <th className="py-2 px-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((u) => (
                <tr key={u.id} className="border-b border-gray-200">
                  <td className="py-2 px-3 text-gray-500">
                    <button className="text-blue-600 hover:underline" onClick={() => openDetailDrawer(u)} title="Open details">{u.id}</button>
                  </td>
                  <td className="py-2 px-3 font-medium">
                    <button className="hover:underline" onClick={() => openDetailDrawer(u)} title="Open details">{u.username}</button>
                  </td>
                  <td className="py-2 px-3">{u.email || ''}</td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap gap-1">
                      {(u.roles || []).map((r) => (
                        <Badge key={r} color="info" variant="soft" className="capitalize">
                          {r}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="py-2 px-3">
                    <Badge color={statusToBadgeColor(u.status)} variant="soft" className="capitalize">
                      {u.status}
                    </Badge>
                  </td>
                  <td className="py-2 px-3 text-sm text-gray-500">{relativeTime(u.last_seen_at)}</td>
                  <td className="py-2 px-3">{u.complaints_count ?? 0}</td>
                  <td className="py-2 px-3">{u.notes_count ?? 0}</td>
                  <td className="py-2 px-3">{u.sanction_count ?? 0}</td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Button size="sm" variant="outlined" onClick={() => openRolesDrawer(u)}>
                        Roles
                      </Button>
                      <Button size="sm" color="error" variant="ghost" onClick={() => openSanctionDrawer(u, 'ban')}>
                        Sanction
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => openNoteDrawer(u)}>
                        Note
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredItems.length === 0 && (
                <tr>
                  <td className="py-4 px-3 text-center text-gray-500" colSpan={10}>No users</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <TablePagination
          page={page}
          pageSize={pageSize}
          currentCount={filteredItems.length}
          hasNext={hasNext}
          totalItems={totalItems}
          onPageChange={(value) => setPage(value)}
          onPageSizeChange={(value) => {
            setPageSize(value);
            resetPagination();
          }}
        />
      </Card>

      <Drawer
        open={!!drawerMode}
        onClose={closeDrawer}
        title={drawerTitle}
        footer={drawerFooter}
        widthClass="w-[520px] md:w-[640px]"
      >
        {drawerBody}
      </Drawer>
    </div>
  );
}
