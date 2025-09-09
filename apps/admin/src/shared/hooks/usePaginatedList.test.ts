import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { usePaginatedList } from './usePaginatedList';

describe('usePaginatedList', () => {
  it('does not auto-reload when loader identity changes', async () => {
    const loader = vi.fn().mockResolvedValue([]);
    const { rerender, result } = renderHook(
      ({ q }: { q: string }) => usePaginatedList(({ limit, offset }) => loader(q, limit, offset)),
      { initialProps: { q: '' } },
    );

    await waitFor(() => expect(loader).toHaveBeenCalledTimes(1));

    rerender({ q: 'foo' });
    await waitFor(() => expect(loader).toHaveBeenCalledTimes(1));

    await act(async () => {
      await result.current.reload();
    });
    expect(loader).toHaveBeenCalledTimes(2);
  });
});
