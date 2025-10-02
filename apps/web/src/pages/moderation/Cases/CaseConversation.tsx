import React from 'react';
import { Avatar, Badge } from '../../../shared/ui';
import { formatDateTime } from '../../../shared/utils/format';
import { CaseNote } from './types';

type Props = {
  notes?: CaseNote[] | null;
  variant: 'internal' | 'external';
  subjectId?: string | null;
  subjectLabel?: string | null;
};

const IMAGE_EXTENSIONS = /\.(png|jpe?g|gif|webp|bmp|svg)$/i;

function normalize(value?: string | null): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
}

function pickDirection(note: CaseNote, subjectId?: string | null): string | null {
  const candidates: Array<string | null | undefined> = [
    note.direction,
    note.meta?.direction,
    (note.meta as any)?.audience,
    (note.meta as any)?.role,
    (note.meta as any)?.actor_type,
    (note.meta as any)?.origin,
  ];
  for (const candidate of candidates) {
    if (!candidate) continue;
    const normalized = String(candidate).toLowerCase();
    if (['inbound', 'outbound', 'customer', 'user', 'agent', 'staff'].includes(normalized)) {
      return normalized;
    }
  }
  if (subjectId && note.author_id && note.author_id === subjectId) {
    return 'inbound';
  }
  return null;
}

