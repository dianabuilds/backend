/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserAIPrefIn } from '../models/UserAIPrefIn';
import type { UserAIPrefOut } from '../models/UserAIPrefOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminAiUserPrefService {
    /**
     * Get User Pref
     * @returns UserAIPrefOut Successful Response
     * @throws ApiError
     */
    public static getUserPrefAdminAiUserPrefGet(): CancelablePromise<UserAIPrefOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/user-pref',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Put User Pref
     * @param requestBody
     * @returns UserAIPrefOut Successful Response
     * @throws ApiError
     */
    public static putUserPrefAdminAiUserPrefPut(
        requestBody: UserAIPrefIn,
    ): CancelablePromise<UserAIPrefOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/ai/user-pref',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
}
