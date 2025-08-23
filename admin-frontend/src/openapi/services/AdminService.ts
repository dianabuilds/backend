/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AdminEchoTraceOut } from '../models/AdminEchoTraceOut';
import type { AdminTransitionOut } from '../models/AdminTransitionOut';
import type { AdminUserOut } from '../models/AdminUserOut';
import type { AuditLogOut } from '../models/AuditLogOut';
import type { AutofixReport } from '../models/AutofixReport';
import type { AutofixRequest } from '../models/AutofixRequest';
import type { Body_embedding_test_admin_embedding_test_post } from '../models/Body_embedding_test_admin_embedding_test_post';
import type { BroadcastCreate } from '../models/BroadcastCreate';
import type { BulkIds } from '../models/BulkIds';
import type { CampaignUpdate } from '../models/CampaignUpdate';
import type { CharacterIn } from '../models/CharacterIn';
import type { CharacterOut } from '../models/CharacterOut';
import type { Status } from '../models/Status';
import type { FeatureFlagOut } from '../models/FeatureFlagOut';
import type { FeatureFlagUpdateIn } from '../models/FeatureFlagUpdateIn';
import type { GenerateQuestIn } from '../models/GenerateQuestIn';
import type { GenerationEnqueued } from '../models/GenerationEnqueued';
import type { GenerationJobOut } from '../models/GenerationJobOut';
import type { InvalidatePatternRequest } from '../models/InvalidatePatternRequest';
import type { MetricsSummary } from '../models/MetricsSummary';
import type { NodeBulkOperation } from '../models/NodeBulkOperation';
import type { NodeOut } from '../models/NodeOut';
import type { NodeTransitionType } from '../models/NodeTransitionType';
import type { NodeTransitionUpdate } from '../models/NodeTransitionUpdate';
import type { PopularityRecomputeRequest } from '../models/PopularityRecomputeRequest';
import type { PublishRequest } from '../models/PublishRequest';
import type { QuestCreateIn } from '../models/QuestCreateIn';
import type { QuestOut } from '../models/QuestOut';
import type { QuestSummary } from '../models/QuestSummary';
import type { QuestUpdate } from '../models/QuestUpdate';
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
import type { UserPremiumUpdate } from '../models/UserPremiumUpdate';
import type { UserRoleUpdate } from '../models/UserRoleUpdate';
import type { ValidateResult } from '../models/ValidateResult';
import type { ValidationReport } from '../models/ValidationReport';
import type { VersionGraphInput } from '../models/VersionGraphInput';
import type { VersionGraphOutput } from '../models/VersionGraphOutput';
import type { WorkspaceIn } from '../models/WorkspaceIn';
import type { WorkspaceMemberIn } from '../models/WorkspaceMemberIn';
import type { WorkspaceMemberOut } from '../models/WorkspaceMemberOut';
import type { WorkspaceOut } from '../models/WorkspaceOut';
import type { WorkspaceUpdate } from '../models/WorkspaceUpdate';
import type { WorldTemplateIn } from '../models/WorldTemplateIn';
import type { WorldTemplateOut } from '../models/WorldTemplateOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminService {
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
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createQuestAdminQuestsCreatePost(
        requestBody: QuestCreateIn,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/create',
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
     * @returns QuestSummary Successful Response
     * @throws ApiError
     */
    public static getQuestAdminQuestsQuestIdGet(
        questId: string,
    ): CancelablePromise<QuestSummary> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{quest_id}',
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
     * Create a draft version
     * @param questId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createDraftAdminQuestsQuestIdDraftPost(
        questId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/{quest_id}/draft',
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
     * Get version graph
     * @param versionId
     * @returns VersionGraphOutput Successful Response
     * @throws ApiError
     */
    public static getVersionAdminQuestsVersionsVersionIdGet(
        versionId: string,
    ): CancelablePromise<VersionGraphOutput> {
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
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteDraftAdminQuestsVersionsVersionIdDelete(
        versionId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
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
     * Replace graph of the version
     * @param versionId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static putGraphAdminQuestsVersionsVersionIdGraphPut(
        versionId: string,
        requestBody: VersionGraphInput,
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
     * @returns ValidateResult Successful Response
     * @throws ApiError
     */
    public static validateVersionAdminQuestsVersionsVersionIdValidatePost(
        versionId: string,
    ): CancelablePromise<ValidateResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/validate',
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
     * @returns any Successful Response
     * @throws ApiError
     */
    public static publishVersionAdminQuestsVersionsVersionIdPublishPost(
        versionId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/publish',
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
     * @param requestBody
     * @returns SimulateResult Successful Response
     * @throws ApiError
     */
    public static simulateVersionAdminQuestsVersionsVersionIdSimulatePost(
        versionId: string,
        requestBody: SimulateIn,
    ): CancelablePromise<SimulateResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/versions/{version_id}/simulate',
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
     * Admin list quests with filters
     * @param workspaceId
     * @param q
     * @param authorRole
     * @param authorId
     * @param draft
     * @param deleted
     * @param freeOnly
     * @param premiumOnly
     * @param length
     * @param createdFrom
     * @param createdTo
     * @param sortBy
     * @param page
     * @param perPage
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static adminListQuestsAdminQuestsGet(
        workspaceId: string,
        q?: (string | null),
        authorRole?: (string | null),
        authorId?: (string | null),
        draft?: (boolean | null),
        deleted?: (boolean | null),
        freeOnly: boolean = false,
        premiumOnly: boolean = false,
        length?: (string | null),
        createdFrom?: (string | null),
        createdTo?: (string | null),
        sortBy: string = 'new',
        page: number = 1,
        perPage: number = 20,
    ): CancelablePromise<Array<QuestOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests',
            query: {
                'workspace_id': workspaceId,
                'q': q,
                'author_role': authorRole,
                'author_id': authorId,
                'draft': draft,
                'deleted': deleted,
                'free_only': freeOnly,
                'premium_only': premiumOnly,
                'length': length,
                'created_from': createdFrom,
                'created_to': createdTo,
                'sort_by': sortBy,
                'page': page,
                'per_page': perPage,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get quest metadata
     * @param questId
     * @param workspaceId
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static getQuestMetaAdminQuestsQuestIdMetaGet(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{quest_id}/meta',
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
     * Update quest metadata
     * @param questId
     * @param workspaceId
     * @param requestBody
     * @returns QuestOut Successful Response
     * @throws ApiError
     */
    public static patchQuestMetaAdminQuestsQuestIdMetaPatch(
        questId: string,
        workspaceId: string,
        requestBody: QuestUpdate,
    ): CancelablePromise<QuestOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/quests/{quest_id}/meta',
            path: {
                'quest_id': questId,
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
     * Validate quest
     * @param questId
     * @param workspaceId
     * @returns ValidationReport Successful Response
     * @throws ApiError
     */
    public static getQuestValidationAdminQuestsQuestIdValidationGet(
        questId: string,
        workspaceId: string,
    ): CancelablePromise<ValidationReport> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/quests/{quest_id}/validation',
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
     * Apply autofix to quest
     * @param questId
     * @param workspaceId
     * @param requestBody
     * @returns AutofixReport Successful Response
     * @throws ApiError
     */
    public static postQuestAutofixAdminQuestsQuestIdAutofixPost(
        questId: string,
        workspaceId: string,
        requestBody: AutofixRequest,
    ): CancelablePromise<AutofixReport> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/{quest_id}/autofix',
            path: {
                'quest_id': questId,
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
     * Publish quest
     * @param questId
     * @param workspaceId
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static postQuestPublishAdminQuestsQuestIdPublishPost(
        questId: string,
        workspaceId: string,
        requestBody: PublishRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/quests/{quest_id}/publish',
            path: {
                'quest_id': questId,
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
     * List workspaces
     * @returns WorkspaceOut Successful Response
     * @throws ApiError
     */
    public static listWorkspacesAdminWorkspacesGet(): CancelablePromise<Array<WorkspaceOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/workspaces',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
            },
        });
    }
    /**
     * Create workspace
     * @param requestBody
     * @returns WorkspaceOut Successful Response
     * @throws ApiError
     */
    public static createWorkspaceAdminWorkspacesPost(
        requestBody: WorkspaceIn,
    ): CancelablePromise<WorkspaceOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/workspaces',
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
     * Get workspace
     * @param workspaceId
     * @returns WorkspaceOut Successful Response
     * @throws ApiError
     */
    public static getWorkspaceAdminWorkspacesWorkspaceIdGet(
        workspaceId: string,
    ): CancelablePromise<WorkspaceOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/workspaces/{workspace_id}',
            path: {
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
     * Update workspace
     * @param workspaceId
     * @param requestBody
     * @returns WorkspaceOut Successful Response
     * @throws ApiError
     */
    public static updateWorkspaceAdminWorkspacesWorkspaceIdPatch(
        workspaceId: string,
        requestBody: WorkspaceUpdate,
    ): CancelablePromise<WorkspaceOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/workspaces/{workspace_id}',
            path: {
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
     * Delete workspace
     * @param workspaceId
     * @returns void
     * @throws ApiError
     */
    public static deleteWorkspaceAdminWorkspacesWorkspaceIdDelete(
        workspaceId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/workspaces/{workspace_id}',
            path: {
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
     * Add workspace member
     * @param workspaceId
     * @param requestBody
     * @returns WorkspaceMemberOut Successful Response
     * @throws ApiError
     */
    public static addMemberAdminWorkspacesWorkspaceIdMembersPost(
        workspaceId: string,
        requestBody: WorkspaceMemberIn,
    ): CancelablePromise<WorkspaceMemberOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/workspaces/{workspace_id}/members',
            path: {
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
     * Update workspace member
     * @param workspaceId
     * @param userId
     * @param requestBody
     * @returns WorkspaceMemberOut Successful Response
     * @throws ApiError
     */
    public static updateMemberAdminWorkspacesWorkspaceIdMembersUserIdPatch(
        workspaceId: string,
        userId: string,
        requestBody: WorkspaceMemberIn,
    ): CancelablePromise<WorkspaceMemberOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/workspaces/{workspace_id}/members/{user_id}',
            path: {
                'workspace_id': workspaceId,
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
     * Remove workspace member
     * @param workspaceId
     * @param userId
     * @returns void
     * @throws ApiError
     */
    public static removeMemberAdminWorkspacesWorkspaceIdMembersUserIdDelete(
        workspaceId: string,
        userId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/admin/workspaces/{workspace_id}/members/{user_id}',
            path: {
                'workspace_id': workspaceId,
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
     * Content dashboard
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static contentDashboardAdminContentGet(
        workspaceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/content/',
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
     * List content items
     * @param workspaceId
     * @param contentType
     * @param status
     * @param tag
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listContentAdminContentAllGet(
        workspaceId: string,
        contentType?: (string | null),
        status?: (Status | null),
        tag?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/content/all',
            query: {
                'workspace_id': workspaceId,
                'content_type': contentType,
                'status': status,
                'tag': tag,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create content item
     * @param contentType
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createContentAdminContentContentTypePost(
        contentType: string,
        workspaceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/content/{content_type}',
            path: {
                'content_type': contentType,
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
     * Get content item
     * @param contentType
     * @param contentId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getContentAdminContentContentTypeContentIdGet(
        contentType: string,
        contentId: string,
        workspaceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/content/{content_type}/{content_id}',
            path: {
                'content_type': contentType,
                'content_id': contentId,
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
     * Update content item
     * @param contentType
     * @param contentId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateContentAdminContentContentTypeContentIdPatch(
        contentType: string,
        contentId: string,
        workspaceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/admin/content/{content_type}/{content_id}',
            path: {
                'content_type': contentType,
                'content_id': contentId,
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
     * Publish content item
     * @param contentType
     * @param contentId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static publishContentAdminContentContentTypeContentIdPublishPost(
        contentType: string,
        contentId: string,
        workspaceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/content/{content_type}/{content_id}/publish',
            path: {
                'content_type': contentType,
                'content_id': contentId,
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
     * Validate content item
     * @param contentType
     * @param contentId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static validateContentItemAdminContentContentTypeContentIdValidatePost(
        contentType: string,
        contentId: string,
        workspaceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/content/{content_type}/{content_id}/validate',
            path: {
                'content_type': contentType,
                'content_id': contentId,
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
     * List nodes (admin)
     * @param author
     * @param tags
     * @param match
     * @param isPublic
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
    public static listNodesAdminAdminNodesGet(
        author?: (string | null),
        tags?: (string | null),
        match: string = 'any',
        isPublic?: (boolean | null),
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
            url: '/admin/nodes',
            headers: {
                'If-None-Match': ifNoneMatch,
            },
            query: {
                'author': author,
                'tags': tags,
                'match': match,
                'is_public': isPublic,
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
     * Bulk node operations
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static bulkNodeOperationAdminNodesBulkPost(
        requestBody: NodeBulkOperation,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/nodes/bulk',
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
