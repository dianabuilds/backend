import React from 'react';
import { apiGet, apiPatch, apiPost } from '../../../shared/api/client';
import { CaseNote, ModerationCaseDetail } from './types';

export function useModerationCase(initialId?: string | null) {
  const [caseId, setCaseId] = React.useState<string | null>(initialId ?? null);
  const [data, setData] = React.useState<ModerationCaseDetail | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const lastLoadedIdRef = React.useRef<string | null>(null);
  const dataCacheRef = React.useRef<ModerationCaseDetail | null>(null);

  const load = React.useCallback(
    async (id?: string | null, opts: { force?: boolean } = {}) => {
      const targetId = id ?? caseId;
      if (!targetId) return null;

      if (!opts.force && lastLoadedIdRef.current === targetId && dataCacheRef.current) {
        setData(dataCacheRef.current);
        return dataCacheRef.current;
      }

      setLoading(true);
      setError(null);
      try {
        const res = await apiGet<ModerationCaseDetail>(`/v1/moderation/cases/${encodeURIComponent(targetId)}`);
        setData(res || null);
        dataCacheRef.current = res || null;
        lastLoadedIdRef.current = targetId;
        return res ?? null;
      } catch (e: any) {
        setError(String(e?.message || e || 'error'));
        setData(null);
        dataCacheRef.current = null;
        return null;
      } finally {
        setLoading(false);
      }
    },
    [caseId]
  );

  const update = React.useCallback(
    async (payload: Record<string, any>) => {
      if (!caseId) throw new Error('case_id_required');
      const updated = await apiPatch<ModerationCaseDetail>(
        `/v1/moderation/cases/${encodeURIComponent(caseId)}`,
        payload
      );
      setData(updated || null);
      dataCacheRef.current = updated || null;
      if (updated) {
        lastLoadedIdRef.current = caseId;
      }
      return updated ?? null;
    },
    [caseId]
  );

  const addNote = React.useCallback(
    async (payload: CaseNote & { text: string }) => {
      if (!caseId) throw new Error('case_id_required');
      await apiPost(`/v1/moderation/cases/${encodeURIComponent(caseId)}/notes`, payload);
      await load(caseId, { force: true });
    },
    [caseId, load]
  );

  const select = React.useCallback((id: string | null) => {
    setCaseId(id);
    setData(null);
    dataCacheRef.current = null;
    lastLoadedIdRef.current = null;
    setError(null);
  }, []);

  return {
    caseId,
    data,
    loading,
    error,
    load,
    update,
    addNote,
    select,
    setData,
  };
}
