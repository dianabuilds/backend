import React from 'react';
import { Card, PageHero } from '@ui';

export default function NotificationsInboxPage(): React.ReactElement {
  return (
    <div className="space-y-6">
      <PageHero
        title="Notifications Inbox"
        description="Страница пользовательских уведомлений будет перенесена после стабилизации shared/api."
        variant="compact"
        tone="light"
        align="start"
        className="bg-white/95 shadow-sm ring-1 ring-gray-200/80 dark:bg-dark-850/85 dark:ring-dark-600/60"
      />
      <Card className="p-6 text-sm text-gray-500 dark:text-gray-300">
        TODO: вернуть список уведомлений и настройки inbox.
      </Card>
    </div>
  );
}
