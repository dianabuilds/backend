import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import ErrorBoundary from "./components/ErrorBoundary";
import { ToastProvider } from "./components/ToastProvider";
import { AppRoutes } from "./app/routes";
import { WorkspaceBranchProvider } from "./workspace/WorkspaceContext";

export default function App() {
  return (
    <AuthProvider>
      <WorkspaceBranchProvider>
        <ToastProvider>
          <BrowserRouter basename="/admin">
            <ErrorBoundary>
              <AppRoutes />
            </ErrorBoundary>
          </BrowserRouter>
        </ToastProvider>
      </WorkspaceBranchProvider>
    </AuthProvider>
  );
}
