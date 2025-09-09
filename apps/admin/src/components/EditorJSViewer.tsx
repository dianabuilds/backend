// @ts-nocheck
/**
 * @deprecated Runtime usage removed. Kept for tests and manual previews.
 */
import type { OutputData } from '../types/editorjs';
import { resolveUrl } from '../utils/resolveUrl';
import { sanitizeHtml } from '../utils/sanitizeHtml';

interface Block {
  id?: string;
  type: string;
  data: Record<string, unknown>;
}

type EditorData = Omit<OutputData, 'blocks'> & { blocks?: Block[] };

interface Props {
  value?: EditorData | null;
  className?: string;
}

/**
 * Render-only viewer for Editor.js data.
 * Supports: paragraph, header, list, checklist, quote, image, table, delimiter.
 */
export default function EditorJSViewer({ value, className }: Props) {
  const data: EditorData = value && typeof value === 'object' ? value : { blocks: [] };
  const blocks = Array.isArray(data.blocks) ? data.blocks : [];

  const renderHTML = (html?: string) => (
    <span dangerouslySetInnerHTML={{ __html: sanitizeHtml(html || '') }} />
  );

  const renderBlock = (block: Block, idx: number) => {
    const type = block.type;
    const d = block.data as Record<string, unknown>;

    switch (type) {
      case 'paragraph':
        return (
          <p key={block.id || idx} className="leading-6">
            {renderHTML(d.text as string | undefined)}
          </p>
        );
      case 'header': {
        const level = Math.min(Math.max(parseInt(String(d.level ?? 2), 10) || 2, 1), 6);
        const Tag = `h${level}` as keyof JSX.IntrinsicElements;
        const levelCls =
          level === 1
            ? 'text-3xl font-bold'
            : level === 2
              ? 'text-2xl font-bold'
              : level === 3
                ? 'text-xl font-semibold'
                : level === 4
                  ? 'text-lg font-semibold'
                  : 'text-base font-semibold';
        return (
          <Tag key={block.id || idx} className={`${levelCls}`}>
            {renderHTML(d.text as string | undefined)}
          </Tag>
        );
      }
      case 'list': {
        const ordered = String(d.style || '').toLowerCase() === 'ordered';
        const items = Array.isArray(d.items) ? (d.items as unknown[]) : [];
        const ListTag = (ordered ? 'ol' : 'ul') as 'ul' | 'ol';
        const listCls = ordered ? 'list-decimal pl-5 space-y-1' : 'list-disc pl-5 space-y-1';
        return (
          <ListTag key={block.id || idx} className={listCls}>
            {items.map((it, i) => (
              <li key={i}>
                {renderHTML(
                  typeof it === 'string'
                    ? it
                    : ((it as Record<string, unknown>).content as string) ||
                        ((it as Record<string, unknown>).text as string) ||
                        '',
                )}
              </li>
            ))}
          </ListTag>
        );
      }
      case 'checklist': {
        const items = Array.isArray(d.items) ? (d.items as unknown[]) : [];
        return (
          <ul key={block.id || idx} className="pl-1 space-y-1">
            {items.map((it, i) => (
              <li key={i} className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={Boolean((it as Record<string, unknown>).checked)}
                  readOnly
                  className="mt-1"
                />
                <span>
                  {renderHTML((it as Record<string, unknown>).text as string | undefined)}
                </span>
              </li>
            ))}
          </ul>
        );
      }
      case 'quote':
        return (
          <figure key={block.id || idx} className="my-2">
            <blockquote className="border-l-4 pl-4 italic opacity-90">
              {renderHTML(d.text as string | undefined)}
            </blockquote>
            {d.caption ? (
              <figcaption className="text-sm opacity-70 mt-1">
                — {renderHTML(d.caption as string | undefined)}
              </figcaption>
            ) : null}
          </figure>
        );
      case 'image': {
        const url = resolveUrl(
          ((d.file as Record<string, unknown> | undefined)?.url as string | undefined) ||
            (d.url as string | undefined),
        );
        const caption = d.caption as string | undefined;
        return (
          <figure key={block.id || idx} className="my-3">
            {url ? <img src={url} alt={caption || ''} className="max-w-full rounded" /> : null}
            {caption ? (
              <figcaption className="text-sm text-center opacity-70 mt-1">
                {renderHTML(caption)}
              </figcaption>
            ) : null}
          </figure>
        );
      }
      case 'table': {
        const content = Array.isArray(d.content) ? (d.content as unknown[][]) : [];
        return (
          <div key={block.id || idx} className="overflow-auto">
            <table className="min-w-full border border-gray-200 dark:border-gray-700 text-sm">
              <tbody>
                {content.map((row, r) => (
                  <tr key={r} className="border-b border-gray-200 dark:border-gray-700">
                    {row.map((cell, c) => (
                      <td
                        key={c}
                        className="px-2 py-1 align-top border-r border-gray-200 dark:border-gray-700"
                      >
                        {renderHTML(
                          typeof cell === 'string'
                            ? cell
                            : ((cell as Record<string, unknown>).text as string) || '',
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
      case 'delimiter':
        return <hr key={block.id || idx} className="my-6 opacity-60" />;
      default:
        // Fallback: показать как есть
        return (
          <pre
            key={block.id || idx}
            className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto"
          >
            {JSON.stringify(block, null, 2)}
          </pre>
        );
    }
  };

  return <article className={`space-y-3 ${className || ''}`}>{blocks.map(renderBlock)}</article>;
}
