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

export type NotificationPayload = {
  id: string;
  user_id: string;
  channel: string | null;
  title: string | null;
  message: string | null;
  type: string | null;
  priority: string;
  meta: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  read_at: string | null;
  is_read: boolean;
};

export type NotificationsListResponse = {
  items: NotificationPayload[];
  unread: number;
};

export type NotificationHistoryItem = NotificationPayload;

export type NotificationResponse = {
  notification: NotificationPayload;
};

export type NotificationBroadcastAudienceType = 'all_users' | 'segment' | 'explicit_users';

export type NotificationBroadcastStatus =
  | 'draft'
  | 'scheduled'
  | 'sending'
  | 'sent'
  | 'failed'
  | 'cancelled';

export type NotificationBroadcastAudience = {
  type: NotificationBroadcastAudienceType;
  filters: Record<string, unknown> | null;
  user_ids: string[] | null;
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
  items: NotificationBroadcast[];
  total: number;
  offset: number;
  limit: number;
  has_next: boolean;
  status_counts: Record<string, number>;
  recipients: number;
};

export type NotificationBroadcastListParams = {
  limit?: number;
  offset?: number;
  statuses?: NotificationBroadcastStatus[] | null;
  search?: string | null;
};

export type NotificationBroadcastAudienceInput = {
  type: NotificationBroadcastAudienceType;
  filters?: Record<string, unknown> | null;
  user_ids?: string[] | null;
};

export type NotificationBroadcastCreatePayload = {
  title: string;
  body?: string | null;
  template_id?: string | null;
  audience: NotificationBroadcastAudienceInput;
  created_by: string;
  scheduled_at?: string | null;
};

export type NotificationBroadcastUpdatePayload = {
  title: string;
  body?: string | null;
  template_id?: string | null;
  audience: NotificationBroadcastAudienceInput;
  scheduled_at?: string | null;
};

export type NotificationHistoryResponse = NotificationsListResponse;

export type NotificationTemplate = {
  id: string;
  slug: string;
  name: string;
  description?: string | null;
  subject?: string | null;
  body: string;
  locale?: string | null;
  variables: Record<string, unknown>;
  meta: Record<string, unknown>;
  created_by?: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type NotificationTemplatePayload = {
  id?: string;
  slug?: string | null;
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
  items: NotificationTemplate[];
};

export type NotificationPreferenceValue = {
  enabled: boolean;
  config?: Record<string, unknown> | null;
};

export type NotificationPreferences = Record<string, unknown>;

export type NotificationPreferencesResponse = {
  preferences?: NotificationPreferences;
};

