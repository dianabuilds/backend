import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Input, Textarea, Button, Spinner, Avatar, Badge, Accordion, CopyButton } from '../../shared/ui';
import { SettingsLayout } from '../../shared/settings/SettingsLayout';
import { CheckCircle2, Copy as CopyIcon } from '../../shared/icons';
import { useWalletConnection } from '../../shared/settings/useWalletConnection';
import { apiGetWithResponse, apiPutWithResponse, apiUploadMedia } from '../../shared/api/client';
import { useSettingsIdempotencyHeader } from '../../shared/settings';
import { extractErrorMessage } from '../../shared/utils/errors';
import { makeIdempotencyKey } from '../../shared/utils/idempotency';

type ProfilePayload = {
  id: string;
  username?: string | null;
  email?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  role?: string | null;
  wallet?: { address?: string | null; chain_id?: string | null } | null;
  limits?: {
    can_change_username: boolean;
    next_username_change_at?: string | null;
  };
};

const USERNAME_LIMIT_HINT = 'You can change the username once every 14 days.';
const BIO_LIMIT = 280;

export default function ProfilePage() {
  const [profile, setProfile] = React.useState<ProfilePayload | null>(null);
  const [formUsername, setFormUsername] = React.useState('');
  const [formBio, setFormBio] = React.useState('');
  const [formAvatar, setFormAvatar] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [saved, setSaved] = React.useState(false);
  const [etag, setEtag] = React.useState<string | null>(null);
  const [avatarPreview, setAvatarPreview] = React.useState<string | null>(null);
  const [avatarUploading, setAvatarUploading] = React.useState(false);
  const [avatarError, setAvatarError] = React.useState<string | null>(null);
  const [avatarUrlEditable, setAvatarUrlEditable] = React.useState(false);
  const avatarInputRef = React.useRef<HTMLInputElement | null>(null);
  const previewUrlRef = React.useRef<string | null>(null);
  const idempotencyHeader = useSettingsIdempotencyHeader();
  const navigate = useNavigate();

  const clearPreview = React.useCallback(() => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
  }, []);

  const applyProfile = React.useCallback(
    (data: ProfilePayload, nextEtag?: string | null) => {
      setProfile(data);
      setFormUsername(data.username ?? '');
      setFormBio(data.bio ?? '');
      setFormAvatar(data.avatar_url ?? '');
      setAvatarUrlEditable(false);
      setAvatarError(null);
      clearPreview();
      setAvatarPreview(data.avatar_url ?? null);
      if (typeof nextEtag === 'string' && nextEtag.length > 0) {
        setEtag(nextEtag);
      }
    },
    [clearPreview],
  );

  const loadProfile = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data, response } = await apiGetWithResponse<ProfilePayload>('/v1/profile/me');
      applyProfile(data, response.headers.get('ETag'));
    } catch (err) {
      setProfile(null);
      setError(extractErrorMessage(err, 'Failed to load profile'));
      clearPreview();
      setAvatarPreview(null);
    } finally {
      setLoading(false);
    }
  }, [applyProfile, clearPreview]);

  React.useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  React.useEffect(() => () => clearPreview(), [clearPreview]);

  React.useEffect(() => {
    if (!saved) return;
    const timer = window.setTimeout(() => setSaved(false), 3000);
    return () => window.clearTimeout(timer);
  }, [saved]);

  const limits = profile?.limits;
  const canChangeUsername = limits?.can_change_username ?? true;
  const nextUsernameAt = limits?.next_username_change_at ? new Date(limits.next_username_change_at) : null;

  const usernameHint = canChangeUsername
    ? USERNAME_LIMIT_HINT
    : nextUsernameAt
        ? `You can change the username after ${nextUsernameAt.toLocaleString()}`
        : USERNAME_LIMIT_HINT;

  const onSaveProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!profile?.id) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const payload: Record<string, any> = {
        username: formUsername.trim() || null,
        bio: formBio.trim() || null,
        avatar_url: formAvatar.trim() || null,
      };
      const headers: Record<string, string> = { [idempotencyHeader]: makeIdempotencyKey() };
      if (etag) headers['If-Match'] = etag;
      const { data, response } = await apiPutWithResponse<ProfilePayload>('/v1/profile/me', payload, { headers });
      applyProfile(data, response.headers.get('ETag'));
      setSaved(true);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to save profile'));
    } finally {
      setSaving(false);
    }
  };

  const onUploadAvatar = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setAvatarError(null);
    setAvatarUploading(true);
    try {
      const preview = URL.createObjectURL(file);
      clearPreview();
      previewUrlRef.current = preview;
      setAvatarPreview(preview);

      const formData = new FormData();
      formData.append('file', file);
      const result = await apiUploadMedia('/v1/profile/me/avatar', formData);
      const uploadedUrl = typeof (result as any)?.url === 'string' ? (result as any).url : null;
      if (uploadedUrl) {
        setFormAvatar(uploadedUrl);
      }
    } catch (err) {
      setAvatarError(extractErrorMessage(err, 'Failed to upload avatar'));
    } finally {
      setAvatarUploading(false);
    }
  };

  const errorBanner = error ? (
    <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
  ) : null;

  const quickLinksCard = (
    <Card className="space-y-4 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm">
      <h2 className="text-sm font-semibold text-gray-700">Quick links</h2>
      <div className="space-y-2 text-sm text-gray-600">
        <p>Adjust notifications, security tools or review billing without leaving settings.</p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" size="sm" variant="ghost" color="neutral" onClick={() => navigate('/settings/security')}>
          Security
        </Button>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          color="neutral"
          onClick={() => navigate('/settings/notifications')}
        >
          Notifications
        </Button>
        <Button type="button" size="sm" color="primary" onClick={() => navigate('/billing')}>
          Billing
        </Button>
      </div>
    </Card>
  );

  const sidePanel = loading ? (
    <Card className="flex items-center gap-2 p-5 text-sm text-gray-500">
      <Spinner size="sm" /> Loading summary...
    </Card>
  ) : (
    <>
      <AccountSnapshotCard
        profile={profile}
        canChangeUsername={canChangeUsername}
        nextUsernameAt={nextUsernameAt}
        onReloadProfile={() => {
          void loadProfile();
        }}
      />
      {quickLinksCard}
    </>
  );

  const profileFormCard = (
    <Card className="space-y-6 rounded-3xl border border-white/60 bg-white/80 p-6 sm:p-8 xl:p-10 shadow-sm">
      {saved && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
          Profile updated.
        </div>
      )}
      <form onSubmit={onSaveProfile} className="flex flex-col gap-7">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col items-center gap-4">
            <div className="rounded-full bg-gradient-to-br from-primary-200/50 via-white to-primary-300/60 p-1 shadow-lg ring-4 ring-white/70">
              <Avatar
                size="lg"
                src={avatarPreview || profile?.avatar_url || undefined}
                name={formUsername || profile?.email || 'avatar'}
                className="h-36 w-36 overflow-hidden rounded-full sm:h-40 sm:w-40"
              />
            </div>
            <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-center sm:gap-4">
              <Button type="button" size="sm" color="primary" onClick={() => avatarInputRef.current?.click()} disabled={avatarUploading}>
                {avatarUploading ? 'Uploading...' : 'Upload avatar'}
              </Button>
              <input ref={avatarInputRef} type="file" accept="image/*" className="hidden" onChange={onUploadAvatar} />
              <Button
                type="button"
                size="sm"
                variant="ghost"
                color="neutral"
                onClick={() => {
                  clearPreview();
                  setAvatarPreview(null);
                  setFormAvatar('');
                }}
                disabled={avatarUploading || (!avatarPreview && !formAvatar)}
              >
                Remove
              </Button>
            </div>
            {avatarError && <div className="text-xs text-rose-600">{avatarError}</div>}
          </div>

          <div className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2 sm:gap-5">
              <Input
                label="Username"
                value={formUsername}
                onChange={(event) => setFormUsername(event.target.value)}
                disabled={saving || !profile?.id || !canChangeUsername}
                hint={usernameHint}
              />
              <Input label="Role" value={profile?.role || 'Member'} disabled />
            </div>
            <Input
              label="Primary email"
              value={profile?.email || ''}
              readOnly
              disabled
              description="Change primary email from the Security settings."
            />
            <div className="space-y-2">
              <Textarea
                label={labelWithHint('Bio', 'Short public blurb. Max 280 characters.')}
                value={formBio}
                onChange={(event) => setFormBio(event.target.value)}
                rows={6}
                maxLength={BIO_LIMIT}
                placeholder="Tell people something useful (max 280 characters)"
                disabled={saving}
              />
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>Keep it short and relevant.</span>
                <span>{`${formBio.length}/${BIO_LIMIT}`}</span>
              </div>
            </div>
            <Accordion
              title={<span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Advanced</span>}
              className="border border-dashed border-gray-200"
            >
              <div className="space-y-3 rounded-xl bg-white/70 px-4 py-4 backdrop-blur-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Avatar URL</span>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    color="neutral"
                    onClick={() => setAvatarUrlEditable((value) => !value)}
                  >
                    {avatarUrlEditable ? 'Lock field' : 'Enable editing'}
                  </Button>
                </div>
                <Input
                  value={formAvatar}
                  onChange={(event) => setFormAvatar(event.target.value)}
                  placeholder="https://assets.example.com/avatar.png"
                  readOnly={!avatarUrlEditable}
                  disabled={saving || avatarUploading}
                />
                <p className="text-xs text-gray-500">Managed automatically after uploads. Edit only if you host the image elsewhere.</p>
              </div>
            </Accordion>
          </div>
        </div>

        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</div>
        )}

        <div className="flex flex-wrap justify-end gap-3">
          <Button type="button" variant="ghost" color="neutral" size="sm" onClick={() => void loadProfile()} disabled={saving}>
            Reset
          </Button>
          <Button type="submit" color="primary" disabled={saving || !profile?.id}>
            {saving ? 'Saving...' : 'Save changes'}
          </Button>
        </div>
      </form>
    </Card>
  );
  const mainContent = loading ? (
    <Card className="flex items-center justify-center gap-3 p-6 text-sm text-gray-500">
      <Spinner size="sm" /> Loading profile...
    </Card>
  ) : (
    <div className="flex flex-col gap-6">
      {profileFormCard}
    </div>
  );

  return (
    <SettingsLayout
      title="Profile"
      description="Manage how people see you and keep contact details up to date."
      error={errorBanner}
      side={sidePanel}
    >
      {mainContent}
    </SettingsLayout>
  );
}

