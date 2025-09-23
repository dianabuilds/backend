import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { Card } from '@ui';

export default function HistoryPage() {
  return (
    <ContentLayout context="notifications" title="Delivery history">
      <Card className="p-6">
        <h2 className="text-base font-semibold text-gray-800 dark:text-dark-50">Activity log</h2>
        <p className="mt-2 text-sm text-gray-600 dark:text-dark-200">
          Track recent sends, delivery rates, and failure diagnostics. This placeholder will host searchable logs aligned with observability counters.
        </p>
      </Card>
    </ContentLayout>
  );
}
