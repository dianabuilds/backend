/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class NavigationService {
    /**
     * Compass recommendations
     * @param nodeId
     * @param userId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static compassEndpointNavigationCompassGet(
        nodeId: string,
        userId?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/navigation/compass',
            query: {
                'node_id': nodeId,
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Navigate from node
     * @param slug
     * @returns any Successful Response
     * @throws ApiError
     */
    public static navigationNavigationSlugGet(
        slug: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/navigation/{slug}',
            path: {
                'slug': slug,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
