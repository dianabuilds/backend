import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { NotificationTemplates } from '../../features/notifications';

export default function TemplatesPage(): React.ReactElement {
  return (
    <ContentLayout
      context="notifications"
      title="Notification templates"
      description="Draft, version, and localise notification templates that power every broadcast."
    >
      <NotificationTemplates />
    </ContentLayout>
  );
}