type AccountSnapshotCardProps = {
  profile: ProfilePayload | null;
  canChangeUsername: boolean;
  nextUsernameAt: Date | null;
  onReloadProfile: () => void;
};

function AccountSnapshotCard({ profile, canChangeUsername, nextUsernameAt, onReloadProfile }: AccountSnapshotCardProps) {
  const initialWalletAddress = profile ? profile.wallet?.address ?? null : undefined;
  const initialWalletChainId = profile ? profile.wallet?.chain_id ?? null : undefined;

  const {
    wallet,
    shortAddress,
    isConnected,
    loading,
    busy,
    error,
    status,
    loadWallet,
    connectWallet,
    disconnectWallet,
  } = useWalletConnection({
    initialWalletAddress,
    initialWalletChainId,
    onWalletChange: onReloadProfile,
  });

  const usernameDisplay = profile?.username || 'Not set';
  const emailDisplay = profile?.email || 'Not set';

  const walletDisplay = isConnected ? (
    <CopyButton value={wallet ?? ''}>
      {({ copy, copied }) => (
        <button
          type="button"
          onClick={copy}
          className="group inline-flex items-center gap-2 font-mono text-sm text-gray-900"
          title="Copy wallet address"
        >
          <span className="max-w-[12rem] truncate">{shortAddress}</span>
          {copied ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          ) : (
            <CopyIcon className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
          )}
        </button>
      )}
    </CopyButton>
  ) : (
    <span className="text-gray-500">Not connected</span>
  );

  return (
    <Card className="space-y-5 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <h2 className="text-sm font-semibold text-gray-700">Account snapshot</h2>
          <p className="text-xs text-gray-500">Overview of your account identity and wallet connection.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {profile?.role && <Badge color="neutral" variant="soft">{profile.role}</Badge>}
          <Badge color={isConnected ? 'success' : 'neutral'} variant="soft">
            {isConnected ? 'Connected' : 'Not connected'}
          </Badge>
        </div>
      </div>

      <div className="space-y-2 text-sm text-gray-600">
        <SnapshotRow label="Username">
          <span className="font-medium text-gray-900">{usernameDisplay}</span>
        </SnapshotRow>
        <SnapshotRow label="Email">
          <span className="max-w-[14rem] truncate font-medium text-gray-900">{emailDisplay}</span>
        </SnapshotRow>
        <SnapshotRow label="Wallet">{walletDisplay}</SnapshotRow>
      </div>

      {(loading || status || error) && (
        <div className="space-y-2">
          {loading && (
            <div className="flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-500">
              <Spinner size="sm" /> Checking wallet status...
            </div>
          )}
          {status && (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">{status}</div>
          )}
          {error && (
            <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</div>
          )}
        </div>
      )}

      <div className="space-y-2">
        <div className="text-xs text-gray-500">Username change status</div>
        <div
          className={`rounded-lg border px-3 py-2 text-xs ${
            canChangeUsername ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700'
          }`}
        >
          {canChangeUsername
            ? 'Ready'
            : nextUsernameAt
                ? `Available after ${nextUsernameAt.toLocaleString()}`
                : 'Cooldown active'}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" size="sm" color="primary" onClick={connectWallet} disabled={busy}>
          {busy ? 'Connecting...' : isConnected ? 'Reconnect wallet' : 'Connect wallet'}
        </Button>
        {isConnected && (
          <Button type="button" size="sm" variant="ghost" color="neutral" onClick={disconnectWallet} disabled={busy}>
            Disconnect
          </Button>
        )}
        <Button type="button" size="sm" variant="ghost" color="neutral" onClick={() => void loadWallet()} disabled={busy || loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      <p className="text-[11px] text-gray-400">
        We attempt to use MetaMask when available. Install a compatible wallet extension if your browser cannot detect a provider.
      </p>
    </Card>
  );
}

type SnapshotRowProps = {
  label: string;
  children: React.ReactNode;
};

function SnapshotRow({ label, children }: SnapshotRowProps) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span>{label}</span>
      <div className="flex min-w-0 items-center justify-end gap-2 text-right">{children}</div>
    </div>
  );
}

function labelWithHint(label: string, hint: string): React.ReactNode {
  return (
    <span className="inline-flex items-center gap-2">
      <span>{label}</span>
      <span
        className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-gray-300 text-[10px] font-semibold uppercase leading-none text-gray-500"
        title={hint}
        aria-label={hint}
      >
        i
      </span>
    </span>
  );
}
