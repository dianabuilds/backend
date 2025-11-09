import React from 'react';
import { managementSiteEditorApi } from '@shared/api/management';
import { extractErrorMessage } from '@shared/utils/errors';
import type { SiteComponentSchemaResponse } from '@shared/api/management/siteEditor/types';

type UseComponentSchemaResult = {
  schema: Record<string, unknown> | null;
  version: string | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<SiteComponentSchemaResponse | null>;
};

export function useComponentSchema(componentKey: string | null): UseComponentSchemaResult {
  const [schema, setSchema] = React.useState<Record<string, unknown> | null>(null);
  const [version, setVersion] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const fetchSchema = React.useCallback(
    async (signal?: AbortSignal): Promise<SiteComponentSchemaResponse | null> => {
      if (!componentKey) {
        setSchema(null);
        setVersion(null);
        setError(null);
        setLoading(false);
        return null;
      }
      setLoading(true);
      setError(null);
      try {
        const response = await managementSiteEditorApi.fetchComponentSchema(componentKey, { signal });
        if (signal?.aborted) {
          return null;
        }
        setSchema(response.schema);
        setVersion(response.version ?? null);
        return response;
      } catch (err) {
        if (signal?.aborted) {
          return null;
        }
        setSchema(null);
        setVersion(null);
        setError(extractErrorMessage(err, 'Не удалось загрузить схему компонента'));
        return null;
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [componentKey],
  );

  React.useEffect(() => {
    if (!componentKey) {
      setSchema(null);
      setVersion(null);
      setError(null);
      setLoading(false);
      return undefined;
    }
    const controller = new AbortController();
    fetchSchema(controller.signal);
    return () => controller.abort();
  }, [componentKey, fetchSchema]);

  const refresh = React.useCallback(() => fetchSchema(), [fetchSchema]);

  return {
    schema,
    version,
    loading,
    error,
    refresh,
  };
}

export default useComponentSchema;
