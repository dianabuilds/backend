import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { useAccount } from '../account/AccountContext';
import { api } from '../api/client';
import { listNodes } from '../api/nodes';
import { getMyReferralCode, getMyReferralStats } from '../api/referrals';
import { useToast } from '../components/ToastProvider';
import PageLayout from './_shared/PageLayout';

type MeResponse = {
  username: string | null;
  bio: string | null;
  avatar_url: string | null;
};

const isValidUrl = (s: string): boolean => {
  try {
    new URL(s);
    return true;
  } catch {
    return false;
  }
};

type AchievementItem = {
  id: string;
  code: string;
  title: string;
  description?: string | null;
  icon?: string | null;
  unlocked: boolean;
  unlocked_at?: string | null;
};

export default function Profile() {
  const { addToast } = useToast();
  const [tab, setTab] = useState<'profile' | 'settings' | 'achievements' | 'my_nodes'>('profile');
  const [username, setUsername] = useState('');
  const [bio, setBio] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [timezone, setTimezone] = useState('');
  const [locale, setLocale] = useState('');

  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: async () => (await api.get<MeResponse>('/users/me')).data,
  });

  const { data: profileData } = useQuery({
    queryKey: ['profile'],
    queryFn: async () =>
      (await api.get<{ timezone: string | null; locale: string | null }>('/users/me/profile')).data,
  });

  const { accountId } = useAccount();
  const { data: myCode } = useQuery({
    queryKey: ['my-referral-code'],
    queryFn: async () => {
      try {
        return await getMyReferralCode();
      } catch {
        return null;
      }
    },
  });
  const { data: myStats } = useQuery({
    queryKey: ['my-referral-stats'],
    queryFn: async () => {
      try {
        return await getMyReferralStats();
      } catch {
        return null;
      }
    },
  });

  const { data: achievements } = useQuery({
    queryKey: ['achievements'],
    queryFn: async () => (await api.get<AchievementItem[]>('/achievements')).data,
  });

  // My Nodes (compact list)
  const [myQ, setMyQ] = useState('');
  const [myVis, setMyVis] = useState<'all' | 'visible' | 'hidden'>('all');
  const [myStatus, setMyStatus] = useState<string | 'all'>('all');
  const { data: myNodes } = useQuery({
    queryKey: ['my-nodes', accountId, myQ, myVis, myStatus],
    enabled: tab === 'my_nodes' && Boolean(accountId),
    queryFn: async () => {
      if (!accountId) return [] as { id: number; title?: string; slug?: string; status?: string }[];
      const params: Record<string, unknown> = { scope_mode: 'mine', limit: 50 };
      if (myQ) params.q = myQ;
      if (myVis !== 'all') params.visible = myVis === 'visible' ? true : false;
      if (myStatus !== 'all') params.status = myStatus;
      const items = await listNodes(accountId, params);
      return items as { id: number; title?: string; slug?: string; status?: string }[];
    },
  });

  useEffect(() => {
    if (me) {
      setUsername(me.username ?? '');
      setBio(me.bio ?? '');
      setAvatarUrl(me.avatar_url ?? '');
    }
  }, [me]);

  useEffect(() => {
    if (profileData) {
      setTimezone(profileData.timezone ?? '');
      setLocale(profileData.locale ?? '');
    }
  }, [profileData]);

  const saveProfile = async () => {
    const u = username.trim();
    const b = bio.trim();
    const a = avatarUrl.trim();
    if (!u) {
      addToast({ title: 'Username is required', variant: 'error' });
      return;
    }
    if (a && !isValidUrl(a)) {
      addToast({ title: 'Invalid avatar URL', variant: 'error' });
      return;
    }
    try {
      await api.patch('/users/me', {
        username: u,
        bio: b || null,
        avatar_url: a || null,
      });
      addToast({ title: 'Profile saved', variant: 'success' });
    } catch (e) {
      addToast({
        title: 'Save failed',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  const saveSettings = async () => {
    await api.patch('/users/me/profile', {
      timezone: timezone || null,
      locale: locale || null,
    });
    addToast({ title: 'Settings saved', variant: 'success' });
  };

  return (
    <PageLayout title="Profile">
      <div className="flex gap-4 mb-4">
        <button onClick={() => setTab('profile')} className={tab === 'profile' ? 'font-bold' : ''}>
          Profile
        </button>
        <button
          onClick={() => setTab('settings')}
          className={tab === 'settings' ? 'font-bold' : ''}
        >
          Settings
        </button>
        <button
          onClick={() => setTab('achievements')}
          className={tab === 'achievements' ? 'font-bold' : ''}
        >
          Achievements
        </button>
        <button
          onClick={() => setTab('my_nodes')}
          className={tab === 'my_nodes' ? 'font-bold ml-auto' : 'ml-auto'}
          title="Мои ноды"
        >
          Мои ноды
        </button>
      </div>
      {tab === 'profile' && (
        <div className="max-w-sm flex flex-col gap-2">
          <label className="text-sm" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <label className="text-sm" htmlFor="bio">
            Bio
          </label>
          <textarea
            id="bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <label className="text-sm" htmlFor="avatar-url">
            Avatar URL
          </label>
          <input
            id="avatar-url"
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <button
            onClick={saveProfile}
            className="mt-2 self-start px-3 py-1 rounded bg-gray-800 text-white text-sm"
          >
            Save profile
          </button>
          <div className="mt-6 p-3 border rounded bg-gray-50">
            <h3 className="font-semibold mb-1">My referral code</h3>
            {!accountId && <p className="text-sm text-gray-600">Select account to get code</p>}
            {accountId && !myCode && <p className="text-sm text-gray-600">Not available</p>}
            {accountId && myCode && (
              <div className="flex items-center gap-2">
                <span className="font-mono">{myCode.code}</span>
                <button
                  className="px-2 py-0.5 text-xs border rounded"
                  onClick={() => {
                    navigator.clipboard.writeText(myCode.code).catch(() => {});
                  }}
                >
                  Copy
                </button>
                {myStats && (
                  <span className="text-xs text-gray-600">Signups: {myStats.total_signups}</span>
                )}
              </div>
            )}
          </div>
        </div>
      )}
      {tab === 'my_nodes' && (
        <div className="mt-2">
          {!accountId && (
            <p className="text-sm text-gray-600">Выберите аккаунт, чтобы увидеть свои ноды.</p>
          )}
          {accountId && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  className="border rounded px-2 py-1 text-sm"
                  placeholder="Поиск..."
                  value={myQ}
                  onChange={(e) => setMyQ(e.target.value)}
                />
                <select
                  className="border rounded px-2 py-1 text-sm"
                  value={myVis}
                  onChange={(e) => setMyVis(e.target.value as 'all' | 'visible' | 'hidden')}
                >
                  <option value="all">Видимость: все</option>
                  <option value="visible">Только видимые</option>
                  <option value="hidden">Только скрытые</option>
                </select>
                <select
                  className="border rounded px-2 py-1 text-sm"
                  value={myStatus}
                  onChange={(e) => setMyStatus(e.target.value)}
                >
                  <option value="all">Статус: все</option>
                  <option value="draft">draft</option>
                  <option value="published">published</option>
                  <option value="archived">archived</option>
                </select>
              </div>
              {myNodes && myNodes.length === 0 && (
                <p className="text-sm text-gray-600">Пока пусто.</p>
              )}
              <ul className="divide-y divide-gray-200 dark:divide-gray-800">
                {(myNodes || []).map((n) => (
                  <li key={n.id} className="py-2 flex items-center justify-between">
                    <div>
                      <div className="font-medium">{n.title || n.slug || `#${n.id}`}</div>
                      {n.status && <div className="text-xs text-gray-500">{n.status}</div>}
                    </div>
                    <a
                      className="text-blue-600 hover:underline text-sm"
                      href={`/admin/nodes/article/${n.id}?account_id=${accountId}`}
                    >
                      Редактировать
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      {tab === 'achievements' && (
        <div className="max-w-2xl">
          {!achievements && <p>Loading…</p>}
          {achievements && achievements.length === 0 && <p>No achievements yet</p>}
          {achievements && achievements.length > 0 && (
            <ul className="divide-y">
              {achievements.map((a) => (
                <li key={a.id} className="py-2 flex items-center gap-3">
                  {a.icon && <img src={a.icon} alt="" className="w-6 h-6" />}
                  <div className="flex-1">
                    <div className="font-medium">{a.title}</div>
                    {a.description && <div className="text-xs text-gray-600">{a.description}</div>}
                  </div>
                  <span
                    className={
                      'text-xs px-2 py-0.5 rounded ' +
                      (a.unlocked ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600')
                    }
                  >
                    {a.unlocked ? 'Unlocked' : 'Locked'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      {tab === 'settings' && (
        <div className="max-w-sm flex flex-col gap-2">
          <label className="text-sm" htmlFor="tz">
            Timezone
          </label>
          <input
            id="tz"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <label className="text-sm" htmlFor="locale">
            Locale
          </label>
          <input
            id="locale"
            value={locale}
            onChange={(e) => setLocale(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <button
            onClick={saveSettings}
            className="mt-2 self-start px-3 py-1 rounded bg-gray-800 text-white text-sm"
          >
            Save settings
          </button>
        </div>
      )}
    </PageLayout>
  );
}
