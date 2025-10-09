import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
}));

import { apiGet } from './client';
import {
  fetchEventsSummary,
  fetchHttpSummary,
  fetchLLMSummary,
  fetchRumEvents,
  fetchRumSummary,
  fetchTelemetryOverview,
  fetchTransitionsSummary,
  fetchWorkerSummary,
} from './observability';

const mockedApiGet = vi.mocked(apiGet);

describe('observability api', () => {
  beforeEach(() => {
    mockedApiGet.mockReset();
  });

  it('normalizes telemetry overview payload', async () => {
    mockedApiGet.mockResolvedValue({
      llm: {
        calls: [{ type: 'calls', provider: 'openai', model: 'gpt', stage: 'prod', count: '10' }],
        latency_avg_ms: [{ provider: 'openai', model: 'gpt', stage: 'prod', avg_ms: '120' }],
        tokens_total: [{ provider: 'openai', model: 'gpt', stage: 'prod', type: 'prompt', total: '500' }],
        cost_usd_total: [{ provider: 'openai', model: 'gpt', stage: 'prod', total_usd: '12.5' }],
      },
      workers: {
        jobs: { started: '20', completed: '18' },
        job_avg_ms: '45',
        cost_usd_total: '3.2',
        tokens: { prompt: '100', completion: '200' },
        stages: { ingest: { count: '5', avg_ms: '80' } },
      },
      events: {
        counts: { save: '12' },
        handlers: [{ event: 'save', handler: 'onSave', success: '10', failure: '2', total: '12', avg_ms: '32' }],
      },
      transitions: [{ mode: 'story', avg_latency_ms: '150', no_route_ratio: '0.1', fallback_ratio: '0.05', entropy: '0.7', repeat_rate: '0.2', novelty_rate: '0.4', count: '50' }],
      ux: { time_to_first_save_avg_s: '5', published_tagged_ratio: '0.6', save_next_total: '40' },
      rum: {
        window: '500',
        counts: { navigation: '30' },
        login_attempt_avg_ms: '250',
        navigation_avg: { ttfb_ms: '120', dom_content_loaded_ms: '300', load_event_ms: '450' },
      },
    });

    const overview = await fetchTelemetryOverview();

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/admin/telemetry/summary', { signal: undefined });
    expect(overview.llm?.calls[0]).toEqual({ type: 'calls', provider: 'openai', model: 'gpt', stage: 'prod', count: 10 });
    expect(overview.workers?.jobs).toEqual({ started: 20, completed: 18 });
    expect(overview.events.counts).toEqual({ save: 12 });
    expect(overview.transitions[0].avg_latency_ms).toBe(150);
    expect(overview.ux.time_to_first_save_avg_s).toBe(5);
    expect(overview.rum.navigation_avg.load_event_ms).toBe(450);
  });

  it('normalizes http summary and handles malformed entries', async () => {
    mockedApiGet.mockResolvedValue({
      paths: [
        { method: 'GET', path: '/health', requests_total: '100', error5xx_ratio: '0.01', avg_duration_ms: '20' },
        { method: null },
      ],
    });

    const summary = await fetchHttpSummary();
    expect(summary.paths).toHaveLength(1);
    expect(summary.paths[0]).toEqual({
      method: 'GET',
      path: '/health',
      requests_total: 100,
      error5xx_total: undefined,
      error5xx_ratio: 0.01,
      avg_duration_ms: 20,
    });
  });

  it('normalizes llm summary arrays', async () => {
    mockedApiGet.mockResolvedValue({
      calls: [{ type: 'errors', provider: 'openai', model: 'gpt', stage: 'prod', count: '3' }],
      latency_avg_ms: [{ provider: 'openai', model: 'gpt', stage: 'prod', avg_ms: '90' }],
      tokens_total: [{ provider: 'openai', model: 'gpt', stage: 'prod', type: 'completion', total: '1200' }],
      cost_usd_total: [{ provider: 'openai', model: 'gpt', stage: 'prod', total_usd: '4.2' }],
    });

    const summary = await fetchLLMSummary();
    expect(summary.calls[0].count).toBe(3);
    expect(summary.latency_avg_ms[0].avg_ms).toBe(90);
    expect(summary.tokens_total[0].total).toBe(1200);
    expect(summary.cost_usd_total[0].total_usd).toBe(4.2);
  });

  it('normalizes workers summary with defaults', async () => {
    mockedApiGet.mockResolvedValue(null);
    const summary = await fetchWorkerSummary();
    expect(summary.jobs).toEqual({});
    expect(summary.tokens).toEqual({ prompt: 0, completion: 0 });
  });

  it('normalizes events summary and transitions list', async () => {
    mockedApiGet
      .mockResolvedValueOnce({ counts: { login: '5' }, handlers: [{ event: 'login', handler: 'onLogin', success: '5', failure: '0', total: '5', avg_ms: '12' }] })
      .mockResolvedValueOnce([{ mode: 'story', avg_latency_ms: '123' }, 'invalid']);

    const events = await fetchEventsSummary();
    expect(events.counts.login).toBe(5);

    const transitions = await fetchTransitionsSummary();
    expect(transitions).toHaveLength(1);
    expect(transitions[0].avg_latency_ms).toBe(123);
  });

  it('normalizes rum summary and events', async () => {
    mockedApiGet
      .mockResolvedValueOnce({ window: '300', counts: { navigation: '15' }, navigation_avg: { ttfb_ms: '150' } })
      .mockResolvedValueOnce([{ ts: '2025-10-05T12:00:00Z', event: 'navigation', url: '/home' }, { invalid: true }]);

    const summary = await fetchRumSummary({ window: 300 });
    expect(mockedApiGet).toHaveBeenCalledWith('/v1/admin/telemetry/rum/summary?window=300', { signal: undefined });
    expect(summary.window).toBe(300);

    const events = await fetchRumEvents({ event: 'navigation', limit: 10 });
    expect(mockedApiGet).toHaveBeenLastCalledWith('/v1/admin/telemetry/rum?event=navigation&limit=10', { signal: undefined });
    expect(events).toHaveLength(1);
    expect(events[0].event).toBe('navigation');
  });
});
