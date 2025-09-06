/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TransitionsService {
    /**
     * Delete transition
     * Delete a specific manual transition between nodes.
     * @param transitionId
     * @param accountId
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteTransitionTransitionsTransitionIdDelete(
        transitionId: string,
        accountId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/transitions/{transition_id}',
            path: {
                'transition_id': transitionId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
