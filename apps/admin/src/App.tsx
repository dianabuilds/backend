import { BrowserRouter } from 'react-router-dom';

import { AccountBranchProvider } from './account/AccountContext';
import { AppRoutes } from './app/routes';
import { AuthProvider } from './auth/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/ToastProvider';

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
