import React from 'react';
import { Card, Checkbox, Button } from '../../shared/ui';

function useLocalBool(key: string, initial = true) {
  const [v, setV] = React.useState<boolean>(() => {
    const s = localStorage.getItem(key);
    return s == null ? initial : s === '1';
  });
  React.useEffect(() => { localStorage.setItem(key, v ? '1' : '0'); }, [key, v]);
  return [v, setV] as const;
}

export default function NotificationSettingsPage() {
  const [email, setEmail] = useLocalBool('notif_email', true);
  const [inbox, setInbox] = useLocalBool('notif_inbox', true);
  const [push, setPush] = useLocalBool('notif_push', false);

  return (
    <div className="grid gap-4">
      <h1 className="text-xl font-semibold text-gray-700">Notification Settings</h1>
      <Card className="p-5 max-w-xl space-y-3">
        <Checkbox label="Inbox notifications" checked={inbox} onChange={(e) => setInbox(e.currentTarget.checked)} />
        <Checkbox label="Email notifications" checked={email} onChange={(e) => setEmail(e.currentTarget.checked)} />
        <Checkbox label="Push notifications" checked={push} onChange={(e) => setPush(e.currentTarget.checked)} />
        <div className="text-xs text-gray-500">Note: persistence API is not available yet; settings are stored locally.</div>
        <Button color="primary">Save</Button>
      </Card>
    </div>
  );
}

