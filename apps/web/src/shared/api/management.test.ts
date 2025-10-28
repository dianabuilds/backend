import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

import { apiDelete, apiGet, apiPost } from './client';
import {
  fetchBillingOverview,
  fetchBillingKpi,
  fetchBillingMetrics,
  fetchBillingOverviewPayouts,
  fetchBillingTransactions,
} from './management/billing';
import {
  deleteFeatureFlag,
  fetchFeatureFlags,
  saveFeatureFlag,
  searchFeatureFlagUsers,
} from './management/flags';
import {
  fetchIntegrationsOverview,
  fetchManagementConfig,
  sendNotificationTest,
} from './management/integrations';
import { fetchSystemConfig, fetchSystemOverview } from './management/system';
import {
  createManagementAiFallback,
  deleteManagementAiFallback,
  deleteManagementAiModel,
  fetchManagementAiFallbacks,
  fetchManagementAiModels,
  fetchManagementAiProviders,
  fetchManagementAiSummary,
  runManagementAiPlayground,
  saveManagementAiModel,
  saveManagementAiProvider,
} from './management/ai';

const mockedApiGet = vi.mocked(apiGet);
const mockedApiPost = vi.mocked(apiPost);
const mockedApiDelete = vi.mocked(apiDelete);

beforeEach(() => {
  mockedApiGet.mockReset();
  mockedApiPost.mockReset();
  mockedApiDelete.mockReset();
});

describe('management flags api', () => {
  it('normalizes feature flags response', async () => {
    mockedApiGet.mockResolvedValue({
      items: [
        {
          slug: 'beta.feature',
          status: 'custom',
          label: 'Beta Feature',
          description: 'Flag description',
          enabled: true,
          rollout: '42',
          testers: ['user-1', '', null],
          roles: ['admin'],
          segments: ['beta', 10],
          rules: [
            { type: 'include', value: 'desktop', rollout: '80', priority: '2' },
            { type: null },
          ],
          meta: { note: 'test' },
        },
        {
          slug: 'legacy.toggle',
          status: 'unknown',
          testers: 'not-an-array',
        },
      ],
    });

    const flags = await fetchFeatureFlags();

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/flags', { signal: undefined });
    expect(flags).toEqual([
      {
        slug: 'beta.feature',
        status: 'custom',
        label: 'Beta Feature',
        description: 'Flag description',
        status_label: undefined,
        audience: undefined,
        enabled: true,
        effective: null,
        rollout: 42,
        release_percent: null,
        testers: ['user-1'],
        roles: ['admin'],
        segments: ['beta'],
        rules: [
          {
            type: 'include',
            value: 'desktop',
            rollout: 80,
            priority: 2,
            meta: undefined,
          },
        ],
        meta: { note: 'test' },
        created_at: undefined,
        updated_at: undefined,
        evaluated_at: undefined,
      },
      {
        slug: 'legacy.toggle',
        status: 'disabled',
        label: undefined,
        description: undefined,
        status_label: undefined,
        audience: undefined,
        enabled: false,
        effective: null,
        rollout: null,
        release_percent: null,
        testers: [],
        roles: [],
        segments: [],
        rules: [],
        meta: null,
        created_at: undefined,
        updated_at: undefined,
        evaluated_at: undefined,
      },
    ]);
  });

  it('delegates saveFeatureFlag to apiPost', async () => {
    mockedApiPost.mockResolvedValue(undefined);
    await saveFeatureFlag({ slug: 'test', status: 'all' });
    expect(mockedApiPost).toHaveBeenCalledWith('/v1/flags', { slug: 'test', status: 'all' }, { signal: undefined });
  });

  it('deletes feature flag with trimmed slug', async () => {
    mockedApiDelete.mockResolvedValue(undefined);
    await deleteFeatureFlag('  flag/id  ');
    expect(mockedApiDelete).toHaveBeenCalledWith('/v1/flags/flag%2Fid', { signal: undefined });
  });

  it('throws when deleting feature flag without slug', async () => {
    await expect(deleteFeatureFlag('   ')).rejects.toThrow('flag_slug_missing');
    expect(mockedApiDelete).not.toHaveBeenCalled();
  });

  it('searches testers and normalizes response', async () => {
    mockedApiGet.mockResolvedValue([
      { id: 'u-1', username: 'tester' },
      { id: 'u-2' },
      'invalid',
    ]);

    const users = await searchFeatureFlagUsers(' qa ', { limit: 5 });

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/users/search?q=qa&limit=5', { signal: undefined });
    expect(users).toEqual([
      { id: 'u-1', username: 'tester' },
      { id: 'u-2', username: undefined },
    ]);
  });

  it('returns empty testers array for blank query', async () => {
    const users = await searchFeatureFlagUsers('   ');
    expect(users).toEqual([]);
    expect(mockedApiGet).not.toHaveBeenCalled();
  });
});

