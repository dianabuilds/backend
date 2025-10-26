import type { ReactNode } from 'react';
export type BillingProviderConfig = {
  linked_contract?: string;
  [key: string]: unknown;
};

export type BillingProvider = {
  slug: string;
  type: string;
  enabled: boolean;
  priority: number;
  config?: BillingProviderConfig | null;
};

export type BillingProviderPayload = {
  slug: string;
  type: string;
  enabled: boolean;
  priority: number;
  config?: BillingProviderConfig | null;
  contract_slug?: string | null;
};

export type BillingContractMethods = {
  list?: string[];
  roles?: string[];
  [key: string]: unknown;
};

export type BillingContract = {
  id: string;
  slug: string;
  title?: string | null;
  chain?: string | null;
  address?: string | null;
  type?: string | null;
  enabled?: boolean;
  testnet?: boolean;
  methods?: BillingContractMethods | null;
  status?: string | null;
  abi_present?: boolean;
  webhook_url?: string | null;
};

export type BillingContractPayload = BillingContract & {
  abi?: unknown;
  abi_text?: string | null;
};

export type BillingTransaction = {
  created_at?: string | null;
  user_id?: string | null;
  gateway_slug?: string | null;
  status?: string | null;
  currency?: string | null;
  gross_cents?: number | null;
};

export type BillingKpi = {
  success: number;
  errors: number;
  volume_cents: number;
  avg_confirm_ms: number;
};

export type BillingContractEvent = {
  id?: string;
  contract_id?: string;
  created_at?: string | null;
  event?: string | null;
  method?: string | null;
  status?: string | null;
  amount?: number | null;
  tx_hash?: string | null;
};

export type BillingContractMethodTimeseriesPoint = {
  day: string;
  method: string;
  calls: number;
};

export type BillingContractVolumeTimeseriesPoint = {
  day: string;
  token: string;
  total: number;
};

export type BillingContractMetricsTimeseries = {
  methods: BillingContractMethodTimeseriesPoint[];
  volume: BillingContractVolumeTimeseriesPoint[];
};

export type BillingMetrics = {
  active_subs: number;
  mrr: number;
  arpu: number;
  churn_30d: number;
};

export type BillingPlanLimits = Record<string, unknown> | null;

export type BillingPlanFeatures = Record<string, unknown> | null;

export type BillingPlan = {
  id: string;
  slug: string;
  title?: string | null;
  description?: string | null;
  price_cents?: number | null;
  currency?: string | null;
  is_active: boolean;
  order?: number | null;
  monthly_limits?: BillingPlanLimits;
  features?: BillingPlanFeatures;
  updated_at?: string | null;
};

export type BillingPlanPayload = {
  id?: string;
  slug: string;
  title?: string | null;
  description?: string | null;
  price_cents?: number | null;
  currency?: string | null;
  is_active?: boolean;
  order?: number | null;
  monthly_limits?: BillingPlanLimits;
  features?: BillingPlanFeatures;
};

export type BillingPlanHistoryItem = {
  id?: string;
  action?: string;
  actor?: string | null;
  resource_id?: string | null;
  created_at?: string | null;
  payload?: Record<string, unknown> | null;
};

export type BillingPlanLimitsUpdate = {
  slug: string;
  monthly_limits: Record<string, unknown>;
};

export type BillingCryptoConfig = {
  rpc_endpoints: Record<string, unknown>;
  retries: number;
  gas_price_cap: number | null;
  fallback_networks: Record<string, unknown>;
};

export type PlatformAdminQuickLink = {
  label: string;
  href: string;
  description?: string;
  icon?: ReactNode;
};

export type PlatformAdminChangelogEntry = {
  id: string;
  title: string;
  category?: string;
  published_at?: string;
  highlights?: string[];
};

export type PlatformAdminIntegrationSummary = {
  id: string;
  label: string;
  status: string;
  link?: string | null;
  hint?: string | null;
};

export type FeatureFlagStatus = 'disabled' | 'testers' | 'premium' | 'all' | 'custom';

export type FeatureFlagRule = {
  type: string;
  value: string;
  rollout: number | null;
  priority: number;
  meta?: Record<string, unknown>;
};

export type FeatureFlag = {
  slug: string;
  label?: string | null;
  description?: string | null;
  status: FeatureFlagStatus;
  status_label?: string | null;
  audience?: string | null;
  enabled: boolean;
  effective?: boolean | null;
  rollout?: number | null;
  release_percent?: number | null;
  testers: string[];
  roles: string[];
  segments: string[];
  rules: FeatureFlagRule[];
  meta?: Record<string, unknown> | null;
  created_at?: string | null;
  updated_at?: string | null;
  evaluated_at?: string | null;
};

