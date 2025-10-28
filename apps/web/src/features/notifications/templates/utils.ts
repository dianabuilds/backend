export type TemplateFieldType = 'string' | 'text' | 'number' | 'boolean' | 'json';

export type TemplateFieldRow = {
  id: number;
  key: string;
  type: TemplateFieldType;
  value: string;
};

export const LOCALE_PRESETS = ['ru', 'en'] as const;

export const TEMPLATE_FIELD_TYPES: Array<{ value: TemplateFieldType; label: string }> = [
  { value: 'string', label: 'Short text' },
  { value: 'text', label: 'Rich text' },
  { value: 'number', label: 'Number' },
  { value: 'boolean', label: 'Yes / No' },
  { value: 'json', label: 'JSON snippet' },
];

export function createTemplateRow(id: number): TemplateFieldRow {
  return { id, key: '', type: 'string', value: '' };
}

export function objectToTemplateRows(
  value: Record<string, unknown> | null | undefined,
  startId: number = 1,
): [TemplateFieldRow[], number] {
  const rows: TemplateFieldRow[] = [];
  let nextId = startId;
  if (value) {
    for (const [key, raw] of Object.entries(value)) {
      let type: TemplateFieldType = 'string';
      let stored = '';
      if (typeof raw === 'boolean') {
        type = 'boolean';
        stored = raw ? 'true' : 'false';
      } else if (typeof raw === 'number') {
        type = 'number';
        stored = String(raw);
      } else if (typeof raw === 'string') {
        type = raw.includes('\n') || raw.length > 80 ? 'text' : 'string';
        stored = raw;
      } else {
        type = 'json';
        try {
          stored = JSON.stringify(raw, null, 2);
        } catch {
          stored = '';
        }
      }
      rows.push({ id: nextId++, key, type, value: stored });
    }
  }
  if (rows.length === 0) {
    rows.push(createTemplateRow(nextId++));
  }
  return [rows, nextId];
}

export function rowsToTemplateObject(rows: TemplateFieldRow[]): { result: Record<string, unknown> | null; error?: string } {
  const payload: Record<string, unknown> = {};
  for (const row of rows) {
    const key = row.key.trim();
    if (!key) {
      continue;
    }
    switch (row.type) {
      case 'string':
      case 'text':
        payload[key] = row.value;
        break;
      case 'number': {
        if (!row.value.trim()) {
          return { result: null, error: `Value for "${key}" must be a number.` };
        }
        const num = Number(row.value);
        if (Number.isNaN(num)) {
          return { result: null, error: `Value for "${key}" must be a number.` };
        }
        payload[key] = num;
        break;
      }
      case 'boolean':
        payload[key] = row.value === 'true';
        break;
      case 'json': {
        if (!row.value.trim()) {
          return { result: null, error: `Value for "${key}" must be valid JSON.` };
        }
        try {
          payload[key] = JSON.parse(row.value);
        } catch {
          return { result: null, error: `Value for "${key}" must be valid JSON.` };
        }
        break;
      }
      default:
        break;
    }
  }
  if (Object.keys(payload).length === 0) {
    return { result: null };
  }
  return { result: payload };
}
