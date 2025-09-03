import { lazy, Suspense, useEffect } from "react";
import { useRoutes, useLocation, type RouteObject } from "react-router-dom";

import ProtectedRoute from "../components/ProtectedRoute";
import AdminLayout from "./layouts/AdminLayout";
import BlankLayout from "./layouts/BlankLayout";
import { sendRUM } from "../perf/rum";
import { ADMIN_DEV_TOOLS } from "../utils/env";

// Lazy-loaded pages
const Login = lazy(() => import("../pages/Login"));
const NotFound = lazy(() => import("../pages/NotFound"));
const Dashboard = lazy(() => import("../pages/Dashboard"));
const Users = lazy(() => import("../pages/Users"));
const Nodes = lazy(() => import("../pages/Nodes"));
const Tags = lazy(() => import("../pages/Tags"));
const TagMerge = lazy(() => import("../pages/TagMerge"));
const Transitions = lazy(() => import("../pages/Transitions"));
const ModerationInbox = lazy(() => import("../pages/ModerationInbox"));
const ModerationCase = lazy(() => import("../pages/ModerationCase"));
const Navigation = lazy(() => import("../pages/Navigation"));
const NavigationProblems = lazy(() => import("../pages/NavigationProblems"));
const Simulation = lazy(() => import("../pages/Simulation"));
const Echo = lazy(() => import("../pages/Echo"));
const Traces = lazy(() => import("../pages/Traces"));
const Notifications = lazy(() => import("../pages/Notifications"));
const NotificationCampaignEditor = lazy(() => import("../pages/NotificationCampaignEditor"));
const ContentDashboard = lazy(() => import("../pages/ContentDashboard"));
const ContentAll = lazy(() => import("../pages/ContentAll"));
const Telemetry = lazy(() => import("../pages/Telemetry"));
const PremiumPlans = lazy(() => import("../pages/PremiumPlans"));
const PremiumLimits = lazy(() => import("../pages/PremiumLimits"));
const PaymentsTransactions = lazy(() => import("../pages/PaymentsTransactions"));
const PaymentsRecent = lazy(() => import("../pages/PaymentsRecent"));
const AIRateLimits = lazy(() => import("../pages/AIRateLimits"));
const AIQuests = lazy(() => import("../pages/AIQuests"));
const AIQuestJobDetails = lazy(() => import("../pages/AIQuestJobDetails"));
const Worlds = lazy(() => import("../pages/Worlds"));
const AISettings = lazy(() => import("../pages/AISettings"));
const AISystemSettings = lazy(() => import("../pages/AISystemSettings"));
const Achievements = lazy(() => import("../pages/Achievements"));
const Workspaces = lazy(() => import("../pages/Workspaces"));
const WorkspaceSettings = lazy(() => import("../pages/WorkspaceSettings"));
const Profile = lazy(() => import("../pages/Profile"));
const Quests = lazy(() => import("../pages/Quests"));
const QuestEditor = lazy(() => import("../pages/QuestEditor"));
const QuestVersionEditor = lazy(() => import("../pages/QuestVersionEditor"));
// Use the redesigned Node editor from features/ with all fields
const NodeEditor = lazy(() => import("../features/content/pages/NodeEditor"));
// Modern preview page (device frames, light/dark)
const NodePreview = lazy(() => import("../features/content/pages/NodePreview"));
const NodeDiff = lazy(() => import("../pages/NodeDiff"));
const ValidationReport = lazy(() => import("../pages/ValidationReport"));
const Authentication = lazy(() => import("../pages/Authentication"));
const PaymentsGateways = lazy(() => import("../pages/PaymentsGateways"));
const Integrations = lazy(() => import("../pages/Integrations"));
const Metrics = lazy(() => import("../pages/Metrics"));
const FeatureFlagsPage = lazy(() => import("../pages/FeatureFlags"));
const CacheTools = lazy(() => import("../pages/CacheTools"));
const RateLimitTools = lazy(() => import("../pages/RateLimitTools"));
const Monitoring = lazy(() => import("../pages/Monitoring"));
const Restrictions = lazy(() => import("../pages/Restrictions"));
const AuditLog = lazy(() => import("../pages/AuditLog"));
const SearchRelevance = lazy(() => import("../pages/SearchRelevance"));
const SearchTop = lazy(() => import("../pages/SearchTop"));
const Limits = lazy(() => import("../pages/Limits"));
const ReliabilityDashboard = lazy(() => import("../pages/ReliabilityDashboard"));
const Alerts = lazy(() => import("../pages/Alerts"));
const AIUsage = lazy(() => import("../pages/AIUsage"));
const Jobs = lazy(() => import("../pages/Jobs"));

