import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { NotificationHistory } from '../../features/notifications';

export default function HistoryPage(): React.ReactElement {
  return (
    <ContentLayout
      context="notifications"
      title="Delivery history"
      description="Review delivery logs, reruns, and channel performance for past broadcasts."
    >
      <NotificationHistory />
    </ContentLayout>
  );
}