export type FeatureFlagUpsertPayload = {
  slug: string;
  status: FeatureFlagStatus;
  description?: string;
  testers?: string[];
  roles?: string[];
  segments?: string[];
  rollout?: number | null;
};

export type FeatureFlagTester = {
  id: string;
  username?: string | null;
};

export type IntegrationItem = {
  id: string;
  status: string;
  connected?: boolean;
  topics?: string[];
  event_group?: string | null;
  idempotency_ttl?: number | null;
  smtp_host?: string | null;
  smtp_port?: number | null;
  smtp_tls?: boolean | null;
  smtp_mock?: boolean | null;
  mail_from?: string | null;
  mail_from_name?: string | null;
};

export type IntegrationOverview = {
  collected_at?: string;
  items?: IntegrationItem[];
};

export type ManagementConfig = Record<string, unknown>;

export type NotificationTestChannel = 'webhook' | 'email';

export type NotificationTestPayload = Record<string, unknown>;

export type SystemSignal = {
  id: string;
  label: string;
  status: string;
  ok?: boolean | null;
  hint?: string | null;
  last_heartbeat?: string | null;
  latency_ms?: number | null;
  pending?: number | null;
  leased?: number | null;
  failed?: number | null;
  succeeded?: number | null;
  oldest_pending_seconds?: number | null;
  avg_duration_ms?: number | null;
  failure_rate?: number | null;
  jobs_completed?: number | null;
  jobs_failed?: number | null;
  success_rate?: number | null;
  total_calls?: number | null;
  error_count?: number | null;
  models?: string[];
  enabled?: boolean;
  link?: string | null;
  [key: string]: unknown;
};

export type IncidentHistoryItem = {
  action: string;
  created_at?: string | null;
  reason?: string | null;
  payload?: Record<string, unknown> | null;
};

export type SystemIncident = {
  id: string;
  title: string;
  status: string;
  severity?: string;
  source?: string;
  first_seen_at?: string | null;
  updated_at?: string | null;
  impacts?: string[];
  history?: IncidentHistoryItem[];
};

export type SystemIncidents = {
  active?: SystemIncident[];
  recent?: SystemIncident[];
  integrations?: PlatformAdminIntegrationSummary[];
  error?: string;
};

export type SystemSummary = {
  collected_at?: string;
  uptime_percent?: number;
  db_latency_ms?: number;
  queue_pending?: number;
  queue_status?: string;
  worker_avg_ms?: number;
  worker_failure_rate?: number;
  llm_success_rate?: number;
  active_incidents?: number;
};

export type SystemOverview = {
  collected_at: string;
  recommendations?: {
    auto_refresh_seconds?: number;
  };
  signals?: Record<string, SystemSignal[] | undefined>;
  summary?: SystemSummary;
  incidents?: SystemIncidents;
  links?: Record<string, string | null | undefined>;
  changelog?: PlatformAdminChangelogEntry[];
};
export type ManagementAiModelLimits = {
  daily_tokens?: number | null;
  monthly_tokens?: number | null;
};

export type ManagementAiModelUsage = {
  content?: boolean;
  quests?: boolean;
  moderation?: boolean;
};

export type ManagementAiModelParams = {
  limits?: ManagementAiModelLimits | null;
  usage?: ManagementAiModelUsage | null;
  fallback_priority?: number | null;
  mode?: string | null;
};

export type ManagementAiModel = {
  id: string;
  name: string;
  provider_slug: string;
  version?: string | null;
  status?: string | null;
  is_default?: boolean | null;
  params?: ManagementAiModelParams | null;
  updated_at?: string | null;
};

export type ManagementAiModelPayload = {
  id?: string;
  name: string;
  provider_slug: string;
  version?: string | null;
  status?: string | null;
  is_default?: boolean | null;
  params?: ManagementAiModelParams | null;
};

export type ManagementAiProviderExtras = {
  retries?: number | null;
};

export type ManagementAiProvider = {
  slug: string;
  title?: string | null;
  enabled?: boolean;
  base_url?: string | null;
  timeout_sec?: number | null;
  extras?: ManagementAiProviderExtras | null;
};