describe('management billing api', () => {
  it('normalizes overview payload', async () => {
    mockedApiGet.mockResolvedValue({
      kpi: {
        success: '5',
        errors: '2',
        pending: null,
        volume_cents: '5500',
        avg_confirm_ms: '120.5',
        contracts: {
          total: '4',
          enabled: '3',
          disabled: '1',
          testnet: '1',
          mainnet: '3',
        },
      },
      subscriptions: {
        active_subs: '12',
        mrr: '240.75',
        arpu: '20.0625',
        churn_30d: '0.15',
        tokens: [
          { token: 'usdc', total: '8', mrr_usd: '160.5' },
          { token: '', total: null, mrr_usd: null },
        ],
        networks: [
          { network: 'ethereum', chain_id: 1, total: '6' },
          { network: '', total: 2 },
        ],
      },
      revenue: [
        { day: '2024-01-01', amount: '42.5' },
        { day: null, amount: 0 },
      ],
    });

    const overview = await fetchBillingOverview();

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/billing/overview/dashboard');
    expect(overview).toMatchInlineSnapshot(`
      {
        "kpi": {
          "avg_confirm_ms": 120.5,
          "contracts": {
            "disabled": 1,
            "enabled": 3,
            "mainnet": 3,
            "testnet": 1,
            "total": 4,
          },
          "errors": 2,
          "pending": 0,
          "success": 5,
          "volume_cents": 5500,
        },
        "revenue": [
          {
            "amount": 42.5,
            "day": "2024-01-01",
          },
        ],
        "subscriptions": {
          "active_subs": 12,
          "arpu": 20.0625,
          "churn_30d": 0.15,
          "mrr": 240.75,
          "networks": [
            {
              "chain_id": "1",
              "network": "ethereum",
              "total": 6,
            },
          ],
          "tokens": [
            {
              "mrr_usd": 160.5,
              "token": "usdc",
              "total": 8,
            },
          ],
        },
      }
    `);
  });

  it('returns normalized KPI', async () => {
    mockedApiGet.mockResolvedValue({
      kpi: {
        success: '3',
        errors: '1',
        pending: '4',
        volume_cents: '3200',
        avg_confirm_ms: 98,
      },
    });

    const kpi = await fetchBillingKpi();

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/billing/overview/dashboard');
    expect(kpi).toMatchInlineSnapshot(`
      {
        "avg_confirm_ms": 98,
        "contracts": {
          "disabled": 0,
          "enabled": 0,
          "mainnet": 0,
          "testnet": 0,
          "total": 0,
        },
        "errors": 1,
        "pending": 4,
        "success": 3,
        "volume_cents": 3200,
      }
    `);
  });

  it('returns normalized subscription metrics', async () => {
    mockedApiGet.mockResolvedValue({
      subscriptions: {
        active_subs: '7',
        mrr: '100',
        arpu: '14.2857',
        churn_30d: '0.2',
        tokens: [{ token: 'usd', total: '5', mrr_usd: '70' }],
        networks: [{ network: 'polygon', chain_id: 137, total: '2' }],
      },
    });

    const metrics = await fetchBillingMetrics();

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/billing/overview/dashboard');
    expect(metrics).toMatchInlineSnapshot(`
      {
        "active_subs": 7,
        "arpu": 14.2857,
        "churn_30d": 0.2,
        "mrr": 100,
        "networks": [
          {
            "chain_id": "137",
            "network": "polygon",
            "total": 2,
          },
        ],
        "tokens": [
          {
            "mrr_usd": 70,
            "token": "usd",
            "total": 5,
          },
        ],
      }
    `);
  });
});

