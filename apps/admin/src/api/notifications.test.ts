import { afterEach, describe, expect, it, vi } from 'vitest';

import { api } from './client';
import { getDraftCampaign, sendDraftCampaign, updateDraftCampaign } from './notifications';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('notifications draft campaign api', () => {
  it('retrieves draft campaign', async () => {
    vi.spyOn(api, 'get').mockResolvedValue({ data: {} } as unknown);
    await getDraftCampaign('c1');
    expect(api.get).toHaveBeenCalledWith('/admin/notifications/campaigns/c1');
  });

  it('updates draft campaign', async () => {
    vi.spyOn(api, 'patch').mockResolvedValue({} as unknown);
    await updateDraftCampaign('c1', { title: 't', message: 'm' });
    expect(api.patch).toHaveBeenCalledWith('/admin/notifications/campaigns/c1', {
      title: 't',
      message: 'm',
    });
  });

  it('sends draft campaign', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({} as unknown);
    await sendDraftCampaign('c1');
    expect(api.post).toHaveBeenCalledWith('/admin/notifications/campaigns/c1/start', {});
  });
});
