import React from 'react';
import { Card, Button, Input, Badge, Spinner, Select } from '../../shared/ui';
import { SettingsLayout } from '../../shared/settings/SettingsLayout';
import { SecurityCard } from '../../shared/settings/SecurityCard';
import { WalletConnectionCard } from '../../shared/settings/WalletConnectionCard';
import { apiGet, apiPost } from '../../shared/api/client';
import { useSettingsIdempotencyHeader } from '../../shared/settings/SettingsContext';
import { extractErrorMessage } from '../../shared/utils/errors';
import { makeIdempotencyKey } from '../../shared/utils/idempotency';

type SessionRecord = {
  id: string;
  ip?: string | null;
  user_agent?: string | null;
  created_at?: string | null;
  last_used_at?: string | null;
  expires_at?: string | null;
  refresh_expires_at?: string | null;
  revoked_at?: string | null;
  active?: boolean;
};

type ProfileSnapshot = {
  id: string;
  email?: string | null;
  pending_email?: string | null;
  limits?: {
    can_change_email: boolean;
    next_email_change_at?: string | null;
  };
};

const EMAIL_LIMIT_HINT = 'You can change the email once every 14 days.';

function formatDate(value?: string | null): string {
  if (!value) return 'N/A';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value || 'N/A';
  }
}

function EmailChangeCard() {
  const [profile, setProfile] = React.useState<ProfileSnapshot | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [message, setMessage] = React.useState<string | null>(null);
  const [emailInput, setEmailInput] = React.useState('');
  const [emailToken, setEmailToken] = React.useState('');
  const [requesting, setRequesting] = React.useState(false);
  const [confirming, setConfirming] = React.useState(false);
  const idempotencyHeader = useSettingsIdempotencyHeader();

  const loadProfile = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<ProfileSnapshot>('/v1/profile/me');
      setProfile(data);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load email settings'));
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  const limits = profile?.limits;
  const canChangeEmail = limits?.can_change_email ?? true;
  const nextEmailAt = limits?.next_email_change_at ? new Date(limits.next_email_change_at) : null;

  const emailHint = canChangeEmail
    ? EMAIL_LIMIT_HINT
    : nextEmailAt
        ? `Next change available after ${nextEmailAt.toLocaleString()}`
        : EMAIL_LIMIT_HINT;

  const disableEmailRequest =
    requesting ||
    !profile?.id ||
    !canChangeEmail ||
    !emailInput.trim() ||
    emailInput.trim().toLowerCase() === (profile?.email || '').toLowerCase();
  const disableConfirm = confirming || !emailToken.trim();

  const onRequestEmail = async (event: React.FormEvent) => {
    event.preventDefault();
    if (disableEmailRequest || !profile?.id) return;
    setRequesting(true);
    setMessage(null);
    setError(null);
    try {
      const headers: Record<string, string> = { [idempotencyHeader]: makeIdempotencyKey() };
      const result = await apiPost('/v1/profile/me/email/request-change', { email: emailInput.trim() }, { headers });
      const token = typeof (result as any)?.token === 'string' ? (result as any).token : null;
      setMessage(token ? `Confirmation email requested. Token: ${token}` : 'Confirmation email requested. Check your inbox.');
      setEmailToken('');
      await loadProfile();
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to request email change'));
    } finally {
      setRequesting(false);
    }
  };

  const onConfirmEmail = async (event: React.FormEvent) => {
    event.preventDefault();
    if (disableConfirm || !profile?.id) return;
    setConfirming(true);
    setMessage(null);
    setError(null);
    try {
      await apiPost('/v1/profile/me/email/confirm', { token: emailToken.trim() });
      setMessage('Email updated successfully.');
      setEmailToken('');
      setEmailInput('');
      await loadProfile();
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to confirm email'));
    } finally {
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <Card className="flex items-center gap-2 rounded-3xl border border-white/60 bg-white/80 p-6 text-sm text-gray-500 shadow-sm">
        <Spinner size="sm" /> Loading email settings...
      </Card>
    );
  }

  return (
    <Card className="flex flex-col gap-6 rounded-3xl border border-white/60 bg-white/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Change email</h2>
          <p className="text-xs text-gray-500">We’ll send a confirmation token before updating your primary address.</p>
        </div>
        <Badge color="warning" variant="soft">Sensitive</Badge>
      </div>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</div>
      )}
      {message && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">{message}</div>
      )}

      <form onSubmit={onRequestEmail} className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
        <div className="space-y-2">
          <Input
            label="New email"
            value={emailInput}
            onChange={(event) => setEmailInput(event.target.value)}
            disabled={disableEmailRequest}
            hint={emailHint}
          />
          {profile?.pending_email && (
            <div className="flex items-center gap-2 text-xs text-amber-700">
              <Badge color="info" variant="soft">Pending</Badge>
              <span>Waiting for confirmation: {profile.pending_email}</span>
            </div>
          )}
        </div>
        <Button type="submit" variant="outlined" color="primary" disabled={disableEmailRequest}>
          {requesting ? 'Requesting...' : 'Request change'}
        </Button>
      </form>

      <form onSubmit={onConfirmEmail} className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
        <Input
          label="Confirmation token"
          value={emailToken}
          onChange={(event) => setEmailToken(event.target.value)}
          placeholder="Paste token from email"
          disabled={disableConfirm || !profile?.pending_email}
        />
        <Button type="submit" variant="ghost" color="primary" disabled={disableConfirm}>
          {confirming ? 'Confirming...' : 'Confirm email'}
        </Button>
      </form>
    </Card>
  );
}

