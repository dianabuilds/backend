export * from './users';
export * from './ai-rules';
export * from './overview';

import {
  createModerationUserNote,
  createModerationUserSanction,
  fetchModerationUserDetail,
  fetchModerationUsers,
  updateModerationUserRoles,
} from './users';
import { fetchModerationOverview } from './overview';
import {
  createModerationAIRule,
  deleteModerationAIRule,
  fetchModerationAIRules,
  updateModerationAIRule,
} from './ai-rules';

export const moderationApi = {
  fetchModerationUsers,
  fetchModerationUserDetail,
  updateModerationUserRoles,
  createModerationUserSanction,
  createModerationUserNote,
  fetchModerationOverview,
  fetchModerationAIRules,
  createModerationAIRule,
  updateModerationAIRule,
  deleteModerationAIRule,
};
