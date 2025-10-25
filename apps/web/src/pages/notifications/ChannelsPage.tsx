import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { NotificationChannels } from '../../features/notifications';

export default function ChannelsPage(): React.ReactElement {
  return (
    <ContentLayout
      context="notifications"
      title="Delivery channels"
      description="Configure delivery touchpoints, monitor health, and keep cohorts reachable."
    >
      <NotificationChannels />
    </ContentLayout>
  );
}
