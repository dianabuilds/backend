/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { app__domains__quests__schemas__graph__QuestGraphOut } from '../models/app__domains__quests__schemas__graph__QuestGraphOut';
import type { NodeOut } from '../models/NodeOut';
import type { QuestBuyIn } from '../models/QuestBuyIn';
import type { QuestCreate } from '../models/QuestCreate';
import type { QuestGraphIn } from '../models/QuestGraphIn';
import type { QuestOut } from '../models/QuestOut';
import type { QuestProgressOut } from '../models/QuestProgressOut';
import type { QuestUpdate } from '../models/QuestUpdate';
import type { QuestVersionOut } from '../models/QuestVersionOut';
import type { SimulateIn } from '../models/SimulateIn';
import type { SimulateResult } from '../models/SimulateResult';
import type { ValidateResult } from '../models/ValidateResult';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class QuestsService {
    /**
     * List quests
     * Return all published quests.
     * @param workspaceId
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static listQuestsQuestsGet(
        workspaceId: string,
    ): CancelablePromise<Array<QuestOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests',
            query: {
                'workspace_id': workspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create quest
     * Create a new quest owned by the current user.
     * @param requestBody
     * @param workspaceId
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static createQuestQuestsPost(
        requestBody: QuestCreate,
        workspaceId?: (string | null),
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests',
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
     * Search quests
     * @param workspaceId
     * @param q
     * @param tags
     * @param authorId
     * @param freeOnly
     * @param premiumOnly
     * @param sortBy
     * @param page
     * @param perPage
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static searchQuestsQuestsSearchGet(
        workspaceId: string,
        q?: (string | null),
        tags?: (string | null),
        authorId?: (string | null),
        freeOnly: boolean = false,
        premiumOnly: boolean = false,
        sortBy: string = 'new',
        page: number = 1,
        perPage: number = 10,
    ): CancelablePromise<Array<QuestOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/search',
            query: {
                'workspace_id': workspaceId,
                'q': q,
                'tags': tags,
                'author_id': authorId,
                'free_only': freeOnly,
                'premium_only': premiumOnly,
                'sort_by': sortBy,
                'page': page,
                'per_page': perPage,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get quest
     * Fetch a quest by slug, ensuring access permissions.
     * @param slug
     * @param workspaceId
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static getQuestQuestsSlugGet(
        slug: string,
        workspaceId: string,
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/{slug}',
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
     * Update quest
     * Modify quest fields if the user is the author.
     * @param questId
     * @param workspaceId
     * @param requestBody
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static updateQuestQuestsQuestIdPut(
        questId: string,
        workspaceId: string,
        requestBody: QuestUpdate,
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/quests/{quest_id}',
            path: {
                'quest_id': questId,
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
    /**
     * Delete quest
     * Soft delete a quest owned by the current user.
     * @param questId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteQuestQuestsQuestIdDelete(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/quests/{quest_id}',
            path: {
                'quest_id': questId,
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
     * Publish quest
     * Mark a draft quest as published.
     * @param questId
     * @param workspaceId
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static publishQuestQuestsQuestIdPublishPost(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests/{quest_id}/publish',
            path: {
                'quest_id': questId,
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
     * Start quest
     * Begin or restart progress for a quest.
     * @param questId
     * @param workspaceId
     * @returns QuestProgressOut Successful Response
     * @throws ApiError
     */
    public static startQuestQuestsQuestIdStartPost(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<QuestProgressOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests/{quest_id}/start',
            path: {
                'quest_id': questId,
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
     * Get progress
     * Retrieve progress of the current user in a quest.
     * @param questId
     * @param workspaceId
     * @returns QuestProgressOut Successful Response
     * @throws ApiError
     */
    public static getProgressQuestsQuestIdProgressGet(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<QuestProgressOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/{quest_id}/progress',
            path: {
                'quest_id': questId,
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
     * Get quest node
     * Return node details within a quest and update progress.
     * @param questId
     * @param nodeId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static getQuestNodeQuestsQuestIdNodesNodeIdGet(
        questId: string,
        nodeId: string,
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/{quest_id}/nodes/{node_id}',
            path: {
                'quest_id': questId,
                'node_id': nodeId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Buy quest
     * Purchase access to a paid quest.
     * @param questId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static buyQuestQuestsQuestIdBuyPost(
        questId: string,
        requestBody: QuestBuyIn,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests/{quest_id}/buy',
            path: {
                'quest_id': questId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List quest versions
     * @param questId
     * @param workspaceId
     * @returns QuestVersionOut Successful Response
     * @throws ApiError
     */
    public static listVersionsQuestsQuestIdVersionsGet(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<Array<QuestVersionOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/{quest_id}/versions',
            path: {
                'quest_id': questId,
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
     * Create quest version
     * @param questId
     * @param workspaceId
     * @returns QuestVersionOut Successful Response
     * @throws ApiError
     */
    public static createVersionQuestsQuestIdVersionsPost(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<QuestVersionOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests/{quest_id}/versions',
            path: {
                'quest_id': questId,
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
     * Get current quest version graph
     * @param questId
     * @param workspaceId
     * @returns app__domains__quests__schemas__graph__QuestGraphOut Successful Response
     * @throws ApiError
     */
    public static getCurrentVersionQuestsQuestIdVersionsCurrentGet(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<app__domains__quests__schemas__graph__QuestGraphOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/{quest_id}/versions/current',
            path: {
                'quest_id': questId,
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
     * Get quest version
     * @param questId
     * @param versionId
     * @param workspaceId
     * @returns QuestVersionOut Successful Response
     * @throws ApiError
     */
    public static getVersionQuestsQuestIdVersionsVersionIdGet(
        questId: string,
        versionId: string,
        workspaceId: string,
    ): CancelablePromise<QuestVersionOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/{quest_id}/versions/{version_id}',
            path: {
                'quest_id': questId,
                'version_id': versionId,
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
     * Delete draft version
     * @param questId
     * @param versionId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteVersionQuestsQuestIdVersionsVersionIdDelete(
        questId: string,
        versionId: string,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/quests/{quest_id}/versions/{version_id}',
            path: {
                'quest_id': questId,
                'version_id': versionId,
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
     * Get version graph
     * @param versionId
     * @param workspaceId
     * @returns app__domains__quests__schemas__graph__QuestGraphOut Successful Response
     * @throws ApiError
     */
    public static getGraphQuestsVersionsVersionIdGraphGet(
        versionId: string,
        workspaceId: string,
    ): CancelablePromise<app__domains__quests__schemas__graph__QuestGraphOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/versions/{version_id}/graph',
            path: {
                'version_id': versionId,
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
     * Replace version graph
     * @param versionId
     * @param workspaceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static putGraphQuestsVersionsVersionIdGraphPut(
        versionId: string,
        workspaceId: string,
        requestBody: QuestGraphIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/quests/versions/{version_id}/graph',
            path: {
                'version_id': versionId,
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
    /**
     * Validate version graph
     * @param versionId
     * @param workspaceId
     * @returns ValidateResult Successful Response
     * @throws ApiError
     */
    public static validateVersionQuestsVersionsVersionIdValidatePost(
        versionId: string,
        workspaceId: string,
    ): CancelablePromise<ValidateResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests/versions/{version_id}/validate',
            path: {
                'version_id': versionId,
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
     * Simulate version graph
     * @param versionId
     * @param workspaceId
     * @param requestBody
     * @returns SimulateResult Successful Response
     * @throws ApiError
     */
    public static simulateVersionQuestsVersionsVersionIdSimulatePost(
        versionId: string,
        workspaceId: string,
        requestBody: SimulateIn,
    ): CancelablePromise<SimulateResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests/versions/{version_id}/simulate',
            path: {
                'version_id': versionId,
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
    /**
     * Publish version
     * @param versionId
     * @param workspaceId
     * @returns QuestVersionOut Successful Response
     * @throws ApiError
     */
    public static publishVersionQuestsVersionsVersionIdPublishPost(
        versionId: string,
        workspaceId: string,
    ): CancelablePromise<QuestVersionOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests/versions/{version_id}/publish',
            path: {
                'version_id': versionId,
            },
            query: {
                'workspace_id': workspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
