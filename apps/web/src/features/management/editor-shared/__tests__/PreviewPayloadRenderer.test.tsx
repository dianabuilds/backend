import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { HomeResponse } from '@shared/types/homePublic';
import { PreviewPayloadRenderer } from '../PreviewPayloadRenderer';

const basePayload: HomeResponse = {
  slug: 'main',
  version: 1,
  updatedAt: '2025-10-27T12:00:00Z',
  publishedAt: '2025-10-20T08:00:00Z',
  generatedAt: '2025-10-27T12:05:00Z',
  blocks: [
    {
      id: 'hero-1',
      type: 'hero',
      title: 'Hero Title',
      enabled: true,
      slots: {
        headline: 'Hero Title',
        subheadline: 'Hero subtitle',
        cta: { label: 'Learn more', href: '/learn-more' },
      },
      layout: null,
      items: null,
      dataSource: null,
    },
  ],
  meta: {
    title: 'Preview',
    preview: { mode: 'site_preview' },
  },
  fallbacks: [],
};

describe('PreviewPayloadRenderer', () => {
  it('renders blocks and prevents navigation on links', () => {
    render(
      <MemoryRouter>
        <PreviewPayloadRenderer payload={basePayload} />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /Hero Title/i })).toBeInTheDocument();

    const link = screen.getByRole('link', { name: /Learn more/i });
    const event = new MouseEvent('click', { bubbles: true, cancelable: true });
    const dispatchResult = link.dispatchEvent(event);

    expect(dispatchResult).toBe(false);
    expect(event.defaultPrevented).toBe(true);
  });

  it('shows fallback entries when present', () => {
    const payloadWithFallback: HomeResponse = {
      ...basePayload,
      fallbacks: [{ id: 'hero-1', reason: 'mock_data' }],
    };

    render(
      <MemoryRouter>
        <PreviewPayloadRenderer payload={payloadWithFallback} />
      </MemoryRouter>,
    );

    expect(screen.getByText(/fallback блоки/i)).toBeInTheDocument();
    expect(screen.getByText(/mock_data/i)).toBeInTheDocument();
  });
});
