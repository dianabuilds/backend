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

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter basename="/admin">
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
              <Route path="nodes" element={<ComingSoon title="Nodes" />} />
              <Route path="tags" element={<ComingSoon title="Tags" />} />
              <Route path="transitions" element={<ComingSoon title="Transitions" />} />
              <Route path="moderation" element={<ComingSoon title="Moderation" />} />
              <Route path="navigation" element={<ComingSoon title="Navigation" />} />
              <Route path="echo" element={<Echo />} />
              <Route path="traces" element={<ComingSoon title="Traces" />} />
              <Route path="notifications" element={<ComingSoon title="Notifications" />} />
              <Route path="achievements" element={<ComingSoon title="Achievements" />} />
              <Route path="quests" element={<ComingSoon title="Quests" />} />
              <Route path="search" element={<ComingSoon title="Search" />} />
              <Route path="tools/cache" element={<ComingSoon title="Cache" />} />
              <Route path="tools/rate-limit" element={<ComingSoon title="Rate limit" />} />
              <Route path="tools/restrictions" element={<Restrictions />} />
              <Route path="tools/audit" element={<AuditLog />} />
              <Route path="system/health" element={<ComingSoon title="Health" />} />
              <Route path="payments" element={<ComingSoon title="Payments" />} />
            </Route>

          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
