/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CharacterIn } from '../models/CharacterIn';
import type { CharacterOut } from '../models/CharacterOut';
import type { WorldTemplateIn } from '../models/WorldTemplateIn';
import type { WorldTemplateOut } from '../models/WorldTemplateOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminWorldsService {
    /**
     * List world templates
     * @param accountId
     * @returns WorldTemplateOut Successful Response
     * @throws ApiError
     */
    public static listWorldsAdminWorldsGet(
        accountId: string,
    ): CancelablePromise<Array<WorldTemplateOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/worlds',
            query: {
                'account_id': accountId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create world template
     * @param accountId
     * @param requestBody
     * @returns WorldTemplateOut Successful Response
     * @throws ApiError
     */
    public static createWorldAdminWorldsPost(
        accountId: string,
        requestBody: WorldTemplateIn,
    ): CancelablePromise<WorldTemplateOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/worlds',
            query: {
                'account_id': accountId,
            },
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
     * Update world template
     * @param worldId
     * @param accountId
     * @param requestBody
     * @returns WorldTemplateOut Successful Response
     * @throws ApiError
     */
    public static updateWorldAdminWorldsWorldIdPatch(
        worldId: string,
        accountId: string,
        requestBody: WorldTemplateIn,
    ): CancelablePromise<WorldTemplateOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/worlds/{world_id}',
            path: {
                'world_id': worldId,
            },
            query: {
                'account_id': accountId,
            },
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
     * Delete world template
     * @param worldId
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteWorldAdminWorldsWorldIdDelete(
        worldId: string,
        accountId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/worlds/{world_id}',
            path: {
                'world_id': worldId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List characters
     * @param worldId
     * @param accountId
     * @returns CharacterOut Successful Response
     * @throws ApiError
     */
    public static listCharactersAdminWorldsWorldIdCharactersGet(
        worldId: string,
        accountId: string,
    ): CancelablePromise<Array<CharacterOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/worlds/{world_id}/characters',
            path: {
                'world_id': worldId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create character
     * @param worldId
     * @param accountId
     * @param requestBody
     * @returns CharacterOut Successful Response
     * @throws ApiError
     */
    public static createCharacterAdminWorldsWorldIdCharactersPost(
        worldId: string,
        accountId: string,
        requestBody: CharacterIn,
    ): CancelablePromise<CharacterOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/worlds/{world_id}/characters',
            path: {
                'world_id': worldId,
            },
            query: {
                'account_id': accountId,
            },
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
     * Update character
     * @param charId
     * @param accountId
     * @param requestBody
     * @returns CharacterOut Successful Response
     * @throws ApiError
     */
    public static updateCharacterAdminWorldsCharactersCharIdPatch(
        charId: string,
        accountId: string,
        requestBody: CharacterIn,
    ): CancelablePromise<CharacterOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/worlds/characters/{char_id}',
            path: {
                'char_id': charId,
            },
            query: {
                'account_id': accountId,
            },
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
     * Delete character
     * @param charId
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteCharacterAdminWorldsCharactersCharIdDelete(
        charId: string,
        accountId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/worlds/characters/{char_id}',
            path: {
                'char_id': charId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
}
