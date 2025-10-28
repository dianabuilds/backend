import React from 'react';
import {
  Button,
  Card,
  Input,
  Textarea,
  useToast,
} from '@ui';

import type { BillingCryptoConfig } from '@shared/types/management';

import { formatDate } from '../helpers';

type CryptoTabProps = {
  config: BillingCryptoConfig;
  onSave: (payload: BillingCryptoConfig) => Promise<void>;
  onTest: () => Promise<void>;
};

export function CryptoTab({ config, onSave, onTest }: CryptoTabProps): React.ReactElement {
  const { pushToast } = useToast();

  const [form, setForm] = React.useState<BillingCryptoConfig>(config);
  const [saving, setSaving] = React.useState(false);
  const [testing, setTesting] = React.useState(false);
  const [history, setHistory] = React.useState<
    Array<{ id: string; at: string; payload: BillingCryptoConfig }>
  >([]);

  React.useEffect(() => {
    setForm(config);
  }, [config]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(form);
      setHistory((prev) => [
        { id: Date.now().toString(36), at: new Date().toISOString(), payload: form },
        ...prev,
      ]);
      pushToast({ intent: 'success', description: 'Настройки сохранены' });
    } catch (err) {
      pushToast({
        intent: 'error',
        description:
          err instanceof Error ? err.message : 'Не удалось сохранить настройки',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      await onTest();
      pushToast({ intent: 'success', description: 'Подключение к RPC проверено' });
    } catch (err) {
      pushToast({
        intent: 'error',
        description:
          err instanceof Error ? err.message : 'Не удалось проверить RPC',
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
      <Card className="p-5 space-y-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Настройки RPC</h2>
          <p className="text-sm text-gray-500">Управление конфигурацией криптоплатежей.</p>
        </div>

        <Textarea
          label="RPC endpoints (JSON)"
          rows={6}
          value={JSON.stringify(form.rpc_endpoints, null, 2)}
          onChange={(event) => {
            try {
              const parsed = JSON.parse(event.target.value);
              setForm((prev) => ({ ...prev, rpc_endpoints: parsed }));
            } catch {
              setForm((prev) => ({ ...prev, rpc_endpoints: prev.rpc_endpoints }));
            }
          }}
        />

        <Textarea
          label="Fallback networks (JSON)"
          rows={6}
          value={JSON.stringify(form.fallback_networks, null, 2)}
          onChange={(event) => {
            try {
              const parsed = JSON.parse(event.target.value);
              setForm((prev) => ({ ...prev, fallback_networks: parsed }));
            } catch {
              setForm((prev) => ({ ...prev, fallback_networks: prev.fallback_networks }));
            }
          }}
        />

        <div className="grid gap-3 sm:grid-cols-2">
          <Input
            label="Retries"
            type="number"
            value={String(form.retries ?? '')}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, retries: Number(event.target.value || 0) }))
            }
          />
          <Input
            label="Gas price cap"
            type="number"
            value={form.gas_price_cap != null ? String(form.gas_price_cap) : ''}
            onChange={(event) =>
              setForm((prev) => ({
                ...prev,
                gas_price_cap: event.target.value === '' ? null : Number(event.target.value),
              }))
            }
          />
        </div>

        <div className="flex items-center justify-end gap-2">
          <Button size="sm" variant="ghost" disabled={testing} onClick={() => void handleTest()}>
            {testing ? 'Проверка…' : 'Проверить подключение'}
          </Button>
          <Button size="sm" onClick={() => void handleSave()} disabled={saving}>
            {saving ? 'Сохранение…' : 'Сохранить'}
          </Button>
        </div>
      </Card>

      <div className="space-y-4">
        <Card className="p-5 space-y-2">
          <h3 className="text-sm font-semibold text-gray-900">Журнал изменений</h3>
          <div className="space-y-2 text-xs text-gray-600">
            {history.length === 0 ? (
              <div>История появится после сохранения изменений.</div>
            ) : (
              history.map((entry) => (
                <div key={entry.id} className="rounded border border-gray-200 p-2">
                  <div className="text-gray-500">{formatDate(entry.at)}</div>
                  <pre className="mt-1 max-h-40 overflow-auto rounded bg-gray-50 p-2">
                    {JSON.stringify(entry.payload, null, 2)}
                  </pre>
                </div>
              ))
            )}
          </div>
        </Card>
        <Card className="p-5 text-xs text-gray-500">
          Для проверки используется текущая конфигурация. Убедитесь, что параметры валидны перед применением на прод.
        </Card>
      </div>
    </div>
  );
}
