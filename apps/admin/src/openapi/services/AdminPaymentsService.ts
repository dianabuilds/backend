/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RecentPayment } from '../models/RecentPayment';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminPaymentsService {
    /**
     * List recent payments
     * @param limit
     * @returns RecentPayment Successful Response
     * @throws ApiError
     */
    public static listRecentPaymentsAdminPaymentsRecentGet(
        limit: number = 20,
    ): CancelablePromise<Array<RecentPayment>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/payments/recent',
            query: {
                'limit': limit,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
}