export type ManagementAiProviderPayload = {
  slug: string;
  title?: string | null;
  enabled?: boolean;
  base_url?: string | null;
  timeout_sec?: number | null;
  api_key?: string;
  extras?: ManagementAiProviderExtras | null;
};

export type ManagementAiFallbackRule = {
  id: string;
  primary_model: string;
  fallback_model: string;
  mode?: string | null;
  priority?: number | null;
  created_at?: string | null;
};

export type ManagementAiFallbackPayload = {
  primary_model: string;
  fallback_model: string;
  mode?: string | null;
  priority?: number | null;
};

export type ManagementAiMetricPoint = {
  provider?: string;
  model?: string;
  type?: string;
  count?: number;
  total?: number;
  total_usd?: number;
  avg_ms?: number;
};

export type ManagementAiSummary = {
  calls?: ManagementAiMetricPoint[];
  tokens_total?: ManagementAiMetricPoint[];
  cost_usd_total?: ManagementAiMetricPoint[];
  latency_avg_ms?: ManagementAiMetricPoint[];
};

export type ManagementAiPlaygroundRequest = {
  prompt: string;
  model?: string;
  model_id?: string;
  provider?: string;
};

export type ManagementAiPlaygroundResponse = {
  result?: string;
};

export type ManagementAuditEventMeta = {
  module?: string | null;
  verb?: string | null;
  resource_label?: string | null;
  result?: string | null;
};

export type ManagementAuditEvent = {
  id: string;
  created_at?: string | null;
  actor_id?: string | null;
  action?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  reason?: string | null;
  ip?: string | null;
  user_agent?: string | null;
  before?: unknown;
  after?: unknown;
  extra?: unknown;
  meta?: ManagementAuditEventMeta | null;
};

export type ManagementAuditFacets = {
  modules?: Record<string, number>;
  resource_types?: Record<string, number>;
  results?: Record<string, number>;
};

export type ManagementAuditTaxonomy = {
  actions?: string[];
};

export type ManagementAuditResponse = {
  items: ManagementAuditEvent[];
  page: number;
  page_size: number;
  has_more: boolean;
  next_page: number | null;
  facets?: ManagementAuditFacets;
  taxonomy?: ManagementAuditTaxonomy;
};

export type ManagementAuditUser = {
  id: string;
  username?: string | null;
};

export type SitePageType = 'landing' | 'collection' | 'article' | 'system';
export type SitePageStatus = 'draft' | 'published' | 'archived';

export type SitePageSummary = {
  id: string;
  slug: string;
  type: SitePageType;
  status: SitePageStatus;
  title: string;
  locale: string;
  owner?: string | null;
  updated_at?: string | null;
  published_version?: number | null;
  draft_version?: number | null;
  has_pending_review?: boolean | null;
};

export type SitePageListResponse = {
  items: SitePageSummary[];
  page: number;
  page_size: number;
  total?: number | null;
};

export type SitePageReviewStatus = 'none' | 'pending' | 'approved' | 'rejected';

export type SitePageDraft = {
  page_id: string;
  version: number;
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
  comment?: string | null;
  review_status: SitePageReviewStatus;
  updated_at?: string | null;
  updated_by?: string | null;
};

export type SiteValidationErrorEntry = {
  path: string;
  message: string;
  validator?: string;
};

export type SiteDraftValidationResult = {
  valid: boolean;
  data?: Record<string, unknown>;
  meta?: Record<string, unknown>;
  code?: string;
  errors?: {
    general: SiteValidationErrorEntry[];
    blocks: Record<string, SiteValidationErrorEntry[]>;
  };
};

export type SiteMetricsPeriod = '1d' | '7d' | '30d';

export type SiteMetricValue = {
  value: number | null;
  delta?: number | null;
  unit?: string | null;
  trend?: number[] | null;
};

export type SiteMetricAlert = {
  code: string;
  message: string;
  severity: 'info' | 'warning' | 'critical';
};

export type SiteMetricsRange = {
  start: string;
  end: string;
};

export type SitePageMetricsResponse = {
  page_id: string;
  period: string;
  range: SiteMetricsRange;
  previous_range?: SiteMetricsRange;
  status: string;
  source_lag_ms?: number | null;
  metrics: Record<string, SiteMetricValue>;
  alerts: SiteMetricAlert[];
};

export type SiteBlockMetricsTopPage = {
  page_id: string;
  slug: string;
  title: string;
  impressions?: number | null;
  clicks?: number | null;
  ctr?: number | null;
};