describe('management integrations api', () => {
  it('normalizes integrations overview and filters invalid items', async () => {
    mockedApiGet.mockResolvedValue({
      collected_at: '2025-10-08T00:00:00Z',
      items: [
        {
          id: 'webhook',
          status: 'connected',
          topics: ['alerts', 1],
          smtp_tls: true,
        },
        { id: null },
      ],
    });

    const overview = await fetchIntegrationsOverview();

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/admin/integrations', { signal: undefined });
    expect(overview).toEqual({
      collected_at: '2025-10-08T00:00:00Z',
      items: [
        {
          id: 'webhook',
          status: 'connected',
          connected: undefined,
          topics: ['alerts'],
          event_group: undefined,
          idempotency_ttl: null,
          smtp_host: undefined,
          smtp_port: undefined,
          smtp_tls: true,
          smtp_mock: undefined,
          mail_from: undefined,
          mail_from_name: undefined,
        },
      ],
    });
  });

  it('normalizes management config', async () => {
    mockedApiGet.mockResolvedValue({
      env: 'production',
      database_url: null,
      extraneous: 42,
    });

    const config = await fetchManagementConfig();

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/admin/config', { signal: undefined });
    expect(config).toEqual({ env: 'production', database_url: undefined });
  });

  it('sends notification tests through apiPost', async () => {
    mockedApiPost.mockResolvedValue(undefined);
    await sendNotificationTest('webhook', { ok: true });
    expect(mockedApiPost).toHaveBeenCalledWith(
      '/v1/notifications/send',
      { channel: 'webhook', payload: { ok: true } },
      { signal: undefined },
    );
  });

  it('loads overview payouts with filters', async () => {
    mockedApiGet.mockResolvedValue({
      items: [
        { id: '1', status: 'failed', gross_cents: 4200 },
        { id: '2', status: 'pending', gross_cents: 2000 },
      ],
    });

    const payouts = await fetchBillingOverviewPayouts({ status: 'failed', limit: 15 });

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/billing/overview/payouts?status=failed&limit=15');
    expect(payouts).toMatchInlineSnapshot(`
      [
        {
          "gross_cents": 4200,
          "id": "1",
          "status": "failed",
        },
        {
          "gross_cents": 2000,
          "id": "2",
          "status": "pending",
        },
      ]
    `);
  });

  it('fetches transactions with filters', async () => {
    mockedApiGet.mockResolvedValue({ items: [] });

    await fetchBillingTransactions({
      status: 'succeeded',
      provider: 'main',
      contract: 'vault',
      network: 'polygon',
      limit: 50,
    });

    expect(mockedApiGet).toHaveBeenCalledWith(
      '/v1/billing/admin/transactions?limit=50&status=succeeded&provider=main&contract=vault&network=polygon',
    );
  });
});

describe('management system api', () => {
  it('normalizes system overview payload', async () => {
    mockedApiGet.mockResolvedValue({
      collected_at: '2025-10-08T12:00:00Z',
      recommendations: { auto_refresh_seconds: '30' },
      signals: {
        workers: [
          { id: 'queue', label: 'Queue', status: 'healthy', pending: '5' },
          'invalid',
        ],
      },
      summary: {
        uptime_percent: '99.9',
        queue_status: 'ok',
      },
      incidents: {
        active: [
          { id: 'INC-1', title: 'Outage', status: 'open', history: [{ action: 'created' }] },
          { id: null },
        ],
        error: 'unavailable',
      },
      links: {
        health: 'https://example.health',
        invalid: 5,
      },
      changelog: [
        { id: 'chg-1', title: 'Fix', category: 'bug', published_at: '2025-10-01T00:00:00Z', highlights: ['a'] },
      ],
    });

    const overview = await fetchSystemOverview();

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/admin/system/overview', { signal: undefined });
    expect(overview).toEqual({
      collected_at: '2025-10-08T12:00:00Z',
      recommendations: { auto_refresh_seconds: 30 },
      signals: {
        workers: [
          {
            id: 'queue',
            label: 'Queue',
            status: 'healthy',
            ok: null,
            hint: undefined,
            last_heartbeat: undefined,
            latency_ms: null,
            pending: 5,
            leased: null,
            failed: null,
            succeeded: null,
            oldest_pending_seconds: null,
            avg_duration_ms: null,
            failure_rate: null,
            jobs_completed: null,
            jobs_failed: null,
            success_rate: null,
            total_calls: null,
            error_count: null,
            models: [],
            enabled: undefined,
            link: undefined,
          },
        ],
      },
      summary: {
        collected_at: undefined,
        uptime_percent: 99.9,
        db_latency_ms: undefined,
        queue_pending: undefined,
        queue_status: 'ok',
        worker_avg_ms: undefined,
        worker_failure_rate: undefined,
        llm_success_rate: undefined,
        active_incidents: undefined,
      },
      incidents: {
        active: [
          {
            id: 'INC-1',
            title: 'Outage',
            status: 'open',
            severity: undefined,
            source: undefined,
            first_seen_at: undefined,
            updated_at: undefined,
            impacts: [],
            history: [
              {
                action: 'created',
                created_at: undefined,
                reason: undefined,
                payload: null,
              },
            ],
          },
        ],
        recent: undefined,
        integrations: undefined,
        error: 'unavailable',
      },
      links: {
        health: 'https://example.health',
        invalid: undefined,
      },
      changelog: [
        {
          id: 'chg-1',
          title: 'Fix',
          category: 'bug',
          published_at: '2025-10-01T00:00:00Z',
          highlights: ['a'],
        },
      ],
    });
  });

  it('throws when system overview lacks timestamp', async () => {
    mockedApiGet.mockResolvedValue({ changelog: [] });
    await expect(fetchSystemOverview()).rejects.toThrow('system_overview_missing_timestamp');
  });

  it('returns empty object for invalid system config payload', async () => {
    mockedApiGet.mockResolvedValue(null);
    const config = await fetchSystemConfig();
    expect(mockedApiGet).toHaveBeenCalledWith('/v1/admin/config', { signal: undefined });
    expect(config).toEqual({});
  });
});


