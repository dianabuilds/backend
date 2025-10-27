import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import LoginPage from './pages/auth/Login';
import { AuthProvider } from '@shared/auth';
import { HomePage, NodePublicPage } from './pages/public';
import { RouteFallback } from './routes/fallback';
import { AppShell, RumRouteTracker } from './AppShell';
import type { InitialDataMap } from '@shared/ssr/InitialDataContext';

const PrivateApp = React.lazy(() => import('./routes/PrivateAppRoutes'));
const DevBlogRoutes = React.lazy(() => import('./routes/DevBlogRoutes'));

export function AppRoutes(): React.ReactElement {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route
        path="/dev-blog/*"
        element={
          <React.Suspense fallback={<RouteFallback />}>
            <DevBlogRoutes />
          </React.Suspense>
        }
      />
      <Route path="/n/:slug" element={<NodePublicPage />} />
      <Route
        path="/login"
        element={
          <AuthProvider>
            <LoginPage />
          </AuthProvider>
        }
      />
      <Route
        path="/*"
        element={
          <React.Suspense fallback={<RouteFallback />}>
            <PrivateApp />
          </React.Suspense>
        }
      />
    </Routes>
  );
}

type AppProps = {
  initialData?: InitialDataMap | null;
};

export default function App({ initialData }: AppProps = {}): React.ReactElement {
  return (
    <AppShell initialData={initialData}>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <RumRouteTracker />
        <AppRoutes />
      </BrowserRouter>
    </AppShell>
  );
}
