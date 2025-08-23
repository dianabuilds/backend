/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AliasOut } from '../models/AliasOut';
import type { BlacklistAdd } from '../models/BlacklistAdd';
import type { BlacklistItem } from '../models/BlacklistItem';
import type { MergeIn } from '../models/MergeIn';
import type { MergeReport } from '../models/MergeReport';
import type { TagCreate } from '../models/TagCreate';
import type { TagListItem } from '../models/TagListItem';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminTagsService {
    /**
     * List tags with usage
     * @param q
     * @param limit
     * @param offset
     * @returns TagListItem Successful Response
     * @throws ApiError
     */
    public static listTagsAdminTagsListGet(
        q?: (string | null),
        limit: number = 200,
        offset?: number,
    ): CancelablePromise<Array<TagListItem>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/tags/list',
            query: {
                'q': q,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List tag aliases
     * @param tagId
     * @returns AliasOut Successful Response
     * @throws ApiError
     */
    public static getAliasesAdminTagsTagIdAliasesGet(
        tagId: string,
    ): CancelablePromise<Array<AliasOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/tags/{tag_id}/aliases',
            path: {
                'tag_id': tagId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add tag alias
     * @param tagId
     * @param alias
     * @returns AliasOut Successful Response
     * @throws ApiError
     */
    public static postAliasAdminTagsTagIdAliasesPost(
        tagId: string,
        alias: string,
    ): CancelablePromise<AliasOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/tags/{tag_id}/aliases',
            path: {
                'tag_id': tagId,
            },
            query: {
                'alias': alias,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Remove tag alias
     * @param aliasId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static delAliasAdminTagsAliasesAliasIdDelete(
        aliasId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/tags/aliases/{alias_id}',
            path: {
                'alias_id': aliasId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Merge tags (dry-run/apply)
     * @param requestBody
     * @returns MergeReport Successful Response
     * @throws ApiError
     */
    public static mergeTagsAdminTagsMergePost(
        requestBody: MergeIn,
    ): CancelablePromise<MergeReport> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/tags/merge',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List blacklisted tags
     * @param q
     * @returns BlacklistItem Successful Response
     * @throws ApiError
     */
    public static getBlacklistAdminTagsBlacklistGet(
        q?: (string | null),
    ): CancelablePromise<Array<BlacklistItem>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/tags/blacklist',
            query: {
                'q': q,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Add tag to blacklist
     * @param requestBody
     * @returns BlacklistItem Successful Response
     * @throws ApiError
     */
    public static addBlacklistAdminTagsBlacklistPost(
        requestBody: BlacklistAdd,
    ): CancelablePromise<BlacklistItem> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/tags/blacklist',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Remove tag from blacklist
     * @param slug
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteBlacklistAdminTagsBlacklistSlugDelete(
        slug: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/tags/blacklist/{slug}',
            path: {
                'slug': slug,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create tag
     * @param requestBody
     * @returns TagListItem Successful Response
     * @throws ApiError
     */
    public static createTagAdminTagsPost(
        requestBody: TagCreate,
    ): CancelablePromise<TagListItem> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/tags/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete tag
     * @param tagId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteTagAdminTagsTagIdDelete(
        tagId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/tags/{tag_id}',
            path: {
                'tag_id': tagId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
}
