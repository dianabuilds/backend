export type NotificationChannelStatus = 'required' | 'recommended' | 'optional';

export type NotificationChannelOverview = {
  key: string;
  label: string;
  status: NotificationChannelStatus;
  opt_in: boolean;
};

export type NotificationTopicChannel = {
  key: string;
  label: string;
  opt_in: boolean;
  delivery: string;
  locked?: boolean;
  digest?: string | null;
  supports_digest?: boolean;
};

export type NotificationTopicOverview = {
  key: string;
  label: string;
  description?: string | null;
  channels: NotificationTopicChannel[];
};

export type NotificationSummaryOverview = {
  active_channels: number;
  total_channels: number;
  email_digest?: string | null;
  updated_at?: string | null;
};

export type NotificationsChannelsOverview = {
  channels: NotificationChannelOverview[];
  topics: NotificationTopicOverview[];
  summary: NotificationSummaryOverview;
};

export type NotificationsChannelsOverviewResponse = {
  overview?: NotificationsChannelsOverview;
};

export type NotificationHistoryItem = {
  id: string;
  title?: string | null;
  message?: string | null;
  type?: string | null;
  priority?: string | null;
  created_at?: string | null;
  read_at?: string | null;
  meta?: Record<string, unknown> | null;
};

export type NotificationHistoryResponse = {
  items?: NotificationHistoryItem[];
};

export type NotificationTemplate = {
  id: string;
  slug: string;
  name: string;
  description?: string | null;
  subject?: string | null;
  body: string;
  locale?: string | null;
  variables?: Record<string, unknown> | null;
  meta?: Record<string, unknown> | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
};

export type NotificationTemplatePayload = {
  id?: string;
  name: string;
  description?: string | null;
  subject?: string | null;
  body: string;
  locale?: string | null;
  variables?: Record<string, unknown> | null;
  meta?: Record<string, unknown> | null;
  created_by?: string | null;
};

export type NotificationTemplatesResponse = {
  items?: NotificationTemplate[];
};

export type NotificationAudienceType = 'all_users' | 'segment' | 'explicit_users';

export type NotificationBroadcastStatus = 'draft' | 'scheduled' | 'sending' | 'sent' | 'failed' | 'cancelled';

export type NotificationBroadcastAudience = {
  type: NotificationAudienceType;
  filters?: Record<string, unknown> | null;
  user_ids?: string[] | null;
};

export type NotificationBroadcast = {
  id: string;
  title: string;
  body: string | null;
  template_id: string | null;
  audience: NotificationBroadcastAudience;
  status: NotificationBroadcastStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
  scheduled_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  total: number;
  sent: number;
  failed: number;
};

export type NotificationBroadcastListResponse = {
  items?: NotificationBroadcast[];
  total?: number;
  offset?: number;
  limit?: number;
  has_next?: boolean;
  status_counts?: Record<string, number>;
  recipients?: number;
};

export type NotificationBroadcastListParams = {
  limit?: number;
  offset?: number;
  status?: NotificationBroadcastStatus | 'all';
  search?: string;
};

export type NotificationBroadcastPayload = {
  title: string;
  body: string | null;
  template_id: string | null;
  audience: NotificationBroadcastAudience;
  scheduled_at: string | null;
  created_by?: string | null;
};

export type NotificationPreferenceValue = {
  enabled: boolean;
  config?: Record<string, unknown> | null;
};

export type NotificationPreferences = Record<string, unknown>;

export type NotificationPreferencesResponse = {
  preferences?: NotificationPreferences;
};

