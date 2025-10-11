import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePrefetchLink } from './usePrefetchLink';
import { __resetPrefetchStateForTests } from '../utils/prefetch';

type ConnectionMock = {
  saveData?: boolean;
  effectiveType?: string;
};

const originalVisibilityDescriptor = Object.getOwnPropertyDescriptor(document, 'visibilityState');
const originalConnectionDescriptor = Object.getOwnPropertyDescriptor(window.navigator, 'connection');
const originalUserAgentDescriptor = Object.getOwnPropertyDescriptor(window.navigator, 'userAgent');
const originalRequestIdleDescriptor = Object.getOwnPropertyDescriptor(window, 'requestIdleCallback');

function restoreEnvironment(): void {
  if (originalVisibilityDescriptor) {
    Object.defineProperty(document, 'visibilityState', originalVisibilityDescriptor);
  } else {
    delete (document as unknown as Record<string, unknown>).visibilityState;
  }
  if (originalConnectionDescriptor) {
    Object.defineProperty(window.navigator, 'connection', originalConnectionDescriptor);
  } else {
    delete (window.navigator as unknown as Record<string, unknown>).connection;
  }
  if (originalUserAgentDescriptor) {
    Object.defineProperty(window.navigator, 'userAgent', originalUserAgentDescriptor);
  }
  if (originalRequestIdleDescriptor) {
    Object.defineProperty(window, 'requestIdleCallback', originalRequestIdleDescriptor);
  } else if ('requestIdleCallback' in window) {
    delete (window as Record<string, unknown>).requestIdleCallback;
  }
}

function mockVisibilityState(value: Document['visibilityState']): void {
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    value,
  });
}

function mockConnection(value: ConnectionMock | undefined): void {
  if (value === undefined) {
    Object.defineProperty(window.navigator, 'connection', {
      configurable: true,
      value: undefined,
    });
    return;
  }
  Object.defineProperty(window.navigator, 'connection', {
    configurable: true,
    value,
  });
}

function mockUserAgent(value: string): void {
  Object.defineProperty(window.navigator, 'userAgent', {
    configurable: true,
    value,
  });
}

function mockRequestIdleCallback(value: typeof window.requestIdleCallback | undefined): void {
  Object.defineProperty(window, 'requestIdleCallback', {
    configurable: true,
    value,
  });
}

describe('usePrefetchLink', () => {
  beforeEach(() => {
    restoreEnvironment();
    vi.useFakeTimers();
    __resetPrefetchStateForTests();
    document.head.innerHTML = '';
    mockVisibilityState('visible');
    mockUserAgent('Mozilla/5.0 (Test)');
    mockConnection(undefined);
    mockRequestIdleCallback(undefined);
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
    document.head.innerHTML = '';
    __resetPrefetchStateForTests();
    restoreEnvironment();
  });

  it('не запускает prefetch при saveData=true', () => {
    mockConnection({ saveData: true });

    const { result } = renderHook(() => usePrefetchLink('/dev-blog'));

    act(() => {
      result.current.onPointerEnter({} as any);
    });
    vi.runOnlyPendingTimers();

    expect(document.head.querySelectorAll('link[rel="prefetch"]').length).toBe(0);
  });

  it('не запускает prefetch при effectiveType=2g', () => {
    mockConnection({ effectiveType: '2g' });

    const { result } = renderHook(() => usePrefetchLink('/dev-blog'));

    act(() => {
      result.current.onFocus({} as any);
    });
    vi.runAllTimers();

    expect(document.head.querySelectorAll('link[rel="prefetch"]').length).toBe(0);
  });

  it('добавляет prefetch ссылку для нормального соединения', () => {
    mockConnection({ saveData: false, effectiveType: '4g' });

    const { result } = renderHook(() => usePrefetchLink('/dev-blog'));

    act(() => {
      result.current.onPointerEnter({} as any);
    });
    vi.advanceTimersByTime(250);

    const links = Array.from(document.head.querySelectorAll('link[rel="prefetch"]'))
      .map((node) => node.getAttribute('href'));
    const expectedHref = new URL('/dev-blog', window.location.href).toString();
    expect(links).toContain(expectedHref);
  });

  it('отключает prefetch для /v1/public/home при lighthouse UA', () => {
    mockUserAgent('Mozilla/5.0 Chrome-Lighthouse');
    mockConnection({ saveData: false, effectiveType: '4g' });

    const { result } = renderHook(() => usePrefetchLink('/v1/public/home'));

    act(() => {
      result.current.onPointerEnter({} as any);
    });
    vi.runOnlyPendingTimers();

    expect(document.head.querySelectorAll('link[rel="prefetch"]').length).toBe(0);
  });
});
