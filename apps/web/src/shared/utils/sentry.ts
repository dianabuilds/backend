export type SentryTags = Record<string, string>;
export type SentryExtras = Record<string, unknown>;

type SentryScope = {
  setTag?: (key: string, value: string) => void;
  setTags?: (tags: SentryTags) => void;
  setExtra?: (key: string, value: unknown) => void;
  setExtras?: (extras: SentryExtras) => void;
  setContext?: (name: string, context: Record<string, unknown> | null) => void;
  setLevel?: (level: string) => void;
};

type SentryClient = {
  captureException: (error: unknown) => void;
  withScope?: (callback: (scope: SentryScope) => void) => void;
};

declare global {
  interface Window {
    Sentry?: SentryClient;
  }
}

export type SentryReportOptions = {
  tags?: SentryTags;
  extras?: SentryExtras;
  level?: 'fatal' | 'error' | 'warning' | 'info' | 'debug' | 'log';
  contextName?: string;
};

function applyTags(scope: SentryScope, tags: SentryTags | undefined) {
  if (!tags) return;
  if (typeof scope.setTags === 'function') {
    scope.setTags(tags);
    return;
  }
  if (typeof scope.setTag === 'function') {
    Object.entries(tags).forEach(([key, value]) => {
      scope.setTag?.(key, value);
    });
  }
}

function applyExtras(scope: SentryScope, extras: SentryExtras | undefined, contextName?: string) {
  if (!extras) return;
  if (typeof scope.setExtras === 'function') {
    scope.setExtras(extras);
  } else if (typeof scope.setExtra === 'function') {
    Object.entries(extras).forEach(([key, value]) => {
      scope.setExtra?.(key, value);
    });
  }
  if (contextName && typeof scope.setContext === 'function') {
    scope.setContext(contextName, extras);
  }
}

export function reportToSentry(error: unknown, options: SentryReportOptions = {}): void {
  if (typeof window === 'undefined') {
    return;
  }
  const sentry = window.Sentry;
  if (!sentry || typeof sentry.captureException !== 'function') {
    if (options.level === 'error' || options.level === 'fatal') {
      try {
        console.error('[sentry:fallback]', error);
      } catch {
        // ignore console errors
      }
    }
    return;
  }
  if (typeof sentry.withScope === 'function') {
    sentry.withScope((scope) => {
      if (options.level && typeof scope.setLevel === 'function') {
        scope.setLevel(options.level);
      }
      applyTags(scope, options.tags);
      applyExtras(scope, options.extras, options.contextName);
      sentry.captureException(error);
    });
    return;
  }
  sentry.captureException(error);
}

export function reportFeatureError(
  error: unknown,
  feature: string,
  extras?: SentryExtras,
  level: SentryReportOptions['level'] = 'error',
): void {
  const tags: SentryTags = { feature };
  reportToSentry(error, { tags, extras, level, contextName: feature });
}


