import Ajv, { type ErrorObject } from 'ajv';
import homeConfigSchema from '../../../shared/schemas/home_config.schema';
import type { HomeBlock, HomeDraftData } from './types';

export type FieldError = {
  path: string;
  message: string;
  keyword: string;
};

export type ValidationSummary = {
  valid: boolean;
  general: FieldError[];
  blocks: Record<string, FieldError[]>;
};

const ajv = new Ajv({
  allErrors: true,
  strict: false,
  allowUnionTypes: true,
});

const validateSchema = ajv.compile(homeConfigSchema as any);

function normalizeBlock(block: HomeBlock): Record<string, unknown> {
  const normalized: Record<string, unknown> = {
    id: block.id,
    type: block.type,
    enabled: block.enabled,
  };
  if (block.title !== undefined) {
    normalized.title = block.title;
  }
  if (block.slots !== undefined) {
    normalized.slots = block.slots ?? null;
  }
  if (block.layout !== undefined) {
    normalized.layout = block.layout ?? null;
  }
  if (block.dataSource !== undefined && block.dataSource !== null) {
    normalized.dataSource = block.dataSource;
  }
  return normalized;
}

function formatError(error: ErrorObject): FieldError {
  const baseMessage = (() => {
    switch (error.keyword) {
      case 'required': {
        const missing = (error.params as any)?.missingProperty;
        return missing ? `Поле "${missing}" обязательно` : 'Обязательное поле';
      }
      case 'minLength':
      case 'maxLength': {
        const limit = (error.params as any)?.limit;
        const suffix = error.keyword === 'minLength' ? 'Минимальная' : 'Максимальная';
        return typeof limit === 'number' ? `${suffix} длина — ${limit}` : 'Недопустимая длина';
      }
      case 'enum': {
        const allowed = (error.params as any)?.allowedValues;
        return Array.isArray(allowed) ? `Допустимые значения: ${allowed.join(', ')}` : 'Недопустимое значение';
      }
      case 'type': {
        const type = (error.params as any)?.type;
        return typeof type === 'string' ? `Ожидается тип ${type}` : 'Некорректный тип значения';
      }
      case 'minimum':
      case 'maximum': {
        const limit = (error.params as any)?.limit;
        const prefix = error.keyword === 'minimum' ? 'Минимальное' : 'Максимальное';
        return typeof limit === 'number' ? `${prefix} значение — ${limit}` : 'Некорректное значение';
      }
      case 'maxItems':
      case 'minItems': {
        const limit = (error.params as any)?.limit;
        const prefix = error.keyword === 'minItems' ? 'Минимальное' : 'Максимальное';
        return typeof limit === 'number' ? `${prefix} количество элементов — ${limit}` : 'Недопустимое количество элементов';
      }
      default:
        return error.message ?? 'Недопустимое значение';
    }
  })();

  return {
    path: error.instancePath || '',
    message: baseMessage,
    keyword: error.keyword,
  };
}

function appendError(map: Record<string, FieldError[]>, key: string, error: FieldError) {
  if (!map[key]) {
    map[key] = [];
  }
  map[key].push(error);
}

function findDuplicateIds(blocks: HomeBlock[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const block of blocks) {
    counts.set(block.id, (counts.get(block.id) ?? 0) + 1);
  }
  const duplicates = new Map<string, number>();
  for (const [id, count] of counts) {
    if (count > 1) {
      duplicates.set(id, count);
    }
  }
  return duplicates;
}

export function validateHomeDraft(data: HomeDraftData): ValidationSummary {
  const payload: Record<string, unknown> = {
    blocks: data.blocks.map(normalizeBlock),
  };
  if (data.meta && Object.keys(data.meta).length > 0) {
    payload.meta = data.meta;
  }

  const generalErrors: FieldError[] = [];
  const blockErrors: Record<string, FieldError[]> = {};

  const duplicates = findDuplicateIds(data.blocks);
  if (duplicates.size > 0) {
    for (const [duplicateId] of duplicates) {
      appendError(blockErrors, duplicateId, {
        keyword: 'duplicate',
        path: '/id',
        message: 'Идентификатор блока должен быть уникальным',
      });
    }
    generalErrors.push({
      keyword: 'duplicate',
      path: '/blocks',
      message: 'Идентификаторы блоков должны быть уникальными',
    });
  }

  const valid = validateSchema(payload);
  if (!valid && Array.isArray(validateSchema.errors)) {
    for (const error of validateSchema.errors) {
      const formatted = formatError(error);
      const segments = (error.instancePath || '').split('/').filter(Boolean);
      if (segments[0] === 'blocks') {
        const indexSegment = segments[1];
        const index = Number.parseInt(indexSegment || '', 10);
        const block = Number.isFinite(index) ? data.blocks[index] : undefined;
        const blockId = block?.id;
        const fieldPath = segments.slice(2).join('/') || '/';
        const scopedError: FieldError = {
          ...formatted,
          path: `/${fieldPath}`,
        };
        if (blockId) {
          appendError(blockErrors, blockId, scopedError);
        } else {
          generalErrors.push(scopedError);
        }
      } else {
        generalErrors.push(formatted);
      }
    }
  }

  const hasBlockErrors = Object.values(blockErrors).some((errors) => errors.length > 0);
  const summary: ValidationSummary = {
    valid: generalErrors.length === 0 && !hasBlockErrors,
    general: generalErrors,
    blocks: blockErrors,
  };

  return summary;
}