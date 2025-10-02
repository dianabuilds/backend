import React from 'react';
import { Card, Input, Button, Badge } from "@ui";
import { apiPost } from '../api/client';
import { useSettingsIdempotencyHeader } from './';
import { extractErrorMessage } from '../utils/errors';
import { makeIdempotencyKey } from '../utils/idempotency';

type SecurityCardProps = {
  id?: string;
  className?: string;
  onPasswordChanged?: () => void;
};

export function SecurityCard({ id, className = '', onPasswordChanged }: SecurityCardProps) {
  const [form, setForm] = React.useState({ current: '', next: '', confirm: '' });
  const [saving, setSaving] = React.useState(false);
  const [message, setMessage] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const idempotencyHeader = useSettingsIdempotencyHeader();

  const resetForm = React.useCallback(() => {
    setForm({ current: '', next: '', confirm: '' });
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (saving) return;

    const current = form.current.trim();
    const next = form.next.trim();
    const confirm = form.confirm.trim();

    if (!current || !next || !confirm) {
      setError('Fill in all password fields.');
      setMessage(null);
      return;
    }
    if (next.length < 8) {
      setError('New password must be at least 8 characters long.');
      setMessage(null);
      return;
    }
    if (next !== confirm) {
      setError('New password and confirmation do not match.');
      setMessage(null);
      return;
    }

    setSaving(true);
    setError(null);
    setMessage(null);

    try {
      const headers: Record<string, string> = { [idempotencyHeader]: makeIdempotencyKey() };
      await apiPost(
        '/v1/profile/me/security/change-password',
        {
          current_password: current,
          new_password: next,
        },
        { headers },
      );
      setMessage('Password updated successfully.');
      resetForm();
      onPasswordChanged?.();
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to change password'));
    } finally {
      setSaving(false);
    }
  };

  const composedClassName = `space-y-6 rounded-3xl border border-white/60 bg-white/80 p-6 shadow-sm ${className}`.trim();

  return (
    <Card id={id} className={composedClassName}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-gray-700">Security</h2>
          <p className="text-xs text-gray-500">Update your password and keep your account protected.</p>
        </div>
        <Badge color="neutral" variant="soft">Security</Badge>
      </div>

      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </div>
      )}
      {message && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
          {message}
        </div>
      )}

      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Input
              type="password"
              label="Current password"
              autoComplete="current-password"
              value={form.current}
              onChange={(event) => setForm((prev) => ({ ...prev, current: event.target.value }))}
              disabled={saving}
            />
          </div>
          <div>
            <Input
              type="password"
              label="New password"
              autoComplete="new-password"
              value={form.next}
              onChange={(event) => setForm((prev) => ({ ...prev, next: event.target.value }))}
              disabled={saving}
              hint="Use at least 8 characters."
            />
          </div>
          <div className="md:col-start-2">
            <Input
              type="password"
              label="Confirm new password"
              autoComplete="new-password"
              value={form.confirm}
              onChange={(event) => setForm((prev) => ({ ...prev, confirm: event.target.value }))}
              disabled={saving}
            />
          </div>
        </div>

        <div className="flex flex-wrap justify-end gap-3">
          <Button
            type="button"
            variant="ghost"
            color="neutral"
            size="sm"
            onClick={resetForm}
            disabled={saving || (!form.current && !form.next && !form.confirm)}
          >
            Clear
          </Button>
          <Button type="submit" color="primary" disabled={saving || !form.current || !form.next || !form.confirm}>
            {saving ? 'Updating...' : 'Update password'}
          </Button>
        </div>
      </form>

      <p className="text-[11px] text-gray-400">
        Password updates will sign out sessions that fail verification. Remember to rotate API keys separately.
      </p>
    </Card>
  );
}
