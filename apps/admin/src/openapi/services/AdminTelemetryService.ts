/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminTelemetryService {
    /**
     * List Rum Events
     * Админ: последние RUM-события (по убыванию времени).
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listRumEventsAdminTelemetryRumGet(
        event?: (string | null),
        url?: (string | null),
        offset?: number,
        limit: number = 200,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/telemetry/rum',
            query: {
                'event': event,
                'url': url,
                'offset': offset,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Rum Summary
     * Админ: сводка по последним событиям.
     * - counts по event
     * - средняя длительность login_attempt.dur_ms
     * - навигационные тайминги (средние по окну): ttfb, domContentLoaded, loadEvent
     * @param window
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rumSummaryAdminTelemetryRumSummaryGet(
        window: number = 500,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/telemetry/rum/summary',
            query: {
                'window': window,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