export type SiteGlobalBlockMetricsResponse = {
  block_id: string;
  period: string;
  range: SiteMetricsRange;
  previous_range?: SiteMetricsRange;
  status: string;
  source_lag_ms?: number | null;
  metrics: Record<string, SiteMetricValue>;
  alerts: SiteMetricAlert[];
  top_pages: SiteBlockMetricsTopPage[];
};

export type SiteDiffChange = 'added' | 'removed' | 'updated' | 'moved';

export type SitePageDiffEntry =
  | {
      type: 'block';
      blockId: string;
      change: SiteDiffChange;
      before?: Record<string, unknown> | null;
      after?: Record<string, unknown> | null;
      from?: number | null;
      to?: number | null;
    }
  | {
      type: 'data' | 'meta';
      field: string;
      change: Exclude<SiteDiffChange, 'moved'>;
      before?: unknown;
      after?: unknown;
    };

export type SitePageVersion = {
  id: string;
  page_id: string;
  version: number;
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
  comment?: string | null;
  diff?: SitePageDiffEntry[] | null;
  published_at?: string | null;
  published_by?: string | null;
};

export type SitePageHistoryResponse = {
  items: SitePageVersion[];
  total: number;
  limit: number;
  offset: number;
};

export type SitePageDraftDiffResponse = {
  draft_version: number;
  published_version?: number | null;
  diff: SitePageDiffEntry[];
};

export type SitePagePreviewLayout = {
  layout: string;
  generated_at: string;
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
};

export type SitePagePreviewResponse = {
  page: SitePageSummary;
  draft_version: number;
  published_version?: number | null;
  requested_version?: number | null;
  version_mismatch: boolean;
  layouts: Record<string, SitePagePreviewLayout>;
};

export type SiteAuditEntry = {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  snapshot?: Record<string, unknown> | null;
  actor?: string | null;
  created_at: string;
};

export type SiteAuditListResponse = {
  items: SiteAuditEntry[];
  total: number;
  limit: number;
  offset: number;
};

export type SiteGlobalBlockStatus = 'draft' | 'published' | 'archived';
export type SiteGlobalBlockReviewStatus = SitePageReviewStatus;

export type SiteGlobalBlock = {
  id: string;
  key: string;
  title: string;
  section: string;
  locale?: string | null;
  status: SiteGlobalBlockStatus;
  review_status: SiteGlobalBlockReviewStatus;
  requires_publisher: boolean;
  published_version?: number | null;
  draft_version?: number | null;
  usage_count?: number | null;
  comment?: string | null;
  data?: Record<string, unknown>;
  meta?: Record<string, unknown>;
  updated_at?: string | null;
  updated_by?: string | null;
  has_pending_publish?: boolean | null;
};

export type SiteGlobalBlockUsage = {
  block_id: string;
  page_id: string;
  slug: string;
  title: string;
  status: SitePageStatus;
  section: string;
  locale?: string | null;
  has_draft?: boolean | null;
  last_published_at?: string | null;
};

export type SiteGlobalBlockWarning = {
  code: string;
  page_id: string;
  message: string;
};

export type SiteGlobalBlockListResponse = {
  items: SiteGlobalBlock[];
  page: number;
  page_size: number;
  total?: number | null;
};

export type SiteGlobalBlockDetailResponse = {
  block: SiteGlobalBlock;
  usage: SiteGlobalBlockUsage[];
  warnings: SiteGlobalBlockWarning[];
};

export type SiteGlobalBlockPublishJob = {
  job_id: string;
  type: string;
  status: string;
};

export type SiteGlobalBlockAffectedPage = {
  page_id: string;
  slug: string;
  title: string;
  status: SitePageStatus;
  republish_status?: string | null;
};

export type SiteGlobalBlockPublishResponse = {
  id: string;
  published_version?: number | null;
  affected_pages: SiteGlobalBlockAffectedPage[];
  jobs: SiteGlobalBlockPublishJob[];
  audit_id: string;
  block: SiteGlobalBlock;
  usage: SiteGlobalBlockUsage[];
};

export type SiteGlobalBlockHistoryItem = {
  id: string;
  block_id: string;
  version: number;
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
  comment?: string | null;
  diff?: SitePageDiffEntry[] | null;
  published_at?: string | null;
  published_by?: string | null;
};

export type SiteGlobalBlockHistoryResponse = {
  items: SiteGlobalBlockHistoryItem[];
  total: number;
  limit: number;
  offset: number;
};


