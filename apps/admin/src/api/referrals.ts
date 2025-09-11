import { api } from './client';

export async function getMyReferralCode(): Promise<{ code: string; active: boolean }> {
  const url = '/referrals/me/code';
  const res = await api.get<{ code: string; active: boolean }>(url);
  return res.data!;
}

export async function getMyReferralStats(): Promise<{ total_signups: number }> {
  const res = await api.get<{ total_signups: number }>('/referrals/me/stats');
  return res.data!;
}
