/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CharacterIn } from '../models/CharacterIn';
import type { CharacterOut } from '../models/CharacterOut';
import type { GenerateQuestIn } from '../models/GenerateQuestIn';
import type { GenerationEnqueued } from '../models/GenerationEnqueued';
import type { GenerationJobOut } from '../models/GenerationJobOut';
import type { Paginated_dict_ } from '../models/Paginated_dict_';
import type { WorldTemplateIn } from '../models/WorldTemplateIn';
import type { WorldTemplateOut } from '../models/WorldTemplateOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminAiQuestsService {
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
     * Get Generation Job Logs
     * @param jobId
     * @param limit
     * @param clip
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getGenerationJobLogsAdminAiQuestsJobsJobIdLogsGet(
        jobId: string,
        limit: number = 200,
        clip: number = 5000,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/jobs/{job_id}/logs',
            path: {
                'job_id': jobId,
            },
            query: {
                'limit': limit,
                'clip': clip,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Generation Job Details
     * @param jobId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getGenerationJobDetailsAdminAiQuestsJobsJobIdDetailsGet(
        jobId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/jobs/{job_id}/details',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Jobs Paged
     * @param page
     * @param perPage
     * @param status
     * @returns Paginated_dict_ Successful Response
     * @throws ApiError
     */
    public static listJobsPagedAdminAiQuestsJobsPagedGet(
        page: number = 1,
        perPage: number = 20,
        status?: (string | null),
    ): CancelablePromise<Paginated_dict_> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/jobs_paged',
            query: {
                'page': page,
                'per_page': perPage,
                'status': status,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Jobs Cursor
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listJobsCursorAdminAiQuestsJobsCursorGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/jobs_cursor',
        });
    }
    /**
     * Get Rate Limits
     * Текущие рантайм-лимиты RPM по провайдерам и моделям (оверрайды).
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getRateLimitsAdminAiQuestsRateLimitsGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/ai/quests/rate_limits',
        });
    }
    /**
     * Set Rate Limits
     * Установить рантайм-лимиты RPM.
     * Формат:
     * {
         * "providers": { "openai": 60, "anthropic": 30, "openai_compatible": 45 },
         * "models": { "gpt-4o-mini": 120, "claude-3-haiku": 100 }
         * }
         * Значения null/0/"" — удаляют оверрайд.
         * @param requestBody
         * @returns any Successful Response
         * @throws ApiError
         */
        public static setRateLimitsAdminAiQuestsRateLimitsPost(
            requestBody: Record<string, any>,
        ): CancelablePromise<Record<string, any>> {
            return __request(OpenAPI, {
                method: 'POST',
                url: '/admin/ai/quests/rate_limits',
                body: requestBody,
                mediaType: 'application/json',
                errors: {
                    422: `Validation Error`,
                },
            });
        }
        /**
         * Get Ai Worker Stats
         * Сводка по задачам/стадиям генерации: счётчики, среднее время, стоимость, токены.
         * @returns any Successful Response
         * @throws ApiError
         */
        public static getAiWorkerStatsAdminAiQuestsStatsGet(): CancelablePromise<Record<string, any>> {
            return __request(OpenAPI, {
                method: 'GET',
                url: '/admin/ai/quests/stats',
                errors: {
                    401: `Unauthorized`,
                    403: `Forbidden`,
                },
            });
        }
        /**
         * Get Version Validation
         * @param versionId
         * @param recalc Пересчитать отчёт принудительно
         * @returns any Successful Response
         * @throws ApiError
         */
        public static getVersionValidationAdminAiQuestsVersionsVersionIdValidationGet(
            versionId: string,
            recalc: boolean = false,
        ): CancelablePromise<Record<string, any>> {
            return __request(OpenAPI, {
                method: 'GET',
                url: '/admin/ai/quests/versions/{version_id}/validation',
                path: {
                    'version_id': versionId,
                },
                query: {
                    'recalc': recalc,
                },
                errors: {
                    422: `Validation Error`,
                },
            });
        }
    }
