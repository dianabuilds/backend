import React from 'react';
import { Card, Spinner, Drawer, Input, Select, Textarea, Switch, Button, TablePagination } from '@ui';
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

export default function ModerationUsers() {
  const [items, setItems] = React.useState<User[]>([]);
  const [selectedDetail, setSelectedDetail] = React.useState<any | null>(null);
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
    const t = setTimeout(() => { void load(); }, 200);
    return () => clearTimeout(t);
  }, [load]);

  const loadDetails = React.useCallback(async (user: User) => {
    try {
      const d = await apiGet(`/api/moderation/users/${encodeURIComponent(user.id)}`);
      setSelectedDetail(d);
    } catch {
      setSelectedDetail(null);
    }
  }, []);

  const openDetailDrawer = React.useCallback((user: User, opts: { reload?: boolean } = {}) => {
    setDrawer({ mode: 'detail', user });
    if (opts.reload !== false) {
      setSelectedDetail(null);
      void loadDetails(user);
    }
  }, [loadDetails]);

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

  const filteredItems = items.filter((u) => {
    const rs = (u.roles || []).map((r) => String(r).toLowerCase());
    const st = String(u.status || '').toLowerCase();
    if (filterRole !== 'all' && !rs.includes(filterRole)) return false;
    if (filterStatus !== 'all' && st !== filterStatus) return false;
    return true;
  });

  const drawerMode = drawer?.mode ?? null;
  const drawerUser = drawer?.user ?? null;

  const goBackToDetail = React.useCallback((reload = false) => {
    if (!drawerUser) {
      closeDrawer();
      return;
    }
    openDetailDrawer(drawerUser, { reload });
  }, [drawerUser, closeDrawer, openDetailDrawer]);

  let drawerTitle = '';
  let drawerBody: React.ReactNode = null;
  let drawerFooter: React.ReactNode = null;

  if (drawerMode === 'detail' && drawerUser) {
    drawerTitle = `User: ${drawerUser.username || drawerUser.id || ''}`;
    drawerBody = (
      <div className="p-4 space-y-3">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-gray-500">ID</div><div className="truncate">{drawerUser.id}</div>
          <div className="text-gray-500">Email</div><div className="truncate">{drawerUser.email || '-'}</div>
          <div className="text-gray-500">Roles</div><div>{(drawerUser.roles || []).join(', ') || '-'}</div>
          <div className="text-gray-500">Status</div><div>{drawerUser.status}</div>
        </div>
        <div className="text-sm text-gray-500">More</div>
        <pre className="rounded bg-gray-50 p-2 text-xs overflow-auto">{JSON.stringify(selectedDetail || {}, null, 2)}</pre>
      </div>
    );
    drawerFooter = (
      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={() => openSanctionDrawer(drawerUser, 'warning')}>Issue warning</Button>
        <Button onClick={() => openSanctionDrawer(drawerUser, 'ban')} className="bg-red-600 text-white hover:bg-red-700">Ban</Button>
        <Button onClick={() => openRolesDrawer(drawerUser)} variant="outlined">Edit role</Button>
        <Button onClick={() => openNoteDrawer(drawerUser)} variant="ghost">Add note</Button>
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
        <button className="text-xs text-gray-500 hover:text-primary-600" onClick={() => goBackToDetail(false)}>{"← Back to user"}</button>
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
        <button className="text-xs text-gray-500 hover:text-primary-600" onClick={() => goBackToDetail(false)}>{"← Back to user"}</button>
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
        <button className="text-xs text-gray-500 hover:text-primary-600" onClick={() => goBackToDetail(false)}>{"← Back to user"}</button>
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
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Total</div><div className="text-lg font-semibold">{total}</div></Card>
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Admins</div><div className="text-lg font-semibold">{admins}</div></Card>
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Moderators</div><div className="text-lg font-semibold">{moderators}</div></Card>
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Editors</div><div className="text-lg font-semibold">{editors}</div></Card>
        <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Banned</div><div className="text-lg font-semibold">{banned}</div></Card>
      </div>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Users</h1>
        <div className="flex items-center gap-2">
          {loading && <Spinner size="sm" />}
          <button className="btn h-9 bg-gray-100 px-3 hover:bg-gray-200 dark:bg-dark-600" onClick={() => void load()}>Refresh</button>
        </div>
      </div>
      <Card skin="shadow" className="p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
          <input className="form-input h-9 w-64" placeholder="Search username or email" value={q} onChange={(e) => { setQ(e.target.value); resetPagination(); }} />
          <select className="form-select h-9 w-40" value={filterStatus} onChange={(e) => { const value = e.target.value as any; setFilterStatus(value); setStatus(value === 'all' ? '' : value); resetPagination(); }}>
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="banned">Banned</option>
          </select>
          <select className="form-select h-9 w-40" value={filterRole} onChange={(e) => { const value = e.target.value as any; setFilterRole(value); setRole(value === 'all' ? '' : value); resetPagination(); }}>
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
                        <span key={r} className="rounded bg-gray-100 px-2 py-0.5 text-xs dark:bg-dark-600">{r}</span>
                      ))}
                    </div>
                  </td>
                  <td className="py-2 px-3">{u.status}</td>
                  <td className="py-2 px-3">{u.complaints_count ?? 0}</td>
                  <td className="py-2 px-3">{u.notes_count ?? 0}</td>
                  <td className="py-2 px-3">{u.sanction_count ?? 0}</td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        className="btn h-8 rounded bg-gray-100 px-2 text-xs hover:bg-gray-200 dark:bg-dark-600"
                        onClick={() => openRolesDrawer(u)}
                      >
                        Roles
                      </button>
                      <button
                        className="btn h-8 rounded bg-red-100 px-2 text-xs text-red-700 hover:bg-red-200 dark:bg-dark-700"
                        onClick={() => openSanctionDrawer(u, 'ban')}
                      >
                        Sanction
                      </button>
                      <button
                        className="btn h-8 rounded bg-blue-100 px-2 text-xs text-blue-800 hover:bg-blue-200 dark:bg-dark-700"
                        onClick={() => openNoteDrawer(u)}
                      >
                        Note
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredItems.length === 0 && (
                <tr>
                  <td className="py-4 px-3 text-center text-gray-500" colSpan={9}>No users</td>
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
          onPageSizeChange={(value) => { setPageSize(value); resetPagination(); }}
        />
      </Card>

      <Drawer
        open={!!drawerMode}
        onClose={closeDrawer}
        title={drawerTitle}
        footer={drawerFooter}
        widthClass="w-[520px]"
      >
        {drawerBody}
      </Drawer>
    </div>
  );
}
