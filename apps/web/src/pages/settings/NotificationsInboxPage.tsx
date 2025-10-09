import React from 'react';
import { Card, PageHeader } from '@ui';

export default function NotificationsInboxPage(): React.ReactElement {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Notifications Inbox"
        description="Страница пользовательских уведомлений будет перенесена после стабилизации shared/api."
      />
      <Card className="p-6 text-sm text-gray-500 dark:text-gray-300">
        TODO: вернуть список уведомлений и настройки inbox.
      </Card>
    </div>
  );
}
