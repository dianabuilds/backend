import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@shared/auth';
import { SettingsProvider } from '@shared/settings';
import { ToastProvider } from '@ui';
import { Guard } from './guards';
import { RouteFallback } from './fallback';
import { AppLayout } from '../layout/AppLayout';

const DashboardPage = React.lazy(() => import('../pages/dashboard/Dashboard'));
const ProfilePage = React.lazy(() => import('../pages/profile/Profile'));
const NotificationSettingsPage = React.lazy(() => import('../pages/notifications/Settings'));
const SecuritySettingsPage = React.lazy(() => import('../pages/security/Security'));
const BillingPage = React.lazy(() => import('../pages/billing/Billing'));
const NodesOverviewPage = React.lazy(() => import('../pages/content/nodes/NodesOverviewPage'));
const NodesPage = React.lazy(() => import('../pages/content/nodes/NodesPage'));
const NodeCreatePage = React.lazy(() => import('../pages/content/nodes/NodeCreatePage'));

const loadAdminNodes = () => import('../pages/admin/nodes');
const NodeEngagementPage = React.lazy(() =>
  loadAdminNodes().then((module) => ({ default: module.NodeEngagementPage })),
);
const NodeModerationPage = React.lazy(() =>
  loadAdminNodes().then((module) => ({ default: module.NodeModerationPage })),
);

const QuestsOverviewPage = React.lazy(() => import('../pages/content/quests/QuestsOverviewPage'));
const QuestsPage = React.lazy(() => import('../pages/content/quests/QuestsPage'));
const QuestCreatePage = React.lazy(() => import('../pages/content/quests/QuestCreatePage'));
const QuestAIStudioPage = React.lazy(() => import('../pages/content/quests/QuestAIStudioPage'));
const NodeTagsPage = React.lazy(() => import('../pages/content/tags/NodeTagsPage'));
const QuestTagsPage = React.lazy(() => import('../pages/content/tags/QuestTagsPage'));
const RelationsPage = React.lazy(() => import('../pages/content/relations/RelationsPage'));
const WorldsPage = React.lazy(() => import('../pages/content/worlds/WorldsPage'));
const WorldsCreatePage = React.lazy(() => import('../pages/content/worlds/WorldsCreatePage'));
const CharacterCardPage = React.lazy(() => import('../pages/content/worlds/CharacterCardPage'));
const ImportExportPage = React.lazy(() => import('../pages/content/import-export/ImportExportPage'));

const NotificationsInboxSettingsPage = React.lazy(
  () => import('../pages/settings/NotificationsInboxPage'),
);
const NotificationsBroadcastsPage = React.lazy(() => import('../pages/notifications/BroadcastsPage'));
const NotificationsTemplatesPage = React.lazy(() => import('../pages/notifications/TemplatesPage'));
const NotificationsChannelsPage = React.lazy(() => import('../pages/notifications/ChannelsPage'));
const NotificationsHistoryPage = React.lazy(() => import('../pages/notifications/HistoryPage'));

const ObservabilityOverview = React.lazy(() => import('../pages/observability/Overview'));
const ObservabilityAPI = React.lazy(() => import('../pages/observability/API'));
const ObservabilityLLM = React.lazy(() => import('../pages/observability/LLM'));
const ObservabilityWorkers = React.lazy(() => import('../pages/observability/Workers'));
const ObservabilityTransitions = React.lazy(() => import('../pages/observability/Transitions'));
const ObservabilityEvents = React.lazy(() => import('../pages/observability/Events'));
const ObservabilityRUM = React.lazy(() => import('../pages/observability/RUM'));

const ManagementAI = React.lazy(() => import('../pages/management/AI'));
const ManagementHome = React.lazy(() => import('../pages/management/Home'));
const ManagementDevBlog = React.lazy(() => import('../pages/management/DevBlog'));
const ManagementPayments = React.lazy(() => import('../pages/management/Payments'));
const PaymentsMonitoring = React.lazy(() => import('../pages/management/PaymentsMonitoring'));
const ManagementTariffs = React.lazy(() => import('../pages/management/Tariffs'));
const ManagementFlags = React.lazy(() => import('../pages/management/Flags'));
const ManagementIntegrations = React.lazy(() => import('../pages/management/Integrations'));
const ManagementSystem = React.lazy(() => import('../pages/management/System'));
const ManagementAudit = React.lazy(() => import('../pages/management/Audit'));

