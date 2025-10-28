import type { CreateSiteGlobalBlockPayload, SiteBlockPreviewResponse } from '@shared/api/management/siteEditor/types';
import React from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { AlertTriangle, ExternalLink } from '@icons';
import { Badge, Button, Card, Input, Select, Spinner, Textarea, useToast } from '@ui';
import { extractErrorMessage } from '@shared/utils/errors';
import { formatDateTime, formatNumber } from '@shared/utils/format';
import { managementSiteEditorApi } from '@shared/api/management';
import {
  GlobalBlockHistoryPanel,
  GlobalBlockMetricsPanel,
  GlobalBlockUsageList,
  GlobalBlockWarnings,
  MetaItem,
} from './SiteGlobalBlockPanels';
import { globalBlockStatusAppearance, reviewAppearance } from '../utils/pageHelpers';
import type {
  SiteGlobalBlock,
  SiteGlobalBlockHistoryItem,
  SiteGlobalBlockMetricsResponse,
  SiteGlobalBlockUsage,
  SiteGlobalBlockWarning,
  SiteMetricsPeriod,
} from '@shared/types/management';

const REVIEW_STATUS_OPTIONS: Array<{ value: SiteGlobalBlock['review_status']; label: string }> = [
  { value: 'none', label: 'Ревью не требуется' },
  { value: 'pending', label: 'На ревью' },
  { value: 'approved', label: 'Одобрено' },
  { value: 'rejected', label: 'Отклонено' },
];

const REVIEW_STATUS_BADGE_COLOR: Record<SiteGlobalBlock['review_status'], 'neutral' | 'warning' | 'success' | 'error'> = {
  none: 'neutral',
  pending: 'warning',
  approved: 'success',
  rejected: 'error',
};

const LOCALE_OPTIONS = [
  { value: 'ru', label: 'Русский (ru)' },
  { value: 'en', label: 'Английский (en)' },
] as const;
const PREVIEW_LIMIT_OPTIONS = [3, 6, 9, 12];

type LocaleOption = (typeof LOCALE_OPTIONS)[number]['value'];

function normalizeLocale(value: string | null | undefined): LocaleOption {
  const normalized = (value ?? '').trim().toLowerCase();
  if (normalized.startsWith('en')) {
    return 'en';
  }
  return 'ru';
}

type TemplateStatePayload = {
  id: string;
  label: string;
  locale: string | null;
  documentationUrl: string | null;
  note: string | null;
  defaults: CreateSiteGlobalBlockPayload;
};

function toPrettyJson(value: unknown): string {
  if (value == null) {
    return '{\n  \n}';
  }
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    try {
      return JSON.stringify(JSON.parse(String(value)), null, 2);
    } catch {
      return '{\n  \n}';
    }
  }
}

function parseJsonField(
  text: string,
  setError: (message: string | null) => void,
  fieldName: string,
): Record<string, unknown> | null {
  const trimmed = text.trim();
  if (!trimmed) {
    setError(`Поле ${fieldName} не может быть пустым`);
    return null;
  }
  try {
    const parsed = JSON.parse(trimmed);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      setError(`Поле ${fieldName} должно содержать JSON-объект`);
      return null;
    }
    setError(null);
    return parsed as Record<string, unknown>;
  } catch (error) {
    setError(`Некорректный JSON (${(error as Error).message})`);
    return null;
  }
}

function readOwner(meta: unknown): string {
  if (meta && typeof meta === 'object' && !Array.isArray(meta) && 'owner' in meta) {
    const ownerValue = (meta as Record<string, unknown>).owner;
    if (typeof ownerValue === 'string') {
      return ownerValue;
    }
  }
  return '';
}

