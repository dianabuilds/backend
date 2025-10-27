import type { SiteGlobalBlock } from '@shared/types/management';
import type { HomeDraftData } from '../../home/types';

type UnknownRecord = Record<string, unknown>;

export type GlobalBlockAssignment = {
  key: string;
  section: string;
};

const KEY_FIELDS = [
  'reference',
  'ref',
  'key',
  'block_key',
  'blockKey',
  'globalKey',
  'global_block_key',
  'globalBlockKey',
] as const;

function isPlainObject(value: unknown): value is UnknownRecord {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function normalizeSection(section: unknown, fallback?: string): string {
  if (typeof section === 'string' && section.trim()) {
    return section.trim();
  }
  if (fallback && fallback.trim()) {
    return fallback.trim();
  }
  return 'global';
}

function extractKey(source: UnknownRecord, allowId = false): string | null {
  for (const field of KEY_FIELDS) {
    const candidate = source[field];
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim();
    }
  }
  if (allowId) {
    const candidate = source.id;
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim();
    }
  }
  return null;
}

function collectAssignmentsFromValue(
  value: unknown,
  fallbackSection?: string,
): GlobalBlockAssignment[] {
  if (!value) {
    return [];
  }

  if (Array.isArray(value)) {
    return value.flatMap((entry) => collectAssignmentsFromValue(entry, fallbackSection));
  }

  if (typeof value === 'string') {
    const key = value.trim();
    return key ? [{ key, section: normalizeSection(null, fallbackSection) }] : [];
  }

  if (!isPlainObject(value)) {
    return [];
  }

  const key = extractKey(value, true);
  if (key) {
    const section = normalizeSection(value.section, fallbackSection);
    return [{ key, section }];
  }

  const entries: GlobalBlockAssignment[] = [];
  for (const [sectionName, entry] of Object.entries(value)) {
    entries.push(
      ...collectAssignmentsFromValue(entry, normalizeSection(null, sectionName)),
    );
  }
  return entries;
}

export function extractGlobalBlockAssignments(
  meta: HomeDraftData['meta'],
): Record<string, GlobalBlockAssignment> {
  if (!isPlainObject(meta)) {
    return {};
  }
  const assignments: Record<string, GlobalBlockAssignment> = {};

  const addAssignment = (entry: GlobalBlockAssignment) => {
    assignments[entry.section] = entry;
  };

  const candidateFields: Array<{ value: unknown; fallback?: string }> = [
    { value: (meta as UnknownRecord).globalBlocks },
    { value: (meta as UnknownRecord).global_blocks },
    { value: (meta as UnknownRecord).header, fallback: 'header' },
    { value: (meta as UnknownRecord).footer, fallback: 'footer' },
  ];

  for (const { value, fallback } of candidateFields) {
    if (value === undefined) {
      continue;
    }
    const entries = collectAssignmentsFromValue(value, fallback);
    entries.forEach(addAssignment);
  }

  return assignments;
}

function isPlainGlobalBlockEntry(value: unknown): boolean {
  if (!isPlainObject(value)) {
    return false;
  }
  if (value.type && value.type !== 'global_block') {
    return false;
  }
  return extractKey(value, true) != null;
}

function buildGlobalBlockEntry(section: string, key: string): UnknownRecord {
  return {
    type: 'global_block',
    reference: key,
    ref: key,
    key,
    section,
  };
}

export function applyGlobalBlockAssignments(
  meta: HomeDraftData['meta'],
  assignments: Record<string, GlobalBlockAssignment>,
): HomeDraftData['meta'] {
  const nextMeta: UnknownRecord = isPlainObject(meta) ? { ...meta } : {};

  const entries = Object.values(assignments);
  if (entries.length > 0) {
    nextMeta.globalBlocks = entries
      .slice()
      .sort((a, b) => a.section.localeCompare(b.section))
      .map((entry) => buildGlobalBlockEntry(entry.section, entry.key));
  } else {
    delete nextMeta.globalBlocks;
    delete nextMeta.global_blocks;
  }

  (['header', 'footer'] as const).forEach((sectionName) => {
    const assignment = assignments[sectionName];
    if (assignment) {
      nextMeta[sectionName] = buildGlobalBlockEntry(sectionName, assignment.key);
    } else if (isPlainGlobalBlockEntry(nextMeta[sectionName])) {
      delete nextMeta[sectionName];
    }
  });

  return Object.keys(nextMeta).length > 0 ? nextMeta : null;
}

export function findGlobalBlockOption(
  candidates: SiteGlobalBlock[],
  key: string | null | undefined,
): SiteGlobalBlock | null {
  if (!key) {
    return null;
  }
  return candidates.find((item) => item.key === key) ?? null;
}