function SessionsCard() {
  const [sessions, setSessions] = React.useState<SessionRecord[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [password, setPassword] = React.useState('');
  const [keepSessionId, setKeepSessionId] = React.useState<string>('none');
  const [reason, setReason] = React.useState('');
  const idempotencyHeader = useSettingsIdempotencyHeader();

  const loadSessions = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<any>('/v1/me/settings/security/sessions');
      const list: SessionRecord[] = Array.isArray(response?.sessions)
        ? response.sessions
        : Array.isArray(response?.data)
            ? response.data
            : [];
      setSessions(list);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load sessions'));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  const handleRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await loadSessions();
    setRefreshing(false);
  }, [loadSessions]);

  const handleTerminate = React.useCallback(
    async (sessionId: string) => {
      if (busy) return;
      setBusy(true);
      setError(null);
      setStatus(null);
      try {
        const headers: Record<string, string> = { [idempotencyHeader]: makeIdempotencyKey() };
        await apiPost(`/v1/me/settings/security/sessions/${sessionId}/terminate`, { reason: null }, { headers });
        setStatus('Session signed out successfully.');
        await loadSessions();
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to sign out session'));
      } finally {
        setBusy(false);
      }
    },
    [busy, idempotencyHeader, loadSessions],
  );

  const handleTerminateOthers = React.useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      if (busy) return;
      if (!password.trim()) {
        setError('Enter your password to sign out other sessions.');
        return;
      }
      setBusy(true);
      setError(null);
      setStatus(null);
      try {
        const headers: Record<string, string> = { [idempotencyHeader]: makeIdempotencyKey() };
        const payload = {
          password: password.trim(),
          keep_session_id: keepSessionId === 'none' ? null : keepSessionId,
          reason: reason.trim() || null,
        };
        await apiPost('/v1/me/settings/security/sessions/terminate-others', payload, { headers });
        setStatus('Other sessions signed out.');
        setPassword('');
        setReason('');
        setKeepSessionId('none');
        await loadSessions();
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to sign out other sessions'));
      } finally {
        setBusy(false);
      }
    },
    [busy, idempotencyHeader, keepSessionId, loadSessions, password, reason],
  );

  const activeSessions = sessions.filter((session) => session.active !== false);
  const hasSessions = sessions.length > 0;

  return (
    <Card className="space-y-6 rounded-3xl border border-white/60 bg-white/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Active sessions</h2>
          <p className="text-xs text-gray-500">Track signed-in devices and sign out sessions remotely.</p>
        </div>
        <Button type="button" size="sm" variant="ghost" color="neutral" onClick={handleRefresh} disabled={refreshing || loading}>
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</div>
      )}
      {status && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">{status}</div>
      )}

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Spinner size="sm" /> Loading sessions...
        </div>
      ) : hasSessions ? (
        <div className="space-y-3">
          {sessions.map((session) => {
            const isActive = session.active !== false && !session.revoked_at;
            return (
              <div key={session.id} className="space-y-3 rounded-2xl border border-white/60 bg-white/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-col gap-1 text-sm text-gray-700">
                    <span className="font-medium text-gray-900">{session.ip || 'Unknown location'}</span>
                    <span className="text-xs text-gray-500">{session.user_agent || 'Device unknown'}</span>
                  </div>
                  <Badge color={isActive ? 'success' : 'neutral'} variant="soft">
                    {isActive ? 'Active' : 'Ended'}
                  </Badge>
                </div>
                <div className="grid gap-2 text-xs text-gray-500 sm:grid-cols-2">
                  <div>
                    <div className="font-semibold text-gray-600">Started</div>
                    <div>{formatDate(session.created_at)}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-600">Last used</div>
                    <div>{formatDate(session.last_used_at)}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-600">Expires</div>
                    <div>{formatDate(session.expires_at)}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-gray-600">Refresh expires</div>
                    <div>{formatDate(session.refresh_expires_at)}</div>
                  </div>
                </div>
                {isActive && (
                  <div className="flex flex-wrap justify-end">
                    <Button type="button" size="sm" variant="ghost" color="neutral" onClick={() => handleTerminate(session.id)} disabled={busy}>
                      Sign out session
                    </Button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-gray-200 bg-white/70 p-4 text-sm text-gray-500">
          No sessions found. You will see sessions here after logging in from other devices.
        </div>
      )}

      <form className="space-y-4 rounded-2xl border border-white/60 bg-white/70 p-4" onSubmit={handleTerminateOthers}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-gray-700">Sign out other sessions</h3>
          {activeSessions.length > 1 && <Badge color="warning" variant="soft">Multiple active sessions</Badge>}
        </div>
        <p className="text-xs text-gray-500">
          Enter your password to end other active sessions. Choose one session to keep if you want to stay signed in elsewhere.
        </p>
        <div className="grid gap-4 md:grid-cols-2">
          <Input
            type="password"
            label="Current password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            disabled={busy}
          />
          <Select
            label="Keep session"
            value={keepSessionId}
            onChange={(event) => setKeepSessionId(event.target.value)}
            disabled={busy || sessions.length === 0}
          >
            <option value="none">Sign out all sessions</option>
            {sessions.map((session) => (
              <option key={session.id} value={session.id}>
                {session.ip || 'Unknown'} - {formatDate(session.last_used_at)}
              </option>
            ))}
          </Select>
          <div className="md:col-span-2">
            <Input
              label="Reason (optional)"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Lost device, suspicious login, etc."
              disabled={busy}
            />
          </div>
        </div>
        <div className="flex justify-end">
          <Button type="submit" color="primary" disabled={busy || !password.trim()}>
            {busy ? 'Signing out...' : 'Sign out other sessions'}
          </Button>
        </div>
      </form>
    </Card>
  );
}

export default function SecuritySettingsPage() {
  const sidePanel = (
    <>
      <WalletConnectionCard />
      <Card className="space-y-3 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700">Security checklist</h2>
        <div className="space-y-2 text-sm text-gray-600">
          <p>Enable unique passwords, connect a trusted wallet and monitor active sessions for unusual activity.</p>
          <p className="text-xs text-gray-500">Need help? Contact support if you notice unfamiliar devices or sign-ins.</p>
        </div>
      </Card>
    </>
  );

  return (
    <SettingsLayout
      title="Security"
      description="Protect your account with strong credentials and visibility into active sessions."
      side={sidePanel}
    >
      <div className="flex flex-col gap-6">
        <EmailChangeCard />
        <SecurityCard id="security-password" />
        <SessionsCard />
      </div>
    </SettingsLayout>
  );
}
