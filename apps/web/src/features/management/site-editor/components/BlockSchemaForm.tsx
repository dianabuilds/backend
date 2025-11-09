import React from 'react';
import { Plus, Trash2 } from '@icons';
import { Button, Card, Input, Select, Switch, Tabs, TagInput, Textarea } from '@ui';

type JsonSchema = {
  title?: string;
  description?: string;
  type?: string | string[];
  properties?: Record<string, JsonSchema>;
  items?: JsonSchema | JsonSchema[];
  enum?: Array<string | number>;
  required?: string[];
  default?: unknown;
  format?: string;
  minimum?: number;
  maximum?: number;
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  Boolean(value) && typeof value === 'object' && !Array.isArray(value);

const normalizeType = (schema?: JsonSchema): string | undefined => {
  if (!schema) return undefined;
  if (Array.isArray(schema.type)) {
    return schema.type[0];
  }
  return schema.type;
};

const buildInitialValue = (schema?: JsonSchema): unknown => {
  if (!schema) return '';
  if (schema.default !== undefined) {
    return schema.default;
  }
  const type = normalizeType(schema);
  switch (type) {
    case 'object': {
      const initial: Record<string, unknown> = {};
      if (schema.properties) {
        Object.entries(schema.properties).forEach(([key, child]) => {
          initial[key] = buildInitialValue(child);
        });
      }
      return initial;
    }
    case 'array':
      return [];
    case 'number':
    case 'integer':
      return schema.minimum ?? 0;
    case 'boolean':
      return false;
    default:
      return '';
  }
};

type FieldRendererProps = {
  schema: JsonSchema;
  value: unknown;
  onChange: (nextValue: unknown) => void;
  required?: boolean;
};

const FieldLabel = ({
  schema,
  required,
}: {
  schema: JsonSchema;
  required?: boolean;
}): React.ReactElement | null => {
  if (!schema.title && !schema.description) {
    return null;
  }
  return (
    <div className="space-y-1">
      {schema.title ? (
        <label className="flex items-center gap-1 text-xs font-semibold text-gray-700 dark:text-dark-100">
          {schema.title}
          {required ? <span className="text-rose-500">*</span> : null}
        </label>
      ) : null}
      {schema.description ? <p className="text-2xs text-gray-500">{schema.description}</p> : null}
    </div>
  );
};

function PrimitiveField({ schema, value, onChange }: FieldRendererProps): React.ReactElement {
  const type = normalizeType(schema);
  if (schema.enum && schema.enum.length) {
    const normalizedValue =
      typeof value === 'string' || typeof value === 'number' ? String(value) : String(schema.enum[0]);
    return (
      <Select value={normalizedValue} onChange={(event) => onChange(event.target.value)}>
        {schema.enum.map((option) => (
          <option key={String(option)} value={String(option)}>
            {String(option)}
          </option>
        ))}
      </Select>
    );
  }
  switch (type) {
    case 'boolean': {
      const checked = typeof value === 'boolean' ? value : Boolean(value);
      return <Switch checked={checked} onChange={(next) => onChange(next)} />;
    }
    case 'number':
    case 'integer': {
      const numeric = typeof value === 'number' ? value : '';
      return (
        <Input
          type="number"
          value={numeric}
          onChange={(event) => {
            const parsed = event.target.value;
            onChange(parsed === '' ? '' : Number(parsed));
          }}
        />
      );
    }
    case 'string': {
      const formatted = typeof value === 'string' ? value : '';
      if (schema.format === 'textarea' || (schema.description && schema.description.length > 80)) {
        return <Textarea rows={4} value={formatted} onChange={(event) => onChange(event.target.value)} />;
      }
      return <Input value={formatted} onChange={(event) => onChange(event.target.value)} />;
    }
    default: {
      const formatted =
        typeof value === 'string'
          ? value
          : value !== undefined
          ? JSON.stringify(value, null, 2)
          : '';
      return (
        <Textarea
          rows={4}
          value={formatted}
          onChange={(event) => onChange(event.target.value)}
          placeholder="JSON"
        />
      );
    }
  }
}

function ArrayField({ schema, value, onChange }: FieldRendererProps): React.ReactElement {
  const itemsSchema = Array.isArray(schema.items) ? schema.items[0] : schema.items;
  const itemsValue = Array.isArray(value) ? value : [];

  if (!itemsSchema || normalizeType(itemsSchema) === 'string') {
    const tags = itemsValue.filter((item): item is string => typeof item === 'string');
    return (
      <TagInput
        value={tags}
        onChange={(next) => onChange(next)}
        placeholder="Введите значения и нажмите Enter"
      />
    );
  }

  return (
    <div className="space-y-3">
      {itemsValue.map((item, index) => (
        <Card
          key={`array-item-${index}`}
          className="space-y-2 border border-dashed border-gray-200 bg-white/90 p-3 shadow-sm"
        >
          <div className="flex items-center justify-between text-xs font-semibold text-gray-600">
            <span>Элемент #{index + 1}</span>
            <Button
              size="xs"
              variant="ghost"
              color="neutral"
              onClick={() => {
                const next = itemsValue.filter((_, idx) => idx !== index);
                onChange(next);
              }}
              className="inline-flex items-center gap-1"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Удалить
            </Button>
          </div>
          {renderField({
            schema: itemsSchema,
            value: item,
            onChange: (nextValue) => {
              const next = [...itemsValue];
              next[index] = nextValue;
              onChange(next);
            },
          })}
        </Card>
      ))}
      <Button
        variant="ghost"
        color="primary"
        size="sm"
        onClick={() => {
          onChange([...itemsValue, buildInitialValue(itemsSchema)]);
        }}
        className="inline-flex items-center gap-1"
      >
        <Plus className="h-4 w-4" />
        Добавить элемент
      </Button>
    </div>
  );
}

function ObjectField({ schema, value, onChange }: FieldRendererProps): React.ReactElement {
  const currentValue = isRecord(value) ? value : {};
  const properties = schema.properties ?? {};
  const requiredSet = new Set(schema.required ?? []);
  return (
    <div className="space-y-3 rounded-2xl border border-gray-100/80 bg-gray-50/70 p-3">
      {Object.entries(properties).map(([key, childSchema]) => {
        const childValue = currentValue[key];
        return (
          <div key={key} className="space-y-1">
            <FieldLabel schema={childSchema} required={requiredSet.has(key)} />
            {renderField({
              schema: childSchema,
              value: childValue,
              onChange: (next) => {
                onChange({ ...currentValue, [key]: next });
              },
            })}
          </div>
        );
      })}
    </div>
  );
}

function renderField(props: FieldRendererProps): React.ReactElement {
  const type = normalizeType(props.schema);
  if (type === 'object' || props.schema.properties) {
    return ObjectField(props);
  }
  if (type === 'array') {
    return ArrayField(props);
  }
  return PrimitiveField(props);
}

export type BlockSchemaFormProps = {
  localeSchema: JsonSchema | null;
  sharedSchema?: JsonSchema | null;
  localeValue: Record<string, unknown>;
  sharedValue?: Record<string, unknown>;
  locales: string[];
  activeLocale: string;
  onActiveLocaleChange: (locale: string) => void;
  onLocaleValueChange: (locale: string, value: Record<string, unknown>) => void;
  onSharedValueChange?: (value: Record<string, unknown>) => void;
};

export function BlockSchemaForm({
  localeSchema,
  sharedSchema,
  localeValue,
  sharedValue,
  locales,
  activeLocale,
  onActiveLocaleChange,
  onLocaleValueChange,
  onSharedValueChange,
}: BlockSchemaFormProps): React.ReactElement {
  const normalizedLocaleValue = isRecord(localeValue) ? localeValue : {};
  const normalizedSharedValue = isRecord(sharedValue) ? sharedValue : {};
  const localeTabs = locales.map((locale) => ({
    key: locale,
    label: locale.toUpperCase(),
  }));

  if (!localeSchema) {
    return (
      <Card className="border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-600 dark:border-dark-600 dark:bg-dark-800">
        Для этого блока пока нет схемы параметров. Обновите библиотеку или переключитесь в ручной режим.
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Параметры блока</h3>
          <p className="text-xs text-gray-500 dark:text-dark-200">
            Заполняйте контент для каждой локали. Обязательные поля отмечены символом *.
          </p>
        </div>
        <Tabs items={localeTabs} value={activeLocale} onChange={(key) => onActiveLocaleChange(String(key))} />
      </div>

      <div className="space-y-3">
        {renderField({
          schema: localeSchema,
          value: normalizedLocaleValue,
          onChange: (next) => onLocaleValueChange(activeLocale, (next as Record<string, unknown>) ?? {}),
        })}
      </div>

      {sharedSchema ? (
        <div className="space-y-3 rounded-3xl border border-dashed border-gray-200 bg-white/80 p-4 shadow-inner dark:border-dark-600">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Общие настройки</h4>
              <p className="text-xs text-gray-500">Применяются для всех локалей.</p>
            </div>
          </div>
          {renderField({
            schema: sharedSchema,
            value: normalizedSharedValue,
            onChange: (next) => onSharedValueChange?.((next as Record<string, unknown>) ?? {}),
          })}
        </div>
      ) : null}
    </div>
  );
}

export default BlockSchemaForm;
