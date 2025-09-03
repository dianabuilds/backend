/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TagCreate } from '../models/TagCreate';
import type { TagOut } from '../models/TagOut';
import type { TagUpdate } from '../models/TagUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TagsService {
    /**
     * Tags Health
     * @returns string Successful Response
     * @throws ApiError
     */
    public static tagsHealthTagsHealthGet(): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/tags/_health',
        });
    }
    /**
     * List tags
     * Retrieve available tags with optional search and popularity filter.
     * @param workspaceId
     * @param q
     * @param popular
     * @param limit
     * @param offset
     * @returns TagOut Successful Response
     * @throws ApiError
     */
    public static listTagsTagsTagsGet(
        workspaceId: string,
        q?: (string | null),
        popular: boolean = false,
        limit: number = 10,
        offset?: number,
    ): CancelablePromise<Array<TagOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/tags/tags/',
            query: {
                'workspace_id': workspaceId,
                'q': q,
                'popular': popular,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create tag
     * @param workspaceId
     * @param requestBody
     * @returns TagOut Successful Response
     * @throws ApiError
     */
    public static createTagTagsTagsPost(
        workspaceId: string,
        requestBody: TagCreate,
    ): CancelablePromise<TagOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/tags/tags/',
            query: {
                'workspace_id': workspaceId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete tag
     * @param slug
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteTagTagsTagsSlugDelete(
        slug: string,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/tags/tags/{slug}',
            path: {
                'slug': slug,
            },
            query: {
                'workspace_id': workspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get tag
     * @param slug
     * @param workspaceId
     * @returns TagOut Successful Response
     * @throws ApiError
     */
    public static getTagTagsTagsSlugGet(
        slug: string,
        workspaceId: string,
    ): CancelablePromise<TagOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/tags/tags/{slug}',
            path: {
                'slug': slug,
            },
            query: {
                'workspace_id': workspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update tag
     * @param slug
     * @param workspaceId
     * @param requestBody
     * @returns TagOut Successful Response
     * @throws ApiError
     */
    public static updateTagTagsTagsSlugPut(
        slug: string,
        workspaceId: string,
        requestBody: TagUpdate,
    ): CancelablePromise<TagOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/tags/tags/{slug}',
            path: {
                'slug': slug,
            },
            query: {
                'workspace_id': workspaceId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
