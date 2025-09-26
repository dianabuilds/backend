import React from 'react';
import { Button, Card, Input, Textarea, Select } from '@ui';
import { apiGet, apiPost } from '../../shared/api/client';
import { extractErrorMessage } from '../../shared/utils/errors';

type ChannelOption = 'webhook' | 'email';

type WebhookField = {
  id: number;
  key: string;
  value: string;
};

type EmailFormState = {
  to: string;
  subject: string;
  text: string;
  html: string;
};

const CHANNEL_OPTIONS: Array<{ value: ChannelOption; label: string; hint: string }> = [
  {
    value: 'webhook',
    label: 'Webhook',
    hint: 'Send a JSON payload to the configured webhook URL (useful for integrations and QA).',
  },
  {
    value: 'email',
    label: 'Email',
    hint: 'Queue a transactional email via the notifications service (SMTP mock or real server).',
  },
];

const INITIAL_WEBHOOK_FIELDS: WebhookField[] = [
  { id: 1, key: 'event', value: 'demo.notification' },
  { id: 2, key: 'message', value: 'Hello from Caves notifications!' },
];

const INITIAL_EMAIL_FORM: EmailFormState = {
  to: '',
  subject: 'Test notification',
  text: 'Hello from Caves!',
  html: '',
};

function coercePrimitive(value: string): unknown {
  const trimmed = value.trim();
  if (!trimmed) return '';
  if (/^(true|false)$/i.test(trimmed)) {
    return trimmed.toLowerCase() === 'true';
  }
  if (/^-?\d+(?:\.\d+)?$/.test(trimmed)) {
    const num = Number(trimmed);
    if (!Number.isNaN(num)) return num;
  }
  if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
    try {
      return JSON.parse(trimmed);
    } catch (error) {
      // Fall through to raw string if parsing fails.
    }
  }
  return value;
}

