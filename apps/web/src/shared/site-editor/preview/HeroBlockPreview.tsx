import React from 'react';
import clsx from 'clsx';
import { Button } from '@ui';
import type { HeroBlockConfig } from '../schemas/heroBlock';
import { getHeroLocaleContent } from '../schemas/heroBlock';

type HeroBlockPreviewProps = {
  config: HeroBlockConfig;
  locale: string;
  theme: 'light' | 'dark';
};

function formatHighlights(highlights: string[]): string[] {
  return highlights.filter((item) => Boolean(item && item.trim().length));
}

function hasCta(cta: { label: string; href: string } | null | undefined): cta is {
  label: string;
  href: string;
} {
  return Boolean(cta && cta.label.trim() && cta.href.trim());
}

export function HeroBlockPreview({ config, locale, theme }: HeroBlockPreviewProps): React.ReactElement {
  const content = getHeroLocaleContent(config, locale);
  const highlights = formatHighlights(content.highlights);
  const primaryCta = hasCta(content.primaryCta) ? content.primaryCta : null;
  const secondaryCta =
    content.secondaryCta && hasCta(content.secondaryCta) ? content.secondaryCta : null;
  const isDark = theme === 'dark';

  const containerClass = clsx(
    'rounded-3xl border p-6 shadow-sm transition-colors lg:p-8',
    isDark
      ? 'border-slate-700 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white'
      : 'border-gray-200 bg-gradient-to-br from-white via-slate-50 to-slate-100 text-gray-900',
  );

  const media = content.media?.url?.trim() ? content.media : null;

  return (
    <div className={containerClass}>
      <div
        className={clsx(
          'flex flex-col gap-8',
          config.layout.variant === 'split' ? 'lg:flex-row lg:items-center' : 'lg:flex-col',
        )}
      >
        <div
          className={clsx(
            'flex-1 space-y-4',
            config.layout.alignment === 'center' ? 'text-center lg:text-left' : 'text-left',
          )}
        >
          {content.tagline ? (
            <p
              className={clsx(
                'text-xs font-semibold uppercase tracking-[0.35em]',
                isDark ? 'text-amber-200' : 'text-indigo-600',
              )}
            >
              {content.tagline}
            </p>
          ) : null}
          <h3 className="text-3xl font-semibold leading-tight lg:text-4xl">{content.headline || 'Hero'}</h3>
          {content.subheadline ? (
            <p
              className={clsx(
                'text-base',
                isDark ? 'text-slate-200' : 'text-gray-600',
              )}
            >
              {content.subheadline}
            </p>
          ) : null}
          <div
            className={clsx(
              'flex flex-wrap gap-3',
              config.layout.alignment === 'center' ? 'justify-center lg:justify-start' : '',
            )}
          >
            {primaryCta ? (
              <Button as="span" color="primary" variant="filled" size="sm" className="pointer-events-none">
                {primaryCta.label || 'CTA'}
              </Button>
            ) : null}
            {secondaryCta ? (
              <Button
                as="span"
                color={secondaryCta.style === 'link' ? 'neutral' : 'primary'}
                variant={secondaryCta.style === 'link' ? 'ghost' : 'outlined'}
                size="sm"
                className="pointer-events-none"
              >
                {secondaryCta.label || 'Подробнее'}
              </Button>
            ) : null}
          </div>
          {highlights.length ? (
            <ul className="grid gap-3 text-sm text-gray-600 dark:text-slate-200 sm:grid-cols-2">
              {highlights.map((item, index) => (
                <li
                  key={`${item}-${index}`}
                  className="rounded-xl border border-white/30 bg-white/10 px-3 py-2 text-left text-sm dark:border-white/5 dark:bg-white/5"
                >
                  {item}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
        <div className="flex-1">
          <div className="overflow-hidden rounded-2xl border border-white/40 bg-white/10 dark:border-white/10">
            {media ? (
              <img
                src={media.url}
                alt={media.alt || content.headline || 'Hero media'}
                className="h-full w-full object-cover"
                loading="lazy"
              />
            ) : (
              <div className="flex h-60 items-center justify-center text-sm text-gray-400 dark:text-slate-500">
                Добавьте изображение
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default HeroBlockPreview;
