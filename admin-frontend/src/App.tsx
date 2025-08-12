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
import ErrorBoundary from "./components/ErrorBoundary";
import { ToastProvider } from "./components/ToastProvider";
import Monitoring from "./pages/Monitoring";
import Notifications from "./pages/Notifications";
import Quests from "./pages/Quests";
import QuestEditor from "./pages/QuestEditor";

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
                  <Route path="transitions" element={<Transitions />} />
                  <Route path="moderation" element={<ComingSoon title="Moderation" />} />
                  <Route path="navigation" element={<Navigation />} />
                  <Route path="echo" element={<Echo />} />
                  <Route path="traces" element={<ComingSoon title="Traces" />} />
                  <Route path="notifications" element={<Notifications />} />
                  <Route path="achievements" element={<Achievements />} />
                  <Route path="quests" element={<Quests />} />
                  <Route path="quests/editor" element={<QuestEditor />} />
                  <Route path="search" element={<ComingSoon title="Search" />} />
                  <Route path="tools/cache" element={<CacheTools />} />
                  <Route path="tools/rate-limit" element={<RateLimitTools />} />
                  <Route path="tools/monitoring" element={<Monitoring />} />
                  <Route path="tools/restrictions" element={<Restrictions />} />
                  <Route path="tools/audit" element={<AuditLog />} />
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