const loadModerationCases = () => import('../pages/moderation/Cases');
const ModerationOverview = React.lazy(() => import('../pages/moderation/Overview'));
const ModerationCases = React.lazy(() => loadModerationCases());
const CaseDetailPage = React.lazy(() =>
  loadModerationCases().then((module) => ({ default: module.CaseDetailPage })),
);
const ModerationUsers = React.lazy(() => import('../pages/moderation/Users'));
const ModerationAIRules = React.lazy(() => import('../pages/moderation/AIRules'));

function PrivateProviders({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <SettingsProvider>
        <ToastProvider>{children}</ToastProvider>
      </SettingsProvider>
    </AuthProvider>
  );
}

type GuardedElementOptions = {
  requireAdmin?: boolean;
};

function withLayout(element: React.ReactElement, options: GuardedElementOptions = {}): React.ReactElement {
  return (
    <Guard requireAdmin={options.requireAdmin}>
      <AppLayout>
        <React.Suspense fallback={<RouteFallback />}>{element}</React.Suspense>
      </AppLayout>
    </Guard>
  );
}

export default function PrivateAppRoutes(): React.ReactElement {
  return (
    <PrivateProviders>
      <Routes>
        <Route path="/dashboard" element={withLayout(<DashboardPage />)} />

        <Route path="/nodes" element={withLayout(<NodesOverviewPage />)} />
        <Route path="/nodes/library" element={withLayout(<NodesPage />)} />
        <Route path="/nodes/new" element={withLayout(<NodeCreatePage />)} />
        <Route path="/nodes/tags" element={withLayout(<NodeTagsPage />)} />
        <Route path="/nodes/relations" element={withLayout(<RelationsPage />)} />
        <Route
          path="/admin/nodes/:nodeId"
          element={withLayout(<NodeEngagementPage />, { requireAdmin: true })}
        />
        <Route
          path="/admin/nodes/:nodeId/moderation"
          element={withLayout(<NodeModerationPage />, { requireAdmin: true })}
        />

        <Route path="/quests" element={withLayout(<QuestsOverviewPage />)} />
        <Route path="/quests/library" element={withLayout(<QuestsPage />)} />
        <Route path="/quests/new" element={withLayout(<QuestCreatePage />)} />
        <Route path="/quests/tags" element={withLayout(<QuestTagsPage />)} />
        <Route path="/quests/worlds" element={withLayout(<WorldsPage />)} />
        <Route path="/quests/worlds/new" element={withLayout(<WorldsCreatePage />)} />
        <Route path="/quests/worlds/edit" element={withLayout(<WorldsCreatePage />)} />
        <Route path="/quests/characters/new" element={withLayout(<CharacterCardPage />)} />
        <Route path="/quests/characters/edit" element={withLayout(<CharacterCardPage />)} />
        <Route path="/quests/ai-studio" element={withLayout(<QuestAIStudioPage />)} />

        <Route
          path="/settings/notifications/inbox"
          element={withLayout(<NotificationsInboxSettingsPage />)}
        />
        <Route path="/notifications" element={withLayout(<NotificationsBroadcastsPage />)} />
        <Route path="/notifications/templates" element={withLayout(<NotificationsTemplatesPage />)} />
        <Route path="/notifications/channels" element={withLayout(<NotificationsChannelsPage />)} />
        <Route path="/notifications/history" element={withLayout(<NotificationsHistoryPage />)} />

        <Route path="/tools/import-export" element={withLayout(<ImportExportPage />)} />
        <Route path="/management/home" element={withLayout(<ManagementHome />, { requireAdmin: true })} />
        <Route path="/management/dev-blog" element={withLayout(<ManagementDevBlog />, { requireAdmin: true })} />

        <Route path="/billing" element={withLayout(<BillingPage />)} />
        <Route
          path="/billing/payments"
          element={withLayout(<ManagementPayments />, { requireAdmin: true })}
        />
        <Route
          path="/billing/payments/monitoring"
          element={withLayout(<PaymentsMonitoring />, { requireAdmin: true })}
        />
        <Route
          path="/billing/tariffs"
          element={withLayout(<ManagementTariffs />, { requireAdmin: true })}
        />

        <Route path="/platform/ai" element={withLayout(<ManagementAI />)} />
        <Route path="/platform/flags" element={withLayout(<ManagementFlags />)} />
        <Route path="/platform/integrations" element={withLayout(<ManagementIntegrations />)} />
        <Route path="/platform/system" element={withLayout(<ManagementSystem />)} />
        <Route path="/platform/audit" element={withLayout(<ManagementAudit />)} />

        <Route path="/moderation" element={withLayout(<ModerationOverview />)} />
        <Route path="/moderation/cases" element={withLayout(<ModerationCases />)} />
        <Route path="/moderation/cases/:caseId" element={withLayout(<CaseDetailPage />)} />
        <Route path="/moderation/users" element={withLayout(<ModerationUsers />)} />
        <Route path="/moderation/ai-rules" element={withLayout(<ModerationAIRules />)} />

        <Route
          path="/observability"
          element={withLayout(<ObservabilityOverview />, { requireAdmin: true })}
        />
        <Route
          path="/observability/api"
          element={withLayout(<ObservabilityAPI />, { requireAdmin: true })}
        />
        <Route
          path="/observability/llm"
          element={withLayout(<ObservabilityLLM />, { requireAdmin: true })}
        />
        <Route
          path="/observability/workers"
          element={withLayout(<ObservabilityWorkers />, { requireAdmin: true })}
        />
        <Route
          path="/observability/transitions"
          element={withLayout(<ObservabilityTransitions />, { requireAdmin: true })}
        />
        <Route
          path="/observability/events"
          element={withLayout(<ObservabilityEvents />, { requireAdmin: true })}
        />
        <Route
          path="/observability/rum"
          element={withLayout(<ObservabilityRUM />, { requireAdmin: true })}
        />

        <Route path="/profile" element={withLayout(<ProfilePage />)} />
        <Route path="/settings/security" element={withLayout(<SecuritySettingsPage />)} />
        <Route path="/settings/notifications" element={withLayout(<NotificationSettingsPage />)} />

        <Route path="/management/notifications" element={<Navigate to="/notifications" replace />} />
        <Route path="/management/payments" element={<Navigate to="/billing/payments" replace />} />
        <Route
          path="/management/payments/monitoring"
          element={<Navigate to="/billing/payments/monitoring" replace />}
        />
        <Route path="/management/tariffs" element={<Navigate to="/billing/tariffs" replace />} />
        <Route path="/management/ai" element={<Navigate to="/platform/ai" replace />} />
        <Route path="/management/flags" element={<Navigate to="/platform/flags" replace />} />
        <Route path="/management/integrations" element={<Navigate to="/platform/integrations" replace />} />
        <Route path="/management/system" element={<Navigate to="/platform/system" replace />} />
        <Route path="/management/audit" element={<Navigate to="/platform/audit" replace />} />
        <Route path="/notifications/settings" element={<Navigate to="/settings/notifications" replace />} />
        <Route path="/content" element={<Navigate to="/nodes" replace />} />
        <Route path="/content/nodes" element={<Navigate to="/nodes/library" replace />} />
        <Route path="/content/nodes/new" element={<Navigate to="/nodes/new" replace />} />
        <Route path="/content/quests" element={<Navigate to="/quests/library" replace />} />
        <Route path="/content/quests/new" element={<Navigate to="/quests/new" replace />} />
        <Route path="/content/tags" element={<Navigate to="/nodes/tags" replace />} />
        <Route path="/content/relations" element={<Navigate to="/nodes/relations" replace />} />
        <Route path="/content/worlds" element={<Navigate to="/quests/worlds" replace />} />
        <Route path="/content/worlds/new" element={<Navigate to="/quests/worlds/new" replace />} />
        <Route path="/content/worlds/edit" element={<Navigate to="/quests/worlds/edit" replace />} />
        <Route path="/content/characters/new" element={<Navigate to="/quests/characters/new" replace />} />
        <Route path="/content/characters/edit" element={<Navigate to="/quests/characters/edit" replace />} />
        <Route path="/content/drafts" element={<Navigate to="/nodes/library?status=draft" replace />} />
        <Route path="/content/import-export" element={<Navigate to="/tools/import-export" replace />} />
      </Routes>
    </PrivateProviders>
  );
}
