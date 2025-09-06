/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AccountIn } from '../models/AccountIn';
import type { AccountMemberIn } from '../models/AccountMemberIn';
import type { AccountMemberOut } from '../models/AccountMemberOut';
import type { AccountOut } from '../models/AccountOut';
import type { AccountUpdate } from '../models/AccountUpdate';
import type { AccountWithRoleOut } from '../models/AccountWithRoleOut';
import type { AchievementAdminOut } from '../models/AchievementAdminOut';
import type { AchievementCreateIn } from '../models/AchievementCreateIn';
import type { AchievementUpdateIn } from '../models/AchievementUpdateIn';
import type { AdminEchoTraceOut } from '../models/AdminEchoTraceOut';
import type { AdminNodeList } from '../models/AdminNodeList';
import type { AdminNodeOut } from '../models/AdminNodeOut';
import type { AdminTransitionOut } from '../models/AdminTransitionOut';
import type { AdminUserOut } from '../models/AdminUserOut';
import type { app__api__admin__quests__steps__QuestGraphOut } from '../models/app__api__admin__quests__steps__QuestGraphOut';
import type { app__domains__navigation__api__admin_transitions_simulate__SimulateRequest } from '../models/app__domains__navigation__api__admin_transitions_simulate__SimulateRequest';
import type { app__domains__navigation__api__preview_router__SimulateRequest } from '../models/app__domains__navigation__api__preview_router__SimulateRequest';
import type { app__domains__nodes__api__articles_admin_router__PublishIn } from '../models/app__domains__nodes__api__articles_admin_router__PublishIn';
import type { app__domains__nodes__content_admin_router__PublishIn } from '../models/app__domains__nodes__content_admin_router__PublishIn';
import type { app__domains__quests__schemas__graph__QuestGraphOut } from '../models/app__domains__quests__schemas__graph__QuestGraphOut';
import type { AuditLogOut } from '../models/AuditLogOut';
import type { BackgroundJobHistoryOut } from '../models/BackgroundJobHistoryOut';
import type { Body_embedding_test_admin_embedding_test_post } from '../models/Body_embedding_test_admin_embedding_test_post';
import type { BulkIds } from '../models/BulkIds';
import type { CampaignCreate } from '../models/CampaignCreate';
import type { CampaignFilters } from '../models/CampaignFilters';
import type { CampaignUpdate } from '../models/CampaignUpdate';
import type { CaseClose } from '../models/CaseClose';
import type { CaseCreate } from '../models/CaseCreate';
import type { CaseFullResponse } from '../models/CaseFullResponse';
import type { CaseListResponse } from '../models/CaseListResponse';
import type { CaseNoteCreate } from '../models/CaseNoteCreate';
import type { CaseNoteOut } from '../models/CaseNoteOut';
import type { CaseOut } from '../models/CaseOut';
import type { CasePatch } from '../models/CasePatch';
import type { CharacterIn } from '../models/CharacterIn';
import type { CharacterOut } from '../models/CharacterOut';
import type { FeatureFlagOut } from '../models/FeatureFlagOut';
import type { FeatureFlagUpdateIn } from '../models/FeatureFlagUpdateIn';
import type { GenerateQuestIn } from '../models/GenerateQuestIn';
import type { GenerationEnqueued } from '../models/GenerationEnqueued';
import type { GenerationJobOut } from '../models/GenerationJobOut';
import type { HidePayload } from '../models/HidePayload';
import type { InvalidatePatternRequest } from '../models/InvalidatePatternRequest';
import type { MetricsSummary } from '../models/MetricsSummary';
import type { NavigationCacheInvalidateRequest } from '../models/NavigationCacheInvalidateRequest';
import type { NavigationCacheSetRequest } from '../models/NavigationCacheSetRequest';
import type { NavigationNodeProblem } from '../models/NavigationNodeProblem';
import type { NavigationRunRequest } from '../models/NavigationRunRequest';
import type { NodeBulkOperation } from '../models/NodeBulkOperation';
import type { NodeBulkPatch } from '../models/NodeBulkPatch';
import type { NodeOut } from '../models/NodeOut';
import type { NodePatchCreate } from '../models/NodePatchCreate';
import type { NodePatchDiffOut } from '../models/NodePatchDiffOut';
import type { NodePatchOut } from '../models/NodePatchOut';
import type { NodeTransitionType } from '../models/NodeTransitionType';
import type { NodeTransitionUpdate } from '../models/NodeTransitionUpdate';
import type { NodeUpdate } from '../models/NodeUpdate';
import type { NotificationRules } from '../models/NotificationRules';
import type { PopularityRecomputeRequest } from '../models/PopularityRecomputeRequest';
import type { PreviewLinkRequest } from '../models/PreviewLinkRequest';
import type { QuestCreateIn } from '../models/QuestCreateIn';
import type { QuestGraphIn } from '../models/QuestGraphIn';
import type { QuestStepCreate } from '../models/QuestStepCreate';
import type { QuestStepOut } from '../models/QuestStepOut';
import type { QuestStepPage } from '../models/QuestStepPage';
import type { QuestStepPatch } from '../models/QuestStepPatch';
import type { QuestStepUpdate } from '../models/QuestStepUpdate';
import type { QuestSummary } from '../models/QuestSummary';
import type { QuestTransitionCreate } from '../models/QuestTransitionCreate';
import type { QuestTransitionOut } from '../models/QuestTransitionOut';
import type { QueueItem } from '../models/QueueItem';
import type { QueueStats } from '../models/QueueStats';
import type { RateLimitDisablePayload } from '../models/RateLimitDisablePayload';
import type { RelevanceApplyOut } from '../models/RelevanceApplyOut';
import type { RelevanceGetOut } from '../models/RelevanceGetOut';
import type { RelevancePutIn } from '../models/RelevancePutIn';
import type { ReliabilityMetrics } from '../models/ReliabilityMetrics';
import type { RestrictionAdminCreate } from '../models/RestrictionAdminCreate';
import type { RestrictionAdminUpdate } from '../models/RestrictionAdminUpdate';
import type { RestrictionOut } from '../models/RestrictionOut';
import type { RuleUpdatePayload } from '../models/RuleUpdatePayload';
import type { SchedulePublishIn } from '../models/SchedulePublishIn';
import type { SearchOverviewOut } from '../models/SearchOverviewOut';
import type { SearchTopQuery } from '../models/SearchTopQuery';
import type { SendNotificationPayload } from '../models/SendNotificationPayload';
import type { SimulateIn } from '../models/SimulateIn';
import type { SimulateResult } from '../models/SimulateResult';
import type { Status } from '../models/Status';
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
     * Resolve Alert
     * Mark alert resolved.
     * @param alertId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static resolveAlertAdminOpsAlertsAlertIdResolvePost(
        alertId: string,
    ): CancelablePromise<{
        status: string;
    }> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/ops/alerts/{alert_id}/resolve',
            path: {
                'alert_id': alertId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                502: `Bad Gateway`,
            },
        });
    }
    /**
     * Get Status
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getStatusAdminOpsStatusGet(
        accountId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ops/status',
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
     * Get Limits
     * @param accountId
     * @returns number Successful Response
     * @throws ApiError
     */
    public static getLimitsAdminOpsLimitsGet(
        accountId?: (string | null),
    ): CancelablePromise<Record<string, number>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ops/limits',
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
        requestBody?: Body_embedding_test_admin_embedding_test_post,
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
     * @param accountId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createQuestAdminQuestsCreatePost(
        accountId: string,
        requestBody: QuestCreateIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/create',
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
     * Quest with versions
     * @param questId
     * @param accountId
     * @returns QuestSummary Successful Response
     * @throws ApiError
     */
    public static getQuestAdminQuestsQuestIdGet(
        questId: string,
        accountId: string,
    ): CancelablePromise<QuestSummary> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{quest_id}',
            path: {
                'quest_id': questId,
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
     * Create a draft version
     * @param questId
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createDraftAdminQuestsQuestIdDraftPost(
        questId: string,
        accountId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/{quest_id}/draft',
            path: {
                'quest_id': questId,
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
     * Get version graph
     * @param versionId
     * @returns app__domains__quests__schemas__graph__QuestGraphOut Successful Response
     * @throws ApiError
     */
    public static getVersionAdminQuestsVersionsVersionIdGet(
        versionId: string,
    ): CancelablePromise<app__domains__quests__schemas__graph__QuestGraphOut> {
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
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteDraftAdminQuestsVersionsVersionIdDelete(
        versionId: string,
        accountId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/quests/versions/{version_id}',
            path: {
                'version_id': versionId,
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
     * @param accountId
     * @returns ValidateResult Successful Response
     * @throws ApiError
     */
    public static validateVersionAdminQuestsVersionsVersionIdValidatePost(
        versionId: string,
        accountId: string,
    ): CancelablePromise<ValidateResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/validate',
            path: {
                'version_id': versionId,
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
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static publishVersionAdminQuestsVersionsVersionIdPublishPost(
        versionId: string,
        accountId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/publish',
            path: {
                'version_id': versionId,
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
     * @param accountId
     * @param requestBody
     * @returns SimulateResult Successful Response
     * @throws ApiError
     */
    public static simulateVersionAdminQuestsVersionsVersionIdSimulatePost(
        versionId: string,
        accountId: string,
        requestBody: SimulateIn,
    ): CancelablePromise<SimulateResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/simulate',
            path: {
                'version_id': versionId,
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
     * List Queue
     * @param type
     * @param status
     * @returns QueueItem Successful Response
     * @throws ApiError
     */
    public static listQueueAdminModerationQueueGet(
        type?: (string | null),
        status?: (string | null),
    ): CancelablePromise<Array<QueueItem>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/moderation/queue',
            query: {
                'type': type,
                'status': status,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Queue Item
     * @param itemId
     * @returns QueueItem Successful Response
     * @throws ApiError
     */
    public static getQueueItemAdminModerationQueueItemIdGet(
        itemId: string,
    ): CancelablePromise<QueueItem> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/moderation/queue/{item_id}',
            path: {
                'item_id': itemId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Approve Item
     * @param itemId
     * @returns string Successful Response
     * @throws ApiError
     */
    public static approveItemAdminModerationQueueItemIdApprovePost(
        itemId: string,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/moderation/queue/{item_id}/approve',
            path: {
                'item_id': itemId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Reject Item
     * @param itemId
     * @returns string Successful Response
     * @throws ApiError
     */
    public static rejectItemAdminModerationQueueItemIdRejectPost(
        itemId: string,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/moderation/queue/{item_id}/reject',
            path: {
                'item_id': itemId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Hide Node
     * @param accountId
     * @param slug
     * @param requestBody
     * @returns string Successful Response
     * @throws ApiError
     */
    public static hideNodeAdminAccountsAccountIdModerationNodesSlugHidePost(
        accountId: string,
        slug: string,
        requestBody: HidePayload,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/moderation/nodes/{slug}/hide',
            path: {
                'account_id': accountId,
                'slug': slug,
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
     * Restore Node
     * @param accountId
     * @param slug
     * @returns string Successful Response
     * @throws ApiError
     */
    public static restoreNodeAdminAccountsAccountIdModerationNodesSlugRestorePost(
        accountId: string,
        slug: string,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/moderation/nodes/{slug}/restore',
            path: {
                'account_id': accountId,
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
     * List Cases
     * @param page
     * @param size
     * @returns CaseListResponse Successful Response
     * @throws ApiError
     */
    public static listCasesAdminModerationCasesGet(
        page: number = 1,
        size: number = 20,
    ): CancelablePromise<CaseListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/moderation/cases',
            query: {
                'page': page,
                'size': size,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Case
     * @param requestBody
     * @returns string Successful Response
     * @throws ApiError
     */
    public static createCaseAdminModerationCasesPost(
        requestBody: CaseCreate,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/moderation/cases',
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
     * Get Case
     * @param caseId
     * @returns CaseFullResponse Successful Response
     * @throws ApiError
     */
    public static getCaseAdminModerationCasesCaseIdGet(
        caseId: string,
    ): CancelablePromise<CaseFullResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/moderation/cases/{case_id}',
            path: {
                'case_id': caseId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Patch Case
     * @param caseId
     * @param requestBody
     * @returns CaseOut Successful Response
     * @throws ApiError
     */
    public static patchCaseAdminModerationCasesCaseIdPatch(
        caseId: string,
        requestBody: CasePatch,
    ): CancelablePromise<CaseOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/moderation/cases/{case_id}',
            path: {
                'case_id': caseId,
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
     * Add Note
     * @param caseId
     * @param requestBody
     * @returns CaseNoteOut Successful Response
     * @throws ApiError
     */
    public static addNoteAdminModerationCasesCaseIdNotesPost(
        caseId: string,
        requestBody: CaseNoteCreate,
    ): CancelablePromise<CaseNoteOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/moderation/cases/{case_id}/notes',
            path: {
                'case_id': caseId,
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
     * Close Case
     * @param caseId
     * @param requestBody
     * @returns string Successful Response
     * @throws ApiError
     */
    public static closeCaseAdminModerationCasesCaseIdActionsClosePost(
        caseId: string,
        requestBody: CaseClose,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/moderation/cases/{case_id}/actions/close',
            path: {
                'case_id': caseId,
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
     * Create campaign
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createCampaignAdminNotificationsCampaignsPost(
        requestBody: CampaignCreate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/notifications/campaigns',
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
     * Delete campaign
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteCampaignAdminNotificationsCampaignsCampaignIdDelete(
        campaignId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
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
     * List achievements (admin)
     * @param accountId
     * @returns AchievementAdminOut Successful Response
     * @throws ApiError
     */
    public static listAchievementsAdminAdminAchievementsGet(
        accountId: string,
    ): CancelablePromise<Array<AchievementAdminOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/achievements',
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
     * Create achievement
     * @param accountId
     * @param requestBody
     * @returns AchievementAdminOut Successful Response
     * @throws ApiError
     */
    public static createAchievementAdminAdminAchievementsPost(
        accountId: string,
        requestBody: AchievementCreateIn,
    ): CancelablePromise<AchievementAdminOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/achievements',
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
     * Update achievement
     * @param achievementId
     * @param accountId
     * @param requestBody
     * @returns AchievementAdminOut Successful Response
     * @throws ApiError
     */
    public static updateAchievementAdminAdminAchievementsAchievementIdPatch(
        achievementId: string,
        accountId: string,
        requestBody: AchievementUpdateIn,
    ): CancelablePromise<AchievementAdminOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/achievements/{achievement_id}',
            path: {
                'achievement_id': achievementId,
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
     * Delete achievement
     * @param achievementId
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteAchievementAdminAdminAchievementsAchievementIdDelete(
        achievementId: string,
        accountId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/achievements/{achievement_id}',
            path: {
                'achievement_id': achievementId,
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
     * Grant achievement to user
     * @param achievementId
     * @param accountId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static grantAchievementAdminAchievementsAchievementIdGrantPost(
        achievementId: string,
        accountId: string,
        requestBody: UserIdIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/achievements/{achievement_id}/grant',
            path: {
                'achievement_id': achievementId,
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
     * Revoke achievement from user
     * @param achievementId
     * @param accountId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static revokeAchievementAdminAchievementsAchievementIdRevokePost(
        achievementId: string,
        accountId: string,
        requestBody: UserIdIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/achievements/{achievement_id}/revoke',
            path: {
                'achievement_id': achievementId,
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
     * Navigation problems
     * @returns NavigationNodeProblem Successful Response
     * @throws ApiError
     */
    public static navigationProblemsAdminNavigationProblemsGet(): CancelablePromise<Array<NavigationNodeProblem>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/navigation/problems',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
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
     * Create Preview Link Get
     * @param accountId
     * @param ttl
     * @returns string Successful Response
     * @throws ApiError
     */
    public static createPreviewLinkGetAdminPreviewLinkGet(
        accountId: string,
        ttl?: (number | null),
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/preview/link',
            query: {
                'account_id': accountId,
                'ttl': ttl,
            },
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
     * Get recent background jobs
     * @returns BackgroundJobHistoryOut Successful Response
     * @throws ApiError
     */
    public static recentJobsAdminJobsRecentGet(): CancelablePromise<Array<BackgroundJobHistoryOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/jobs/recent',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Get queue sizes
     * @returns QueueStats Successful Response
     * @throws ApiError
     */
    public static queueSizesAdminJobsQueuesGet(): CancelablePromise<Record<string, QueueStats>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/jobs/queues',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
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
     * List node patches
     * @param nodeId
     * @returns NodePatchDiffOut Successful Response
     * @throws ApiError
     */
    public static listPatchesAdminHotfixPatchesGet(
        nodeId?: (number | null),
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
        patchId: number,
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
        patchId: number,
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
     * List accounts
     * @returns AccountWithRoleOut Successful Response
     * @throws ApiError
     */
    public static listAccountsAdminAccountsGet(): CancelablePromise<Array<AccountWithRoleOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Create account
     * @param requestBody
     * @returns AccountOut Successful Response
     * @throws ApiError
     */
    public static createAccountAdminAccountsPost(
        requestBody: AccountIn,
    ): CancelablePromise<AccountOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts',
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
     * Get account
     * @param accountId
     * @returns AccountOut Successful Response
     * @throws ApiError
     */
    public static getAccountAdminAccountsAccountIdGet(
        accountId: string,
    ): CancelablePromise<AccountOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}',
            path: {
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
     * Update account
     * @param accountId
     * @param requestBody
     * @returns AccountOut Successful Response
     * @throws ApiError
     */
    public static updateAccountAdminAccountsAccountIdPatch(
        accountId: string,
        requestBody: AccountUpdate,
    ): CancelablePromise<AccountOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/accounts/{account_id}',
            path: {
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
     * Delete account
     * @param accountId
     * @returns void
     * @throws ApiError
     */
    public static deleteAccountAdminAccountsAccountIdDelete(
        accountId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/accounts/{account_id}',
            path: {
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
     * Add account member
     * @param accountId
     * @param requestBody
     * @returns AccountMemberOut Successful Response
     * @throws ApiError
     */
    public static addMemberAdminAccountsAccountIdMembersPost(
        accountId: string,
        requestBody: AccountMemberIn,
    ): CancelablePromise<AccountMemberOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/members',
            path: {
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
     * List account members
     * @param accountId
     * @returns AccountMemberOut Successful Response
     * @throws ApiError
     */
    public static listMembersAdminAccountsAccountIdMembersGet(
        accountId: string,
    ): CancelablePromise<Array<AccountMemberOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/members',
            path: {
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
     * Update account member
     * @param accountId
     * @param userId
     * @param requestBody
     * @returns AccountMemberOut Successful Response
     * @throws ApiError
     */
    public static updateMemberAdminAccountsAccountIdMembersUserIdPatch(
        accountId: string,
        userId: string,
        requestBody: AccountMemberIn,
    ): CancelablePromise<AccountMemberOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/accounts/{account_id}/members/{user_id}',
            path: {
                'account_id': accountId,
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
     * Remove account member
     * @param accountId
     * @param userId
     * @returns void
     * @throws ApiError
     */
    public static removeMemberAdminAccountsAccountIdMembersUserIdDelete(
        accountId: string,
        userId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/accounts/{account_id}/members/{user_id}',
            path: {
                'account_id': accountId,
                'user_id': userId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get account AI presets
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAiPresetsAdminAccountsAccountIdSettingsAiPresetsGet(
        accountId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/settings/ai-presets',
            path: {
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
     * Update account AI presets
     * @param accountId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static putAiPresetsAdminAccountsAccountIdSettingsAiPresetsPut(
        accountId: string,
        requestBody: Record<string, any>,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/accounts/{account_id}/settings/ai-presets',
            path: {
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
     * Get account notification rules
     * @param accountId
     * @returns NotificationRules Successful Response
     * @throws ApiError
     */
    public static getNotificationsAdminAccountsAccountIdSettingsNotificationsGet(
        accountId: string,
    ): CancelablePromise<NotificationRules> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/settings/notifications',
            path: {
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
     * Update account notification rules
     * @param accountId
     * @param requestBody
     * @returns NotificationRules Successful Response
     * @throws ApiError
     */
    public static putNotificationsAdminAccountsAccountIdSettingsNotificationsPut(
        accountId: string,
        requestBody: NotificationRules,
    ): CancelablePromise<NotificationRules> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/accounts/{account_id}/settings/notifications',
            path: {
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
     * Get account limits
     * @param accountId
     * @returns number Successful Response
     * @throws ApiError
     */
    public static getLimitsAdminAccountsAccountIdSettingsLimitsGet(
        accountId: string,
    ): CancelablePromise<Record<string, number>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/settings/limits',
            path: {
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
     * Update account limits
     * @param accountId
     * @param requestBody
     * @returns number Successful Response
     * @throws ApiError
     */
    public static putLimitsAdminAccountsAccountIdSettingsLimitsPut(
        accountId: string,
        requestBody: Record<string, number>,
    ): CancelablePromise<Record<string, number>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/accounts/{account_id}/settings/limits',
            path: {
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
     * Get account AI usage
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getAccountUsageAdminAccountsAccountIdUsageGet(
        accountId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/usage',
            path: {
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
     * Get node item by id
     * @param nodeId
     * @param accountId
     * @returns AdminNodeOut Successful Response
     * @throws ApiError
     */
    public static getNodeByIdAdminAccountsAccountIdNodesNodeIdGet(
        nodeId: number,
        accountId: string,
    ): CancelablePromise<AdminNodeOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/nodes/{node_id}',
            path: {
                'node_id': nodeId,
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
     * Update node item by id
     * @param nodeId
     * @param accountId
     * @param requestBody
     * @param next
     * @returns AdminNodeOut Successful Response
     * @throws ApiError
     */
    public static updateNodeByIdAdminAccountsAccountIdNodesNodeIdPatch(
        nodeId: number,
        accountId: string,
        requestBody: Record<string, any>,
        next?: number,
    ): CancelablePromise<AdminNodeOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/accounts/{account_id}/nodes/{node_id}',
            path: {
                'node_id': nodeId,
                'account_id': accountId,
            },
            query: {
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
     * Replace node item by id
     * @param nodeId
     * @param accountId
     * @param requestBody
     * @param next
     * @returns AdminNodeOut Successful Response
     * @throws ApiError
     */
    public static replaceNodeByIdAdminAccountsAccountIdNodesNodeIdPut(
        nodeId: number,
        accountId: string,
        requestBody: Record<string, any>,
        next?: number,
    ): CancelablePromise<AdminNodeOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/accounts/{account_id}/nodes/{node_id}',
            path: {
                'node_id': nodeId,
                'account_id': accountId,
            },
            query: {
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
     * Publish node item by id
     * @param nodeId
     * @param accountId
     * @param requestBody
     * @returns AdminNodeOut Successful Response
     * @throws ApiError
     */
    public static publishNodeByIdAdminAccountsAccountIdNodesNodeIdPublishPost(
        nodeId: number,
        accountId: string,
        requestBody?: (app__domains__nodes__content_admin_router__PublishIn | null),
    ): CancelablePromise<AdminNodeOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/nodes/{node_id}/publish',
            path: {
                'node_id': nodeId,
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
     * List nodes by type
     * @param nodeType
     * @param accountId
     * @param page
     * @param perPage
     * @param q
     * @returns AdminNodeList Successful Response
     * @throws ApiError
     */
    public static listNodesAdminAccountsAccountIdNodesTypesNodeTypeGet(
        nodeType: string,
        accountId: string,
        page: number = 1,
        perPage: number = 10,
        q?: (string | null),
    ): CancelablePromise<AdminNodeList> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/nodes/types/{node_type}',
            path: {
                'node_type': nodeType,
                'account_id': accountId,
            },
            query: {
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
     * @param accountId
     * @returns AdminNodeOut Successful Response
     * @throws ApiError
     */
    public static createNodeAdminAccountsAccountIdNodesTypesNodeTypePost(
        nodeType: string,
        accountId: string,
    ): CancelablePromise<AdminNodeOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/nodes/types/{node_type}',
            path: {
                'node_type': nodeType,
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
     * Get node item
     * @param nodeType
     * @param nodeId
     * @param accountId
     * @returns AdminNodeOut Successful Response
     * @throws ApiError
     */
    public static getNodeAdminAccountsAccountIdNodesTypesNodeTypeNodeIdGet(
        nodeType: string,
        nodeId: number,
        accountId: string,
    ): CancelablePromise<AdminNodeOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/nodes/types/{node_type}/{node_id}',
            path: {
                'node_type': nodeType,
                'node_id': nodeId,
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
     * Update node item
     * @param nodeType
     * @param nodeId
     * @param accountId
     * @param requestBody
     * @param next
     * @returns AdminNodeOut Successful Response
     * @throws ApiError
     */
    public static updateNodeAdminAccountsAccountIdNodesTypesNodeTypeNodeIdPatch(
        nodeType: string,
        nodeId: number,
        accountId: string,
        requestBody: Record<string, any>,
        next?: number,
    ): CancelablePromise<AdminNodeOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/accounts/{account_id}/nodes/types/{node_type}/{node_id}',
            path: {
                'node_type': nodeType,
                'node_id': nodeId,
                'account_id': accountId,
            },
            query: {
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
     * @param accountId
     * @param requestBody
     * @returns AdminNodeOut Successful Response
     * @throws ApiError
     */
    public static publishNodeAdminAccountsAccountIdNodesTypesNodeTypeNodeIdPublishPost(
        nodeType: string,
        nodeId: number,
        accountId: string,
        requestBody?: (app__domains__nodes__content_admin_router__PublishIn | null),
    ): CancelablePromise<AdminNodeOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/nodes/types/{node_type}/{node_id}/publish',
            path: {
                'node_type': nodeType,
                'node_id': nodeId,
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
     * Publish node item (PATCH alias)
     * @param nodeType
     * @param nodeId
     * @param accountId
     * @param requestBody
     * @returns AdminNodeOut Successful Response
     * @throws ApiError
     */
    public static publishNodePatchAdminAccountsAccountIdNodesTypesNodeTypeNodeIdPublishPatch(
        nodeType: string,
        nodeId: number,
        accountId: string,
        requestBody?: (app__domains__nodes__content_admin_router__PublishIn | null),
    ): CancelablePromise<AdminNodeOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/accounts/{account_id}/nodes/types/{node_type}/{node_id}/publish',
            path: {
                'node_type': nodeType,
                'node_id': nodeId,
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
     * Create article (admin)
     * @param accountId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createArticleAdminAccountsAccountIdArticlesPost(
        accountId: string,
        requestBody?: (Record<string, any> | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/articles',
            path: {
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
     * Get article (admin)
     * @param nodeId
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getArticleAdminAccountsAccountIdArticlesNodeIdGet(
        nodeId: number,
        accountId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/articles/{node_id}',
            path: {
                'node_id': nodeId,
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
     * Update article (admin)
     * @param nodeId
     * @param accountId
     * @param requestBody
     * @param next
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateArticleAdminAccountsAccountIdArticlesNodeIdPatch(
        nodeId: number,
        accountId: string,
        requestBody: Record<string, any>,
        next?: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/accounts/{account_id}/articles/{node_id}',
            path: {
                'node_id': nodeId,
                'account_id': accountId,
            },
            query: {
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
     * Publish article (admin)
     * @param nodeId
     * @param accountId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static publishArticleAdminAccountsAccountIdArticlesNodeIdPublishPost(
        nodeId: number,
        accountId: string,
        requestBody?: (app__domains__nodes__api__articles_admin_router__PublishIn | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/articles/{node_id}/publish',
            path: {
                'node_id': nodeId,
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
     * List nodes (admin)
     * List nodes in account.
     *
     * See :class:`AdminNodeListParams` for available query parameters.
     * @param accountId
     * @param author
     * @param sort
     * @param status
     * @param visible
     * @param premiumOnly
     * @param recommendable
     * @param limit
     * @param offset
     * @param dateFrom
     * @param dateTo
     * @param q
     * @param ifNoneMatch
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static listNodesAdminAdminAccountsAccountIdNodesGet(
        accountId: string,
        author?: (string | null),
        sort: 'updated_desc' | 'created_desc' | 'created_asc' | 'views_desc' = 'updated_desc',
        status?: (Status | null),
        visible?: (boolean | null),
        premiumOnly?: (boolean | null),
        recommendable?: (boolean | null),
        limit: number = 25,
        offset?: number,
        dateFrom?: (string | null),
        dateTo?: (string | null),
        q?: (string | null),
        ifNoneMatch?: (string | null),
    ): CancelablePromise<Array<NodeOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/nodes',
            path: {
                'account_id': accountId,
            },
            headers: {
                'If-None-Match': ifNoneMatch,
            },
            query: {
                'author': author,
                'sort': sort,
                'status': status,
                'visible': visible,
                'premium_only': premiumOnly,
                'recommendable': recommendable,
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
     * Create node (admin)
     * @param accountId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createNodeAdminAdminAccountsAccountIdNodesPost(
        accountId: string,
        requestBody?: (Record<string, any> | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/nodes',
            path: {
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
     * Bulk node operations
     * @param accountId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkNodeOperationAdminAccountsAccountIdNodesBulkPost(
        accountId: string,
        requestBody: NodeBulkOperation,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/nodes/bulk',
            path: {
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
     * Bulk update nodes
     * @param accountId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkPatchNodesAdminAccountsAccountIdNodesBulkPatch(
        accountId: string,
        requestBody: NodeBulkPatch,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/accounts/{account_id}/nodes/bulk',
            path: {
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
     * Get node by ID (admin, full)
     * Единая точка для загрузки полной ноды по ID (числовой node.id).
     * Делегирует обработку в контент‑роутер, который самостоятельно
     * резолвит идентификатор контента.
     * @param accountId
     * @param id
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getNodeByIdAdminAdminAccountsAccountIdNodesIdGet(
        accountId: string,
        id: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/nodes/{id}',
            path: {
                'account_id': accountId,
                'id': id,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update node by ID (admin, full)
     * Обновление полной ноды по числовому ID с возвратом полного объекта.
     * Делегируем в контент‑роутер, который резолвит идентификатор контента.
     * @param accountId
     * @param id
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateNodeByIdAdminAdminAccountsAccountIdNodesIdPatch(
        accountId: string,
        id: number,
        requestBody: Record<string, any>,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/accounts/{account_id}/nodes/{id}',
            path: {
                'account_id': accountId,
                'id': id,
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
     * Publish node by ID (admin)
     * Публикация ноды по числовому ID. Возвращает обновлённую полную ноду.
     * Делегируем в контент‑роутер, который резолвит идентификатор контента.
     * @param accountId
     * @param id
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static publishNodeByIdAdminAdminAccountsAccountIdNodesIdPublishPost(
        accountId: string,
        id: number,
        requestBody?: (Record<string, any> | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/nodes/{id}/publish',
            path: {
                'account_id': accountId,
                'id': id,
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
     * Publish status and schedule (admin)
     * Возвращает статус публикации и запланированную публикацию.
     * @param accountId
     * @param id
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPublishInfoAdminAccountsAccountIdNodesIdPublishInfoGet(
        accountId: string,
        id: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/accounts/{account_id}/nodes/{id}/publish_info',
            path: {
                'account_id': accountId,
                'id': id,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Schedule publish by date/time (admin)
     * Создаёт или заменяет задание на публикацию.
     * @param accountId
     * @param id
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static schedulePublishAdminAccountsAccountIdNodesIdSchedulePublishPost(
        accountId: string,
        id: number,
        requestBody: SchedulePublishIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/accounts/{account_id}/nodes/{id}/schedule_publish',
            path: {
                'account_id': accountId,
                'id': id,
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
     * Cancel scheduled publish (admin)
     * @param accountId
     * @param id
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelScheduledPublishAdminAccountsAccountIdNodesIdSchedulePublishDelete(
        accountId: string,
        id: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/accounts/{account_id}/nodes/{id}/schedule_publish',
            path: {
                'account_id': accountId,
                'id': id,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get global node by ID
     * @param nodeId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static getGlobalNodeByIdAdminNodesNodeIdGet(
        nodeId: number,
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/nodes/{node_id}',
            path: {
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
     * Update global node by ID
     * @param nodeId
     * @param requestBody
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static updateGlobalNodeByIdAdminNodesNodeIdPut(
        nodeId: number,
        requestBody: NodeUpdate,
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/nodes/{node_id}',
            path: {
                'node_id': nodeId,
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
     * List drafts with missing fields
     * @param limit
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listDraftIssuesAdminDraftsIssuesGet(
        limit: number = 5,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/drafts/issues',
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
     * List quest steps
     * @param questId
     * @param limit
     * @param offset
     * @returns QuestStepPage Successful Response
     * @throws ApiError
     */
    public static listStepsAdminQuestsQuestIdStepsGet(
        questId: string,
        limit: number = 25,
        offset?: number,
    ): CancelablePromise<QuestStepPage> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{quest_id}/steps',
            path: {
                'quest_id': questId,
            },
            query: {
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
     * Create quest step
     * @param questId
     * @param requestBody
     * @returns QuestStepOut Successful Response
     * @throws ApiError
     */
    public static createStepAdminQuestsQuestIdStepsPost(
        questId: string,
        requestBody: QuestStepCreate,
    ): CancelablePromise<QuestStepOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/{quest_id}/steps',
            path: {
                'quest_id': questId,
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
     * Get quest step
     * @param questId
     * @param stepId
     * @returns QuestStepOut Successful Response
     * @throws ApiError
     */
    public static getStepAdminQuestsQuestIdStepsStepIdGet(
        questId: string,
        stepId: string,
    ): CancelablePromise<QuestStepOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{quest_id}/steps/{step_id}',
            path: {
                'quest_id': questId,
                'step_id': stepId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Replace quest step
     * @param questId
     * @param stepId
     * @param requestBody
     * @returns QuestStepOut Successful Response
     * @throws ApiError
     */
    public static putStepAdminQuestsQuestIdStepsStepIdPut(
        questId: string,
        stepId: string,
        requestBody: QuestStepUpdate,
    ): CancelablePromise<QuestStepOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/admin/quests/{quest_id}/steps/{step_id}',
            path: {
                'quest_id': questId,
                'step_id': stepId,
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
     * Update quest step
     * @param questId
     * @param stepId
     * @param requestBody
     * @returns QuestStepOut Successful Response
     * @throws ApiError
     */
    public static patchStepAdminQuestsQuestIdStepsStepIdPatch(
        questId: string,
        stepId: string,
        requestBody: QuestStepPatch,
    ): CancelablePromise<QuestStepOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/quests/{quest_id}/steps/{step_id}',
            path: {
                'quest_id': questId,
                'step_id': stepId,
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
     * Delete quest step
     * @param questId
     * @param stepId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteStepAdminQuestsQuestIdStepsStepIdDelete(
        questId: string,
        stepId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/quests/{quest_id}/steps/{step_id}',
            path: {
                'quest_id': questId,
                'step_id': stepId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List transitions from step
     * @param questId
     * @param stepId
     * @returns QuestTransitionOut Successful Response
     * @throws ApiError
     */
    public static listTransitionsAdminQuestsQuestIdStepsStepIdTransitionsGet(
        questId: string,
        stepId: string,
    ): CancelablePromise<Array<QuestTransitionOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{quest_id}/steps/{step_id}/transitions',
            path: {
                'quest_id': questId,
                'step_id': stepId,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create transition
     * @param questId
     * @param stepId
     * @param requestBody
     * @returns QuestTransitionOut Successful Response
     * @throws ApiError
     */
    public static createTransitionAdminQuestsQuestIdStepsStepIdTransitionsPost(
        questId: string,
        stepId: string,
        requestBody: QuestTransitionCreate,
    ): CancelablePromise<QuestTransitionOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/{quest_id}/steps/{step_id}/transitions',
            path: {
                'quest_id': questId,
                'step_id': stepId,
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
     * @param questId
     * @param stepId
     * @param transitionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteTransitionAdminQuestsQuestIdStepsStepIdTransitionsTransitionIdDelete(
        questId: string,
        stepId: string,
        transitionId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/quests/{quest_id}/steps/{step_id}/transitions/{transition_id}',
            path: {
                'quest_id': questId,
                'step_id': stepId,
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
     * Get quest graph
     * @param questId
     * @returns app__api__admin__quests__steps__QuestGraphOut Successful Response
     * @throws ApiError
     */
    public static getGraphAdminQuestsQuestIdGraphGet(
        questId: string,
    ): CancelablePromise<app__api__admin__quests__steps__QuestGraphOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{quest_id}/graph',
            path: {
                'quest_id': questId,
            },
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
     * @param accountId
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
        accountId?: (string | null),
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
                'account_id': accountId,
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
    /**
     * Top search queries
     * @returns SearchTopQuery Successful Response
     * @throws ApiError
     */
    public static getTopAdminSearchTopGet(): CancelablePromise<Array<SearchTopQuery>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/search/top',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Metrics Reliability
     * @param account
     * @returns ReliabilityMetrics Successful Response
     * @throws ApiError
     */
    public static metricsReliabilityAdminMetricsReliabilityGet(
        account?: string,
    ): CancelablePromise<ReliabilityMetrics> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/metrics/reliability',
            query: {
                'account': account,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Estimate campaign recipients
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static estimateCampaignAdminNotificationsCampaignsEstimatePost(
        requestBody: CampaignFilters,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/notifications/campaigns/estimate',
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
     * Cancel campaign
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelCampaignAdminNotificationsCampaignsCampaignIdCancelPost(
        campaignId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/notifications/campaigns/{campaign_id}/cancel',
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
     * Start campaign
     * @param campaignId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static startCampaignAdminNotificationsCampaignsCampaignIdStartPost(
        campaignId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/notifications/campaigns/{campaign_id}/start',
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
}
