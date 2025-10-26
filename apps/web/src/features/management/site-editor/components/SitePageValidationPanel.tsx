import React from 'react';
import { Badge, Button, Card } from '@ui';
import type { SiteDraftValidationResult } from '@shared/types/management';
import type { ValidationSummary } from '../../home/validation';

type SitePageValidationPanelProps = {
  clientValidation: ValidationSummary;
  serverValidation: SiteDraftValidationResult | null;
  serverValidationLoading: boolean;
  serverValidationError: string | null;
  onRunServerValidation: () => void;
};

type ErrorEntry = {
  path: string;
  message: string;
  validator?: string;
};

function renderErrorList(errors: ErrorEntry[] | undefined, keyPrefix: string): React.ReactNode {
  if (!errors || errors.length === 0) {
    return null;
  }
  return (
    <ul className="space-y-1 pl-4 text-xs text-rose-600 dark:text-rose-400">
      {errors.map((error, index) => (
        <li key={`${keyPrefix}-${index}`}>
          <span className="font-mono text-[11px] text-rose-500/80">{error.path || '/'}</span>
          <span className="mx-1 text-rose-500/60">—</span>
          <span>{error.message}</span>
        </li>
      ))}
    </ul>
  );
}

export function SitePageValidationPanel({
  clientValidation,
  serverValidation,
  serverValidationLoading,
  serverValidationError,
  onRunServerValidation,
}: SitePageValidationPanelProps): React.ReactElement {
  const hasClientErrors = !clientValidation.valid;
  const clientBlockErrors = React.useMemo(
    () => Object.entries(clientValidation.blocks || {}).filter(([, errors]) => errors.length > 0),
    [clientValidation.blocks],
  );

  const serverErrors = serverValidation?.errors;
  const serverBlockErrors = React.useMemo(
    () =>
      Object.entries(serverErrors?.blocks ?? {}).filter(([, errors]) => Array.isArray(errors) && errors.length > 0),
    [serverErrors?.blocks],
  );

  const handleServerValidation = React.useCallback(() => {
    if (!serverValidationLoading) {
      onRunServerValidation();
    }
  }, [onRunServerValidation, serverValidationLoading]);

  return (
    <Card padding="md" className="space-y-4">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Валидация конфигурации</h2>
          <p className="text-xs text-gray-500 dark:text-dark-200">
            Клиентская проверка выполняется автоматически. Серверная — проверяет схему и ограничения API.
          </p>
        </div>
        <Button
          size="xs"
          variant="outlined"
          disabled={serverValidationLoading}
          onClick={handleServerValidation}
        >
          {serverValidationLoading ? 'Проверка…' : 'Проверить сервером'}
        </Button>
      </div>

      {serverValidationError ? (
        <div className="rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-600/60 dark:bg-rose-950/40 dark:text-rose-200">
          {serverValidationError}
        </div>
      ) : null}

      {hasClientErrors ? (
        <div className="space-y-2 rounded-md border border-amber-300/70 bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:border-amber-600/60 dark:bg-amber-950/40 dark:text-amber-200">
          <div className="flex items-center gap-2">
            <Badge color="warning">
              Клиент
            </Badge>
            <span className="font-medium">Найдены ошибки</span>
          </div>
          {renderErrorList(clientValidation.general, 'client-general')}
          {clientBlockErrors.length ? (
            <div className="space-y-1">
              {clientBlockErrors.map(([blockId, errors]) => (
                <div key={`client-block-${blockId}`}>
                  <div className="font-semibold text-amber-700 dark:text-amber-300">{`Блок ${blockId}`}</div>
                  {renderErrorList(errors, `client-block-${blockId}`)}
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : (
        <div className="rounded-md border border-emerald-300/70 bg-emerald-50 px-3 py-2 text-xs text-emerald-800 dark:border-emerald-600/60 dark:bg-emerald-950/40 dark:text-emerald-200">
          <div className="flex items-center gap-2">
            <Badge color="success">
              Клиент
            </Badge>
            <span className="font-medium">Ошибок не найдено</span>
          </div>
        </div>
      )}

      {serverValidation ? (
        serverValidation.valid ? (
          <div className="rounded-md border border-emerald-300/70 bg-emerald-50 px-3 py-2 text-xs text-emerald-800 dark:border-emerald-600/60 dark:bg-emerald-950/40 dark:text-emerald-200">
            <div className="flex items-center gap-2">
              <Badge color="success">
                Сервер
              </Badge>
              <span className="font-medium">Серверная проверка прошла успешно</span>
            </div>
          </div>
        ) : (
          <div className="space-y-2 rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-600/60 dark:bg-rose-950/40 dark:text-rose-200">
            <div className="flex items-center gap-2">
              <Badge color="error">
                Сервер
              </Badge>
              <span className="font-medium">Серверная проверка не прошла</span>
            </div>
            {renderErrorList(serverErrors?.general, 'server-general')}
            {serverBlockErrors.length ? (
              <div className="space-y-1">
                {serverBlockErrors.map(([blockId, errors]) => (
                  <div key={`server-block-${blockId}`}>
                    <div className="font-semibold text-rose-700 dark:text-rose-200">{`Блок ${blockId}`}</div>
                    {renderErrorList(errors, `server-block-${blockId}`)}
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        )
      ) : (
        <p className="text-xs text-gray-500 dark:text-dark-200">
          Серверная проверка ещё не выполнялась. Запустите её, чтобы убедиться, что конфигурация пройдет проверку API.
        </p>
      )}
    </Card>
  );
}

export default SitePageValidationPanel;