export default function SiteGlobalBlockEditor(): React.ReactElement {
  const { blockId: routeBlockId } = useParams<{ blockId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { pushToast } = useToast();

  const templateState = (location.state as { template?: TemplateStatePayload } | null)?.template;
  const isCreateMode = !routeBlockId || routeBlockId === 'new';
  const blockId = !isCreateMode ? routeBlockId : null;

  const [loading, setLoading] = React.useState<boolean>(!isCreateMode);
  const [error, setError] = React.useState<string | null>(null);
  const [block, setBlock] = React.useState<SiteGlobalBlock | null>(null);
  const [usage, setUsage] = React.useState<SiteGlobalBlockUsage[]>([]);
  const [warnings, setWarnings] = React.useState<SiteGlobalBlockWarning[]>([]);
  const [history, setHistory] = React.useState<SiteGlobalBlockHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = React.useState(false);
  const [historyError, setHistoryError] = React.useState<string | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = React.useState(0);
  const [metrics, setMetrics] = React.useState<SiteGlobalBlockMetricsResponse | null>(null);
  const [metricsLoading, setMetricsLoading] = React.useState(false);
  const [metricsError, setMetricsError] = React.useState<string | null>(null);
  const [metricsPeriod, setMetricsPeriod] = React.useState<SiteMetricsPeriod>('7d');
  const [metricsRefreshKey, setMetricsRefreshKey] = React.useState(0);
  const [preview, setPreview] = React.useState<SiteBlockPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = React.useState(false);
  const [previewError, setPreviewError] = React.useState<string | null>(null);
  const [previewLocale, setPreviewLocale] = React.useState<LocaleOption>(normalizeLocale(templateState?.defaults.locale));
  const [previewLimit, setPreviewLimit] = React.useState<number>(6);

  const [dataText, setDataText] = React.useState<string>(toPrettyJson(templateState?.defaults.data ?? {}));
  const [metaText, setMetaText] = React.useState<string>(toPrettyJson(templateState?.defaults.meta ?? {}));
  const [dataError, setDataError] = React.useState<string | null>(null);
  const [metaError, setMetaError] = React.useState<string | null>(null);

  const [formKey, setFormKey] = React.useState<string>(templateState?.defaults.key ?? '');
  const [formTitle, setFormTitle] = React.useState<string>(templateState?.defaults.title ?? '');
  const [formSection, setFormSection] = React.useState<string>(templateState?.defaults.section ?? 'header');
  const [formLocale, setFormLocale] = React.useState<LocaleOption>(normalizeLocale(templateState?.defaults.locale));
  const [formRequiresPublisher, setFormRequiresPublisher] = React.useState<boolean>(
    templateState?.defaults.requires_publisher ?? true,
  );
  const [formOwner, setFormOwner] = React.useState<string>(readOwner(templateState?.defaults.meta));

  const [comment, setComment] = React.useState<string>('');
  const [reviewStatus, setReviewStatus] = React.useState<SiteGlobalBlock['review_status']>('none');
  const [dirty, setDirty] = React.useState<boolean>(isCreateMode);

  const [saving, setSaving] = React.useState(false);
  const [creating, setCreating] = React.useState(false);
  const [publishing, setPublishing] = React.useState(false);
  const [saveError, setSaveError] = React.useState<string | null>(null);
  const [publishError, setPublishError] = React.useState<string | null>(null);

  const [detailRefreshKey, setDetailRefreshKey] = React.useState(0);

  const hasUnsavedChanges = dirty;

  React.useEffect(() => {
    if (!isCreateMode && blockId) {
      const controller = new AbortController();
      setLoading(true);
      setError(null);
      managementSiteEditorApi
        .fetchSiteGlobalBlock(blockId, { signal: controller.signal })
        .then((response) => {
          if (controller.signal.aborted) {
            return;
          }
          const fetchedBlock = response.block ?? null;
          if (!fetchedBlock) {
            setError('Блок не найден или недоступен');
            setBlock(null);
            setLoading(false);
            return;
          }
          setBlock(fetchedBlock);
          setUsage(response.usage ?? []);
          setWarnings(response.warnings ?? []);
          setDataText(toPrettyJson(fetchedBlock.data));
          setMetaText(toPrettyJson(fetchedBlock.meta));
          setFormKey(fetchedBlock.key);
          setFormTitle(fetchedBlock.title);
          setFormSection(fetchedBlock.section ?? 'header');
          setFormLocale(normalizeLocale(fetchedBlock.locale));
          setFormRequiresPublisher(Boolean(fetchedBlock.requires_publisher));
          setFormOwner(readOwner(fetchedBlock.meta));
          setReviewStatus(fetchedBlock.review_status);
          setComment(fetchedBlock.comment ?? '');
          setPreviewLocale(normalizeLocale(fetchedBlock.locale));
          setDirty(false);
        })
        .catch((err) => {
          if (controller.signal.aborted) {
            return;
          }
          setError(extractErrorMessage(err, 'Не удалось получить данные блока'));
          setBlock(null);
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setLoading(false);
          }
        });

      return () => controller.abort();
    }

    setLoading(false);
    setError(null);
    setBlock(null);
    const defaults = templateState?.defaults;
    if (defaults) {
      setFormKey(defaults.key);
      setFormTitle(defaults.title);
      setFormSection(defaults.section);
      setFormLocale(normalizeLocale(defaults.locale));
      setFormRequiresPublisher(defaults.requires_publisher ?? true);
      const owner = readOwner(defaults.meta);
      setFormOwner(owner);
      const metaWithOwner = { ...(defaults.meta ?? {}) } as Record<string, unknown>;
      if (owner) {
        metaWithOwner.owner = owner;
      }
      setMetaText(toPrettyJson(metaWithOwner));
      setDataText(toPrettyJson(defaults.data ?? {}));
      setPreviewLocale(normalizeLocale(defaults.locale));
    }
    setReviewStatus('none');
    setComment('');
    setDirty(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [blockId, detailRefreshKey, isCreateMode]);

  React.useEffect(() => {
    if (isCreateMode || !blockId) {
      return;
    }
    const controller = new AbortController();
    setHistoryLoading(true);
    setHistoryError(null);
    managementSiteEditorApi
      .fetchSiteGlobalBlockHistory(
        blockId,
        { limit: 10 },
        { signal: controller.signal },
      )
      .then((response) => {
        if (!controller.signal.aborted) {
          setHistory(response.items ?? []);
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setHistoryError(extractErrorMessage(err, 'Не удалось получить историю блока'));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setHistoryLoading(false);
        }
      });

    return () => controller.abort();
  }, [blockId, historyRefreshKey, isCreateMode]);

  React.useEffect(() => {
    if (isCreateMode || !blockId) {
      return;
    }
    const controller = new AbortController();
    setMetricsLoading(true);
    setMetricsError(null);
    managementSiteEditorApi
      .fetchSiteGlobalBlockMetrics(
        blockId,
        { period: metricsPeriod },
        { signal: controller.signal },
      )
      .then((response) => {
        if (!controller.signal.aborted) {
          setMetrics(response ?? null);
        }
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setMetricsError(extractErrorMessage(err, 'Не удалось получить метрики блока'));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setMetricsLoading(false);
        }
      });

    return () => controller.abort();
  }, [blockId, metricsPeriod, metricsRefreshKey, isCreateMode]);

  const handleDataChange = React.useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDataText(event.target.value);
    setDirty(true);
    if (dataError) {
      setDataError(null);
    }
  }, [dataError]);

  const handleMetaChange = React.useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMetaText(event.target.value);
    setDirty(true);
    if (metaError) {
      setMetaError(null);
    }
  }, [metaError]);

  const handleFormKeyChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setFormKey(event.target.value);
    setDirty(true);
  }, []);

  const handleFormTitleChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setFormTitle(event.target.value);
    setDirty(true);
  }, []);

  const handleFormSectionChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setFormSection(event.target.value);
    setDirty(true);
  }, []);

  const handleFormLocaleChange = React.useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    setFormLocale(event.target.value as LocaleOption);
    setDirty(true);
  }, []);

  const handleFormOwnerChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setFormOwner(event.target.value);
    setDirty(true);
  }, []);

  const handleRequiresPublisherChange = React.useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    setFormRequiresPublisher(event.target.value === 'true');
    setDirty(true);
  }, []);

  const handleReviewStatusChange = React.useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    setReviewStatus(event.target.value as SiteGlobalBlock['review_status']);
    setDirty(true);
  }, []);

  const handleCommentChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setComment(event.target.value);
  }, []);

  const handleDetailRefresh = React.useCallback(() => {
    setDetailRefreshKey((key) => key + 1);
  }, []);

  const handleHistoryRefresh = React.useCallback(() => {
    setHistoryRefreshKey((key) => key + 1);
  }, []);

  const handleMetricsRefresh = React.useCallback(() => {
    setMetricsRefreshKey((key) => key + 1);
  }, []);

  const handleSaveDraft = React.useCallback(async (): Promise<boolean> => {
    if (!blockId || !block) {
      return false;
    }
    const parsedData = parseJsonField(dataText, setDataError, 'data');
    if (!parsedData) {
      return false;
    }
    const parsedMeta = parseJsonField(metaText, setMetaError, 'meta');
    if (!parsedMeta) {
      return false;
    }
    const trimmedOwner = formOwner.trim();
    if (trimmedOwner) {
      parsedMeta.owner = trimmedOwner;
    } else if ('owner' in parsedMeta) {
      delete parsedMeta.owner;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const nextBlock = await managementSiteEditorApi.saveSiteGlobalBlock(blockId, {
        version: block.draft_version ?? undefined,
        data: parsedData,
        meta: parsedMeta,
        comment: comment.trim() || null,
        review_status: reviewStatus,
      });
      setBlock(nextBlock);
      setDataText(toPrettyJson(nextBlock.data));
      setMetaText(toPrettyJson(nextBlock.meta));
      setFormOwner(readOwner(nextBlock.meta));
      setReviewStatus(nextBlock.review_status);
      setDirty(false);
      setSaveError(null);
      pushToast({ intent: 'success', description: 'Черновик сохранён' });
      return true;
    } catch (err) {
      setSaveError(extractErrorMessage(err, 'Не удалось сохранить черновик'));
      return false;
    } finally {
      setSaving(false);
    }
  }, [block, blockId, comment, dataText, formOwner, metaText, pushToast, reviewStatus]);

  const handlePreview = React.useCallback(async () => {
    if (!block?.key) {
      setPreviewError('Предпросмотр доступен после создания блока');
      return;
    }
    if (dirty) {
      const saved = await handleSaveDraft();
      if (!saved) {
        return;
      }
    }
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const response = await managementSiteEditorApi.previewSiteBlock(block.key, {
        locale: previewLocale,
        limit: previewLimit,
      });
      setPreview(response);
    } catch (err) {
      setPreview(null);
      setPreviewError(extractErrorMessage(err, 'Не удалось получить предпросмотр'));
    } finally {
      setPreviewLoading(false);
    }
  }, [block?.key, dirty, handleSaveDraft, previewLimit, previewLocale]);

  const handlePublish = React.useCallback(async () => {
    if (!blockId || !block) {
      return;
    }
    if (dirty) {
      const saved = await handleSaveDraft();
      if (!saved) {
        return;
      }
    }
    setPublishing(true);
    setPublishError(null);
    try {
      const response = await managementSiteEditorApi.publishSiteGlobalBlock(blockId, {
        version: block.draft_version ?? undefined,
        comment: comment.trim() || undefined,
      });
      setBlock(response.block);
      setUsage(response.usage ?? []);
      setPublishError(null);
      setDirty(false);
      pushToast({ intent: 'success', description: 'Глобальный блок опубликован' });
      setHistoryRefreshKey((key) => key + 1);
      setMetricsRefreshKey((key) => key + 1);
    } catch (err) {
      setPublishError(extractErrorMessage(err, 'Не удалось опубликовать блок'));
    } finally {
      setPublishing(false);
    }
  }, [block, blockId, comment, dirty, handleSaveDraft, pushToast]);

  const handleCreateBlock = React.useCallback(async () => {
    if (!isCreateMode) {
      return;
    }
    const trimmedKey = formKey.trim();
    const trimmedTitle = formTitle.trim();
    const trimmedSection = formSection.trim();
    if (!trimmedKey) {
      setSaveError('Укажите системный ключ блока');
      return;
    }
    if (!trimmedTitle) {
      setSaveError('Укажите название блока');
      return;
    }
    if (!trimmedSection) {
      setSaveError('Укажите зону, где используется блок');
      return;
    }
    const parsedData = parseJsonField(dataText, setDataError, 'data');
    if (!parsedData) {
      return;
    }
    const parsedMeta = parseJsonField(metaText, setMetaError, 'meta');
    if (!parsedMeta) {
      return;
    }
    const ownerValue = formOwner.trim();
    if (ownerValue) {
      parsedMeta.owner = ownerValue;
    } else if ('owner' in parsedMeta) {
      delete parsedMeta.owner;
    }
    setCreating(true);
    setSaveError(null);
    try {
      const payload: CreateSiteGlobalBlockPayload = {
        key: trimmedKey,
        title: trimmedTitle,
        section: trimmedSection,
        locale: formLocale,
        requires_publisher: formRequiresPublisher,
        data: parsedData,
        meta: parsedMeta,
      };
      const created = await managementSiteEditorApi.createSiteGlobalBlock(payload);
      pushToast({ intent: 'success', description: `Глобальный блок «${created.title}» создан` });
      navigate(`/management/site-editor/global-blocks/${created.id}`, { replace: true });
      setBlock(created);
      setUsage([]);
      setWarnings([]);
      setReviewStatus(created.review_status);
      setComment('');
      setDirty(false);
    } catch (err) {
      setSaveError(extractErrorMessage(err, 'Не удалось создать глобальный блок'));
    } finally {
      setCreating(false);
    }
  }, [
    dataText,
    formKey,
    formLocale,
    formOwner,
    formRequiresPublisher,
    formSection,
    formTitle,
    isCreateMode,
    metaText,
    navigate,
    pushToast,
  ]);

  if (isCreateMode) {
    return (
      <div className="space-y-6 pb-24">
        {templateState ? (
          <Card className="space-y-2 border-primary-200/70 bg-primary-50/80 p-4 text-sm text-primary-700 dark:border-primary-500/40 dark:bg-primary-500/15 dark:text-primary-100">
            <div className="flex flex-wrap items-center gap-2">
              <span>
                Создаёте блок на основе шаблона «{templateState.label}».
                {templateState.locale ? ` Базовая локаль — ${templateState.locale}.` : ''}
              </span>
              {templateState.documentationUrl ? (
                <a
                  href={templateState.documentationUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-semibold underline-offset-2 hover:underline"
                >
                  Документация
                  <ExternalLink className="h-3 w-3" />
                </a>
              ) : null}
            </div>
            {templateState.note ? (
              <div className="text-xs text-primary-700/80 dark:text-primary-200/80">{templateState.note}</div>
            ) : null}
          </Card>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <Button as={Link} to="/management/site-editor?tab=blocks" variant="ghost" size="sm">
            ← К каталогу
          </Button>
          <div className="space-y-0.5">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">Новый глобальный блок</div>
            <div className="text-xs text-gray-500 dark:text-dark-200">{formKey || 'Укажите ключ'}</div>
          </div>
        </div>

        <Card className="space-y-4 p-5">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200" htmlFor="formTitle">
                Название
              </label>
              <Input
                id="formTitle"
                value={formTitle}
                onChange={handleFormTitleChange}
                placeholder="Например, Глобальный хедер"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200" htmlFor="formKey">
                Системный ключ
              </label>
              <Input id="formKey" value={formKey} onChange={handleFormKeyChange} placeholder="header-default" />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200" htmlFor="formSection">
                Зона (section)
              </label>
              <Input
                id="formSection"
                value={formSection}
                onChange={handleFormSectionChange}
                placeholder="header, footer, promo..."
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200" htmlFor="formLocale">
                Базовая локаль
              </label>
              <Select id="formLocale" value={formLocale} onChange={handleFormLocaleChange}>
                {LOCALE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200" htmlFor="formOwner">
                Ответственный владелец
              </label>
              <Input
                id="formOwner"
                value={formOwner}
                onChange={handleFormOwnerChange}
                placeholder="team_public_site"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-600 dark:text-dark-200" htmlFor="formRequires">
                Требует подтверждения publisher
              </label>
              <Select id="formRequires" value={String(formRequiresPublisher)} onChange={handleRequiresPublisherChange}>
                <option value="true">Да, только publisher</option>
                <option value="false">Нет, достаточно роли editor</option>
              </Select>
            </div>
          </div>
          {saveError ? (
            <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/40 dark:text-rose-200">
              <AlertTriangle className="mt-0.5 h-4 w-4" />
              <span>{saveError}</span>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleCreateBlock} disabled={creating}>
              {creating ? 'Создание…' : 'Создать блок'}
            </Button>
            <Button as={Link} to="/management/site-editor?tab=blocks" variant="ghost">
              Отмена
            </Button>
          </div>
        </Card>

        <Card className="space-y-2 p-5">
          <div>
            <div className="text-sm font-semibold text-gray-900 dark:text-white">Конфигурация блока (data)</div>
            <p className="text-xs text-gray-500 dark:text-dark-200">
              JSON данных блока. Убедитесь, что структура соответствует схеме шаблона.
            </p>
          </div>
          <Textarea rows={18} value={dataText} onChange={handleDataChange} className="font-mono text-xs" />
          {dataError ? <div className="text-xs text-rose-600 dark:text-rose-300">{dataError}</div> : null}
        </Card>

        <Card className="space-y-2 p-5">
          <div>
            <div className="text-sm font-semibold text-gray-900 dark:text-white">Метаданные блока (meta)</div>
            <p className="text-xs text-gray-500 dark:text-dark-200">
              Дополнительные параметры. Значение владельца синхронизируется с полем выше.
            </p>
          </div>
          <Textarea rows={12} value={metaText} onChange={handleMetaChange} className="font-mono text-xs" />
          {metaError ? <div className="text-xs text-rose-600 dark:text-rose-300">{metaError}</div> : null}
        </Card>

        <Card className="space-y-3 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-gray-900 dark:text-white">Предпросмотр</div>
              <p className="text-xs text-gray-500 dark:text-dark-200">
                Предпросмотр станет доступен после создания блока.
              </p>
            </div>
            <Button type="button" variant="outlined" disabled>
              Недоступно
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (!blockId) {
    return (
      <div className="space-y-4 p-6">
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
          Не указан идентификатор блока.
        </div>
        <Button as={Link} to="/management/site-editor?tab=blocks" variant="ghost" size="sm">
          Вернуться к каталогу
        </Button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center py-24">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4 p-6">
        <div className="flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
          <AlertTriangle className="mt-0.5 h-4 w-4" />
          <span>{error}</span>
        </div>
        <Button as={Link} to="/management/site-editor?tab=blocks" variant="ghost" size="sm">
          Вернуться к каталогу
        </Button>
      </div>
    );
  }

  if (!block) {
    return (
      <div className="space-y-4 p-6">
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
          Блок не найден или недоступен.
        </div>
        <Button as={Link} to="/management/site-editor?tab=blocks" variant="ghost" size="sm">
          Вернуться к каталогу
        </Button>
      </div>
    );
  }

  const statusInfo = globalBlockStatusAppearance(block.status);
  const reviewInfo = reviewAppearance(reviewStatus);
  const reviewBadgeColor = REVIEW_STATUS_BADGE_COLOR[reviewStatus] ?? 'neutral';
  const requiresPublisher = block.requires_publisher;

  return (
    <div className="space-y-6 pb-24">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <Button as={Link} to="/management/site-editor?tab=blocks" variant="ghost" size="sm">
            ← К каталогу
          </Button>
          <div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">{block.title}</div>
            <div className="text-xs text-gray-500 dark:text-dark-200">{block.key}</div>
          </div>
          <Badge color={statusInfo.color} variant="soft">
            {statusInfo.label}
          </Badge>
          <Badge color={reviewBadgeColor} variant="outline">
            {reviewInfo.label}
          </Badge>
          {requiresPublisher ? (
            <Badge color="warning" variant="soft">
              Только publisher
            </Badge>
          ) : null}
          {hasUnsavedChanges ? (
            <Badge color="warning" variant="outline">
              Черновик изменён
            </Badge>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
          <div>
            Обновлён{' '}
            {formatDateTime(block.updated_at, {
              fallback: '—',
              withSeconds: true,
            })}
          </div>
          <div>Изменил: {block.updated_by || '—'}</div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-8">
          <Card className="space-y-4 p-5">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Название</label>
                <Input value={formTitle} disabled placeholder="Название блока" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Системный ключ</label>
                <Input value={formKey} disabled />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Зона</label>
                <Input value={formSection} disabled />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Локаль</label>
                <Select value={formLocale} disabled>
                  {LOCALE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Ответственный</label>
                <Input value={formOwner} onChange={handleFormOwnerChange} placeholder="team_public_site" />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-600 dark:text-dark-200">Права публикации</label>
                <Input value={requiresPublisher ? 'Только publisher' : 'Доступно редакторам'} disabled />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <MetaItem label="Версия черновика" value={block.draft_version ?? '—'} />
              <MetaItem label="Опубликованная версия" value={block.published_version ?? '—'} />
              <MetaItem label="Комментарий" value={block.comment || '—'} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <label className="text-sm font-medium text-gray-700 dark:text-dark-100" htmlFor="reviewStatus">
                  Статус ревью
                </label>
                <Select id="reviewStatus" value={reviewStatus} onChange={handleReviewStatusChange}>
                  {REVIEW_STATUS_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium text-gray-700 dark:text-dark-100" htmlFor="comment">
                  Комментарий к черновику
                </label>
                <Input
                  id="comment"
                  value={comment}
                  onChange={handleCommentChange}
                  placeholder="Опишите изменения"
                />
              </div>
            </div>
            {saveError ? (
              <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/40 dark:text-rose-200">
                <AlertTriangle className="mt-0.5 h-4 w-4" />
                <span>{saveError}</span>
              </div>
            ) : null}
            <div className="flex flex-wrap gap-2">
              <Button type="button" onClick={handleSaveDraft} disabled={saving}>
                {saving ? 'Сохранение…' : 'Сохранить черновик'}
              </Button>
              <Button type="button" variant="outlined" onClick={handlePublish} disabled={publishing}>
                {publishing ? 'Публикация…' : 'Опубликовать'}
              </Button>
              <Button type="button" variant="ghost" onClick={handleDetailRefresh}>
                Обновить данные
              </Button>
            </div>
            {publishError ? (
              <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/40 dark:text-rose-200">
                <AlertTriangle className="mt-0.5 h-4 w-4" />
                <span>{publishError}</span>
              </div>
            ) : null}
          </Card>

          <Card className="space-y-2 p-5">
            <div>
              <div className="text-sm font-semibold text-gray-900 dark:text-white">Конфигурация (data)</div>
              <p className="text-xs text-gray-500 dark:text-dark-200">
                Обновляйте JSON и сохраняйте черновик, чтобы зафиксировать изменения.
              </p>
            </div>
            <Textarea rows={16} value={dataText} onChange={handleDataChange} className="font-mono text-xs" />
            {dataError ? <div className="text-xs text-rose-600 dark:text-rose-300">{dataError}</div> : null}
          </Card>

          <Card className="space-y-2 p-5">
            <div>
              <div className="text-sm font-semibold text-gray-900 dark:text-white">Метаданные (meta)</div>
              <p className="text-xs text-gray-500 dark:text-dark-200">
                Дополнительные параметры блока. Значение владельца синхронизируется с полем выше.
              </p>
            </div>
            <Textarea rows={12} value={metaText} onChange={handleMetaChange} className="font-mono text-xs" />
            {metaError ? <div className="text-xs text-rose-600 dark:text-rose-300">{metaError}</div> : null}
          </Card>

          <Card className="space-y-4 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">Предпросмотр</div>
                <p className="text-xs text-gray-500 dark:text-dark-200">
                  Обновите предварительный просмотр, чтобы увидеть актуальную выдачу.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Select
                  value={previewLocale}
                  onChange={(event) => setPreviewLocale(event.target.value as LocaleOption)}
                >
                  {LOCALE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
                <Select value={previewLimit} onChange={(event) => setPreviewLimit(Number(event.target.value))}>
                  {PREVIEW_LIMIT_OPTIONS.map((limit) => (
                    <option key={limit} value={limit}>
                      {limit} элементов
                    </option>
                  ))}
                </Select>
                <Button type="button" variant="outlined" onClick={handlePreview} disabled={previewLoading}>
                  {previewLoading ? 'Обновляем…' : 'Обновить предпросмотр'}
                </Button>
              </div>
            </div>
            {previewError ? (
              <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/40 dark:text-rose-200">
                <AlertTriangle className="mt-0.5 h-4 w-4" />
                <span>{previewError}</span>
              </div>
            ) : null}
            {previewLoading ? (
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
                <Spinner className="h-4 w-4" />
                Загружаем предпросмотр…
              </div>
            ) : null}
            {preview && !previewLoading ? (
              <div className="space-y-3">
                <div className="text-xs text-gray-500 dark:text-dark-200">
                  Источник: {preview.source ?? '—'} · Получено:{' '}
                  {formatDateTime(preview.fetched_at ?? preview.fetchedAt ?? null, {
                    fallback: '—',
                    withSeconds: true,
                  })}
                </div>
                {preview.items && preview.items.length ? (
                  <ul className="space-y-2">
                    {preview.items.map((item, index) => (
                      <li
                        key={`${item.id ?? index}-${item.href ?? index}`}
                        className="rounded-xl border border-gray-200 p-3 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200"
                      >
                        <div className="text-sm font-semibold text-gray-900 dark:text-white">
                          {item.title || 'Без названия'}
                        </div>
                        {item.subtitle ? (
                          <div className="text-xs text-gray-500 dark:text-dark-300">{item.subtitle}</div>
                        ) : null}
                        {item.href ? (
                          <div className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-dark-300">
                            {item.href}
                          </div>
                        ) : null}
                        <div className="mt-2 grid gap-2 sm:grid-cols-2">
                          <MetaItem label="Поставщик" value={item.provider || '—'} />
                          <MetaItem
                            label="Счёт"
                            value={formatNumber(item.score ?? null, {
                              defaultValue: '—',
                              maximumFractionDigits: 2,
                            })}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="rounded-xl border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-300">
                    Предпросмотр пуст. Проверьте источники данных или обновите конфигурацию.
                  </div>
                )}
              </div>
            ) : null}
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-4">
          <GlobalBlockWarnings warnings={warnings} />
          <GlobalBlockUsageList usage={usage} loading={loading} />
          <GlobalBlockHistoryPanel
            entries={history}
            loading={historyLoading}
            error={historyError}
            onRefresh={handleHistoryRefresh}
          />
          <GlobalBlockMetricsPanel
            metrics={metrics}
            loading={metricsLoading}
            error={metricsError}
            period={metricsPeriod}
            onChangePeriod={setMetricsPeriod}
            onRefresh={handleMetricsRefresh}
          />
        </div>
      </div>
    </div>
  );
}
