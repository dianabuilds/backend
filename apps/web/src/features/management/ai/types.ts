import type {
  ManagementAiFallbackRule,
  ManagementAiMetricPoint,
  ManagementAiModel,
  ManagementAiModelParams,
  ManagementAiProvider,
  ManagementAiSummary,
} from '@shared/types/management';

export type ModelParams = ManagementAiModelParams;
export type Model = ManagementAiModel;
export type Provider = ManagementAiProvider;
export type FallbackRule = ManagementAiFallbackRule;
export type MetricPoint = ManagementAiMetricPoint;
export type LLMSummary = ManagementAiSummary;

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