function recipientsFromInput(input: string): string[] {
  return input
    .split(/[,\n\r\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function ManagementIntegrations(): JSX.Element {
  const [config, setConfig] = React.useState<any>(null);
  const [channel, setChannel] = React.useState<ChannelOption>('webhook');
  const [webhookFields, setWebhookFields] = React.useState<WebhookField[]>(INITIAL_WEBHOOK_FIELDS);
  const [emailForm, setEmailForm] = React.useState<EmailFormState>(INITIAL_EMAIL_FORM);
  const nextWebhookFieldId = React.useRef<number>(INITIAL_WEBHOOK_FIELDS.length + 1);
  const [sending, setSending] = React.useState(false);
  const [flash, setFlash] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    (async () => {
      try {
        const c = await apiGet('/v1/admin/config');
        setConfig(c);
      } catch {
        setConfig(null);
      }
    })();
  }, []);

  const buildWebhookPayload = React.useCallback((): Record<string, unknown> => {
    const payload: Record<string, unknown> = {};
    webhookFields.forEach(({ key, value }) => {
      const trimmedKey = key.trim();
      if (!trimmedKey) return;
      payload[trimmedKey] = coercePrimitive(value);
    });
    return payload;
  }, [webhookFields]);

  const buildEmailPayload = React.useCallback(() => {
    const toList = recipientsFromInput(emailForm.to);
    const payload: Record<string, unknown> = {
      to: toList,
      subject: emailForm.subject,
      text: emailForm.text,
    };
    if (emailForm.html.trim()) {
      payload.html = emailForm.html;
    }
    return { payload, toList };
  }, [emailForm]);

  const payloadPreview = React.useMemo(() => {
    if (channel === 'webhook') {
      return buildWebhookPayload();
    }
    const { payload } = buildEmailPayload();
    return payload;
  }, [channel, buildWebhookPayload, buildEmailPayload]);

  const canSend = React.useMemo(() => {
    if (channel === 'webhook') {
      return webhookFields.some((field) => field.key.trim());
    }
    return recipientsFromInput(emailForm.to).length > 0;
  }, [channel, emailForm.to, webhookFields]);

  const updateWebhookField = (id: number, patch: Partial<WebhookField>) => {
    setWebhookFields((fields) =>
      fields.map((field) => (field.id === id ? { ...field, ...patch } : field)),
    );
  };

  const removeWebhookField = (id: number) => {
    setWebhookFields((fields) => {
      if (fields.length === 1) return fields;
      return fields.filter((field) => field.id !== id);
    });
  };

  const addWebhookField = () => {
    setWebhookFields((fields) => [
      ...fields,
      { id: nextWebhookFieldId.current++, key: '', value: '' },
    ]);
  };

  const resetForms = () => {
    setWebhookFields(INITIAL_WEBHOOK_FIELDS);
    setEmailForm(INITIAL_EMAIL_FORM);
  };

  const sendNotification = async () => {
    if (!canSend || sending) return;
    setSending(true);
    setFlash(null);
    setError(null);
    try {
      if (channel === 'webhook') {
        const payload = buildWebhookPayload();
        if (Object.keys(payload).length === 0) {
          setError('Add at least one field to the webhook payload.');
          return;
        }
        await apiPost('/v1/notifications/send', { channel: 'webhook', payload });
        setFlash('Webhook notification sent. Check logs or your endpoint.');
      } else {
        const { payload, toList } = buildEmailPayload();
        if (toList.length === 0) {
          setError('Add at least one recipient.');
          return;
        }
        await apiPost('/v1/notifications/send', { channel: 'email', payload });
        setFlash('Email notification queued.');
      }
    } catch (err) {
      setError(extractErrorMessage(err) || 'Failed to send notification.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <Card>
        <div className="space-y-2 p-4">
          <div className="text-sm font-medium">Current configuration</div>
          <pre className="rounded bg-gray-50 p-3 text-xs">{JSON.stringify(config || {}, null, 2)}</pre>
        </div>
      </Card>

      <Card>
        <div className="space-y-6 p-4">
          <div className="space-y-1">
            <div className="text-sm font-semibold text-gray-900">Send a test notification</div>
            <p className="text-xs text-gray-500">
              Pick a channel and fill in the required fields — we will build the payload for you.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs font-medium uppercase tracking-wide text-gray-500">Channel</label>
              <Select value={channel} onChange={(event) => setChannel(event.currentTarget.value as ChannelOption)}>
                {CHANNEL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
              <p className="text-xs text-gray-500">{CHANNEL_OPTIONS.find((option) => option.value === channel)?.hint}</p>
            </div>
            <div className="flex items-end justify-end gap-2">
              <Button type="button" variant="ghost" color="neutral" onClick={resetForms}>
                Reset
              </Button>
            </div>
          </div>

          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600">
              {error}
            </div>
          )}
          {flash && (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
              {flash}
            </div>
          )}

          {channel === 'webhook' ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-gray-800">Webhook payload</div>
                <Button type="button" variant="ghost" onClick={addWebhookField}>
                  Add field
                </Button>
              </div>
              <div className="space-y-2">
                {webhookFields.map((field) => (
                  <div key={field.id} className="grid gap-2 sm:grid-cols-5">
                    <Input
                      className="sm:col-span-2"
                      placeholder="Key"
                      value={field.key}
                      onChange={(event) => updateWebhookField(field.id, { key: event.target.value })}
                    />
                    <Textarea
                      className="sm:col-span-3"
                      placeholder="Value"
                      rows={2}
                      value={field.value}
                      onChange={(event) => updateWebhookField(field.id, { value: event.target.value })}
                    />
                    <div className="sm:col-span-5 flex justify-end">
                      <Button
                        type="button"
                        variant="ghost"
                        color="neutral"
                        onClick={() => removeWebhookField(field.id)}
                        disabled={webhookFields.length === 1}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="sm:col-span-2 space-y-1">
                  <label className="text-xs font-medium uppercase tracking-wide text-gray-500">Recipients</label>
                  <Input
                    placeholder="user@example.com, second@example.com"
                    value={emailForm.to}
                    onChange={(event) => setEmailForm((prev) => ({ ...prev, to: event.target.value }))}
                  />
                  <p className="text-xs text-gray-500">
                    You can provide multiple addresses separated by commas or new lines.
                  </p>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium uppercase tracking-wide text-gray-500">Subject</label>
                  <Input
                    placeholder="Subject"
                    value={emailForm.subject}
                    onChange={(event) => setEmailForm((prev) => ({ ...prev, subject: event.target.value }))}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium uppercase tracking-wide text-gray-500">Plain text</label>
                  <Textarea
                    rows={3}
                    placeholder="Plain text"
                    value={emailForm.text}
                    onChange={(event) => setEmailForm((prev) => ({ ...prev, text: event.target.value }))}
                  />
                </div>
                <div className="sm:col-span-2 space-y-1">
                  <label className="text-xs font-medium uppercase tracking-wide text-gray-500">HTML (optional)</label>
                  <Textarea
                    rows={4}
                    placeholder="&lt;p&gt;Hello&lt;/p&gt;"
                    value={emailForm.html}
                    onChange={(event) => setEmailForm((prev) => ({ ...prev, html: event.target.value }))}
                  />
                </div>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <div className="text-xs font-medium uppercase tracking-wide text-gray-500">Payload preview</div>
            <pre className="rounded bg-gray-50 p-3 text-xs text-gray-700">{JSON.stringify(payloadPreview, null, 2)}</pre>
          </div>

          <div className="flex justify-end">
            <Button type="button" color="primary" onClick={sendNotification} disabled={!canSend || sending}>
              {sending ? 'Sending…' : 'Send notification'}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
