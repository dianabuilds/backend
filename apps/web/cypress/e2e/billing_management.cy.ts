const overviewResponse = {
  kpi: {
    success: 24,
    errors: 3,
    pending: 5,
    volume_cents: 185000,
    avg_confirm_ms: 110,
    contracts: {
      total: 4,
      enabled: 3,
      disabled: 1,
      testnet: 1,
      mainnet: 3,
    },
  },
  subscriptions: {
    active_subs: 90,
    mrr: 360000,
    arpu: 4000,
    churn_30d: 0.07,
    tokens: [
      { token: 'USDC', total: 60, mrr_usd: 250000 },
      { token: 'DAI', total: 15, mrr_usd: 60000 },
    ],
    networks: [
      { network: 'polygon', chain_id: '137', total: 40 },
      { network: 'base', chain_id: '8453', total: 12 },
    ],
  },
  revenue: [
    { day: '2024-02-01', amount: 1200 },
    { day: '2024-02-02', amount: 1500 },
    { day: '2024-02-03', amount: 1800 },
  ],
};

const payoutsResponse = {
  items: [
    { id: 'payout-1', status: 'failed', gross_cents: 12000, created_at: '2024-02-02T10:00:00Z' },
    { id: 'payout-2', status: 'pending', gross_cents: 8000, created_at: '2024-02-03T12:00:00Z' },
  ],
};

describe('Billing management flows', () => {
  beforeEach(() => {
    cy.intercept('GET', '/v1/users/me', {
      user: {
        id: 'finance-ops',
        email: 'finance@caves.dev',
        roles: ['finance_ops'],
      },
    }).as('getCurrentUser');

    cy.intercept('POST', '/v1/metrics/rum', { statusCode: 204, body: {} }).as('rumEvent');
  });

  it('shows billing overview metrics', () => {
    cy.intercept('GET', '/v1/billing/overview/dashboard', {
      statusCode: 200,
      body: overviewResponse,
    }).as('getOverview');

    cy.intercept('GET', /\/v1\/billing\/overview\/payouts.*/, {
      statusCode: 200,
      body: payoutsResponse,
    }).as('getPayouts');

    cy.visit('/finance/billing/overview');

    cy.wait(['@getCurrentUser', '@getOverview', '@getPayouts', '@rumEvent']);

    cy.contains('Billing Overview').should('be.visible');
    cy.contains('Успешные транзакции').should('be.visible');
    cy.contains('Обновить данные').click();
    cy.wait('@getOverview');
  });

  it('creates and lists a payment provider', () => {
    const providers: any[] = [
      {
        slug: 'stripe',
        type: 'stripe',
        enabled: true,
        priority: 10,
        contract_slug: 'main-vault',
        networks: ['polygon'],
        supported_tokens: ['USDC'],
        default_network: 'polygon',
        config: { webhook_secret: '***' },
      },
    ];

    cy.intercept('GET', '/v1/billing/overview/dashboard', {
      statusCode: 200,
      body: overviewResponse,
    }).as('getOverview');

    cy.intercept('GET', /\/v1\/billing\/overview\/payouts.*/, {
      statusCode: 200,
      body: payoutsResponse,
    }).as('getPayouts');

    cy.intercept('GET', '/v1/billing/admin/providers', (req) => {
      req.reply({ statusCode: 200, body: { items: providers } });
    }).as('getProviders');

    cy.intercept('GET', '/v1/billing/admin/contracts', {
      statusCode: 200,
      body: {
        items: [
          {
            id: 'ctr-1',
            slug: 'main-vault',
            title: 'Main vault',
            chain: 'polygon',
            address: '0x123',
            type: 'ERC-20',
            enabled: true,
            testnet: false,
            methods: { list: ['deposit'], roles: ['ops'] },
            status: 'active',
            abi_present: true,
            webhook_url: '',
          },
        ],
      },
    }).as('getContracts');

    cy.intercept('GET', /\/v1\/billing\/admin\/contracts\/events.*/, {
      statusCode: 200,
      body: { items: [] },
    }).as('getContractEvents');

    cy.intercept('GET', '/v1/billing/overview/crypto-config', {
      statusCode: 200,
      body: {
        config: {
          rpc_endpoints: { polygon: 'https://rpc.polygon.example' },
          retries: 2,
          gas_price_cap: null,
          fallback_networks: {},
        },
      },
    }).as('getCryptoConfig');

    cy.intercept('GET', /\/v1\/billing\/admin\/transactions.*/, {
      statusCode: 200,
      body: {
        items: [
          {
            id: 'tx-1',
            created_at: '2024-02-02T10:00:00Z',
            gateway_slug: 'stripe',
            status: 'succeeded',
            net_cents: 9800,
            gross_cents: 10000,
            token: 'USDC',
            network: 'polygon',
          },
        ],
      },
    }).as('getTransactions');

    cy.intercept('POST', '/v1/billing/admin/providers', (req) => {
      providers.push({
        ...req.body,
        priority: req.body.priority ?? 100,
        networks: req.body.networks ?? [],
        supported_tokens: req.body.supported_tokens ?? [],
      });
      req.reply({ statusCode: 200, body: {} });
    }).as('saveProvider');

    cy.visit('/finance/billing/payments');

    cy.wait([
      '@getCurrentUser',
      '@getOverview',
      '@getPayouts',
      '@getProviders',
      '@getContracts',
      '@getContractEvents',
      '@getCryptoConfig',
      '@getTransactions',
      '@rumEvent',
    ]);

    cy.contains('Новый провайдер').click();
    cy.get('input[aria-label="Slug"]').clear().type('sandbox-gateway');
    cy.get('textarea[aria-label="Networks (JSON или CSV)"]').type('polygon, base');
    cy.get('textarea[aria-label="Supported tokens (JSON или CSV)"]').type('USDC, DAI');

    cy.contains('button', 'Сохранить').filter(':visible').click();
    cy.wait('@saveProvider');
    cy.wait('@getProviders');

    cy.contains('sandbox-gateway').should('be.visible');
  });

  it('updates a tariff plan title', () => {
    const plans: any[] = [
      {
        id: 'plan-starter',
        slug: 'starter',
        title: 'Starter',
        description: 'Base plan',
        price_cents: 9900,
        currency: 'USD',
        price_token: 'USDC',
        billing_interval: 'month',
        is_active: true,
        order: 1,
        gateway_slug: 'stripe-main',
        contract_slug: 'main-vault',
        monthly_limits: { api_quota: 100000 },
        features: { status: 'active', audience: 'all', ab_variant: 'control' },
      },
    ];

    cy.intercept('GET', '/v1/billing/overview/dashboard', {
      statusCode: 200,
      body: overviewResponse,
    }).as('getOverview');

    cy.intercept('GET', '/v1/billing/admin/plans/all', (req) => {
      req.reply({ statusCode: 200, body: { items: plans } });
    }).as('getPlans');

    cy.intercept('POST', '/v1/billing/admin/plans', (req) => {
      plans[0] = { ...plans[0], ...req.body, title: req.body.title || plans[0].title };
      req.reply({ statusCode: 200, body: {} });
    }).as('savePlan');

    cy.visit('/finance/billing/tariffs');

    cy.wait(['@getCurrentUser', '@getOverview', '@getPlans', '@rumEvent']);

    cy.contains('Редактировать').click();
    cy.get('input[aria-label="Название"]').clear().type('Starter Plus');
    cy.contains('button', 'Сохранить').filter(':visible').click();

    cy.wait('@savePlan');
    cy.wait('@getPlans');

    cy.contains('Starter Plus').should('be.visible');
  });
});
