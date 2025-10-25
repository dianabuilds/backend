import React from 'react';
import { ContentLayout } from '../content/ContentLayout';
import { NotificationBroadcasts } from '../../features/notifications/broadcasts';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

type HeroState = {
  actions?: React.ReactNode;
  metrics?: PageHeroMetric[];
};

function shallowEqualMetrics(a?: PageHeroMetric[], b?: PageHeroMetric[]): boolean {
  if (a === b) return true;
  if (!a || !b) return !a && !b;
  if (a.length !== b.length) return false;
  for (let index = 0; index < a.length; index += 1) {
    const left = a[index];
    const right = b[index];
    if (!right) return false;
    if (
      left.id !== right.id ||
      left.label !== right.label ||
      left.helper !== right.helper ||
      left.trend !== right.trend ||
      left.accent !== right.accent ||
      left.value !== right.value
    ) {
      return false;
    }
  }
  return true;
}

export default function NotificationsBroadcastsPage(): React.ReactElement {
  const [heroState, setHeroState] = React.useState<HeroState | null>(null);

  const handleHeroData = React.useCallback((payload: HeroState | null) => {
    setHeroState((prev) => {
      if (
        prev?.actions === payload?.actions &&
        shallowEqualMetrics(prev?.metrics, payload?.metrics)
      ) {
        return prev;
      }
      return payload;
    });
  }, []);

  return (
    <ContentLayout
      context="notifications"
      title="Broadcasts"
      description="Plan announcements, hand off targeting to the platform, and keep delivery in sync with your operators."
      actions={heroState?.actions}
      metrics={heroState?.metrics}
    >
      <NotificationBroadcasts onHeroData={handleHeroData} />
    </ContentLayout>
  );
}
