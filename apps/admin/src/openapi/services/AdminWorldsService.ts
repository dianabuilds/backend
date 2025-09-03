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
     * @param workspaceId
     * @returns WorldTemplateOut Successful Response
     * @throws ApiError
     */
    public static listWorldsAdminWorldsGet(
        workspaceId: string,
    ): CancelablePromise<Array<WorldTemplateOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/worlds',
            query: {
                'workspace_id': workspaceId,
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
     * @param workspaceId
     * @param requestBody
     * @returns WorldTemplateOut Successful Response
     * @throws ApiError
     */
    public static createWorldAdminWorldsPost(
        workspaceId: string,
        requestBody: WorldTemplateIn,
    ): CancelablePromise<WorldTemplateOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/worlds',
            query: {
                'workspace_id': workspaceId,
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
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteCharacterAdminWorldsCharactersCharIdDelete(
        charId: string,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/worlds/characters/{char_id}',
            path: {
                'char_id': charId,
            },
            query: {
                'workspace_id': workspaceId,
            },
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
     * @param workspaceId
     * @param requestBody
     * @returns CharacterOut Successful Response
     * @throws ApiError
     */
    public static updateCharacterAdminWorldsCharactersCharIdPatch(
        charId: string,
        workspaceId: string,
        requestBody: CharacterIn,
    ): CancelablePromise<CharacterOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/worlds/characters/{char_id}',
            path: {
                'char_id': charId,
            },
            query: {
                'workspace_id': workspaceId,
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
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteWorldAdminWorldsWorldIdDelete(
        worldId: string,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/worlds/{world_id}',
            path: {
                'world_id': worldId,
            },
            query: {
                'workspace_id': workspaceId,
            },
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
     * @param workspaceId
     * @param requestBody
     * @returns WorldTemplateOut Successful Response
     * @throws ApiError
     */
    public static updateWorldAdminWorldsWorldIdPatch(
        worldId: string,
        workspaceId: string,
        requestBody: WorldTemplateIn,
    ): CancelablePromise<WorldTemplateOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/worlds/{world_id}',
            path: {
                'world_id': worldId,
            },
            query: {
                'workspace_id': workspaceId,
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
     * List characters
     * @param worldId
     * @param workspaceId
     * @returns CharacterOut Successful Response
     * @throws ApiError
     */
    public static listCharactersAdminWorldsWorldIdCharactersGet(
        worldId: string,
        workspaceId: string,
    ): CancelablePromise<Array<CharacterOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/worlds/{world_id}/characters',
            path: {
                'world_id': worldId,
            },
            query: {
                'workspace_id': workspaceId,
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
     * @param workspaceId
     * @param requestBody
     * @returns CharacterOut Successful Response
     * @throws ApiError
     */
    public static createCharacterAdminWorldsWorldIdCharactersPost(
        worldId: string,
        workspaceId: string,
        requestBody: CharacterIn,
    ): CancelablePromise<CharacterOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/worlds/{world_id}/characters',
            path: {
                'world_id': worldId,
            },
            query: {
                'workspace_id': workspaceId,
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
}
