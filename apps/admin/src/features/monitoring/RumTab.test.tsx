import '@testing-library/jest-dom';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import { AdminTelemetryService } from '../../openapi';
import RumTab, { type RumEvent } from './RumTab';

describe('RumTab', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders average login duration and chart uses dur_ms', async () => {
    const now = Date.now();

    vi.spyOn(AdminTelemetryService, 'rumSummaryAdminTelemetryRumSummaryGet').mockResolvedValue({
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

  it('requests summary with computed window', async () => {
    vi.spyOn(AdminTelemetryService, 'rumSummaryAdminTelemetryRumSummaryGet').mockResolvedValue({
      window: 60,
      counts: {},
      login_attempt_avg_ms: null,
      navigation_avg: { ttfb_ms: null, dom_content_loaded_ms: null, load_event_ms: null },
    } as unknown);

    vi.spyOn(AdminTelemetryService, 'listRumEventsAdminTelemetryRumGet').mockResolvedValue(
      [] as unknown as RumEvent[],
    );

    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <RumTab />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(AdminTelemetryService.rumSummaryAdminTelemetryRumSummaryGet).toHaveBeenCalledWith({
        window: 60,
      });
    });
  });

  it('passes filters and pagination to API', async () => {
    vi.spyOn(AdminTelemetryService, 'rumSummaryAdminTelemetryRumSummaryGet').mockResolvedValue({
      window: 60,
      counts: {},
      login_attempt_avg_ms: null,
      navigation_avg: { ttfb_ms: null, dom_content_loaded_ms: null, load_event_ms: null },
    } as unknown);

    const spy = vi
      .spyOn(AdminTelemetryService, 'listRumEventsAdminTelemetryRumGet')
      .mockResolvedValue([] as unknown as RumEvent[]);

    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <RumTab />
      </QueryClientProvider>,
    );

    await waitFor(() => expect(spy).toHaveBeenCalledWith(undefined, undefined, 0, 50));

    fireEvent.change(screen.getByPlaceholderText('event'), {
      target: { value: 'login' },
    });
    await waitFor(() => expect(spy).toHaveBeenLastCalledWith('login', undefined, 0, 50));

    fireEvent.click(screen.getByText('Next'));
    await waitFor(() => expect(spy).toHaveBeenLastCalledWith('login', undefined, 50, 50));
  });

  it('filters events by chart click and scrolls table', async () => {
    const now = Date.now();

    vi.spyOn(AdminTelemetryService, 'rumSummaryAdminTelemetryRumSummaryGet').mockResolvedValue({
      window: 60,
      counts: {},
      login_attempt_avg_ms: null,
      navigation_avg: { ttfb_ms: null, dom_content_loaded_ms: null, load_event_ms: null },
    } as unknown);

    const events: RumEvent[] = [
      { event: 'a', ts: now } as RumEvent,
      { event: 'a', ts: now + 60_000 } as RumEvent,
    ];
    vi.spyOn(AdminTelemetryService, 'listRumEventsAdminTelemetryRumGet').mockResolvedValue(
      events as unknown as RumEvent[],
    );

    const qc = new QueryClient();
    const { container } = render(
      <QueryClientProvider client={qc}>
        <RumTab />
      </QueryClientProvider>,
    );

    const firstTime = new Date(now).toLocaleTimeString();
    const secondTime = new Date(now + 60_000).toLocaleTimeString();

    await screen.findByText(firstTime);
    await screen.findByText(secondTime);

    const scrollSpy = vi.fn();
    (HTMLElement.prototype as unknown as { scrollIntoView: () => void }).scrollIntoView = scrollSpy;

    const bar = container.querySelector('[data-testid="bar-1"]');
    expect(bar).toBeTruthy();
    if (bar) fireEvent.click(bar);

    await waitFor(() => expect(scrollSpy).toHaveBeenCalled());
    expect(screen.queryByText(firstTime)).toBeNull();
    expect(screen.getByText(secondTime)).toBeInTheDocument();
  });
});
