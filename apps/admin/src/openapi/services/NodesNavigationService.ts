/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class NodesNavigationService {
    /**
     * Get next transitions (auto)
     * @param slug
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getNextNodesNodesSlugNextGet(
        slug: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes/{slug}/next',
            path: {
                'slug': slug,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get next modes options
     * @param slug
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getNextModesNodesSlugNextModesGet(
        slug: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes/{slug}/next_modes',
            path: {
                'slug': slug,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
