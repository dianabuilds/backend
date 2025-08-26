import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import ComingSoon from "./components/ComingSoon";
import ErrorBoundary from "./components/ErrorBoundary";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import { ToastProvider } from "./components/ToastProvider";
import Achievements from "./pages/Achievements";
import AuditLog from "./pages/AuditLog";
import CacheTools from "./pages/CacheTools";
import ContentAll from "./pages/ContentAll";
import ContentDashboard from "./pages/ContentDashboard";
import Dashboard from "./pages/Dashboard";
import Echo from "./pages/Echo";
import FeatureFlagsPage from "./pages/FeatureFlags";
import Authentication from "./pages/Authentication";
import Integrations from "./pages/Integrations";
import Metrics from "./pages/Metrics";
import Login from "./pages/Login";
import ModerationCase from "./pages/ModerationCase";
import ModerationInbox from "./pages/ModerationInbox";
import Monitoring from "./pages/Monitoring";
import ReliabilityDashboard from "./pages/ReliabilityDashboard";
import Navigation from "./pages/Navigation";
import Nodes from "./pages/Nodes";
import NotificationCampaignEditor from "./pages/NotificationCampaignEditor";
import Notifications from "./pages/Notifications";
import Simulation from "./pages/Simulation";
import Profile from "./pages/Profile";
import QuestsList from "./pages/QuestsList";
import NodeEditor from "./pages/NodeEditor";
import NodeDiff from "./pages/NodeDiff";
import QuestVersionEditor from "./pages/QuestVersionEditor";
import RateLimitTools from "./pages/RateLimitTools";
import Restrictions from "./pages/Restrictions";
import SearchRelevance from "./pages/SearchRelevance";
import TagMerge from "./pages/TagMerge";
import Tags from "./pages/Tags";
import Traces from "./pages/Traces";
import Transitions from "./pages/Transitions";
import Users from "./pages/Users";
import Workspaces from "./pages/Workspaces";
import WorkspaceSettings from "./pages/WorkspaceSettings";
import ValidationReport from "./pages/ValidationReport";
import { WorkspaceBranchProvider, useWorkspace } from "./workspace/WorkspaceContext";
import Limits from "./pages/Limits";
import Alerts from "./pages/Alerts";
import AIUsage from "./pages/AIUsage";
import NotFound from "./pages/NotFound";
import { ADMIN_DEV_TOOLS } from "./utils/env";
const AIQuests = lazy(() => import("./pages/AIQuests"));
const Worlds = lazy(() => import("./pages/Worlds"));
const AISettings = lazy(() => import("./pages/AISettings"));
const AISystemSettings = lazy(() => import("./pages/AISystemSettings"));
const AIQuestJobDetails = lazy(() => import("./pages/AIQuestJobDetails"));
const Telemetry = lazy(() => import("./pages/Telemetry"));
const PremiumPlans = lazy(() => import("./pages/PremiumPlans"));
const PremiumLimits = lazy(() => import("./pages/PremiumLimits"));
const PaymentsTransactions = lazy(() => import("./pages/PaymentsTransactions"));
const PaymentsGateways = lazy(() => import("./pages/PaymentsGateways"));
const AIRateLimits = lazy(() => import("./pages/AIRateLimits"));

const queryClient = new QueryClient();

