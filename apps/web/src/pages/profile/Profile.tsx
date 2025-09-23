import React from 'react';
import { Card, Input, Textarea, Button, InputErrorMsg, Spinner } from '../../shared/ui';
import { apiGetWithResponse, apiPost, apiPutWithResponse } from '../../shared/api/client';
import { useSettingsIdempotencyHeader } from '../../shared/settings/SettingsContext';

interface ProfilePayload {
  id: string;
  username?: string | null;
  email?: string | null;
  pending_email?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  role?: string | null;
  wallet?: { address?: string | null };
  limits?: {
    can_change_username: boolean;
    next_username_change_at?: string | null;
    can_change_email: boolean;
    next_email_change_at?: string | null;
  };
}

const USERNAME_LIMIT_HINT = 'You can change the username once every 14 days.';
const EMAIL_LIMIT_HINT = 'You can change the email once every 14 days.';

function makeIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return `tmp-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function ProfilePage() {
  const [profile, setProfile] = React.useState<ProfilePayload | null>(null);
  const [formUsername, setFormUsername] = React.useState('');
  const [formBio, setFormBio] = React.useState('');
  const [formAvatar, setFormAvatar] = React.useState('');
  const [emailInput, setEmailInput] = React.useState('');
  const [emailToken, setEmailToken] = React.useState('');
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [requestingEmail, setRequestingEmail] = React.useState(false);
  const [confirmingEmail, setConfirmingEmail] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [ok, setOk] = React.useState(false);
  const [emailMessage, setEmailMessage] = React.useState<string | null>(null);
  const [etag, setEtag] = React.useState<string | null>(null);
  const idempotencyHeader = useSettingsIdempotencyHeader();

  const applyProfile = React.useCallback((data: ProfilePayload, nextEtag?: string | null) => {
    setProfile(data);
    setFormUsername(data.username ?? '');
    setFormBio(data.bio ?? '');
    setFormAvatar(data.avatar_url ?? '');
    if (typeof nextEtag === 'string' && nextEtag.length) {
      setEtag(nextEtag);
    }
  }, []);

  const loadProfile = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    setEmailMessage(null);
    try {
      const { data, response } = await apiGetWithResponse<ProfilePayload>('/v1/profile/me');
      applyProfile(data, response.headers.get('ETag'));
    } catch (err: any) {
      setError(err?.message || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  }, [applyProfile]);

  React.useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const onSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile?.id) return;
    setSaving(true);
    setError(null);
    setOk(false);
    try {
      const payload: Record<string, any> = {
        username: formUsername,
        bio: formBio,
        avatar_url: formAvatar || null,
      };
      const headers: Record<string, string> = {};
      if (etag) headers['If-Match'] = etag;
      const { data, response } = await apiPutWithResponse<ProfilePayload>('/v1/profile/me', payload, { headers });
      applyProfile(data, response.headers.get('ETag'));
      setOk(true);
    } catch (err: any) {
      setError(err?.message || 'Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  const onRequestEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile?.id) return;
    setRequestingEmail(true);
    setEmailMessage(null);
    setError(null);
    try {
      const headers: Record<string, string> = { [idempotencyHeader]: makeIdempotencyKey() };
      const result = await apiPost('/v1/profile/me/email/request-change', { email: emailInput }, { headers });
      const token = typeof result?.token === 'string' ? result.token : null;
      setEmailMessage(
        token
          ? `Confirmation email requested. Token: ${token}`
          : 'Confirmation email requested. Check your inbox.'
      );
      setEmailToken('');
      await loadProfile();
    } catch (err: any) {
      setError(err?.message || 'Failed to request email change');
    } finally {
      setRequestingEmail(false);
    }
  };

  const onConfirmEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile?.id) return;
    setConfirmingEmail(true);
    setEmailMessage(null);
    setError(null);
    try {
      await apiPost('/v1/profile/me/email/confirm', { token: emailToken });
      setEmailMessage('Email updated successfully.');
      setEmailToken('');
      setEmailInput('');
      await loadProfile();
    } catch (err: any) {
      setError(err?.message || 'Failed to confirm email');
    } finally {
      setConfirmingEmail(false);
    }
  };

  const limits = profile?.limits;
  const canChangeUsername = limits?.can_change_username ?? true;
  const nextUsernameAt = limits?.next_username_change_at
    ? new Date(limits.next_username_change_at)
    : null;
  const canChangeEmail = limits?.can_change_email ?? true;
  const nextEmailAt = limits?.next_email_change_at ? new Date(limits.next_email_change_at) : null;

  return (
    <div className="grid gap-4">
      <h1 className="text-xl font-semibold text-gray-700">Profile</h1>
      <Card className="p-5 max-w-3xl space-y-6">
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Spinner size="sm" /> Loading…
          </div>
        ) : (
          <>
            <form onSubmit={onSaveProfile} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  label="Username"
                  value={formUsername}
                  onChange={(e) => setFormUsername(e.target.value)}
                  disabled={saving || !canChangeUsername}
                  hint={canChangeUsername ? USERNAME_LIMIT_HINT : nextUsernameAt ? `You can change the username after ${nextUsernameAt.toLocaleString()}` : USERNAME_LIMIT_HINT}
                />
                <Input label="Email" value={profile?.email || ''} disabled />
              </div>
              <Textarea
                label="Bio"
                value={formBio}
                onChange={(e) => setFormBio(e.target.value)}
                rows={4}
                placeholder="Tell a bit about yourself, projects, links…"
                disabled={saving}
              />
              <Input
                label="Avatar URL"
                value={formAvatar}
                onChange={(e) => setFormAvatar(e.target.value)}
                placeholder="https://..."
                disabled={saving}
              />
              {profile?.wallet?.address && (
                <div className="text-sm text-gray-500">
                  Connected wallet: <span className="font-mono">{profile.wallet.address}</span>
                </div>
              )}
              {error && <InputErrorMsg when className="block">{error}</InputErrorMsg>}
              {ok && <div className="text-xs text-success">Profile saved</div>}
              <div className="flex gap-3">
                <Button type="submit" color="primary" disabled={saving || !profile?.id}>
                  {saving ? 'Saving…' : 'Save'}
                </Button>
                <Button type="button" variant="ghost" disabled={saving} onClick={loadProfile}>
                  Reset
                </Button>
              </div>
            </form>

            <div className="border-t border-gray-200 pt-4 space-y-4">
              <h2 className="text-sm font-semibold text-gray-600">Email change</h2>
              <form onSubmit={onRequestEmail} className="grid gap-3 md:grid-cols-[2fr,auto] md:items-end">
                <div>
                  <Input
                    label="New email"
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    disabled={requestingEmail || !canChangeEmail}
                    hint={canChangeEmail ? EMAIL_LIMIT_HINT : nextEmailAt ? `Next change available after ${nextEmailAt.toLocaleString()}` : EMAIL_LIMIT_HINT}
                  />
                  {profile?.pending_email && (
                    <div className="mt-2 text-xs text-gray-500">
                      Pending confirmation: <strong>{profile.pending_email}</strong>
                    </div>
                  )}
                </div>
                <Button type="submit" color="primary" disabled={requestingEmail || !profile?.id || !canChangeEmail}>
                  {requestingEmail ? 'Requesting…' : 'Request change'}
                </Button>
              </form>

              <form onSubmit={onConfirmEmail} className="grid gap-3 md:grid-cols-[2fr,auto] md:items-end">
                <Input
                  label="Confirmation token"
                  value={emailToken}
                  onChange={(e) => setEmailToken(e.target.value)}
                  placeholder="Paste token from email"
                  disabled={confirmingEmail || !profile?.pending_email}
                />
                <Button type="submit" color="secondary" disabled={confirmingEmail || !emailToken.trim()}>
                  {confirmingEmail ? 'Confirming…' : 'Confirm email'}
                </Button>
              </form>
              {emailMessage && <div className="text-xs text-success">{emailMessage}</div>}
            </div>
          </>
        )}
      </Card>
    </div>
  );
}

