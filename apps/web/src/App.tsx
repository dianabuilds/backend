import React from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import LoginPage from './pages/auth/Login';
import { AuthProvider, useAuth } from './shared/auth/AuthContext';
import { SettingsProvider } from './shared/settings/SettingsContext';
import { AppLayout } from './layout/AppLayout';
import DashboardPage from './pages/dashboard/Dashboard';
import ProfilePage from './pages/profile/Profile';
import NotificationSettingsPage from './pages/notifications/Settings';
import SecuritySettingsPage from './pages/security/Security';
import BillingPage from './pages/billing/Billing';
import NodesOverviewPage from './pages/content/nodes/NodesOverviewPage';
import NodesPage from './pages/content/nodes/NodesPageEnhanced';
import NodeCreatePage from './pages/content/nodes/NodeCreatePage';
import NodePublicPage from './pages/public/NodePublicPage';
import QuestsOverviewPage from './pages/content/quests/QuestsOverviewPage';
import QuestsPage from './pages/content/quests/QuestsPage';
import QuestCreatePage from './pages/content/quests/QuestCreatePage';
import QuestAIStudioPage from './pages/content/quests/QuestAIStudioPage';
import NodeTagsPage from './pages/content/tags/NodeTagsPage';
import QuestTagsPage from './pages/content/tags/QuestTagsPage';
import RelationsPage from './pages/content/relations/RelationsPage';
import WorldsPage from './pages/content/worlds/WorldsPage';
import WorldsCreatePage from './pages/content/worlds/WorldsCreatePage';
import CharacterCardPage from './pages/content/worlds/CharacterCardPage';
import ImportExportPage from './pages/content/import-export/ImportExportPage';
import NotificationsInboxSettingsPage from './pages/settings/NotificationsInboxPage';
import NotificationsBroadcastsPage from './pages/notifications/BroadcastsPage';
import NotificationsTemplatesPage from './pages/notifications/TemplatesPage';
import NotificationsChannelsPage from './pages/notifications/ChannelsPage';
import NotificationsHistoryPage from './pages/notifications/HistoryPage';
import { rumEvent } from './shared/rum';
import ObservabilityOverview from './pages/observability/Overview';
import ObservabilityAPI from './pages/observability/API';
import ObservabilityLLM from './pages/observability/LLM';
import ObservabilityWorkers from './pages/observability/Workers';
import ObservabilityTransitions from './pages/observability/Transitions';
import ObservabilityEvents from './pages/observability/Events';
import ObservabilityRUM from './pages/observability/RUM';
import ManagementAI from './pages/management/AI';
import ManagementPayments from './pages/management/Payments';
import PaymentsMonitoring from './pages/management/PaymentsMonitoring';
import ManagementTariffs from './pages/management/Tariffs';
import ManagementFlags from './pages/management/Flags';
import ManagementIntegrations from './pages/management/Integrations';
import ManagementSystem from './pages/management/System';
import ManagementAudit from './pages/management/Audit';
import ModerationOverview from './pages/moderation/Overview';
import ModerationUsers from './pages/moderation/Users';
import ModerationContent from './pages/moderation/Content';
import ModerationReports from './pages/moderation/Reports';
import ModerationTickets from './pages/moderation/Tickets';
import ModerationAppeals from './pages/moderation/Appeals';
import ModerationAIRules from './pages/moderation/AIRules';

const ADMIN_ROLES = ['admin', 'superadmin', 'owner', 'platform_admin', 'billing_admin'];

