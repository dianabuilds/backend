import React from 'react';
import { Link } from 'react-router-dom';
import { usePrefetchLink } from '@shared/hooks/usePrefetchLink';
import { Button } from '@ui';
import type { HomeBlockComponentProps } from './types';

type HeroSlots = {
  headline?: string;
  subheadline?: string;
  cta?: { label?: string; href?: string } | null;
  media?: string | null;
};

function isHeroSlots(slots: Record<string, unknown> | null | undefined): slots is HeroSlots {
  return Boolean(slots && typeof slots === 'object');
}

export default function HeroBlock({ block, position }: HomeBlockComponentProps): React.ReactElement {
  const slots = isHeroSlots(block.slots) ? (block.slots as HeroSlots) : {};
  const headline = typeof slots.headline === 'string' && slots.headline.trim().length ? slots.headline : block.title ?? 'Hero';
  const subheadline = typeof slots.subheadline === 'string' ? slots.subheadline : null;
  const media = typeof slots.media === 'string' ? slots.media : null;
  const cta = slots.cta && typeof slots.cta === 'object' ? slots.cta : null;
  const ctaHref = typeof cta?.href === 'string' ? cta.href : null;
  const ctaPrefetch = usePrefetchLink(ctaHref);
  const isPrimaryHero = position === 1;
  const imageLoading: 'eager' | 'lazy' = isPrimaryHero ? 'eager' : 'lazy';
  const imageFetchPriority = isPrimaryHero ? ({ fetchpriority: 'high' as const }) : null;
  const imageSizes = isPrimaryHero ? '(min-width: 1024px) 36rem, 100vw' : undefined;

  return (
    <section className="rounded-3xl border border-gray-200 bg-white p-8 dark:border-dark-600 dark:bg-dark-800 lg:p-10">
      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="flex-1 space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-indigo-600 dark:text-indigo-300">{block.type}</p>
          <h1 className="text-4xl font-semibold text-gray-900 dark:text-white">{headline}</h1>
          {subheadline && <p className="max-w-xl text-base text-gray-600 dark:text-dark-100">{subheadline}</p>}
          {cta && typeof cta?.label === 'string' && ctaHref && (
            <Button as={Link} to={ctaHref} color="primary" variant="filled" {...ctaPrefetch}>
              {cta.label}
            </Button>
          )}
        </div>
        {media && (
          <div className="flex-1">
            <div className="aspect-[4/3] overflow-hidden rounded-2xl border border-gray-200 bg-gray-100 dark:border-dark-600 dark:bg-dark-700">
              <img
                src={media}
                alt={headline}
                loading={imageLoading}
                decoding="async"
                {...(imageFetchPriority ?? {})}
                className="h-full w-full object-cover"
                sizes={imageSizes}
              />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
