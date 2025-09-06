import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import ErrorBoundary from "./components/ErrorBoundary";
import { ToastProvider } from "./components/ToastProvider";
import { AppRoutes } from "./app/routes";
import { AccountBranchProvider } from "./account/AccountContext";

export default function App() {
  return (
    <AuthProvider>
      <AccountBranchProvider>
        <ToastProvider>
          <BrowserRouter basename="/admin">
            <ErrorBoundary>
              <AppRoutes />
            </ErrorBoundary>
          </BrowserRouter>
        </ToastProvider>
      </AccountBranchProvider>
    </AuthProvider>
  );
}
