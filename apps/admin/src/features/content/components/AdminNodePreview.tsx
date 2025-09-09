import React, { useState } from 'react';

import { sanitizeHtml } from '../../../utils/sanitizeHtml';

// -----------------------------
// Types
// -----------------------------
export type Block = {
  id: string;
  type: 'header' | 'paragraph' | 'image' | 'quote' | string;
  data?: unknown;
};

export type Doc = {
  title: string;
  cover?: string;
  tags?: string[];
  author?: {
    name?: string;
    handle?: string;
    avatar?: string;
    date?: string;
  };
  reactions?: {
    like?: number;
    comment?: number;
    bookmark?: number;
    share?: number;
  };
  navActions?: { id: string; label: string; href: string }[];
  blocks: Block[];
};

// -----------------------------
// Renderer
// -----------------------------
function RenderBlocks({ blocks, invert }: { blocks: Block[]; invert?: boolean }) {
  const proseClass = invert ? 'prose prose-invert max-w-none' : 'prose max-w-none';
  return (
    <div className={proseClass}>
      {blocks.map((b) => {
        if (b.type === 'header') {
          const d = (b.data as { level?: number; text?: unknown }) || {};
          const level = Math.min(Math.max(Number(d.level ?? 2), 1), 6) as 1 | 2 | 3 | 4 | 5 | 6;
          const text = String(d.text ?? '');
          const H = `h${level}` as unknown as keyof JSX.IntrinsicElements;
          return <H key={b.id}>{text}</H>;
        }
        if (b.type === 'paragraph') {
          return (
            <p
              key={b.id}
              dangerouslySetInnerHTML={{
                __html: sanitizeHtml(
                  String((b.data as { text?: unknown } | undefined)?.text ?? ''),
                ),
              }}
            />
          );
        }
        if (b.type === 'image') {
          const d = (b.data as { file?: { url?: string }; caption?: string } | undefined) || {};
          return (
            <figure key={b.id} className="my-6">
              <img src={d.file?.url} alt={d.caption || 'image'} className="rounded-xl w-full" />
              {d.caption && (
                <figcaption className="text-sm opacity-70 mt-2">{d.caption}</figcaption>
              )}
            </figure>
          );
        }
        if (b.type === 'quote') {
          const d = (b.data as { text?: unknown; caption?: string } | undefined) || {};
          return (
            <blockquote key={b.id}>
              <p
                dangerouslySetInnerHTML={{
                  __html: sanitizeHtml(String(d.text ?? '')),
                }}
              />
              {d.caption && <cite className="block text-sm opacity-70">{d.caption}</cite>}
            </blockquote>
          );
        }
        return (
          <pre key={b.id} className="bg-black/30 p-3 rounded">
            Unsupported block: {b.type}
          </pre>
        );
      })}
    </div>
  );
}

// -----------------------------
// Main Component
// -----------------------------
export default function AdminNodePreview({ doc }: { doc: Doc }) {
  const [vp, setVp] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const widths: Record<typeof vp, number> = { desktop: 1200, tablet: 900, mobile: 480 } as const;

  return (
    <div className={theme === 'dark' ? 'bg-[#0b0f1a] text-white' : 'bg-white text-gray-900'}>
      {/* Toolbar */}
      <div className="sticky top-0 z-20 border-b backdrop-blur bg-black/10">
        <div className="max-w-7xl mx-auto px-4 py-2 flex items-center gap-2">
          <span className="text-sm opacity-80">Preview</span>
          <div className="ml-auto flex items-center gap-2">
            <div className="inline-flex rounded-lg overflow-hidden border">
              {['desktop', 'tablet', 'mobile'].map((k) => (
                <button
                  key={k}
                  onClick={() => setVp(k as 'desktop' | 'tablet' | 'mobile')}
                  className={`px-3 py-1 text-sm ${vp === k ? 'bg-white/20' : 'bg-transparent'}`}
                >
                  {k}
                </button>
              ))}
            </div>
            <button
              onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
              className="px-3 py-1 text-sm rounded border"
            >
              {theme === 'dark' ? 'Light' : 'Dark'}
            </button>
          </div>
        </div>
      </div>

      {/* Device frame */}
      <div className="w-full flex justify-center py-8">
        <div
          className="rounded-3xl shadow-2xl border overflow-hidden"
          style={{ width: widths[vp] }}
        >
          {/* Page shell matching site theme */}
          <div
            className={
              theme === 'dark'
                ? 'bg-gradient-to-b from-[#0b0f1a] to-[#0f1726]'
                : 'bg-gradient-to-b from-white to-gray-50'
            }
          >
            {/* Cover */}
            {doc.cover && (
              <div className="h-72 w-full overflow-hidden relative">
                <img src={doc.cover} alt="cover" className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-black/40" />
                <div className="absolute bottom-6 left-8 text-white pr-8">
                  <h1 className="text-4xl font-extrabold drop-shadow-lg">{doc.title}</h1>
                  {!!doc.tags?.length && (
                    <div className="flex gap-2 mt-2">
                      {doc.tags.map((t) => (
                        <span
                          key={t}
                          className="px-3 py-1 rounded-full text-xs bg-black/60 text-white"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Author + reactions */}
            <div className="max-w-4xl mx-auto px-8 pt-6 pb-4 flex items-center gap-4">
              {doc.author?.avatar && (
                <img
                  src={doc.author.avatar}
                  alt="avatar"
                  className="w-10 h-10 rounded-full object-cover"
                />
              )}
              <div className="min-w-0">
                <div className="font-semibold truncate">
                  {doc.author?.name}{' '}
                  <span className="opacity-60 font-normal">{doc.author?.handle}</span>
                </div>
                <div className="text-xs opacity-60">{doc.author?.date}</div>
              </div>
              <div className="ml-auto flex items-center gap-4 text-sm opacity-90">
                <span className="inline-flex items-center gap-1">
                  <span>❤️</span>
                  {doc.reactions?.like ?? 0}
                </span>
                <span className="inline-flex items-center gap-1">
                  <span>💬</span>
                  {doc.reactions?.comment ?? 0}
                </span>
                <span className="inline-flex items-center gap-1">
                  <span>🔖</span>
                  {doc.reactions?.bookmark ?? 0}
                </span>
                <span className="inline-flex items-center gap-1">
                  <span>↗️</span>
                  {doc.reactions?.share ?? 0}
                </span>
              </div>
            </div>

            {/* Article body */}
            <div className="max-w-4xl mx-auto px-8 py-8">
              <RenderBlocks blocks={doc.blocks || []} invert={theme === 'dark'} />
            </div>

            {/* Bottom navigation */}
            {doc.navActions?.length ? (
              <div className="max-w-4xl mx-auto px-8 pb-10">
                <div className="border-t border-white/10 pt-6 overflow-x-auto">
                  <div className="min-w-max flex gap-3">
                    {doc.navActions.slice(0, 4).map((a) => (
                      <a
                        key={a.id}
                        href={a.href}
                        className="flex-1 whitespace-nowrap px-4 py-2 rounded-xl border bg-white/5 hover:bg-white/10 transition text-sm text-center"
                      >
                        {a.label}
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
          {/* END Page shell */}
        </div>
        {/* END device frame */}
      </div>
    </div>
  );
}
