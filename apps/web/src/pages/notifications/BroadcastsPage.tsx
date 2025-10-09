import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { NotificationBroadcasts } from '../../features/notifications/broadcasts';

export default function NotificationsBroadcastsPage(): React.ReactElement {
  return (
    <ContentLayout
      context="notifications"
      title="Broadcasts"
      description="Plan announcements, hand off targeting to the platform, and keep delivery in sync with your operators."
    >
      <NotificationBroadcasts />
    </ContentLayout>
  );
}
