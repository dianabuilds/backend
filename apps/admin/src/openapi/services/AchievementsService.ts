/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AchievementAdminOut } from '../models/AchievementAdminOut';
import type { AchievementCreateIn } from '../models/AchievementCreateIn';
import type { AchievementOut } from '../models/AchievementOut';
import type { AchievementUpdateIn } from '../models/AchievementUpdateIn';
import type { UserIdIn } from '../models/UserIdIn';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AchievementsService {
    /**
     * List achievements
     * @param workspaceId
     * @returns AchievementOut Successful Response
     * @throws ApiError
     */
    public static listAchievementsAchievementsGet(
        workspaceId: string,
    ): CancelablePromise<Array<AchievementOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/achievements',
            query: {
                'workspace_id': workspaceId,
            },
            errors: {
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
}
