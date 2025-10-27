import React from 'react';
import { Badge, Button, Card, Input, Select, Spinner, Textarea } from '@ui';
import { fetchIntegrationsOverview, fetchManagementConfig, sendNotificationTest } from '@shared/api/management';
import type { IntegrationItem as IntegrationItemModel, IntegrationOverview as IntegrationOverviewModel, ManagementConfig, NotificationTestChannel } from '@shared/types/management';
import { extractErrorMessage } from '@shared/utils/errors';
import { PlatformAdminFrame } from '@shared/layouts/management';

type ChannelOption = NotificationTestChannel;

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

type IntegrationItem = IntegrationItemModel;

type IntegrationOverview = IntegrationOverviewModel;

type ChannelCardModel = {
  id: string;
  label: string;
  statusLabel: string;
  statusColor: 'success' | 'warning' | 'error' | 'neutral';
  statusDescription?: string;
  description: string;
  usage: string[];
  details: Array<{ label: string; value: string }>;
  hint?: string;
};

type ConfigResponse = ManagementConfig;

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
    } catch {
      // keep raw string when parsing fails
    }
  }
  return value;
}

function recipientsFromInput(input: string): string[] {
  return input
    .split(/[\s,]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatTopics(topics: string[]): string {
  if (!topics.length) return '-';
  if (topics.length <= 3) return topics.join(', ');
  return `${topics.slice(0, 3).join(', ')} +${topics.length - 3}`;
}

function formatSeconds(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return '-';
  if (value % 3600 === 0) return `${value / 3600} h`;
  if (value % 60 === 0) return `${value / 60} min`;
  return `${value} s`;
}

function combineMailFrom(name?: string | null, address?: string | null): string {
  const trimmedName = name?.trim();
  const trimmedAddress = address?.trim();
  if (trimmedName && trimmedAddress) return `${trimmedName} <${trimmedAddress}>`;
  if (trimmedAddress) return trimmedAddress;
  if (trimmedName) return trimmedName;
  return '-';
}

function formatTimestamp(value?: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString();
}

export default function ManagementIntegrations(): JSX.Element {
  const [channel, setChannel] = React.useState<ChannelOption>('webhook');
  const [webhookFields, setWebhookFields] = React.useState<WebhookField[]>(INITIAL_WEBHOOK_FIELDS);
  const [emailForm, setEmailForm] = React.useState<EmailFormState>(INITIAL_EMAIL_FORM);
  const nextWebhookFieldId = React.useRef<number>(INITIAL_WEBHOOK_FIELDS.length + 1);
  const [sending, setSending] = React.useState(false);
  const [flash, setFlash] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [overview, setOverview] = React.useState<IntegrationOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = React.useState(true);
  const [overviewError, setOverviewError] = React.useState<string | null>(null);
  const [config, setConfig] = React.useState<ConfigResponse | null>(null);
  const [configLoading, setConfigLoading] = React.useState(true);
  const [configError, setConfigError] = React.useState<string | null>(null);
  const [configExpanded, setConfigExpanded] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;

    const fetchOverview = async () => {
      setOverviewLoading(true);
      setOverviewError(null);
      try {
        const payload = await fetchIntegrationsOverview();
        if (!cancelled) {
          setOverview(payload);
        }
      } catch (err) {
        if (!cancelled) {
          setOverview(null);
          setOverviewError(extractErrorMessage(err) || 'Failed to load integration overview.');
        }
      } finally {
        if (!cancelled) {
          setOverviewLoading(false);
        }
      }
    };

    const fetchConfig = async () => {
      setConfigLoading(true);
      setConfigError(null);
      try {
        const payload = await fetchManagementConfig();
        if (!cancelled) {
          setConfig(payload);
        }
      } catch (err) {
        if (!cancelled) {
          setConfig(null);
          setConfigError(extractErrorMessage(err) || 'Failed to load configuration.');
        }
      } finally {
        if (!cancelled) {
          setConfigLoading(false);
        }
      }
    };

    fetchOverview();
    fetchConfig();

    return () => {
      cancelled = true;
    };
  }, []);

  const integrationMap = React.useMemo(() => {
    const map = new Map<string, IntegrationItem>();
    (overview?.items || []).forEach((item) => {
      map.set(item.id, item);
    });
    return map;
  }, [overview]);

  const channelCards = React.useMemo(() => buildChannelCards(integrationMap), [integrationMap]);
  const collectedAt = React.useMemo(() => formatTimestamp(overview?.collected_at), [overview?.collected_at]);

  const stats = React.useMemo(() => {
    const total = channelCards.length;
    const healthy = channelCards.filter((card) => card.statusColor === 'success').length;
    const warning = channelCards.filter((card) => card.statusColor === 'warning').length;
    return [
      {
        id: 'integrations-total',
        label: 'Channels',
        value: String(total),
        trend: total > 0 ? `${healthy} healthy` : 'No data',
      },
      {
        id: 'integrations-warning',
        label: 'Need attention',
        value: String(warning),
        trend: warning > 0 ? 'Review configuration' : 'All clear',
      },
      {
        id: 'integrations-refreshed',
        label: 'Last updated',
        value: collectedAt || 'Not available',
      },
    ];
  }, [channelCards, collectedAt]);

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
    setWebhookFields((fields) => fields.map((field) => (field.id === id ? { ...field, ...patch } : field)));
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
    setFlash(null);
    setError(null);
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
        await sendNotificationTest('webhook', payload);
        setFlash('Webhook sent. Check the service logs or your endpoint.');
      } else {
        const { payload, toList } = buildEmailPayload();
        if (toList.length === 0) {
          setError('Add at least one recipient.');
          return;
        }
        await sendNotificationTest('email', payload);
        setFlash('Email queued.');
      }
    } catch (err) {
      setError(extractErrorMessage(err) || 'Failed to send notification.');
    } finally {
      setSending(false);
    }
  };

  const selectedCard = React.useMemo(() => {
    if (channel === 'webhook') return channelCards.find((card) => card.id === 'webhook') || null;
    return channelCards.find((card) => card.id === 'email') || null;
  }, [channel, channelCards]);

  const overviewEmpty = !overviewLoading && channelCards.length === 0 && !overviewError;

  return (
    <PlatformAdminFrame
      title="Integrations"
      description="Monitor external notification channels and run manual checks before incidents escalate."
      breadcrumbs={[{ label: 'Platform', to: '/platform/system' }, { label: 'Integrations' }]}
      stats={stats}
      heroVariant="compact"
      heroClassName="sm:px-6 sm:py-6"
    >
      <div className="space-y-6">
        <Card className="space-y-4 p-6 bg-white shadow-sm dark:bg-dark-800">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-white">Channel status</h2>
              <p className="text-sm text-gray-600 dark:text-dark-100">
                Review the health of each integration and confirm that live alerts are leaving the platform.
              </p>
            </div>
            <Button type="button" variant="outlined" color="neutral" onClick={() => setConfigExpanded((prev) => !prev)}>
              {configExpanded ? 'Hide configuration' : 'Show configuration'}
            </Button>
          </div>

          {configExpanded ? (
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-xs text-gray-700 dark:border-dark-600 dark:bg-dark-800 dark:text-dark-50">
              {configLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-dark-200">
                  <Spinner size="sm" /> Loading configuration...
                </div>
              ) : configError ? (
                <div className="text-sm text-rose-600 dark:text-rose-300">{configError}</div>
              ) : (
                <pre className="whitespace-pre-wrap break-all">{JSON.stringify(config ?? {}, null, 2)}</pre>
              )}
            </div>
          ) : null}

          {overviewLoading ? (
            <div className="flex h-32 items-center justify-center"><Spinner /></div>
          ) : overviewError ? (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-600 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200">
              {overviewError}
            </div>
          ) : overviewEmpty ? (
            <div className="rounded-lg border border-dashed border-gray-200 p-5 text-sm text-gray-600 dark:border-dark-600 dark:text-dark-200">
              No integrations reported yet. Configure webhook or SMTP credentials and refresh the page.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {channelCards.map((card) => (
                <ChannelCard key={card.id} channel={card} />
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-4 p-5 bg-white shadow-sm dark:bg-dark-800">
          <div className="grid gap-4 lg:grid-cols-[1.8fr,1fr]">
            <div className="space-y-3">
              <div>
                <h2 className="text-base font-semibold text-gray-900 dark:text-white">Manual channel test</h2>
                <p className="text-sm text-gray-600 dark:text-dark-100">
                  Send a sample message to validate a channel before relying on it during incidents.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3 rounded-xl border border-gray-200/70 bg-gray-50/80 p-3 text-xs text-gray-600 dark:border-dark-700 dark:bg-dark-800/60 dark:text-dark-200">
                <div className="flex flex-col gap-1">
                  <span className="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Channel</span>
                  <Select
                    value={channel}
                    onChange={(event) => setChannel(event.currentTarget.value as ChannelOption)}
                    className="h-9 w-44"
                  >
                    <option value="webhook">Webhook</option>
                    <option value="email">Email</option>
                  </Select>
                </div>
                <div className="flex min-w-[200px] flex-1 flex-col gap-1 text-xs leading-relaxed">
                  <div className="flex flex-wrap items-center gap-2">
                    {selectedCard ? (
                      <Badge color={selectedCard.statusColor} variant="soft">
                        {selectedCard.statusLabel}
                      </Badge>
                    ) : null}
                    <span>
                      {channel === 'webhook'
                        ? 'JSON payload will be delivered to subscribed webhooks.'
                        : 'Email will be queued via SMTP or mock logger.'}
                    </span>
                  </div>
                  {selectedCard?.statusDescription ? (
                    <span className="text-gray-500 dark:text-dark-300">Status: {selectedCard.statusDescription}</span>
                  ) : null}
                </div>
              </div>
            </div>
            <div className="flex flex-col items-start justify-between gap-2 lg:items-end">
              <Button type="button" variant="ghost" color="neutral" size="sm" onClick={resetForms}>
                Reset
              </Button>
              <Button type="button" color="primary" onClick={sendNotification} disabled={!canSend || sending}>
                {sending ? 'Sending...' : 'Send test'}
              </Button>
            </div>
          </div>

          {error ? (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
              {error}
            </div>
          ) : null}
          {flash ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200">
              {flash}
            </div>
          ) : null}

          {channel === 'webhook' ? (
            <div className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-sm font-medium text-gray-800 dark:text-dark-50">Webhook payload</div>
                <Button type="button" variant="ghost" size="sm" onClick={addWebhookField}>
                  Add field
                </Button>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {webhookFields.map((field) => (
                  <div key={field.id} className="rounded-xl border border-gray-200/60 bg-white/80 p-3 dark:border-dark-600 dark:bg-dark-800/60">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-dark-300">Key</span>
                      <Button
                        type="button"
                        variant="ghost"
                        color="neutral"
                        size="sm"
                        onClick={() => removeWebhookField(field.id)}
                        disabled={webhookFields.length === 1}
                        className="!px-2 !py-1"
                      >
                        Remove
                      </Button>
                    </div>
                    <Input
                      className="mt-1"
                      placeholder="event"
                      value={field.key}
                      onChange={(event) => updateWebhookField(field.id, { key: event.target.value })}
                    />
                    <span className="mt-3 block text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-dark-300">
                      Value
                    </span>
                    <Textarea
                      rows={2}
                      placeholder="Value"
                      value={field.value}
                      onChange={(event) => updateWebhookField(field.id, { value: event.target.value })}
                    />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="sm:col-span-2 space-y-1">
                  <label className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-dark-300">Recipients</label>
                  <Input
                    placeholder="user@example.com, second@example.com"
                    value={emailForm.to}
                    onChange={(event) => setEmailForm((prev) => ({ ...prev, to: event.target.value }))}
                  />
                  <p className="text-xs text-gray-500 dark:text-dark-200">Provide comma or newline separated addresses.</p>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-dark-300">Subject</label>
                  <Input
                    placeholder="Subject"
                    value={emailForm.subject}
                    onChange={(event) => setEmailForm((prev) => ({ ...prev, subject: event.target.value }))}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-dark-300">Plain text</label>
                  <Textarea
                    rows={3}
                    placeholder="Plain text"
                    value={emailForm.text}
                    onChange={(event) => setEmailForm((prev) => ({ ...prev, text: event.target.value }))}
                  />
                </div>
                <div className="sm:col-span-2 space-y-1">
                  <label className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-dark-300">HTML (optional)</label>
                  <Textarea
                    rows={3}
                    placeholder="<p>Hello</p>"
                    value={emailForm.html}
                    onChange={(event) => setEmailForm((prev) => ({ ...prev, html: event.target.value }))}
                  />
                </div>
              </div>
            </div>
          )}

          <div className="space-y-1.5">
            <div className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-dark-300">Payload preview</div>
            <pre className="rounded bg-gray-50 p-3 text-xs text-gray-700 dark:bg-dark-800 dark:text-dark-50">{JSON.stringify(payloadPreview, null, 2)}</pre>
          </div>
        </Card>
      </div>
    </PlatformAdminFrame>
  );
}

type ChannelCardProps = {
  channel: ChannelCardModel;
};

function ChannelCard({ channel }: ChannelCardProps) {
  return (
    <Card className="flex h-full flex-col gap-3 p-4 bg-white/90 shadow-sm backdrop-blur-sm dark:bg-dark-800/90">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="text-sm font-semibold text-gray-900 dark:text-white">{channel.label}</div>
          <p className="text-sm leading-relaxed text-gray-600 dark:text-dark-100">{channel.description}</p>
        </div>
        <Badge color={channel.statusColor} variant="soft">
          {channel.statusLabel}
        </Badge>
      </div>
      {channel.statusDescription ? (
        <p className="text-xs text-gray-500 dark:text-dark-200">{channel.statusDescription}</p>
      ) : null}
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Use cases</div>
          <ul className="space-y-1 text-xs text-gray-600 dark:text-dark-100">
            {channel.usage.map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </div>
        {channel.details.length ? (
          <div className="space-y-1.5">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Technical details</div>
            <dl className="space-y-1 text-xs text-gray-600 dark:text-dark-100">
              {channel.details.map((detail) => (
                <div key={detail.label} className="flex items-center justify-between gap-2">
                  <dt className="text-gray-500 dark:text-dark-300">{detail.label}</dt>
                  <dd className="text-gray-900 dark:text-white">{detail.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        ) : null}
      </div>
      {channel.hint ? <p className="text-xs text-gray-500 dark:text-dark-200">{channel.hint}</p> : null}
    </Card>
  );
}

function buildChannelCards(items: Map<string, IntegrationItem>): ChannelCardModel[] {
  const slack = items.get('slack');
  const webhook = items.get('webhook');
  const email = items.get('email');

  const slackTopics = slack?.topics && slack.topics.length ? slack.topics : webhook?.topics || [];
  const slackConnected = Boolean(slack?.status === 'connected' || slack?.connected);
  const slackCard: ChannelCardModel = {
    id: 'slack',
    label: 'Slack',
    statusLabel: slackConnected ? 'Connected' : 'Disconnected',
    statusColor: slackConnected ? 'success' : 'error',
    statusDescription: slackConnected
      ? 'Incoming webhook active - events are mirrored into Slack.'
      : 'Webhook not configured; Slack alerts are not delivered.',
    description: 'Forwards critical platform incidents to the corporate Slack.',
    usage: [
      'On-call and SRE alerts',
      'Incident escalation from Platform Admin',
      'Instant alerts about service degradation',
    ],
    details: [
      { label: 'Event topics', value: slackTopics.length ? formatTopics(slackTopics) : 'Uses APP_EVENT_TOPICS' },
      { label: 'Delivery type', value: 'Slack incoming webhook' },
    ],
    hint: slackConnected
      ? 'APP_NOTIFY_WEBHOOK_URL is set. Watch the #platform-admin channel.'
      : 'Set APP_NOTIFY_WEBHOOK_URL with an incoming webhook to enable delivery.',
  };

  const webhookTopics = webhook?.topics && webhook.topics.length ? webhook.topics : slackTopics;
  const webhookReady = webhookTopics.length > 0 || webhook?.status === 'ready';
  const webhookCard: ChannelCardModel = {
    id: 'webhook',
    label: 'Webhook',
    statusLabel: webhookReady ? 'Ready' : 'Needs setup',
    statusColor: webhookReady ? 'success' : 'warning',
    statusDescription: webhookReady
      ? 'Registered webhooks receive JSON from /v1/notifications/send.'
      : 'Add at least one topic before the platform can publish events.',
    description: 'Delivers structured JSON events to internal and external HTTP endpoints.',
    usage: [
      'Platform incidents such as PagerDuty or Opsgenie',
      'Automation for internal tools and workflows',
      'QA staging and integration tests',
    ],
    details: [
      { label: 'Delivery topics', value: webhookTopics.length ? formatTopics(webhookTopics) : '-' },
      { label: 'Consumer group', value: webhook?.event_group ? String(webhook.event_group) : '-' },
      { label: 'Idempotency TTL', value: formatSeconds(webhook?.idempotency_ttl) },
    ],
    hint: 'Endpoint /v1/notifications/send accepts JSON payloads. Manage topics via APP_NOTIFY_TOPICS or APP_EVENT_TOPICS.',
  };

  const emailStatus = email?.status ?? 'unknown';
  let emailStatusLabel = 'Unknown';
  let emailStatusColor: 'success' | 'warning' | 'error' | 'neutral' = 'neutral';
  let emailStatusDescription = 'No SMTP configuration found.';
  let emailHint = 'Provide APP_SMTP_HOST, port, and credentials to send via SMTP.';
  if (emailStatus === 'connected') {
    emailStatusLabel = 'Connected';
    emailStatusColor = 'success';
    emailStatusDescription = 'SMTP is configured - emails are delivered through the external server.';
    emailHint = 'Monitor SMTP provider limits and error logs.';
  } else if (emailStatus === 'sandbox') {
    emailStatusLabel = 'Sandbox';
    emailStatusColor = 'warning';
    emailStatusDescription = 'Mock mode enabled - emails are logged only.';
    emailHint = 'Disable APP_SMTP_MOCK and set SMTP_HOST to send real emails.';
  } else if (emailStatus === 'disconnected') {
    emailStatusLabel = 'Disconnected';
    emailStatusColor = 'error';
    emailStatusDescription = 'SMTP host is not configured - emails will not be delivered.';
    emailHint = 'Populate APP_SMTP_HOST, port, and credentials, then restart the service.';
  }

  const emailCard: ChannelCardModel = {
    id: 'email',
    label: 'Email',
    statusLabel: emailStatusLabel,
    statusColor: emailStatusColor,
    statusDescription: emailStatusDescription,
    description: 'Transactional emails and alerts for users and administrators via SMTP or mock mode.',
    usage: [
      'Billing and subscription notifications',
      'Administrator alerts about critical events',
      'Backup communication channel when the app is unavailable',
    ],
    details: [
      { label: 'SMTP host', value: email?.smtp_host ? String(email.smtp_host) : '-' },
      { label: 'SMTP port', value: email?.smtp_port != null ? String(email.smtp_port) : '-' },
      { label: 'TLS', value: email?.smtp_tls === true ? 'Enabled' : email?.smtp_tls === false ? 'Disabled' : '-' },
      { label: 'Mock mode', value: email?.smtp_mock === true ? 'Yes' : email?.smtp_mock === false ? 'No' : '-' },
      { label: 'Sender', value: combineMailFrom(email?.mail_from_name, email?.mail_from) },
    ],
    hint: emailHint,
  };

  return [slackCard, webhookCard, emailCard];
}
