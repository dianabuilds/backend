export * from './channels';
export * from './history';
export * from './preferences';
export * from './broadcasts';
export * from './templates';

import { fetchNotificationsChannelsOverview } from './channels';
import { fetchNotificationsHistory } from './history';
import { fetchNotificationPreferences, updateNotificationPreferences } from './preferences';
import { fetchNotificationBroadcasts } from './broadcasts';
import {
  deleteNotificationTemplate,
  fetchNotificationTemplates,
  saveNotificationTemplate,
} from './templates';

export const notificationsApi = {
  fetchChannelsOverview: fetchNotificationsChannelsOverview,
  fetchHistory: fetchNotificationsHistory,
  fetchPreferences: fetchNotificationPreferences,
  updatePreferences: updateNotificationPreferences,
  fetchBroadcasts: fetchNotificationBroadcasts,
  fetchTemplates: fetchNotificationTemplates,
  saveTemplate: saveNotificationTemplate,
  deleteTemplate: deleteNotificationTemplate,
};
