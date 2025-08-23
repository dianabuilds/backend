import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Suspense, lazy } from "react";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Users from "./pages/Users";
import Echo from "./pages/Echo";
import AuditLog from "./pages/AuditLog";
import Login from "./pages/Login";
import Restrictions from "./pages/Restrictions";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./auth/AuthContext";
import { WorkspaceProvider } from "./workspace/WorkspaceContext";
import ContentDashboard from "./pages/ContentDashboard";
import ContentAll from "./pages/ContentAll";
import ComingSoon from "./components/ComingSoon";
import Navigation from "./pages/Navigation";
import Achievements from "./pages/Achievements";
import CacheTools from "./pages/CacheTools";
import RateLimitTools from "./pages/RateLimitTools";
import Health from "./pages/Health";
import Nodes from "./pages/Nodes";
import Tags from "./pages/Tags";
import Transitions from "./pages/Transitions";
import Traces from "./pages/Traces";
import ErrorBoundary from "./components/ErrorBoundary";
import { ToastProvider } from "./components/ToastProvider";
import Monitoring from "./pages/Monitoring";
import Notifications from "./pages/Notifications";
import NotificationCampaignEditor from "./pages/NotificationCampaignEditor";
import QuestEditor from "./pages/QuestEditor";
import FeatureFlagsPage from "./pages/FeatureFlags";
import ModerationInbox from "./pages/ModerationInbox";
import ModerationCase from "./pages/ModerationCase";
import QuestsList from "./pages/QuestsList";
import QuestVersionEditor from "./pages/QuestVersionEditor";
import SearchRelevance from "./pages/SearchRelevance";
import TagMerge from "./pages/TagMerge";
import WorldEditor from "./pages/WorldEditor";
import CharacterEditor from "./pages/CharacterEditor";
import BlogPostEditor from "./pages/BlogPostEditor";
import AchievementEditor from "./pages/AchievementEditor";
import WorkspaceSettings from "./pages/WorkspaceSettings";
const AIQuests = lazy(() => import("./pages/AIQuests"));
const Worlds = lazy(() => import("./pages/Worlds"));
const AISettings = lazy(() => import("./pages/AISettings"));
const AIQuestJobDetails = lazy(() => import("./pages/AIQuestJobDetails"));
const Telemetry = lazy(() => import("./pages/Telemetry"));
const PremiumPlans = lazy(() => import("./pages/PremiumPlans"));
const PremiumLimits = lazy(() => import("./pages/PremiumLimits"));
const PaymentsTransactions = lazy(() => import("./pages/PaymentsTransactions"));
const PaymentsGateways = lazy(() => import("./pages/PaymentsGateways"));
const AIRateLimits = lazy(() => import("./pages/AIRateLimits"));

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WorkspaceProvider>
          <ToastProvider>
            <BrowserRouter basename="/admin">
              <ErrorBoundary>
                <Suspense fallback={<div className="p-4 text-sm text-gray-500">Loading…</div>}>
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
                      <Route path="moderation/cases/:id" element={<ModerationCase />} />
                    <Route path="navigation" element={<Navigation />} />
                    <Route path="echo" element={<Echo />} />
                    <Route path="traces" element={<Traces />} />
                    <Route path="notifications" element={<Notifications />} />
                    <Route path="notifications/campaigns/:id" element={<NotificationCampaignEditor />} />
                      <Route path="content" element={<ContentDashboard />} />
                      <Route path="content/all" element={<ContentAll />} />
                    <Route path="telemetry" element={<Telemetry />} />
                    <Route path="premium/plans" element={<PremiumPlans />} />
                    <Route path="premium/limits" element={<PremiumLimits />} />
                    <Route path="payments/transactions" element={<PaymentsTransactions />} />
                    <Route path="ai/rate-limits" element={<AIRateLimits />} />
                    <Route path="ai/quests" element={<AIQuests />} />
                    <Route path="ai/quests/jobs/:id" element={<AIQuestJobDetails />} />
                    <Route path="ai/worlds" element={<Worlds />} />
                    <Route path="ai/settings" element={<AISettings />} />
                    <Route path="achievements" element={<Achievements />} />
                    <Route path="achievements/editor" element={<AchievementEditor />} />
                    <Route path="workspaces/:id" element={<WorkspaceSettings />} />
                    <Route path="quests" element={<QuestsList />} />
                    <Route path="quests/editor" element={<QuestEditor />} />
                    <Route path="quests/version/:id" element={<QuestVersionEditor />} />
                    <Route path="worlds/editor" element={<WorldEditor />} />
                    <Route path="characters/editor" element={<CharacterEditor />} />
                    <Route path="blog/editor" element={<BlogPostEditor />} />
                    <Route path="search" element={<ComingSoon title="Search" />} />
                    <Route path="tools/cache" element={<CacheTools />} />
                    <Route path="tools/rate-limit" element={<RateLimitTools />} />
                    <Route path="tools/monitoring" element={<Monitoring />} />
                    <Route path="tools/restrictions" element={<Restrictions />} />
                    <Route path="tools/audit" element={<AuditLog />} />
                    <Route path="tools/flags" element={<FeatureFlagsPage />} />
                    <Route path="tools/search-settings" element={<SearchRelevance />} />
                    <Route path="system/health" element={<Health />} />
                    <Route path="payments" element={<PaymentsGateways />} />
                  </Route>
                </Routes>
              </Suspense>
            </ErrorBoundary>
          </BrowserRouter>
        </ToastProvider>
        </WorkspaceProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
