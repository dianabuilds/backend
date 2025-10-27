import React from 'react';
import { createRoot, hydrateRoot } from 'react-dom/client';
import App from './App';
import './styles/index.css';
import { startRUM } from '@shared/rum';
import type { InitialDataMap } from '@shared/ssr/InitialDataContext';

declare global {
  interface Window {
    __INITIAL_DATA__?: InitialDataMap;
  }
}

const container = document.getElementById('root');
const initialData = (typeof window !== 'undefined' ? window.__INITIAL_DATA__ : undefined) ?? undefined;

if (container) {
  const app = (
    <React.StrictMode>
      <App initialData={initialData} />
    </React.StrictMode>
  );

  const hasSSRMarkup = container.childElementCount > 0;
  if (hasSSRMarkup) {
    hydrateRoot(container, app);
  } else {
    createRoot(container).render(app);
  }
}

if (typeof window !== 'undefined' && window.__INITIAL_DATA__) {
  delete window.__INITIAL_DATA__;
}

try {
  startRUM();
} catch {}
