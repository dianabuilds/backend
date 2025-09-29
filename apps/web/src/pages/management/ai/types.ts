export type ModelParams = {
  limits?: {
    daily_tokens?: number | null;
    monthly_tokens?: number | null;
  };
  usage?: {
    content?: boolean;
    quests?: boolean;
    moderation?: boolean;
  };
  fallback_priority?: number | null;
  mode?: string | null;
};

export type Model = {
  id: string;
  name: string;
  provider_slug: string;
  version?: string | null;
  status?: string | null;
  is_default?: boolean | null;
  params?: ModelParams | null;
  updated_at?: string | null;
};

export type Provider = {
  slug: string;
  title?: string | null;
  enabled?: boolean;
  base_url?: string | null;
  timeout_sec?: number | null;
  extras?: {
    retries?: number | null;
  } | null;
};

export type FallbackRule = {
  id: string;
  primary_model: string;
  fallback_model: string;
  mode?: string | null;
  priority?: number | null;
  created_at?: string | null;
};

export type MetricPoint = {
  provider?: string;
  model?: string;
  type?: string;
  count?: number;
  total?: number;
  total_usd?: number;
  avg_ms?: number;
};

export type LLMSummary = {
  calls?: MetricPoint[];
  tokens_total?: MetricPoint[];
  cost_usd_total?: MetricPoint[];
  latency_avg_ms?: MetricPoint[];
};

export type ModelFormState = {
  id?: string;
  name: string;
  provider_slug: string;
  version?: string | null;
  status: string;
  is_default?: boolean;
  params: ModelParams;
};

export type ProviderFormState = {
  slug: string;
  title?: string | null;
  enabled: boolean;
  base_url?: string | null;
  timeout_sec?: number | null;
  retries?: number | null;
  api_key?: string;
  originalSlug?: string;
};

export type UsageRow = {
  key: string;
  provider: string;
  model: string;
  calls: number;
  errors: number;
  promptTokens: number;
  completionTokens: number;
  costUsd: number;
  latencyMs: number | null;
};
