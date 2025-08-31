/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AchievementAdminOut } from '../models/AchievementAdminOut';
import type { AchievementCreateIn } from '../models/AchievementCreateIn';
import type { AchievementUpdateIn } from '../models/AchievementUpdateIn';
import type { AdminEchoTraceOut } from '../models/AdminEchoTraceOut';
import type { AdminTransitionOut } from '../models/AdminTransitionOut';
import type { AdminUserOut } from '../models/AdminUserOut';
import type { app__domains__navigation__api__admin_transitions_simulate__SimulateRequest } from '../models/app__domains__navigation__api__admin_transitions_simulate__SimulateRequest';
import type { app__domains__navigation__api__preview_router__SimulateRequest } from '../models/app__domains__navigation__api__preview_router__SimulateRequest';
import type { AuditLogOut } from '../models/AuditLogOut';
import type { Body_embedding_test_admin_embedding_test_post } from '../models/Body_embedding_test_admin_embedding_test_post';
import type { BroadcastCreate } from '../models/BroadcastCreate';
import type { BulkIds } from '../models/BulkIds';
import type { CampaignUpdate } from '../models/CampaignUpdate';
import type { CharacterIn } from '../models/CharacterIn';
import type { CharacterOut } from '../models/CharacterOut';
import type { FeatureFlagOut } from '../models/FeatureFlagOut';
import type { FeatureFlagUpdateIn } from '../models/FeatureFlagUpdateIn';
import type { GenerateQuestIn } from '../models/GenerateQuestIn';
import type { GenerationEnqueued } from '../models/GenerationEnqueued';
import type { GenerationJobOut } from '../models/GenerationJobOut';
import type { InvalidatePatternRequest } from '../models/InvalidatePatternRequest';
import type { MetricsSummary } from '../models/MetricsSummary';
import type { NavigationCacheInvalidateRequest } from '../models/NavigationCacheInvalidateRequest';
import type { NavigationCacheSetRequest } from '../models/NavigationCacheSetRequest';
import type { NavigationRunRequest } from '../models/NavigationRunRequest';
import type { NodeBulkOperation } from '../models/NodeBulkOperation';
import type { NodeBulkPatch } from '../models/NodeBulkPatch';
import type { NodeOut } from '../models/NodeOut';
import type { NodePatchCreate } from '../models/NodePatchCreate';
import type { NodePatchDiffOut } from '../models/NodePatchDiffOut';
import type { NodePatchOut } from '../models/NodePatchOut';
import type { DraftIssueOut } from '../models/DraftIssueOut';
import type { NodeTransitionType } from '../models/NodeTransitionType';
import type { NodeTransitionUpdate } from '../models/NodeTransitionUpdate';
import type { NodeType } from '../models/NodeType';
import type { PopularityRecomputeRequest } from '../models/PopularityRecomputeRequest';
import type { PreviewLinkRequest } from '../models/PreviewLinkRequest';
import type { PublishIn } from '../models/PublishIn';
import type { QuestCreateIn } from '../models/QuestCreateIn';
import type { QuestGraphIn } from '../models/QuestGraphIn';
import type { QuestGraphOut } from '../models/QuestGraphOut';
import type { QuestSummary } from '../models/QuestSummary';
import type { RateLimitDisablePayload } from '../models/RateLimitDisablePayload';
import type { RelevanceApplyOut } from '../models/RelevanceApplyOut';
import type { RelevanceGetOut } from '../models/RelevanceGetOut';
import type { RelevancePutIn } from '../models/RelevancePutIn';
import type { RestrictionAdminCreate } from '../models/RestrictionAdminCreate';
import type { RestrictionAdminUpdate } from '../models/RestrictionAdminUpdate';
import type { RestrictionOut } from '../models/RestrictionOut';
import type { RuleUpdatePayload } from '../models/RuleUpdatePayload';
import type { SearchOverviewOut } from '../models/SearchOverviewOut';
import type { SendNotificationPayload } from '../models/SendNotificationPayload';
import type { SimulateIn } from '../models/SimulateIn';
import type { SimulateResult } from '../models/SimulateResult';
import type { SubscriptionPlanIn } from '../models/SubscriptionPlanIn';
import type { SubscriptionPlanOut } from '../models/SubscriptionPlanOut';
import type { TransitionDisableRequest } from '../models/TransitionDisableRequest';
import type { UserIdIn } from '../models/UserIdIn';
import type { UserPremiumUpdate } from '../models/UserPremiumUpdate';
import type { UserRoleUpdate } from '../models/UserRoleUpdate';
import type { ValidateResult } from '../models/ValidateResult';
import type { WorldTemplateIn } from '../models/WorldTemplateIn';
import type { WorldTemplateOut } from '../models/WorldTemplateOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminService {
    /**
     * Get Cors Config
     * Return CORS configuration used by the application.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCorsConfigAdminOpsCorsGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ops/cors',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Get Alerts
     * Return active alerts for operational dashboard.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAlertsAdminOpsAlertsGet(): CancelablePromise<Record<string, Array<Record<string, any>>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ops/alerts',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Get Status
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getStatusAdminOpsStatusGet(
        workspaceId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ops/status',
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
     * Get Limits
     * @param workspaceId
     * @returns number Successful Response
     * @throws ApiError
     */
    public static getLimitsAdminOpsLimitsGet(
        workspaceId?: (string | null),
    ): CancelablePromise<Record<string, number>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ops/limits',
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
     * List world templates
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listWorldTemplatesAdminAiQuestsTemplatesGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/templates',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Enqueue AI quest generation
     * @param requestBody
     * @param reuse
     * @returns GenerationEnqueued Successful Response
     * @throws ApiError
     */
    public static generateAiQuestAdminAiQuestsGeneratePost(
        requestBody: GenerateQuestIn,
        reuse: boolean = true,
    ): CancelablePromise<GenerationEnqueued> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/ai/quests/generate',
            query: {
                'reuse': reuse,
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
     * List AI generation jobs
     * @returns GenerationJobOut Successful Response
     * @throws ApiError
     */
    public static listJobsAdminAiQuestsJobsGet(): CancelablePromise<Array<GenerationJobOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/jobs',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Get job by id
     * @param jobId
     * @returns GenerationJobOut Successful Response
     * @throws ApiError
     */
    public static getJobAdminAiQuestsJobsJobIdGet(
        jobId: string,
    ): CancelablePromise<GenerationJobOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/jobs/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Simulate job completion (DEV)
     * @param jobId
     * @returns GenerationJobOut Successful Response
     * @throws ApiError
     */
    public static simulateCompleteAdminAiQuestsJobsJobIdSimulateCompletePost(
        jobId: string,
    ): CancelablePromise<GenerationJobOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/ai/quests/jobs/{job_id}/simulate_complete',
            path: {
                'job_id': jobId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Advance job progress (DEV)
     * @param jobId
     * @param requestBody
     * @returns GenerationJobOut Successful Response
     * @throws ApiError
     */
    public static tickJobAdminAiQuestsJobsJobIdTickPost(
        jobId: string,
        requestBody?: (Record<string, any> | null),
    ): CancelablePromise<GenerationJobOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/ai/quests/jobs/{job_id}/tick',
            path: {
                'job_id': jobId,
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
     * List worlds
     * @returns WorldTemplateOut Successful Response
     * @throws ApiError
     */
    public static listWorldsAdminAiQuestsWorldsGet(): CancelablePromise<Array<WorldTemplateOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/worlds',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Create world
     * @param requestBody
     * @returns WorldTemplateOut Successful Response
     * @throws ApiError
     */
    public static createWorldAdminAiQuestsWorldsPost(
        requestBody: WorldTemplateIn,
    ): CancelablePromise<WorldTemplateOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/ai/quests/worlds',
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
     * Update world
     * @param worldId
     * @param requestBody
     * @returns WorldTemplateOut Successful Response
     * @throws ApiError
     */
    public static updateWorldAdminAiQuestsWorldsWorldIdPut(
        worldId: string,
        requestBody: WorldTemplateIn,
    ): CancelablePromise<WorldTemplateOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/ai/quests/worlds/{world_id}',
            path: {
                'world_id': worldId,
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
     * Delete world
     * @param worldId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteWorldAdminAiQuestsWorldsWorldIdDelete(
        worldId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/ai/quests/worlds/{world_id}',
            path: {
                'world_id': worldId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List characters for world
     * @param worldId
     * @returns CharacterOut Successful Response
     * @throws ApiError
     */
    public static listCharactersAdminAiQuestsWorldsWorldIdCharactersGet(
        worldId: string,
    ): CancelablePromise<Array<CharacterOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/worlds/{world_id}/characters',
            path: {
                'world_id': worldId,
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
     * @param requestBody
     * @returns CharacterOut Successful Response
     * @throws ApiError
     */
    public static createCharacterAdminAiQuestsWorldsWorldIdCharactersPost(
        worldId: string,
        requestBody: CharacterIn,
    ): CancelablePromise<CharacterOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/ai/quests/worlds/{world_id}/characters',
            path: {
                'world_id': worldId,
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
     * @param characterId
     * @param requestBody
     * @returns CharacterOut Successful Response
     * @throws ApiError
     */
    public static updateCharacterAdminAiQuestsCharactersCharacterIdPut(
        characterId: string,
        requestBody: CharacterIn,
    ): CancelablePromise<CharacterOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/ai/quests/characters/{character_id}',
            path: {
                'character_id': characterId,
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
     * @param characterId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteCharacterAdminAiQuestsCharactersCharacterIdDelete(
        characterId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/ai/quests/characters/{character_id}',
            path: {
                'character_id': characterId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Проверка статуса embedding-провайдера
     * @returns any Successful Response
     * @throws ApiError
     */
    public static embeddingStatusAdminEmbeddingStatusGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/embedding/status',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Протестировать векторизацию произвольного текста
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static embeddingTestAdminEmbeddingTestPost(
        requestBody: Body_embedding_test_admin_embedding_test_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/embedding/test',
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
     * Create a quest (skeleton)
     * @param workspaceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createQuestAdminQuestsCreatePost(
        workspaceId: string,
        requestBody: QuestCreateIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/create',
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
     * Quest with versions
     * @param questId
     * @param workspaceId
     * @returns QuestSummary Successful Response
     * @throws ApiError
     */
    public static getQuestAdminQuestsQuestIdGet(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<QuestSummary> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{quest_id}',
            path: {
                'quest_id': questId,
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
     * Create a draft version
     * @param questId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createDraftAdminQuestsQuestIdDraftPost(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/{quest_id}/draft',
            path: {
                'quest_id': questId,
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
     * Get version graph
     * @param versionId
     * @returns QuestGraphOut Successful Response
     * @throws ApiError
     */
    public static getVersionAdminQuestsVersionsVersionIdGet(
        versionId: string,
    ): CancelablePromise<QuestGraphOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/versions/{version_id}',
            path: {
                'version_id': versionId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete draft version
     * @param versionId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteDraftAdminQuestsVersionsVersionIdDelete(
        versionId: string,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/quests/versions/{version_id}',
            path: {
                'version_id': versionId,
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
     * Replace graph of the version
     * @param versionId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static putGraphAdminQuestsVersionsVersionIdGraphPut(
        versionId: string,
        requestBody: QuestGraphIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/quests/versions/{version_id}/graph',
            path: {
                'version_id': versionId,
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
     * Validate graph
     * @param versionId
     * @param workspaceId
     * @returns ValidateResult Successful Response
     * @throws ApiError
     */
    public static validateVersionAdminQuestsVersionsVersionIdValidatePost(
        versionId: string,
        workspaceId: string,
    ): CancelablePromise<ValidateResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/validate',
            path: {
                'version_id': versionId,
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
     * Autofix graph (basic)
     * @param versionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static autofixVersionAdminQuestsVersionsVersionIdAutofixPost(
        versionId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/autofix',
            path: {
                'version_id': versionId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Publish version
     * @param versionId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static publishVersionAdminQuestsVersionsVersionIdPublishPost(
        versionId: string,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/publish',
            path: {
                'version_id': versionId,
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
     * Rollback to version
     * @param versionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rollbackVersionAdminQuestsVersionsVersionIdRollbackPost(
        versionId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/rollback',
            path: {
                'version_id': versionId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Simulate run
     * @param versionId
     * @param workspaceId
     * @param requestBody
     * @returns SimulateResult Successful Response
     * @throws ApiError
     */
    public static simulateVersionAdminQuestsVersionsVersionIdSimulatePost(
        versionId: string,
        workspaceId: string,
        requestBody: SimulateIn,
    ): CancelablePromise<SimulateResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/simulate',
            path: {
                'version_id': versionId,
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
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPathPatch(
        path: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/quests/{path}',
            path: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPathPatch1(
        path: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/quests/{path}',
            path: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPathPatch2(
        path: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/quests/{path}',
            path: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPathPatch3(
        path: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/{path}',
            path: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPathPatch4(
        path: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'OPTIONS',
            url: '/admin/quests/{path}',
            path: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPathPatch5(
        path: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{path}',
            path: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPatch(
        path: string = '',
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/quests',
            query: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPatch1(
        path: string = '',
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/quests',
            query: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPatch2(
        path: string = '',
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/quests',
            query: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPatch3(
        path: string = '',
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests',
            query: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPatch4(
        path: string = '',
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'OPTIONS',
            url: '/admin/quests',
            query: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Redirect Quests
     * Redirect legacy quest admin requests to node endpoints.
     * @param path
     * @returns any Successful Response
     * @throws ApiError
     */
    public static redirectQuestsAdminQuestsPatch5(
        path: string = '',
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests',
            query: {
                'path': path,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Send notification to user
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static sendNotificationAdminNotificationsPost(
        requestBody: SendNotificationPayload,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/notifications',
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
     * Create broadcast campaign (or dry-run)
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createBroadcastAdminNotificationsBroadcastPost(
        requestBody: BroadcastCreate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/notifications/broadcast',
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
     * List broadcast campaigns
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listBroadcastsAdminNotificationsBroadcastGet(
        limit: number = 50,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/notifications/broadcast',
            query: {
                'limit': limit,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get campaign
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getBroadcastAdminNotificationsBroadcastCampaignIdGet(
        campaignId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/notifications/broadcast/{campaign_id}',
            path: {
                'campaign_id': campaignId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel campaign
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelBroadcastAdminNotificationsBroadcastCampaignIdCancelPost(
        campaignId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/notifications/broadcast/{campaign_id}/cancel',
            path: {
                'campaign_id': campaignId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List campaigns
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listCampaignsAdminNotificationsCampaignsGet(
        limit: number = 50,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/notifications/campaigns',
            query: {
                'limit': limit,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get campaign
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCampaignAdminNotificationsCampaignsCampaignIdGet(
        campaignId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/notifications/campaigns/{campaign_id}',
            path: {
                'campaign_id': campaignId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update campaign
     * @param campaignId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateCampaignAdminNotificationsCampaignsCampaignIdPatch(
        campaignId: string,
        requestBody: CampaignUpdate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/notifications/campaigns/{campaign_id}',
            path: {
                'campaign_id': campaignId,
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
     * Dispatch campaign
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static sendCampaignAdminNotificationsCampaignsCampaignIdSendPost(
        campaignId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/notifications/campaigns/{campaign_id}/send',
            path: {
                'campaign_id': campaignId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List subscription plans
     * @returns SubscriptionPlanOut Successful Response
     * @throws ApiError
     */
    public static listPlansAdminPremiumPlansGet(): CancelablePromise<Array<SubscriptionPlanOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/premium/plans',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Create subscription plan
     * @param requestBody
     * @returns SubscriptionPlanOut Successful Response
     * @throws ApiError
     */
    public static createPlanAdminPremiumPlansPost(
        requestBody: SubscriptionPlanIn,
    ): CancelablePromise<SubscriptionPlanOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/premium/plans',
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
     * Update subscription plan
     * @param planId
     * @param requestBody
     * @returns SubscriptionPlanOut Successful Response
     * @throws ApiError
     */
    public static updatePlanAdminPremiumPlansPlanIdPut(
        planId: string,
        requestBody: SubscriptionPlanIn,
    ): CancelablePromise<SubscriptionPlanOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/premium/plans/{plan_id}',
            path: {
                'plan_id': planId,
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
     * Delete subscription plan
     * @param planId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deletePlanAdminPremiumPlansPlanIdDelete(
        planId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/premium/plans/{plan_id}',
            path: {
                'plan_id': planId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List achievements (admin)
     * @param workspaceId
     * @returns AchievementAdminOut Successful Response
     * @throws ApiError
     */
    public static listAchievementsAdminAdminAchievementsGet(
        workspaceId: string,
    ): CancelablePromise<Array<AchievementAdminOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/achievements',
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
     * Create achievement
     * @param workspaceId
     * @param requestBody
     * @returns AchievementAdminOut Successful Response
     * @throws ApiError
     */
    public static createAchievementAdminAdminAchievementsPost(
        workspaceId: string,
        requestBody: AchievementCreateIn,
    ): CancelablePromise<AchievementAdminOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/achievements',
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
     * Update achievement
     * @param achievementId
     * @param workspaceId
     * @param requestBody
     * @returns AchievementAdminOut Successful Response
     * @throws ApiError
     */
    public static updateAchievementAdminAdminAchievementsAchievementIdPatch(
        achievementId: string,
        workspaceId: string,
        requestBody: AchievementUpdateIn,
    ): CancelablePromise<AchievementAdminOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/achievements/{achievement_id}',
            path: {
                'achievement_id': achievementId,
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
     * Delete achievement
     * @param achievementId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteAchievementAdminAdminAchievementsAchievementIdDelete(
        achievementId: string,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/achievements/{achievement_id}',
            path: {
                'achievement_id': achievementId,
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
     * Grant achievement to user
     * @param achievementId
     * @param workspaceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static grantAchievementAdminAchievementsAchievementIdGrantPost(
        achievementId: string,
        workspaceId: string,
        requestBody: UserIdIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/achievements/{achievement_id}/grant',
            path: {
                'achievement_id': achievementId,
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
     * Revoke achievement from user
     * @param achievementId
     * @param workspaceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static revokeAchievementAdminAchievementsAchievementIdRevokePost(
        achievementId: string,
        workspaceId: string,
        requestBody: UserIdIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/achievements/{achievement_id}/revoke',
            path: {
                'achievement_id': achievementId,
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
     * Run navigation generation
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static runNavigationAdminNavigationRunPost(
        requestBody: NavigationRunRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/navigation/run',
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
     * Set navigation cache
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static setCacheAdminNavigationCacheSetPost(
        requestBody: NavigationCacheSetRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/navigation/cache/set',
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
     * Invalidate navigation cache
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static invalidateCacheAdminNavigationCacheInvalidatePost(
        requestBody: NavigationCacheInvalidateRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/navigation/cache/invalidate',
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
     * pgvector status
     * @returns any Successful Response
     * @throws ApiError
     */
    public static pgvectorStatusAdminNavigationPgvectorStatusGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/navigation/pgvector/status',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Create Preview Link
     * @param requestBody
     * @returns string Successful Response
     * @throws ApiError
     */
    public static createPreviewLinkAdminPreviewLinkPost(
        requestBody: PreviewLinkRequest,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/preview/link',
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
     * Simulate transitions with preview
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static simulateTransitionsAdminPreviewTransitionsSimulatePost(
        requestBody: app__domains__navigation__api__preview_router__SimulateRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/preview/transitions/simulate',
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
     * Get admin menu
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAdminMenuAdminMenuGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/menu',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Invalidate admin menu cache
     * @returns any Successful Response
     * @throws ApiError
     */
    public static invalidateAdminMenuAdminMenuInvalidatePost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/menu/invalidate',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * List feature flags
     * @returns FeatureFlagOut Successful Response
     * @throws ApiError
     */
    public static listFlagsAdminFlagsGet(): CancelablePromise<Array<FeatureFlagOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/flags',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Update feature flag
     * @param key
     * @param requestBody
     * @returns FeatureFlagOut Successful Response
     * @throws ApiError
     */
    public static updateFlagAdminFlagsKeyPatch(
        key: string,
        requestBody: FeatureFlagUpdateIn,
    ): CancelablePromise<FeatureFlagOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/flags/{key}',
            path: {
                'key': key,
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
     * Cache statistics
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cacheStatsAdminCacheStatsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/cache/stats',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Invalidate cache by pattern
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static invalidateByPatternAdminCacheInvalidateByPatternPost(
        requestBody: InvalidatePatternRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/cache/invalidate_by_pattern',
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
     * Admin dashboard data
     * @returns any Successful Response
     * @throws ApiError
     */
    public static adminDashboardAdminDashboardGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/dashboard',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * List drafts with issues
     * @returns DraftIssueOut Successful Response
     * @throws ApiError
     */
    public static listDraftIssuesAdminDraftsIssuesGet(): CancelablePromise<Array<DraftIssueOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/drafts/issues',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * List node patches
     * @param nodeId
     * @returns NodePatchDiffOut Successful Response
     * @throws ApiError
     */
    public static listPatchesAdminHotfixPatchesGet(
        nodeId?: (string | null),
    ): CancelablePromise<Array<NodePatchDiffOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/hotfix/patches',
            query: {
                'node_id': nodeId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create node patch
     * @param requestBody
     * @returns NodePatchOut Successful Response
     * @throws ApiError
     */
    public static createPatchAdminHotfixPatchesPost(
        requestBody: NodePatchCreate,
    ): CancelablePromise<NodePatchOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/hotfix/patches',
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
     * Revert patch
     * @param patchId
     * @returns NodePatchOut Successful Response
     * @throws ApiError
     */
    public static revertPatchAdminHotfixPatchesPatchIdRevertPost(
        patchId: string,
    ): CancelablePromise<NodePatchOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/hotfix/patches/{patch_id}/revert',
            path: {
                'patch_id': patchId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get patch
     * @param patchId
     * @returns NodePatchDiffOut Successful Response
     * @throws ApiError
     */
    public static getPatchAdminHotfixPatchesPatchIdGet(
        patchId: string,
    ): CancelablePromise<NodePatchDiffOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/hotfix/patches/{patch_id}',
            path: {
                'patch_id': patchId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List users
     * @param q
     * @param role
     * @param isActive
     * @param premium
     * @param limit
     * @param offset
     * @returns AdminUserOut Successful Response
     * @throws ApiError
     */
    public static listUsersAdminUsersGet(
        q?: (string | null),
        role?: (string | null),
        isActive?: (boolean | null),
        premium?: (string | null),
        limit: number = 100,
        offset?: number,
    ): CancelablePromise<Array<AdminUserOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/users',
            query: {
                'q': q,
                'role': role,
                'is_active': isActive,
                'premium': premium,
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
     * Set user premium status
     * @param userId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static setUserPremiumAdminUsersUserIdPremiumPost(
        userId: string,
        requestBody: UserPremiumUpdate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/users/{user_id}/premium',
            path: {
                'user_id': userId,
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
     * Change user role
     * @param userId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static setUserRoleAdminUsersUserIdRolePost(
        userId: string,
        requestBody: UserRoleUpdate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/users/{user_id}/role',
            path: {
                'user_id': userId,
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
     * List nodes by type
     * @param nodeType
     * @param workspaceId
     * @param page
     * @param perPage
     * @param q
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listNodesAdminNodesNodeTypeGet(
        nodeType: NodeType,
        workspaceId: string,
        page: number = 1,
        perPage: number = 10,
        q?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/nodes/{node_type}',
            path: {
                'node_type': nodeType,
            },
            query: {
                'workspace_id': workspaceId,
                'page': page,
                'per_page': perPage,
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
     * Create node item
     * @param nodeType
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createNodeAdminNodesNodeTypePost(
        nodeType: NodeType,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/nodes/{node_type}',
            path: {
                'node_type': nodeType,
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
     * Get node item
     * @param nodeType
     * @param nodeId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getNodeAdminNodesNodeTypeNodeIdGet(
        nodeType: NodeType,
        nodeId: string,
        workspaceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/nodes/{node_type}/{node_id}',
            path: {
                'node_type': nodeType,
                'node_id': nodeId,
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
     * Update node item
     * @param nodeType
     * @param nodeId
     * @param workspaceId
     * @param requestBody
     * @param next
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateNodeAdminNodesNodeTypeNodeIdPatch(
        nodeType: NodeType,
        nodeId: string,
        workspaceId: string,
        requestBody: Record<string, any>,
        next?: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/nodes/{node_type}/{node_id}',
            path: {
                'node_type': nodeType,
                'node_id': nodeId,
            },
            query: {
                'workspace_id': workspaceId,
                'next': next,
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
     * Publish node item
     * @param nodeType
     * @param nodeId
     * @param workspaceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static publishNodeAdminNodesNodeTypeNodeIdPublishPost(
        nodeType: NodeType,
        nodeId: string,
        workspaceId: string,
        requestBody?: (PublishIn | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/nodes/{node_type}/{node_id}/publish',
            path: {
                'node_type': nodeType,
                'node_id': nodeId,
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
     * List nodes (admin)
     * @param workspaceId
     * @param author
     * @param tags
     * @param match
     * @param sort
     * @param isPublic
     * @param visible
     * @param premiumOnly
     * @param recommendable
     * @param nodeType
     * @param limit
     * @param offset
     * @param dateFrom
     * @param dateTo
     * @param q
     * @param ifNoneMatch
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static listNodesAdminAdminNodesGet(
        workspaceId: string,
        author?: (string | null),
        tags?: (string | null),
        match: string = 'any',
        sort: string = 'updated_desc',
        isPublic?: (boolean | null),
        visible?: (boolean | null),
        premiumOnly?: (boolean | null),
        recommendable?: (boolean | null),
        nodeType?: (string | null),
        limit: number = 25,
        offset?: number,
        dateFrom?: (string | null),
        dateTo?: (string | null),
        q?: (string | null),
        ifNoneMatch?: (string | null),
    ): CancelablePromise<Array<NodeOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/nodes',
            headers: {
                'If-None-Match': ifNoneMatch,
            },
            query: {
                'workspace_id': workspaceId,
                'author': author,
                'tags': tags,
                'match': match,
                'sort': sort,
                'is_public': isPublic,
                'visible': visible,
                'premium_only': premiumOnly,
                'recommendable': recommendable,
                'node_type': nodeType,
                'limit': limit,
                'offset': offset,
                'date_from': dateFrom,
                'date_to': dateTo,
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
     * Bulk node operations
     * @param workspaceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkNodeOperationAdminNodesBulkPost(
        workspaceId: string,
        requestBody: NodeBulkOperation,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/nodes/bulk',
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
     * Bulk update nodes
     * @param workspaceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkPatchNodesAdminNodesBulkPatch(
        workspaceId: string,
        requestBody: NodeBulkPatch,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/nodes/bulk',
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
     * List transitions
     * @param from
     * @param to
     * @param type
     * @param author
     * @param page
     * @param pageSize
     * @returns AdminTransitionOut Successful Response
     * @throws ApiError
     */
    public static listTransitionsAdminAdminTransitionsGet(
        from?: (string | null),
        to?: (string | null),
        type?: (NodeTransitionType | null),
        author?: (string | null),
        page: number = 1,
        pageSize: number = 50,
    ): CancelablePromise<Array<AdminTransitionOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/transitions',
            query: {
                'from': from,
                'to': to,
                'type': type,
                'author': author,
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update transition
     * @param transitionId
     * @param requestBody
     * @returns AdminTransitionOut Successful Response
     * @throws ApiError
     */
    public static updateTransitionAdminAdminTransitionsTransitionIdPatch(
        transitionId: string,
        requestBody: NodeTransitionUpdate,
    ): CancelablePromise<AdminTransitionOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/transitions/{transition_id}',
            path: {
                'transition_id': transitionId,
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
     * Delete transition
     * @param transitionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteTransitionAdminAdminTransitionsTransitionIdDelete(
        transitionId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/transitions/{transition_id}',
            path: {
                'transition_id': transitionId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Disable transitions by node
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static disableTransitionsByNodeAdminTransitionsDisableByNodePost(
        requestBody: TransitionDisableRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/transitions/disable_by_node',
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
     * Simulate transitions
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static simulateTransitionsAdminTransitionsSimulatePost(
        requestBody: app__domains__navigation__api__admin_transitions_simulate__SimulateRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/transitions/simulate',
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
     * List rate limit rules
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listRulesAdminRatelimitRulesGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ratelimit/rules',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Update single rate limit rule
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateRuleAdminRatelimitRulesPatch(
        requestBody: RuleUpdatePayload,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/ratelimit/rules',
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
     * Recent rate limit hits
     * @returns any Successful Response
     * @throws ApiError
     */
    public static recentHitsAdminRatelimitRecent429Get(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ratelimit/recent429',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Toggle rate limiter
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static disableRateLimitAdminRatelimitDisablePost(
        requestBody: RateLimitDisablePayload,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/ratelimit/disable',
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
     * List audit logs
     * @param actorId
     * @param action
     * @param resource
     * @param workspaceId
     * @param dateFrom
     * @param dateTo
     * @param page
     * @param pageSize
     * @returns AuditLogOut Successful Response
     * @throws ApiError
     */
    public static listAuditLogsAdminAuditGet(
        actorId?: (string | null),
        action?: (string | null),
        resource?: (string | null),
        workspaceId?: (string | null),
        dateFrom?: (string | null),
        dateTo?: (string | null),
        page: number = 1,
        pageSize: number = 50,
    ): CancelablePromise<Array<AuditLogOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/audit',
            query: {
                'actor_id': actorId,
                'action': action,
                'resource': resource,
                'workspace_id': workspaceId,
                'date_from': dateFrom,
                'date_to': dateTo,
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Metrics Summary
     * @param range
     * @returns MetricsSummary Successful Response
     * @throws ApiError
     */
    public static metricsSummaryAdminMetricsSummaryGet(
        range: string = '1h',
    ): CancelablePromise<MetricsSummary> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/metrics/summary',
            query: {
                'range': range,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Metrics Timeseries
     * Таймсерии: counts per status class (2xx/4xx/5xx) и p95 latency по бакетам.
     * @param range
     * @param step
     * @returns any Successful Response
     * @throws ApiError
     */
    public static metricsTimeseriesAdminMetricsTimeseriesGet(
        range: string = '1h',
        step: number = 60,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/metrics/timeseries',
            query: {
                'range': range,
                'step': step,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Metrics Top Endpoints
     * Топ маршрутов по p95 | error_rate | rps.
     * @param range
     * @param by
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static metricsTopEndpointsAdminMetricsEndpointsTopGet(
        range: string = '1h',
        by: string = 'p95',
        limit: number = 20,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/metrics/endpoints/top',
            query: {
                'range': range,
                'by': by,
                'limit': limit,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Metrics Errors Recent
     * Последние ошибки (4xx/5xx).
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static metricsErrorsRecentAdminMetricsErrorsRecentGet(
        limit: number = 100,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/metrics/errors/recent',
            query: {
                'limit': limit,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Metrics Transitions
     * @returns any Successful Response
     * @throws ApiError
     */
    public static metricsTransitionsAdminMetricsTransitionsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/metrics/transitions',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Metrics Events
     * @returns any Successful Response
     * @throws ApiError
     */
    public static metricsEventsAdminMetricsEventsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/metrics/events',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * List echo traces
     * @param from
     * @param to
     * @param userId
     * @param source
     * @param channel
     * @param dateFrom
     * @param dateTo
     * @param page
     * @param pageSize
     * @returns AdminEchoTraceOut Successful Response
     * @throws ApiError
     */
    public static listEchoTracesAdminEchoGet(
        from?: (string | null),
        to?: (string | null),
        userId?: (string | null),
        source?: (string | null),
        channel?: (string | null),
        dateFrom?: (string | null),
        dateTo?: (string | null),
        page: number = 1,
        pageSize: number = 50,
    ): CancelablePromise<Array<AdminEchoTraceOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/echo',
            query: {
                'from': from,
                'to': to,
                'user_id': userId,
                'source': source,
                'channel': channel,
                'date_from': dateFrom,
                'date_to': dateTo,
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Anonymize echo trace
     * @param traceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static anonymizeEchoTraceAdminEchoTraceIdAnonymizePost(
        traceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/echo/{trace_id}/anonymize',
            path: {
                'trace_id': traceId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete echo trace
     * @param traceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteEchoTraceAdminEchoTraceIdDelete(
        traceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/echo/{trace_id}',
            path: {
                'trace_id': traceId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Bulk anonymize echo traces
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkAnonymizeEchoAdminEchoBulkAnonymizePost(
        requestBody: BulkIds,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/echo/bulk/anonymize',
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
     * Bulk delete echo traces
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkDeleteEchoAdminEchoBulkDeletePost(
        requestBody: BulkIds,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/echo/bulk/delete',
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
     * Recompute node popularity
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static recomputePopularityAdminEchoRecomputePopularityPost(
        requestBody: PopularityRecomputeRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/echo/recompute_popularity',
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
     * List navigation traces
     * @param from
     * @param to
     * @param userId
     * @param type
     * @param source
     * @param channel
     * @param dateFrom
     * @param dateTo
     * @param page
     * @param pageSize
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listTracesAdminTracesGet(
        from?: (string | null),
        to?: (string | null),
        userId?: (string | null),
        type?: (string | null),
        source?: (string | null),
        channel?: (string | null),
        dateFrom?: (string | null),
        dateTo?: (string | null),
        page: number = 1,
        pageSize: number = 50,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/traces',
            query: {
                'from': from,
                'to': to,
                'user_id': userId,
                'type': type,
                'source': source,
                'channel': channel,
                'date_from': dateFrom,
                'date_to': dateTo,
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Anonymize trace (remove user reference)
     * @param traceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static anonymizeTraceAdminTracesTraceIdAnonymizePost(
        traceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/traces/{trace_id}/anonymize',
            path: {
                'trace_id': traceId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete trace
     * @param traceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteTraceAdminTracesTraceIdDelete(
        traceId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/traces/{trace_id}',
            path: {
                'trace_id': traceId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Bulk anonymize traces
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkAnonymizeTracesAdminTracesBulkAnonymizePost(
        requestBody: BulkIds,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/traces/bulk/anonymize',
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
     * Bulk delete traces
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkDeleteTracesAdminTracesBulkDeletePost(
        requestBody: BulkIds,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/traces/bulk/delete',
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
     * List Restrictions
     * @param userId
     * @param type
     * @param page
     * @returns RestrictionOut Successful Response
     * @throws ApiError
     */
    public static listRestrictionsAdminRestrictionsGet(
        userId?: (string | null),
        type?: (string | null),
        page: number = 1,
    ): CancelablePromise<Array<RestrictionOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/restrictions',
            query: {
                'user_id': userId,
                'type': type,
                'page': page,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Restriction
     * @param requestBody
     * @returns RestrictionOut Successful Response
     * @throws ApiError
     */
    public static createRestrictionAdminRestrictionsPost(
        requestBody: RestrictionAdminCreate,
    ): CancelablePromise<RestrictionOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/restrictions',
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
     * Update Restriction
     * @param restrictionId
     * @param requestBody
     * @returns RestrictionOut Successful Response
     * @throws ApiError
     */
    public static updateRestrictionAdminRestrictionsRestrictionIdPatch(
        restrictionId: string,
        requestBody: RestrictionAdminUpdate,
    ): CancelablePromise<RestrictionOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/restrictions/{restriction_id}',
            path: {
                'restriction_id': restrictionId,
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
     * Delete Restriction
     * @param restrictionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteRestrictionAdminRestrictionsRestrictionIdDelete(
        restrictionId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/restrictions/{restriction_id}',
            path: {
                'restriction_id': restrictionId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get active relevance config
     * @returns RelevanceGetOut Successful Response
     * @throws ApiError
     */
    public static getRelevanceAdminSearchRelevanceGet(): CancelablePromise<RelevanceGetOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/search/relevance',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Dry-run or apply relevance config
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static putRelevanceAdminSearchRelevancePut(
        requestBody: RelevancePutIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/search/relevance',
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
     * Rollback to specified relevance version
     * @param toVersion
     * @returns RelevanceApplyOut Successful Response
     * @throws ApiError
     */
    public static postRollbackAdminSearchRelevanceRollbackPost(
        toVersion: number,
    ): CancelablePromise<RelevanceApplyOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/search/relevance/rollback',
            query: {
                'toVersion': toVersion,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Search overview KPIs
     * @returns SearchOverviewOut Successful Response
     * @throws ApiError
     */
    public static getOverviewAdminSearchOverviewGet(): CancelablePromise<SearchOverviewOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/search/overview',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
}
