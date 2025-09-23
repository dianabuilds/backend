import React from 'react';
import { Button, Card, Input, Textarea } from '@ui';
import { apiGet, apiPost } from '../../shared/api/client';

export default function ManagementIntegrations() {
  const [config, setConfig] = React.useState<any>(null);
  const [whUrl, setWhUrl] = React.useState('');
  const [whPayload, setWhPayload] = React.useState('{"hello":"world"}');
  const [email, setEmail] = React.useState('');

  React.useEffect(() => {
    (async () => {
      try {
        const c = await apiGet('/v1/admin/config');
        setConfig(c);
      } catch {}
    })();
  }, []);

  const sendWebhook = async () => {
    let payload: any = {};
    try { payload = JSON.parse(whPayload || '{}'); } catch {}
    await apiPost('/v1/notifications/send', { channel: 'webhook', payload: payload || {} });
    alert('Webhook payload sent (see server logs/endpoint)');
  };

  const sendEmail = async () => {
    if (!email) return;
    await apiPost('/v1/notifications/send', { channel: 'email', payload: { to: [email], subject: 'Test email', text: 'Hello!' } });
    alert('Email notification queued (mock or SMTP)');
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <div className="p-4 space-y-2">
          <div className="text-sm font-medium">Current Config</div>
          <pre className="rounded bg-gray-50 p-3 text-xs">{JSON.stringify(config || {}, null, 2)}</pre>
        </div>
      </Card>
      <Card>
        <div className="p-4 space-y-2">
          <div className="text-sm font-medium">Webhook test</div>
          <div className="grid grid-cols-2 gap-2">
            <Input placeholder="Use configured URL (optional)" value={whUrl} onChange={(e) => setWhUrl(e.target.value)} />
            <div />
          </div>
          <Textarea placeholder="Payload JSON" value={whPayload} onChange={(e) => setWhPayload(e.target.value)} />
          <Button onClick={sendWebhook}>Send webhook</Button>
        </div>
      </Card>
      <Card>
        <div className="p-4 space-y-2">
          <div className="text-sm font-medium">Email test</div>
          <div className="flex gap-2">
            <Input placeholder="to@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            <Button onClick={sendEmail} disabled={!email}>Send email</Button>
          </div>
          <div className="text-xs text-gray-500">SMTP mock may log instead of sending depending on server config.</div>
        </div>
      </Card>
    </div>
  );
}


