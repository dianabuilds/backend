import '@testing-library/jest-dom';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import { AdminTelemetryService } from '../../openapi';
import RumTab, { type RumEvent } from './RumTab';

describe('RumTab', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders average login duration and chart uses dur_ms', async () => {
    const now = Date.now();

    vi.spyOn(
      AdminTelemetryService,
      'rumSummaryAdminTelemetryRumSummaryGet',
    ).mockResolvedValue({
      window: 100,
      counts: {},
      login_attempt_avg_ms: 150,
      navigation_avg: { ttfb_ms: null, dom_content_loaded_ms: null, load_event_ms: null },
    } as unknown);

    vi.spyOn(AdminTelemetryService, 'listRumEventsAdminTelemetryRumGet').mockResolvedValue([
      { event: 'login_attempt', ts: now, data: { dur_ms: 100 } } as RumEvent,
      { event: 'login_attempt', ts: now + 1000, data: { dur_ms: 200 } } as RumEvent,
    ] as unknown as RumEvent[]);

    const qc = new QueryClient();
    const { container } = render(
      <QueryClientProvider client={qc}>
        <RumTab />
      </QueryClientProvider>,
    );

    await screen.findByText('Login avg: 150 ms');

    const path = container.querySelector('svg path');
    expect(path?.getAttribute('d')).toBe('M 4 0');
  });
});
