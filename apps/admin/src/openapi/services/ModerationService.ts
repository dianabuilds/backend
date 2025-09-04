/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CaseCreate } from '../models/CaseCreate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ModerationService {
    /**
     * Create Moderation Case
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createCaseModerationCasesPost(
        requestBody: CaseCreate,
    ): CancelablePromise<{
        id?: string;
    }> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/moderation/cases',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
