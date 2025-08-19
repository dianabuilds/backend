import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Users from "./pages/Users";
import Echo from "./pages/Echo";
import AuditLog from "./pages/AuditLog";
import Login from "./pages/Login";
import Restrictions from "./pages/Restrictions";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./auth/AuthContext";
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
import QuestEditor from "./pages/QuestEditor";
import FeatureFlagsPage from "./pages/FeatureFlags";
import ModerationInbox from "./pages/ModerationInbox";
import ModerationCase from "./pages/ModerationCase";
import QuestsList from "./pages/QuestsList";
import QuestVersionEditor from "./pages/QuestVersionEditor";
import SearchRelevance from "./pages/SearchRelevance";
import TagMerge from "./pages/TagMerge";
import AIQuests from "./pages/AIQuests";
import Worlds from "./pages/Worlds";
import AISettings from "./pages/AISettings";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter basename="/admin">
            <ErrorBoundary>
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
                  <Route path="ai/quests" element={<AIQuests />} />
                  <Route path="ai/worlds" element={<Worlds />} />
                  <Route path="ai/settings" element={<AISettings />} />
                  <Route path="achievements" element={<Achievements />} />
                  <Route path="quests" element={<QuestsList />} />
                  <Route path="quests/editor" element={<QuestEditor />} />
                  <Route path="quests/version/:id" element={<QuestVersionEditor />} />
                  <Route path="search" element={<ComingSoon title="Search" />} />
                  <Route path="tools/cache" element={<CacheTools />} />
                  <Route path="tools/rate-limit" element={<RateLimitTools />} />
                  <Route path="tools/monitoring" element={<Monitoring />} />
                  <Route path="tools/restrictions" element={<Restrictions />} />
                  <Route path="tools/audit" element={<AuditLog />} />
                  <Route path="tools/flags" element={<FeatureFlagsPage />} />
                  <Route path="tools/search-settings" element={<SearchRelevance />} />
                  <Route path="system/health" element={<Health />} />
                  <Route path="payments" element={<ComingSoon title="Payments" />} />
                </Route>
              </Routes>
            </ErrorBoundary>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
