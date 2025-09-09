import { afterEach, describe, expect, it, vi } from 'vitest';

import { initPreviewTokenFromUrl } from './previewToken';

describe('initPreviewTokenFromUrl', () => {
  afterEach(() => {
    window.sessionStorage.clear();
    vi.restoreAllMocks();
    // Reset URL
    window.history.replaceState(null, 'test', '/admin/');
  });

  it('stores token from search param and cleans URL', () => {
    window.history.replaceState(null, 'test', '/admin/?token=abc.def.ghi&x=1');
    const save = vi.fn();
    initPreviewTokenFromUrl(save);
    expect(save).toHaveBeenCalledWith('abc.def.ghi');
    expect(window.location.search).toBe('?x=1');
  });

  it('stores token from hash param and cleans hash', () => {
    window.history.replaceState(null, 'test', '/admin/#token=zzz.yyy.xxx');
    const save = vi.fn();
    initPreviewTokenFromUrl(save);
    expect(save).toHaveBeenCalledWith('zzz.yyy.xxx');
    expect(window.location.hash).toBe('');
  });

  it('does nothing when no token provided', () => {
    window.history.replaceState(null, 'test', '/admin/?a=1#b=2');
    const save = vi.fn();
    initPreviewTokenFromUrl(save);
    expect(save).not.toHaveBeenCalled();
    expect(window.location.search).toBe('?a=1');
    expect(window.location.hash).toBe('#b=2');
  });
});
