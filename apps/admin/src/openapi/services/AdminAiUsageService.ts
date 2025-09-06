/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminAiUsageService {
    /**
     * System-wide usage totals
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getSystemUsageAdminAiUsageSystemGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/usage/system',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Usage by workspace
     * @param format
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getUsageByWorkspaceAdminAiUsageWorkspacesGet(
        format?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/usage/workspaces',
            query: {
                'format': format,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Usage by user in workspace
     * @param accountId
     * @param format
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getUsageByUserAdminAiUsageWorkspacesAccountIdUsersGet(
        accountId: string,
        format?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/usage/workspaces/{account_id}/users',
            path: {
                'account_id': accountId,
            },
            query: {
                'format': format,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Usage by model in workspace
     * @param accountId
     * @param format
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getUsageByModelAdminAiUsageWorkspacesAccountIdModelsGet(
        accountId: string,
        format?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/usage/workspaces/{account_id}/models',
            path: {
                'account_id': accountId,
            },
            query: {
                'format': format,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
}