function useRouteTelemetry() {
  const location = useLocation();
  useEffect(() => {
    const pathnames = location.pathname.split("/").filter(Boolean);
    const segmentMap: Record<string, string> = { preview: "Simulation" };
    const breadcrumbs = pathnames.map((segment) => {
      const label = segmentMap[segment] || segment.replace(/-/g, " ");
      return label.charAt(0).toUpperCase() + label.slice(1);
    });
    const routeId = pathnames.join("/") || "root";
    sendRUM("route", { route_id: routeId, breadcrumbs });
  }, [location]);
}

const protectedChildren: RouteObject[] = [
  { index: true, element: <Dashboard /> },
  { path: "users", element: <Users /> },
  { path: "nodes", element: <Nodes /> },
  { path: "tags", element: <Tags /> },
  { path: "tags/merge", element: <TagMerge /> },
  { path: "transitions", element: <Transitions /> },
  { path: "moderation", element: <ModerationInbox /> },
  { path: "moderation/cases/:id", element: <ModerationCase /> },
  { path: "navigation", element: <Navigation /> },
  { path: "navigation/problems", element: <NavigationProblems /> },
  { path: "traces", element: <Traces /> },
  { path: "notifications", element: <Notifications /> },
  { path: "notifications/campaigns/:id", element: <NotificationCampaignEditor /> },
  { path: "content", element: <ContentDashboard /> },
  { path: "content/all", element: <ContentAll /> },
  { path: "telemetry", element: <Telemetry /> },
  { path: "premium/plans", element: <PremiumPlans /> },
  { path: "premium/limits", element: <PremiumLimits /> },
  { path: "payments/transactions", element: <PaymentsTransactions /> },
  { path: "payments/recent", element: <PaymentsRecent /> },
  { path: "ai/rate-limits", element: <AIRateLimits /> },
  { path: "ai/quests", element: <AIQuests /> },
  { path: "ai/quests/jobs/:id", element: <AIQuestJobDetails /> },
  { path: "ai/worlds", element: <Worlds /> },
  { path: "ai/settings", element: <AISettings /> },
  { path: "ai/system", element: <AISystemSettings /> },
  { path: "achievements", element: <Achievements /> },
  { path: "workspaces", element: <Workspaces /> },
  { path: "workspaces/:id", element: <WorkspaceSettings /> },
  { path: "profile", element: <Profile /> },
  { path: "quests", element: <Quests /> },
  { path: "quests/:id", element: <QuestEditor /> },
  { path: "quests/:id/versions/:versionId", element: <QuestVersionEditor /> },
    // Newer editor/preview routes with explicit type
    { path: "nodes/:type/:id/validate", element: <ValidationReport /> },
    { path: "nodes/:type/:id/preview", element: <NodePreview /> },
    { path: "nodes/:type/:id", element: <NodeEditor /> },
    // Backward compatibility for older links without type
    { path: "nodes/:id/validate", element: <ValidationReport /> },
    { path: "nodes/:id/preview", element: <NodePreview /> },
    { path: "nodes/:id", element: <NodeEditor /> },
    { path: "nodes/:id/diff", element: <NodeDiff /> },
  { path: "search", element: <SearchTop /> },
  { path: "settings/authentication", element: <Authentication /> },
  { path: "settings/payments", element: <PaymentsGateways /> },
  { path: "settings/integrations", element: <Integrations /> },
  { path: "settings/metrics", element: <Metrics /> },
  { path: "settings/feature-flags", element: <FeatureFlagsPage /> },
  { path: "tools/cache", element: <CacheTools /> },
  { path: "tools/rate-limit", element: <RateLimitTools /> },
  { path: "monitoring", element: <Monitoring /> },
  { path: "tools/restrictions", element: <Restrictions /> },
  { path: "tools/audit", element: <AuditLog /> },
  { path: "tools/flags", element: <FeatureFlagsPage /> },
  { path: "tools/search-settings", element: <SearchRelevance /> },
  { path: "ops/limits", element: <Limits /> },
  { path: "ops/reliability", element: <ReliabilityDashboard /> },
  { path: "ops/alerts", element: <Alerts /> },
  { path: "ops/ai-usage", element: <AIUsage /> },
  { path: "ops/jobs", element: <Jobs /> },
  { path: "payments", element: <PaymentsGateways /> },
];

if (ADMIN_DEV_TOOLS) {
  protectedChildren.push(
    { path: "preview", element: <Simulation /> },
    { path: "echo", element: <Echo /> },
  );
}

const routes: RouteObject[] = [
  {
    element: <BlankLayout />,
    children: [
      { path: "/login", element: <Login /> },
      { path: "*", element: <NotFound /> },
    ],
  },
  {
    element: (
      <ProtectedRoute>
        <AdminLayout />
      </ProtectedRoute>
    ),
    children: protectedChildren,
  },
];

export function AppRoutes() {
  const element = useRoutes(routes);
  useRouteTelemetry();
  return (
    <Suspense fallback={<div className="p-4 text-sm text-gray-500">Loading…</div>}>
      {element}
    </Suspense>
  );
}
