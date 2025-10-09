import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { NotificationTemplates } from '../../features/notifications';

export default function TemplatesPage(): React.ReactElement {
  return (
    <ContentLayout
      context="notifications"
      title="Notification templates"
      description="Coordinate announcements, automate broadcasts, and keep every player cohort informed."
    >
      <NotificationTemplates />
    </ContentLayout>
  );
}