function RequireAuth({ children }: { children: JSX.Element }) {
  const { isAuthenticated, isReady } = useAuth();
  if (!isReady) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

function RequireAdmin({ children }: { children: JSX.Element }) {
  const { isAuthenticated, isReady, user } = useAuth();
  if (!isReady) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  const roles: string[] = [];
  if (Array.isArray(user?.roles)) {
    roles.push(...user.roles.map((role) => String(role).toLowerCase()));
  }
  if (user?.role) {
    roles.push(String(user.role).toLowerCase());
  }
  if (!roles.some((role) => ADMIN_ROLES.includes(role))) {
    return <Navigate to="/billing" replace />;
  }
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <SettingsProvider>
      <BrowserRouter>
        <RumRouteTracker />
        <Routes>
          {/* Public */}
          <Route path="/n/:slug" element={<NodePublicPage />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Home */}
          <Route path="/" element={<RequireAuth><AppLayout><DashboardPage /></AppLayout></RequireAuth>} />
          <Route path="/dashboard" element={<RequireAuth><AppLayout><DashboardPage /></AppLayout></RequireAuth>} />

          {/* Nodes workspace */}
          <Route path="/nodes" element={<RequireAuth><AppLayout><NodesOverviewPage /></AppLayout></RequireAuth>} />
          <Route path="/nodes/library" element={<RequireAuth><AppLayout><NodesPage /></AppLayout></RequireAuth>} />
          <Route path="/nodes/new" element={<RequireAuth><AppLayout><NodeCreatePage /></AppLayout></RequireAuth>} />
          <Route path="/nodes/tags" element={<RequireAuth><AppLayout><NodeTagsPage /></AppLayout></RequireAuth>} />
          <Route path="/nodes/relations" element={<RequireAuth><AppLayout><RelationsPage /></AppLayout></RequireAuth>} />

          {/* Quests workspace */}
          <Route path="/quests" element={<RequireAuth><AppLayout><QuestsOverviewPage /></AppLayout></RequireAuth>} />
          <Route path="/quests/library" element={<RequireAuth><AppLayout><QuestsPage /></AppLayout></RequireAuth>} />
          <Route path="/quests/new" element={<RequireAuth><AppLayout><QuestCreatePage /></AppLayout></RequireAuth>} />
          <Route path="/quests/tags" element={<RequireAuth><AppLayout><QuestTagsPage /></AppLayout></RequireAuth>} />
          <Route path="/quests/worlds" element={<RequireAuth><AppLayout><WorldsPage /></AppLayout></RequireAuth>} />
          <Route path="/quests/worlds/new" element={<RequireAuth><AppLayout><WorldsCreatePage /></AppLayout></RequireAuth>} />
          <Route path="/quests/worlds/edit" element={<RequireAuth><AppLayout><WorldsCreatePage /></AppLayout></RequireAuth>} />
          <Route path="/quests/characters/new" element={<RequireAuth><AppLayout><CharacterCardPage /></AppLayout></RequireAuth>} />
          <Route path="/quests/characters/edit" element={<RequireAuth><AppLayout><CharacterCardPage /></AppLayout></RequireAuth>} />
          <Route path="/quests/ai-studio" element={<RequireAuth><AppLayout><QuestAIStudioPage /></AppLayout></RequireAuth>} />

          {/* Notifications workspace */}
          <Route path="/settings/notifications/inbox" element={<RequireAuth><AppLayout><NotificationsInboxSettingsPage /></AppLayout></RequireAuth>} />
          <Route path="/notifications" element={<RequireAuth><AppLayout><NotificationsBroadcastsPage /></AppLayout></RequireAuth>} />
          <Route path="/notifications/templates" element={<RequireAuth><AppLayout><NotificationsTemplatesPage /></AppLayout></RequireAuth>} />
          <Route path="/notifications/channels" element={<RequireAuth><AppLayout><NotificationsChannelsPage /></AppLayout></RequireAuth>} />
          <Route path="/notifications/history" element={<RequireAuth><AppLayout><NotificationsHistoryPage /></AppLayout></RequireAuth>} />

          {/* Shared tooling */}
          <Route path="/tools/import-export" element={<RequireAuth><AppLayout><ImportExportPage /></AppLayout></RequireAuth>} />

          {/* Billing & plans */}
          <Route path="/billing" element={<RequireAuth><AppLayout><BillingPage /></AppLayout></RequireAuth>} />
          <Route path="/billing/payments" element={<RequireAdmin><AppLayout><ManagementPayments /></AppLayout></RequireAdmin>} />
          <Route path="/billing/payments/monitoring" element={<RequireAdmin><AppLayout><PaymentsMonitoring /></AppLayout></RequireAdmin>} />
          <Route path="/billing/tariffs" element={<RequireAdmin><AppLayout><ManagementTariffs /></AppLayout></RequireAdmin>} />

          {/* Platform admin */}
          <Route path="/platform/ai" element={<RequireAuth><AppLayout><ManagementAI /></AppLayout></RequireAuth>} />
          <Route path="/platform/flags" element={<RequireAuth><AppLayout><ManagementFlags /></AppLayout></RequireAuth>} />
          <Route path="/platform/integrations" element={<RequireAuth><AppLayout><ManagementIntegrations /></AppLayout></RequireAuth>} />
          <Route path="/platform/system" element={<RequireAuth><AppLayout><ManagementSystem /></AppLayout></RequireAuth>} />
          <Route path="/platform/audit" element={<RequireAuth><AppLayout><ManagementAudit /></AppLayout></RequireAuth>} />

          {/* Moderation */}
          <Route path="/moderation" element={<RequireAuth><AppLayout><ModerationOverview /></AppLayout></RequireAuth>} />
          <Route path="/moderation/users" element={<RequireAuth><AppLayout><ModerationUsers /></AppLayout></RequireAuth>} />
          <Route path="/moderation/content" element={<RequireAuth><AppLayout><ModerationContent /></AppLayout></RequireAuth>} />
          <Route path="/moderation/reports" element={<RequireAuth><AppLayout><ModerationReports /></AppLayout></RequireAuth>} />
          <Route path="/moderation/tickets" element={<RequireAuth><AppLayout><ModerationTickets /></AppLayout></RequireAuth>} />
          <Route path="/moderation/appeals" element={<RequireAuth><AppLayout><ModerationAppeals /></AppLayout></RequireAuth>} />
          <Route path="/moderation/ai-rules" element={<RequireAuth><AppLayout><ModerationAIRules /></AppLayout></RequireAuth>} />

          {/* Observability */}
          <Route path="/observability" element={<RequireAuth><AppLayout><ObservabilityOverview /></AppLayout></RequireAuth>} />
          <Route path="/observability/api" element={<RequireAuth><AppLayout><ObservabilityAPI /></AppLayout></RequireAuth>} />
          <Route path="/observability/llm" element={<RequireAuth><AppLayout><ObservabilityLLM /></AppLayout></RequireAuth>} />
          <Route path="/observability/workers" element={<RequireAuth><AppLayout><ObservabilityWorkers /></AppLayout></RequireAuth>} />
          <Route path="/observability/transitions" element={<RequireAuth><AppLayout><ObservabilityTransitions /></AppLayout></RequireAuth>} />
          <Route path="/observability/events" element={<RequireAuth><AppLayout><ObservabilityEvents /></AppLayout></RequireAuth>} />
          <Route path="/observability/rum" element={<RequireAuth><AppLayout><ObservabilityRUM /></AppLayout></RequireAuth>} />

          {/* Account & personal settings */}
          <Route path="/profile" element={<RequireAuth><AppLayout><ProfilePage /></AppLayout></RequireAuth>} />
          <Route path="/settings/security" element={<RequireAuth><AppLayout><SecuritySettingsPage /></AppLayout></RequireAuth>} />
          <Route path="/settings/notifications" element={<RequireAuth><AppLayout><NotificationSettingsPage /></AppLayout></RequireAuth>} />

          {/* Legacy redirects */}
          <Route path="/management/notifications" element={<Navigate to="/notifications" replace />} />
          <Route path="/management/payments" element={<Navigate to="/billing/payments" replace />} />
          <Route path="/management/payments/monitoring" element={<Navigate to="/billing/payments/monitoring" replace />} />
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
      </BrowserRouter>
      </SettingsProvider>
    </AuthProvider>
  );
}

function RumRouteTracker() {
  const loc = useLocation();
  React.useEffect(() => {
    try {
      rumEvent('pageview', {
        path: loc.pathname + (loc.search || ''),
        title: typeof document !== 'undefined' ? document.title : '',
      });
    } catch {}
  }, [loc.pathname, loc.search]);
  return null;
}





