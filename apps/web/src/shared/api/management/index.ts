export * from './billing';
export * from './ai';
export * from './flags';
export * from './integrations';
export * from './system';
export * from './audit';

import {
  fetchBillingKpi,
  fetchBillingProviders,
  saveBillingProvider,
  deleteBillingProvider,
  fetchBillingTransactions,
  fetchBillingContracts,
  saveBillingContract,
  deleteBillingContract,
  fetchBillingContractEvents,
  fetchBillingCryptoConfig,
  updateBillingCryptoConfig,
  fetchBillingMetrics,
  fetchBillingPlans,
  saveBillingPlan,
  deleteBillingPlan,
  updateBillingPlanLimits,
  fetchBillingPlanHistory,
} from './billing';
import {
  fetchManagementAiModels,
  saveManagementAiModel,
  deleteManagementAiModel,
  fetchManagementAiProviders,
  saveManagementAiProvider,
  fetchManagementAiFallbacks,
  createManagementAiFallback,
  deleteManagementAiFallback,
  fetchManagementAiSummary,
  runManagementAiPlayground,
} from './ai';
import {
  fetchFeatureFlags,
  saveFeatureFlag,
  deleteFeatureFlag,
  searchFeatureFlagUsers,
} from './flags';
import {
  fetchIntegrationsOverview,
  fetchManagementConfig,
  sendNotificationTest,
} from './integrations';
import { fetchSystemConfig, fetchSystemOverview } from './system';
import {
  fetchAuditEvents,
  fetchAuditUsers,
} from './audit';

export const managementApi = {
  fetchBillingKpi,
  fetchBillingProviders,
  saveBillingProvider,
  deleteBillingProvider,
  fetchBillingTransactions,
  fetchBillingContracts,
  saveBillingContract,
  deleteBillingContract,
  fetchBillingContractEvents,
  fetchBillingCryptoConfig,
  updateBillingCryptoConfig,
  fetchBillingMetrics,
  fetchBillingPlans,
  saveBillingPlan,
  deleteBillingPlan,
  updateBillingPlanLimits,
  fetchBillingPlanHistory,
  fetchManagementAiModels,
  saveManagementAiModel,
  deleteManagementAiModel,
  fetchManagementAiProviders,
  saveManagementAiProvider,
  fetchManagementAiFallbacks,
  createManagementAiFallback,
  deleteManagementAiFallback,
  fetchManagementAiSummary,
  runManagementAiPlayground,
  fetchFeatureFlags,
  saveFeatureFlag,
  deleteFeatureFlag,
  searchFeatureFlagUsers,
  fetchIntegrationsOverview,
  fetchManagementConfig,
  sendNotificationTest,
  fetchSystemOverview,
  fetchSystemConfig,
  fetchAuditEvents,
  fetchAuditUsers,
};
