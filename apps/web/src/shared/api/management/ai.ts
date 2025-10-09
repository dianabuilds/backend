import { apiDelete, apiGet, apiPost } from '../client';
import type {
  ManagementAiFallbackPayload,
  ManagementAiFallbackRule,
  ManagementAiModel,
  ManagementAiModelPayload,
  ManagementAiPlaygroundRequest,
  ManagementAiPlaygroundResponse,
  ManagementAiProvider,
  ManagementAiProviderPayload,
  ManagementAiSummary,
} from '../../types/management';

const AI_ADMIN_BASE = '/v1/ai/admin';
const TELEMETRY_SUMMARY_PATH = '/v1/admin/telemetry/llm/summary';

type ListResponse<T> = {
  items?: T[] | null;
};

export async function fetchManagementAiModels(): Promise<ManagementAiModel[]> {
  const response = await apiGet<ListResponse<ManagementAiModel>>(`${AI_ADMIN_BASE}/models`);
  return response?.items?.filter(Boolean) ?? [];
}

export async function saveManagementAiModel(payload: ManagementAiModelPayload): Promise<ManagementAiModel> {
  return apiPost<ManagementAiModel>(`${AI_ADMIN_BASE}/models`, payload);
}

export async function deleteManagementAiModel(id: string): Promise<void> {
  await apiDelete(`${AI_ADMIN_BASE}/models/${encodeURIComponent(id)}`);
}

export async function fetchManagementAiProviders(): Promise<ManagementAiProvider[]> {
  const response = await apiGet<ListResponse<ManagementAiProvider>>(`${AI_ADMIN_BASE}/providers`);
  return response?.items?.filter(Boolean) ?? [];
}

export async function saveManagementAiProvider(payload: ManagementAiProviderPayload): Promise<ManagementAiProvider> {
  return apiPost<ManagementAiProvider>(`${AI_ADMIN_BASE}/providers`, payload);
}

export async function fetchManagementAiFallbacks(): Promise<ManagementAiFallbackRule[]> {
  const response = await apiGet<ListResponse<ManagementAiFallbackRule>>(`${AI_ADMIN_BASE}/fallbacks`);
  return response?.items?.filter(Boolean) ?? [];
}

export async function createManagementAiFallback(payload: ManagementAiFallbackPayload): Promise<ManagementAiFallbackRule> {
  return apiPost<ManagementAiFallbackRule>(`${AI_ADMIN_BASE}/fallbacks`, payload);
}

export async function deleteManagementAiFallback(id: string): Promise<void> {
  await apiDelete(`${AI_ADMIN_BASE}/fallbacks/${encodeURIComponent(id)}`);
}

export async function fetchManagementAiSummary(): Promise<ManagementAiSummary> {
  const summary = await apiGet<ManagementAiSummary>(TELEMETRY_SUMMARY_PATH);
  return summary ?? {};
}

export async function runManagementAiPlayground(
  payload: ManagementAiPlaygroundRequest,
): Promise<ManagementAiPlaygroundResponse> {
  return apiPost<ManagementAiPlaygroundResponse>(`${AI_ADMIN_BASE}/playground`, payload);
}