describe('management ai api', () => {
  it('returns empty array when AI models payload missing', async () => {
    mockedApiGet.mockResolvedValue({ items: [null, { id: 'm1', name: 'gpt', provider_slug: 'openai' }] });
    const models = await fetchManagementAiModels();
    expect(mockedApiGet).toHaveBeenCalledWith('/v1/ai/admin/models');
    expect(models).toEqual([{ id: 'm1', name: 'gpt', provider_slug: 'openai' }]);
  });

  it('persists AI model via POST', async () => {
    const payload = { id: 'm1', name: 'gpt', provider_slug: 'openai' };
    mockedApiPost.mockResolvedValue({ id: 'm1' });
    const saved = await saveManagementAiModel(payload);
    expect(mockedApiPost).toHaveBeenCalledWith('/v1/ai/admin/models', payload);
    expect(saved).toEqual({ id: 'm1' });
  });

  it('deletes AI model via DELETE', async () => {
    mockedApiDelete.mockResolvedValue(undefined);
    await deleteManagementAiModel('model/id');
    expect(mockedApiDelete).toHaveBeenCalledWith('/v1/ai/admin/models/model%2Fid');
  });

  it('returns providers list', async () => {
    mockedApiGet.mockResolvedValue({ items: [{ slug: 'openai' }, undefined] });
    const providers = await fetchManagementAiProviders();
    expect(mockedApiGet).toHaveBeenCalledWith('/v1/ai/admin/providers');
    expect(providers).toEqual([{ slug: 'openai' }]);
  });

  it('persists provider via POST', async () => {
    const payload = { slug: 'openai', enabled: true };
    mockedApiPost.mockResolvedValue({ slug: 'openai' });
    const saved = await saveManagementAiProvider(payload);
    expect(mockedApiPost).toHaveBeenCalledWith('/v1/ai/admin/providers', payload);
    expect(saved).toEqual({ slug: 'openai' });
  });

  it('fetches fallback rules', async () => {
    mockedApiGet.mockResolvedValue({ items: [{ id: 'f1', primary_model: 'a', fallback_model: 'b' }] });
    const fallbacks = await fetchManagementAiFallbacks();
    expect(mockedApiGet).toHaveBeenCalledWith('/v1/ai/admin/fallbacks');
    expect(fallbacks).toEqual([{ id: 'f1', primary_model: 'a', fallback_model: 'b' }]);
  });

  it('creates fallback rule', async () => {
    const payload = { primary_model: 'a', fallback_model: 'b' };
    mockedApiPost.mockResolvedValue({ id: 'f2' });
    const created = await createManagementAiFallback(payload);
    expect(mockedApiPost).toHaveBeenCalledWith('/v1/ai/admin/fallbacks', payload);
    expect(created).toEqual({ id: 'f2' });
  });

  it('deletes fallback rule', async () => {
    mockedApiDelete.mockResolvedValue(undefined);
    await deleteManagementAiFallback('fb/1');
    expect(mockedApiDelete).toHaveBeenCalledWith('/v1/ai/admin/fallbacks/fb%2F1');
  });

  it('returns summary object even when payload null', async () => {
    mockedApiGet.mockResolvedValue(null);
    const summary = await fetchManagementAiSummary();
    expect(mockedApiGet).toHaveBeenCalledWith('/v1/admin/telemetry/llm/summary');
    expect(summary).toEqual({});
  });

  it('runs playground request', async () => {
    const payload = { prompt: 'hi', model: 'gpt' };
    mockedApiPost.mockResolvedValue({ result: 'ok' });
    const response = await runManagementAiPlayground(payload);
    expect(mockedApiPost).toHaveBeenCalledWith('/v1/ai/admin/playground', payload);
    expect(response).toEqual({ result: 'ok' });
  });
});

