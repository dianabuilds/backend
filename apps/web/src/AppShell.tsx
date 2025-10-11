import React from 'react';
import { Helmet, HelmetProvider, type FilledContext } from 'react-helmet-async';
import { useLocation } from 'react-router-dom';
import { InitialDataProvider, type InitialDataMap } from '@shared/ssr/InitialDataContext';
import { rumEvent } from '@shared/rum';
import { useLocale } from '@shared/i18n/locale';
import type { Locale } from '@shared/i18n/locale';

const DEFAULT_DESCRIPTIONS: Record<Locale, string> = {
  en: 'News and updates from the Caves developer blog.',
  ru: 'Новости и заметки команды разработки Caves.',
};

export function LocaleHelmet(): React.ReactElement {
  const locale = useLocale();
  const description = DEFAULT_DESCRIPTIONS[locale] ?? DEFAULT_DESCRIPTIONS.ru;
  return (
    <Helmet defaultTitle="Caves Control" titleTemplate="%s — Caves Control" htmlAttributes={{ lang: locale }}>
      <meta name="description" content={description} />
    </Helmet>
  );
}

export type AppShellProps = {
  initialData?: InitialDataMap | null;
  helmetContext?: FilledContext | undefined;
  children: React.ReactNode;
};

export function AppShell({ initialData, helmetContext, children }: AppShellProps): React.ReactElement {
  return (
    <HelmetProvider context={helmetContext}>
      <InitialDataProvider data={initialData ?? undefined}>
        <>
          <LocaleHelmet />
          {children}
        </>
      </InitialDataProvider>
    </HelmetProvider>
  );
}

export function RumRouteTracker(): React.ReactElement | null {
  const loc = useLocation();
  React.useEffect(() => {
    try {
      rumEvent('pageview', {
        path: loc.pathname + (loc.search || ''),
        title: typeof document !== 'undefined' ? document.title : '',
      });
    } catch {}
  }, [loc.pathname, loc.search]);
  return null;
}
