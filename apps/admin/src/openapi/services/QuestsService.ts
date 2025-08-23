/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeOut } from '../models/NodeOut';
import type { QuestBuyIn } from '../models/QuestBuyIn';
import type { QuestCreate } from '../models/QuestCreate';
import type { QuestOut } from '../models/QuestOut';
import type { QuestProgressOut } from '../models/QuestProgressOut';
import type { QuestUpdate } from '../models/QuestUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class QuestsService {
    /**
     * List quests
     * Return all published quests.
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static listQuestsQuestsGet(): CancelablePromise<Array<QuestOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests',
        });
    }
    /**
     * Create quest
     * Create a new quest owned by the current user.
     * @param requestBody
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static createQuestQuestsPost(
        requestBody: QuestCreate,
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Search quests
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
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static getQuestQuestsSlugGet(
        slug: string,
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/{slug}',
            path: {
                'slug': slug,
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
     * @param requestBody
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static updateQuestQuestsQuestIdPut(
        questId: string,
        requestBody: QuestUpdate,
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/quests/{quest_id}',
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
     * Delete quest
     * Soft delete a quest owned by the current user.
     * @param questId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteQuestQuestsQuestIdDelete(
        questId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/quests/{quest_id}',
            path: {
                'quest_id': questId,
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
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static publishQuestQuestsQuestIdPublishPost(
        questId: string,
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests/{quest_id}/publish',
            path: {
                'quest_id': questId,
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
     * @returns QuestProgressOut Successful Response
     * @throws ApiError
     */
    public static startQuestQuestsQuestIdStartPost(
        questId: string,
    ): CancelablePromise<QuestProgressOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/quests/{quest_id}/start',
            path: {
                'quest_id': questId,
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
     * @returns QuestProgressOut Successful Response
     * @throws ApiError
     */
    public static getProgressQuestsQuestIdProgressGet(
        questId: string,
    ): CancelablePromise<QuestProgressOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/quests/{quest_id}/progress',
            path: {
                'quest_id': questId,
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
}