function QuestEditorRedirect() {
  const { workspaceId } = useWorkspace();
  const to = workspaceId
    ? `/nodes/new?workspace_id=${workspaceId}`
    : "/nodes/new";
  return <Navigate to={to} replace />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WorkspaceBranchProvider>
          <ToastProvider>
            <BrowserRouter basename="/admin">
              <ErrorBoundary>
                <Suspense
                  fallback={
                    <div className="p-4 text-sm text-gray-500">Loading…</div>
                  }
                >
                  <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route
                      element={
                        <ProtectedRoute>
                          <Layout />
                        </ProtectedRoute>
                      }
                    >
                        <Route index element={<Dashboard />} />
                      <Route path="users" element={<Users />} />
                      <Route path="nodes" element={<Nodes />} />
                      <Route path="tags" element={<Tags />} />
                      <Route path="tags/merge" element={<TagMerge />} />
                      <Route path="transitions" element={<Transitions />} />
                      <Route path="moderation" element={<ModerationInbox />} />
                      <Route
                        path="moderation/cases/:id"
                        element={<ModerationCase />}
                      />
                      <Route path="navigation" element={<Navigation />} />
                      {ADMIN_DEV_TOOLS && (
                        <Route path="preview" element={<Simulation />} />
                      )}
                      {ADMIN_DEV_TOOLS && <Route path="echo" element={<Echo />} />}
                      <Route path="traces" element={<Traces />} />
                      <Route path="notifications" element={<Notifications />} />
                      <Route
                        path="notifications/campaigns/:id"
                        element={<NotificationCampaignEditor />}
                      />
                      <Route path="content" element={<ContentDashboard />} />
                      <Route path="content/all" element={<ContentAll />} />
                      <Route path="telemetry" element={<Telemetry />} />
                      <Route path="premium/plans" element={<PremiumPlans />} />
                      <Route
                        path="premium/limits"
                        element={<PremiumLimits />}
                      />
                      <Route
                        path="payments/transactions"
                        element={<PaymentsTransactions />}
                      />
                      <Route path="ai/rate-limits" element={<AIRateLimits />} />
                      <Route path="ai/quests" element={<AIQuests />} />
                      <Route
                        path="ai/quests/jobs/:id"
                        element={<AIQuestJobDetails />}
                      />
                      <Route path="ai/worlds" element={<Worlds />} />
                      <Route path="ai/settings" element={<AISettings />} />
                      <Route path="ai/system" element={<AISystemSettings />} />
                      <Route path="achievements" element={<Achievements />} />
                      <Route path="workspaces" element={<Workspaces />} />
                      <Route
                        path="workspaces/:id"
                        element={<WorkspaceSettings />}
                      />
                      <Route path="profile" element={<Profile />} />
                      <Route path="quests" element={<QuestsList />} />
                      <Route
                        path="quests/editor"
                        element={<QuestEditorRedirect />}
                      />
                      <Route
                        path="quests/version/:id"
                        element={<QuestVersionEditor />}
                      />
                      <Route
                        path="nodes/:type/:id/validate"
                        element={<ValidationReport />}
                      />
                      <Route path="nodes/:id" element={<NodeEditor />} />
                      <Route path="nodes/:id/diff" element={<NodeDiff />} />
                      <Route
                        path="search"
                        element={<ComingSoon title="Search" />}
                      />
                      <Route
                        path="settings/authentication"
                        element={<Authentication />}
                      />
                      <Route
                        path="settings/payments"
                        element={<PaymentsGateways />}
                      />
                      <Route
                        path="settings/integrations"
                        element={<Integrations />}
                      />
                      <Route
                        path="settings/metrics"
                        element={<Metrics />}
                      />
                      <Route
                        path="settings/feature-flags"
                        element={<FeatureFlagsPage />}
                      />
                      <Route path="tools/cache" element={<CacheTools />} />
                      <Route
                        path="tools/rate-limit"
                        element={<RateLimitTools />}
                      />
                      <Route path="tools/monitoring" element={<Monitoring />} />
                      <Route
                        path="tools/restrictions"
                        element={<Restrictions />}
                      />
                      <Route path="tools/audit" element={<AuditLog />} />
                      <Route
                        path="tools/flags"
                        element={<FeatureFlagsPage />}
                      />
                      <Route
                        path="tools/search-settings"
                        element={<SearchRelevance />}
                      />
                      <Route path="ops/limits" element={<Limits />} />
                      <Route
                        path="ops/reliability"
                        element={<ReliabilityDashboard />}
                      />
                      <Route path="ops/alerts" element={<Alerts />} />
                      <Route path="ops/ai-usage" element={<AIUsage />} />
                      <Route path="payments" element={<PaymentsGateways />} />
                      <Route path="*" element={<NotFound />} />
                    </Route>
                  </Routes>
                </Suspense>
              </ErrorBoundary>
            </BrowserRouter>
          </ToastProvider>
        </WorkspaceBranchProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
