import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { Card } from '@ui';

export default function ChannelsPage() {
  return (
    <ContentLayout context="notifications" title="Delivery channels">
      <Card className="p-6">
        <h2 className="text-base font-semibold text-gray-800 dark:text-dark-50">Channels</h2>
        <p className="mt-2 text-sm text-gray-600 dark:text-dark-200">
          Manage push, email, in-product, and partner webhooks. Once APIs are connected we will surface provider health, rate limits, and per-region toggles in this workspace.
        </p>
      </Card>
    </ContentLayout>
  );
}
