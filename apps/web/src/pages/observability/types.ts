export type HttpPathStats = {
  method: string;
  path: string;
  requests_total: number;
  error5xx_total?: number;
  error5xx_ratio: number;
  avg_duration_ms: number;
};

export type HttpSummary = {
  paths: HttpPathStats[];
};

export type LLMCallMetric = {
  type: string;
  provider: string;
  model: string;
  stage: string;
  count: number;
};

export type LLMLatencyMetric = {
  provider: string;
  model: string;
  stage: string;
  avg_ms: number;
};

export type LLMTokensMetric = {
  provider: string;
  model: string;
  stage: string;
  type: 'prompt' | 'completion' | string;
  total: number;
};

export type LLMCostMetric = {
  provider: string;
  model: string;
  stage: string;
  total_usd: number;
};

export type LLMSummary = {
  calls: LLMCallMetric[];
  latency_avg_ms: LLMLatencyMetric[];
  tokens_total: LLMTokensMetric[];
  cost_usd_total: LLMCostMetric[];
};

export type WorkerStageSummary = {
  count: number;
  avg_ms: number;
};

export type WorkersSummary = {
  jobs: Record<string, number>;
  job_avg_ms: number;
  cost_usd_total: number;
  tokens: {
    prompt: number;
    completion: number;
  };
  stages: Record<string, WorkerStageSummary>;
};

export type TransitionModeSummary = {
  mode: string;
  avg_latency_ms: number;
  no_route_ratio: number;
  fallback_ratio: number;
  entropy: number;
  repeat_rate: number;
  novelty_rate: number;
  count: number;
};

export type EventHandlerRow = {
  event: string;
  handler: string;
  success: number;
  failure: number;
  total: number;
  avg_ms: number;
};

export type EventsSummary = {
  counts: Record<string, number>;
  handlers: EventHandlerRow[];
};

export type UXSummary = {
  time_to_first_save_avg_s: number;
  published_tagged_ratio: number;
  save_next_total: number;
};

export type RumNavigationAverages = {
  ttfb_ms: number | null;
  dom_content_loaded_ms: number | null;
  load_event_ms: number | null;
};

export type RumSummary = {
  window: number;
  counts: Record<string, number>;
  login_attempt_avg_ms: number | null;
  navigation_avg: RumNavigationAverages;
};

export type RumEventRow = {
  ts: string | number;
  event: string;
  url: string;
  data?: Record<string, unknown> | null;
};

export type TelemetryOverview = {
  llm: LLMSummary | null;
  workers: WorkersSummary | null;
  events: EventsSummary;
  transitions: TransitionModeSummary[];
  ux: UXSummary;
  rum: RumSummary;
};
