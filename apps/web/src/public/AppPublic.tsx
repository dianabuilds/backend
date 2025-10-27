import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import type { FilledContext } from 'react-helmet-async';
import { AppShell, RumRouteTracker } from '../AppShell';
import type { InitialDataMap } from '@shared/ssr/InitialDataContext';
import { HomePage, NodePublicPage } from '../pages/public';
import { RouteFallback } from '../routes/fallback';

const DevBlogRoutes = React.lazy(() => import('../routes/DevBlogRoutes'));

export function AppPublicRoutes(): React.ReactElement {
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
      <Route path="*" element={<RouteFallback />} />
    </Routes>
  );
}

type AppPublicProps = {
  initialData?: InitialDataMap | null;
  helmetContext?: FilledContext | undefined;
};

export default function AppPublic({ initialData, helmetContext }: AppPublicProps = {}): React.ReactElement {
  return (
    <AppShell initialData={initialData} helmetContext={helmetContext}>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <RumRouteTracker />
        <AppPublicRoutes />
      </BrowserRouter>
    </AppShell>
  );
}