function humanize(value?: string | null): string | null {
  const normalized = normalize(value);
  if (!normalized) return null;
  return normalized
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function resolveDisplayName(note: CaseNote, isCustomer: boolean, subjectLabel?: string | null) {
  const meta = (note.meta || {}) as Record<string, unknown>;
  const candidates: Array<string | null | undefined> = [
    note.author_name,
    (meta as any)?.author_name,
    (meta as any)?.author_username,
    (meta as any)?.username,
    (meta as any)?.user_name,
    (meta as any)?.display_name,
    (meta as any)?.actor_name,
    (meta as any)?.created_by,
    isCustomer ? subjectLabel : null,
    note.author_id,
  ];
  for (const candidate of candidates) {
    const normalized = normalize(candidate);
    if (normalized) return normalized;
  }
  return isCustomer ? 'Customer' : 'Team';
}

function isImageAttachment(file: { type?: string; url?: string | null }): boolean {
  if (!file) return false;
  if (typeof file.type === 'string' && file.type.trim().length) {
    return file.type.toLowerCase().startsWith('image/');
  }
  if (typeof file.url === 'string') {
    return IMAGE_EXTENSIONS.test(file.url);
  }
  return false;
}

function renderAttachments(
  attachments: Array<{ id?: string; url?: string; name?: string; type?: string }>,
  alignEnd: boolean,
) {
  if (!attachments.length) return null;
  return (
    <div className={`flex flex-wrap gap-2 ${alignEnd ? 'justify-end text-right' : 'text-left'}`}>
      {attachments.map((file, index) => {
        const key = file.id || file.url || `${file.name || 'attachment'}-${index}`;
        const isImage = isImageAttachment(file);
        const label = file.name || `Attachment ${index + 1}`;
        const url = file.url;
        if (isImage && url) {
          return (
            <div
              key={key}
              className="max-w-[160px] overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-dark-600 dark:bg-dark-700/60"
            >
              <img src={url} alt={label} className="h-32 w-full object-cover" />
              <div className="truncate px-2 py-1 text-[11px] text-gray-500 dark:text-gray-300">{label}</div>
            </div>
          );
        }
        if (url) {
          return (
            <a
              key={key}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded-full border border-gray-200 px-3 py-1 text-xs text-primary-600 transition hover:border-primary-200 hover:bg-primary-50 dark:border-dark-600 dark:text-primary-200 dark:hover:border-primary-500/40 dark:hover:bg-primary-500/10"
            >
              {label}
            </a>
          );
        }
        return (
          <span
            key={key}
            className="inline-flex items-center rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-500 dark:border-dark-600 dark:text-gray-300"
          >
            {label}
          </span>
        );
      })}
    </div>
  );
}

export function CaseConversation({ notes, variant, subjectId, subjectLabel }: Props) {
  const filtered = React.useMemo(() => {
    if (!Array.isArray(notes)) return [];
    return notes
      .filter((note) => {
        const visibility = (normalize(note.visibility) || 'internal').toLowerCase();
        return variant === 'internal' ? visibility !== 'external' : visibility === 'external';
      })
      .sort((a, b) => {
        const at = a.created_at ? new Date(a.created_at).getTime() : 0;
        const bt = b.created_at ? new Date(b.created_at).getTime() : 0;
        return at - bt;
      });
  }, [notes, variant]);

  const isInternalView = variant === 'internal';
  const isExternalView = !isInternalView;

  if (!filtered.length) {
    return <div className="py-10 text-center text-sm text-gray-500">No messages</div>;
  }

  return (
    <ul className={isInternalView ? 'space-y-4 py-2' : 'space-y-6 py-4'}>
      {filtered.map((note, index) => {
        const direction = pickDirection(note, subjectId);
        const customerHint = direction ? ['inbound', 'customer', 'user'].includes(direction) : false;
        const isCustomer =
          isExternalView &&
          (customerHint || (!!subjectId && !!note.author_id && note.author_id === subjectId));
        const isTeam = !isCustomer;
        const displayName = resolveDisplayName(note, isCustomer, subjectLabel);
        const status =
          humanize((note.meta as any)?.delivery_status) ||
          humanize((note.meta as any)?.status) ||
          humanize(note.status);
        const attachments = Array.isArray(note.attachments) ? note.attachments.filter(Boolean) : [];
        const visibility = humanize(note.visibility);
        const key = note.id || `${note.created_at || 'note'}-${index}`;

        if (isInternalView) {
          return (
            <li
              key={key}
              className="rounded-2xl border border-gray-200 bg-white p-4 text-sm shadow-sm dark:border-dark-600 dark:bg-dark-700/60"
            >
              <div className="flex items-start gap-3">
                <Avatar size="sm" name={displayName} />
                <div className="flex-1 space-y-3">
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-gray-500 dark:text-gray-400">
                    <span className="font-medium text-gray-600 dark:text-gray-100">{displayName}</span>
                    <span>{formatDateTime(note.created_at)}</span>
                    {status && <Badge color="neutral" variant="soft">{status}</Badge>}
                    {note.pinned && <Badge color="warning">Pinned</Badge>}
                    {visibility && <Badge color="neutral" variant="soft">{visibility}</Badge>}
                  </div>
                  <div className="whitespace-pre-line leading-relaxed text-gray-800 dark:text-gray-100">
                    {note.text || <span className="italic text-gray-500 dark:text-gray-400">No content</span>}
                  </div>
                  {renderAttachments(attachments, false)}
                </div>
              </div>
            </li>
          );
        }

        const alignment = isTeam ? 'justify-end' : 'justify-start';
        const containerDirection = isTeam ? 'flex-row-reverse text-right' : '';
        const bubbleClass = isTeam
          ? 'border border-gray-200 bg-gray-100 text-gray-900 shadow-sm dark:border-dark-600 dark:bg-dark-700/80 dark:text-gray-100'
          : 'border border-gray-200 bg-white text-gray-900 shadow-sm dark:border-dark-600 dark:bg-dark-700/60 dark:text-gray-100';

        return (
          <li key={key} className={`flex ${alignment}`}>
            <div className={`flex w-full max-w-3xl items-start gap-3 ${containerDirection}`}>
              <Avatar
                size="sm"
                name={displayName}
                className={isTeam ? 'bg-gray-200 text-gray-700 dark:bg-dark-600 dark:text-gray-200' : ''}
              />
              <div className="w-full space-y-3">
                <div className={`flex flex-wrap items-center gap-2 text-[11px] text-gray-400 ${isTeam ? 'justify-end' : ''}`}>
                  <span className="font-medium text-gray-600 dark:text-gray-100">{displayName}</span>
                  <span>{formatDateTime(note.created_at)}</span>
                  {note.id && (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] uppercase tracking-wide text-gray-500 dark:bg-dark-600 dark:text-gray-300">
                      {String(note.id).slice(0, 8)}
                    </span>
                  )}
                  {status && <Badge color="neutral" variant="soft">{status}</Badge>}
                  {note.pinned && <Badge color="warning">Pinned</Badge>}
                  {isExternalView && (
                    <Badge color={isCustomer ? 'neutral' : 'primary'} variant="soft">
                      {isCustomer ? 'Customer' : 'Team'}
                    </Badge>
                  )}
                </div>
                <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${bubbleClass}`}>
                  {note.text || <span className="italic text-gray-500">No content</span>}
                </div>
                {renderAttachments(attachments, isTeam)}
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export default CaseConversation;
