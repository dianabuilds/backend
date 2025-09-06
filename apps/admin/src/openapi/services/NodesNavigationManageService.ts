/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTransitionCreate } from '../models/NodeTransitionCreate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class NodesNavigationManageService {
    /**
     * Record visit
     * @param slug
     * @param toSlug
     * @param accountId
     * @param source
     * @param channel
     * @param xAccountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static recordVisitNodesSlugVisitToSlugPost(
        slug: string,
        toSlug: string,
        accountId: string,
        source?: (string | null),
        channel?: (string | null),
        xAccountId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes/{slug}/visit/{to_slug}',
            path: {
                'slug': slug,
                'to_slug': toSlug,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
                'source': source,
                'channel': channel,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create transition
     * @param slug
     * @param accountId
     * @param requestBody
     * @param xAccountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createTransitionNodesSlugTransitionsPost(
        slug: string,
        accountId: string,
        requestBody: NodeTransitionCreate,
        xAccountId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes/{slug}/transitions',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
