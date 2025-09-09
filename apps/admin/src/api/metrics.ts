import { api } from './client';

export interface ReliabilityMetrics {
    rps: number;
    p95: number;
    errors_4xx: number;
    errors_5xx: number;
    no_route_percent: number;
    fallback_percent: number;
}

export async function getReliabilityMetrics(account?: string): Promise<ReliabilityMetrics> {
    const params = new URLSearchParams();
    if (account) params.append('account', account);
    const qs = params.toString();
    const res = await api.get<ReliabilityMetrics>(`/admin/metrics/reliability${qs ? `?${qs}` : ''}`);
    return (
        res.data || {
            rps: 0,
            p95: 0,
            errors_4xx: 0,
            errors_5xx: 0,
            no_route_percent: 0,
            fallback_percent: 0,
        }
    );
}
