import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';

import { api } from '../api/client';
import {
  listNotifications,
  markNotificationRead,
  type NotificationItem,
} from '../api/notifications';
import TagInput from '../components/TagInput';
import { useToast } from '../components/ToastProvider';
import type { UserOut } from '../openapi';
import { Button } from '../shared/ui';
import PageLayout from './_shared/PageLayout';

type PremiumLimits = { plan: string; limits: Record<string, unknown> };

type MySettings = { preferences: Record<string, any> };

type AchievementItem = {
  id: string;
  code: string;
  title: string;
  description?: string | null;
  icon?: string | null;
  unlocked: boolean;
  unlocked_at?: string | null;
};

// Lightweight section card
function SectionCard({
  title,
  children,
  actions,
}: {
  title: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <section className="mb-6">
      <div className="border rounded-lg bg-white dark:bg-gray-900 shadow-sm">
        <div className="flex items-center gap-2 px-4 py-3 border-b">
          <h2 className="font-semibold">{title}</h2>
          <div className="ml-auto flex items-center gap-2">{actions}</div>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </section>
  );
}

export default function ProfileV2() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  // Owner/public preview toggle (public hides owner-only blocks)
  const [publicPreview] = useState(false);
  const ownerOnly = !publicPreview;

  // Inline edit mode for profile basics
  const [_avatarModalOpen, setAvatarModalOpen] = useState(false);
  const [tab, setTab] = useState<'edit' | 'language' | 'password' | 'notifications'>('edit');

  // Fetch current user (owner mode)
  const { data: me } = useQuery({
    queryKey: ['me.v2'],
    queryFn: async () => (await api.get<UserOut>('/users/me')).data,
  });

  const { data: premium } = useQuery({
    queryKey: ['premium.me'],
    queryFn: async () => (await api.get<PremiumLimits>('/premium/me/limits')).data,
  });

  const { data: settings } = useQuery({
    queryKey: ['me.settings.v2'],
    queryFn: async () => (await api.get<MySettings>('/users/me/settings')).data,
  });

  const { data: achievements } = useQuery({
    queryKey: ['me.achievements.v2'],
    queryFn: async () => (await api.get<AchievementItem[]>('/achievements')).data,
  });

  const { data: notifications } = useQuery({
    queryKey: ['me.notifications.v2'],
    queryFn: async () => listNotifications(),
  });

  // Local editable fields
  const [username, setUsername] = useState('');
  const [bio, setBio] = useState('');
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [contentLangs, setContentLangs] = useState<string[]>([]);

  useEffect(() => {
    if (me) {
      setUsername(me.username ?? '');
      setBio(me.bio ?? '');
      setAvatarUrl(me.avatar_url ?? null);
    }
  }, [me]);

  useEffect(() => {
    if (settings?.preferences) {
      const langs = (settings.preferences as any).content_languages as string[] | undefined;
      setContentLangs(Array.isArray(langs) ? langs : []);
    }
  }, [settings]);

  const saveProfileMut = useMutation({
    mutationFn: async (payload: Partial<Pick<UserOut, 'username' | 'bio' | 'avatar_url'>>) => {
      const res = await api.patch<typeof payload, UserOut>('/users/me', payload);
      return res.data;
    },
    onSuccess: () => {
      addToast({ title: 'Profile saved', variant: 'success' });
      void qc.invalidateQueries({ queryKey: ['me.v2'] });
    },
    onError: (e: any) => {
      addToast({ title: 'Save failed', description: String(e?.message || e), variant: 'error' });
    },
  });

  const saveSettingsMut = useMutation({
    mutationFn: async (prefs: Record<string, any>) => {
      const res = await api.patch('/users/me/settings', { preferences: prefs });
      return res.data;
    },
    onSuccess: () => {
      addToast({ title: 'Settings saved', variant: 'success' });
      void qc.invalidateQueries({ queryKey: ['me.settings.v2'] });
    },
    onError: (e: any) => {
      addToast({ title: 'Save failed', description: String(e?.message || e), variant: 'error' });
    },
  });

  const markReadMut = useMutation({
    mutationFn: async (id: string) => markNotificationRead(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['me.notifications.v2'] }),
  });

  const [oldPwd, setOldPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const changePwdMut = useMutation({
    mutationFn: async () =>
      (await api.post('/auth/change-password', { old_password: oldPwd, new_password: newPwd }))
        .data,
    onSuccess: () => {
      addToast({ title: 'Password updated', variant: 'success' });
      setOldPwd('');
      setNewPwd('');
    },
    onError: (e: any) =>
      addToast({ title: 'Change failed', description: String(e?.message || e), variant: 'error' }),
  });

  const isPremium = useMemo(() => (premium?.plan && premium.plan !== 'free') || false, [premium]);
  const planBadgeLabel = useMemo(() => {
    if (!premium?.plan || premium.plan === 'free') return 'Free';
    // Map common slugs to nice labels
    if (/plus/i.test(premium.plan)) return 'Premium+';
    return 'Premium';
  }, [premium]);

  // Helper: enforce ~200 chars for bio
  const bioRemaining = 200 - (bio?.length || 0);
  // Track initial values for dirty state and add simple validation
  const [initial, setInitial] = useState<{
    username: string;
    bio: string;
    avatar_url: string | null;
  }>({ username: '', bio: '', avatar_url: null });
  useEffect(() => {
    if (me)
      setInitial({
        username: me.username || '',
        bio: me.bio || '',
        avatar_url: me.avatar_url || null,
      });
  }, [me?.username, me?.bio, me?.avatar_url]);
  const isUsernameValid = useMemo(
    () => /^[a-z0-9._-]{3,20}$/.test((username || '').trim()),
    [username],
  );
  const isDirty = useMemo(
    () =>
      (username || '') !== (initial.username || '') ||
      (bio || '') !== (initial.bio || '') ||
      (avatarUrl || null) !== (initial.avatar_url || null),
    [username, bio, avatarUrl, initial],
  );

  const saveProfile = () => {
    const u = username.trim();
    const b = (bio || '').trim().slice(0, 200);
    if (!u) {
      addToast({ title: 'Username is required', variant: 'error' });
      return;
    }
    saveProfileMut.mutate({ username: u, bio: b, avatar_url: avatarUrl || null });
  };

  const saveContentLangs = () => {
    const current = settings?.preferences || {};
    saveSettingsMut.mutate({ ...current, content_languages: contentLangs });
  };

  // Wallet connect (EVM)
  const [connecting, setConnecting] = useState(false);
  const connectWallet = async () => {
    try {
      setConnecting(true);
      const eth = (window as any).ethereum;
      if (!eth) {
        addToast({ title: 'No wallet provider found', variant: 'error' });
        return;
      }
      const accs: string[] = await eth.request({ method: 'eth_requestAccounts' });
      const addr = accs?.[0];
      if (!addr) {
        addToast({ title: 'Wallet not selected', variant: 'error' });
        return;
      }
      const nonceRes = await api.post('/users/me/wallets/siwe-nonce', {});
      const nonce = (nonceRes.data as any)?.nonce as string;
      if (!nonce) {
        addToast({ title: 'Failed to get nonce', variant: 'error' });
        return;
      }
      let sig = '';
      try {
        sig = await eth.request({ method: 'personal_sign', params: [nonce, addr] });
      } catch {
        // Signature optional for now
      }
      await api.post('/users/me/wallets/siwe-verify', {
        message: nonce,
        signature: sig || '',
        wallet_address: addr,
      });
      addToast({ title: 'Wallet connected', variant: 'success' });
      void qc.invalidateQueries({ queryKey: ['me.v2'] });
    } catch (e: any) {
      addToast({ title: 'Connect failed', description: String(e?.message || e), variant: 'error' });
    } finally {
      setConnecting(false);
    }
  };
  const disconnectWallet = async () => {
    try {
      await api.post('/users/me/wallets/unlink', {});
      addToast({ title: 'Wallet disconnected', variant: 'success' });
      void qc.invalidateQueries({ queryKey: ['me.v2'] });
    } catch (e: any) {
      addToast({
        title: 'Disconnect failed',
        description: String(e?.message || e),
        variant: 'error',
      });
    }
  };

  return (
    <PageLayout title="Profile">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Left summary column */}
        <div className="md:col-span-1">
          <SectionCard title="">
            <div className="flex items-center gap-3">
              <img
                src={avatarUrl || ''}
                alt="avatar"
                className="w-16 h-16 rounded-full object-cover border bg-gray-100"
              />
              <div className="flex-1">
                <div className="text-lg font-semibold">
                  {username ? username : <span className="text-gray-500">Not set</span>}
                </div>
                <div className="text-xs text-gray-600">
                  {me?.email || <span className="text-gray-400">Not set</span>}
                </div>
                <div className="mt-1">
                  <a
                    href="/admin/premium/limits"
                    className={`inline-block text-xs px-2 py-0.5 rounded-full border ${isPremium ? 'bg-yellow-50 border-yellow-300 text-yellow-700' : 'bg-gray-50 border-gray-300 text-gray-700'}`}
                  >
                    {isPremium ? planBadgeLabel : 'Free'}
                  </a>
                </div>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs">
              <Button
                className="text-xs"
                onClick={() =>
                  navigator.clipboard
                    .writeText(`/u/${username || ''}`)
                    .then(() => addToast({ title: 'URL copied', variant: 'success' }))
                    .catch(() => {})
                }
              >
                Copy public URL
              </Button>
              <Button className="text-xs" onClick={() => setTab('notifications')}>
                Manage notifications
              </Button>
            </div>
          </SectionCard>

          <SectionCard title="Personal Info">
            <div className="text-sm space-y-1">
              <div className="flex items-center justify-between gap-2">
                <div className="truncate" title={username || ''}>
                  <span className="text-gray-500">Username:</span>{' '}
                  {username ? username : <span className="text-gray-500">Not set</span>}
                </div>
              </div>
              <div className="flex items-center justify-between gap-2">
                <div className="truncate" title={me?.email || ''}>
                  <span className="text-gray-500">Email:</span>{' '}
                  {me?.email || <span className="text-gray-500">Not set</span>}
                </div>
              </div>
              <div>
                <span className="text-gray-500">Role:</span>{' '}
                {me?.role || <span className="text-gray-500">Not set</span>}
              </div>
              <div className="flex items-center justify-between gap-2">
                <div className="truncate" title={me?.wallet_address || ''}>
                  <span className="text-gray-500">Wallet:</span>{' '}
                  {me?.wallet_address ? (
                    me.wallet_address
                  ) : (
                    <span className="text-gray-500">Not connected</span>
                  )}
                </div>
                {me?.wallet_address ? (
                  <div className="flex items-center gap-2">
                    <Button
                      className="text-xs"
                      onClick={() =>
                        navigator.clipboard.writeText(me.wallet_address || '').catch(() => {})
                      }
                    >
                      Copy
                    </Button>
                    <Button className="text-xs" onClick={disconnectWallet}>
                      Disconnect
                    </Button>
                  </div>
                ) : (
                  <Button
                    className="text-xs"
                    onClick={() => {
                      setTab('edit');
                      connectWallet();
                    }}
                  >
                    Connect wallet
                  </Button>
                )}
              </div>
              <div className="truncate" title={bio || ''}>
                <span className="text-gray-500">Bio:</span>{' '}
                {bio ? bio : <span className="text-gray-500">Not set</span>}
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Achievements">
            <ul className="flex flex-wrap gap-2">
              {(achievements || [])
                .filter((a) => a.unlocked)
                .slice(0, 10)
                .map((a) => (
                  <li
                    key={a.id}
                    className="inline-flex items-center gap-1 px-2 py-1 border rounded text-xs bg-white/60 dark:bg-gray-800/60"
                  >
                    {a.icon && <img src={a.icon} alt="" className="w-4 h-4" />}
                    <span>{a.title}</span>
                  </li>
                ))}
              {(achievements || []).filter((a) => a.unlocked).length === 0 && (
                <li className="text-xs text-gray-600">No achievements yet</li>
              )}
            </ul>
          </SectionCard>
        </div>

        {/* Right editor column */}
        <div className="md:col-span-2">
          <div className="mb-3 flex items-center gap-2 border-b">
            {(
              [
                { id: 'edit', label: 'Edit Profile' },
                { id: 'language', label: 'Language Settings' },
                { id: 'password', label: 'Change Password' },
                { id: 'notifications', label: 'Notification Settings' },
              ] as const
            ).map((t) => (
              <button
                key={t.id}
                className={`px-3 py-2 text-sm border-b-2 -mb-px ${tab === t.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-600'}`}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === 'edit' && (
            <SectionCard
              title="Avatar"
              actions={
                ownerOnly && (
                  <Button
                    className="text-sm bg-blue-600 hover:bg-blue-700 text-white"
                    onClick={saveProfile}
                    disabled={saveProfileMut.isPending}
                  >
                    Save profile
                  </Button>
                )
              }
            >
              <div className="grid grid-cols-1 gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-24 h-24 rounded-full overflow-hidden border bg-gray-100">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={avatarUrl || ''}
                      alt="avatar"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <Button className="text-sm" onClick={() => setAvatarModalOpen(true)}>
                    Change
                  </Button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm mb-1 block">Username</label>
                    <input
                      className={`border rounded px-2 py-1 w-full ${isUsernameValid ? '' : 'border-red-500'}`}
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                    />
                    <div className="text-xs text-gray-500 flex items-center justify-between">
                      <span>Use 3–20: a-z 0-9 . _ -</span>
                      <span>{(username || '').length}/20</span>
                    </div>
                    {!isUsernameValid && (
                      <div className="text-xs text-red-600">Invalid username format</div>
                    )}
                  </div>
                  <div>
                    <label className="text-sm mb-1 block">Email</label>
                    <input
                      className="border rounded px-2 py-1 w-full bg-gray-50"
                      value={me?.email || ''}
                      readOnly
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-sm mb-1 block">Bio</label>
                    <textarea
                      className="border rounded px-2 py-2 w-full"
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      maxLength={200}
                      placeholder="Short bio (200 chars)"
                    />
                    <div className="text-xs text-gray-500">{bioRemaining} characters left</div>
                  </div>
                </div>
              </div>
            </SectionCard>
          )}

          {tab === 'language' && (
            <SectionCard title="Language settings">
              <div>
                <label className="text-sm mb-1 block">Preferred content languages</label>
                <TagInput
                  value={contentLangs}
                  onChange={setContentLangs}
                  placeholder="Add code and press Enter (e.g., ru, en)"
                />
                <Button
                  className="mt-2 text-xs bg-blue-600 hover:bg-blue-700 text-white"
                  onClick={saveContentLangs}
                  disabled={saveSettingsMut.isPending}
                >
                  Save languages
                </Button>
              </div>
            </SectionCard>
          )}

          {tab === 'password' && (
            <SectionCard title="Change password">
              <div className="flex flex-col gap-2 max-w-md">
                <label className="text-sm" htmlFor="oldpwd">
                  Current password
                </label>
                <input
                  id="oldpwd"
                  type="password"
                  className="border rounded px-2 py-1 text-sm"
                  value={oldPwd}
                  onChange={(e) => setOldPwd(e.target.value)}
                />
                <label className="text-sm" htmlFor="newpwd">
                  New password
                </label>
                <input
                  id="newpwd"
                  type="password"
                  className="border rounded px-2 py-1 text-sm"
                  value={newPwd}
                  onChange={(e) => setNewPwd(e.target.value)}
                />
                <div className="flex items-center gap-2 mt-2">
                  <Button
                    className="text-sm bg-blue-600 hover:bg-blue-700 text-white"
                    onClick={() => changePwdMut.mutate()}
                    disabled={changePwdMut.isPending || !oldPwd || !newPwd}
                  >
                    Save
                  </Button>
                </div>
              </div>
            </SectionCard>
          )}

          {tab === 'notifications' && (
            <SectionCard title="Notification settings">
              <div className="mb-3">
                <label className="text-sm inline-flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={!!(settings?.preferences as any)?.notif_prefs?.mute_all}
                    onChange={(e) => {
                      const current = settings?.preferences || {};
                      const notif = { ...(current as any).notif_prefs, mute_all: e.target.checked };
                      saveSettingsMut.mutate({ ...current, notif_prefs: notif });
                    }}
                  />
                  Mute all
                </label>
              </div>
              <ul className="divide-y">
                {(notifications || []).slice(0, 10).map((n: NotificationItem) => (
                  <li key={n.id} className="py-2 flex items-center justify-between">
                    <div>
                      <div className="font-medium text-sm">
                        {n.title || n.type || 'Notification'}
                      </div>
                      <div className="text-xs text-gray-600">{n.message}</div>
                    </div>
                    {ownerOnly && !n.read_at && (
                      <Button className="text-xs" onClick={() => markReadMut.mutate(n.id)}>
                        Mark read
                      </Button>
                    )}
                  </li>
                ))}
                {(notifications || []).length === 0 && (
                  <li className="py-2 text-sm text-gray-600">No notifications</li>
                )}
              </ul>
            </SectionCard>
          )}

          {/* Wallet connect block (also accessible from summary) */}
          {tab === 'edit' && (
            <SectionCard title="Wallet">
              <div className="flex items-center justify-between">
                <div className="text-sm">
                  ETH wallet:{' '}
                  {me?.wallet_address ? (
                    <button
                      type="button"
                      title="Click to copy"
                      className="text-blue-600 hover:underline"
                      onClick={() =>
                        navigator.clipboard
                          .writeText(me.wallet_address || '')
                          .then(() => addToast({ title: 'Address copied', variant: 'success' }))
                          .catch(() => {})
                      }
                    >
                      {me.wallet_address}
                    </button>
                  ) : (
                    <span className="text-gray-600">Not connected</span>
                  )}
                </div>
                {ownerOnly && (
                  <div className="flex items-center gap-2">
                    {!me?.wallet_address && (
                      <Button
                        className="text-xs bg-blue-600 hover:bg-blue-700 text-white"
                        onClick={connectWallet}
                        disabled={connecting}
                      >
                        {connecting ? 'Connecting…' : 'Connect wallet'}
                      </Button>
                    )}
                    {me?.wallet_address && (
                      <Button className="text-xs" onClick={disconnectWallet}>
                        Disconnect
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </SectionCard>
          )}

          {tab === 'edit' && (
            <div className="sticky-save mt-2">
              <style>{`.sticky-save{position:sticky;bottom:0;background:#fff;border-top:1px solid #e5e7eb;padding:12px 16px;display:flex;justify-content:flex-end;gap:8px}`}</style>
              <Button
                className="text-sm"
                onClick={() => {
                  setUsername(initial.username || '');
                  setBio(initial.bio || '');
                  setAvatarUrl(initial.avatar_url || null);
                }}
              >
                Cancel
              </Button>
              <Button
                className={`text-sm ${isDirty && isUsernameValid ? 'bg-blue-600 text-white' : ''}`}
                disabled={!isDirty || !isUsernameValid}
                onClick={saveProfile}
              >
                Save changes
              </Button>
            </div>
          )}
        </div>
      </div>
    </PageLayout>
  );
}
