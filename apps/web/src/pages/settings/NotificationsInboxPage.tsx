import React from 'react';
import { PageHero } from '@ui';
import { NotificationInbox } from '@features/notifications/inbox';

export default function NotificationsInboxPage(): React.ReactElement {
  return (
    <div className="space-y-6">
      <PageHero
        title="Notifications Inbox"
        description="Просматривайте и управляйте личными уведомлениями, не покидая раздел настроек."
        variant="compact"
        tone="light"
        align="start"
        className="bg-white/95 shadow-sm ring-1 ring-gray-200/80 dark:bg-dark-850/85 dark:ring-dark-600/60"
      />
      <NotificationInbox />
    </div>
  );
}
