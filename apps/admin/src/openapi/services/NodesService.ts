/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FeedbackCreate } from '../models/FeedbackCreate';
import type { FeedbackOut } from '../models/FeedbackOut';
import type { NodeCreate } from '../models/NodeCreate';
import type { NodeNotificationSettingsOut } from '../models/NodeNotificationSettingsOut';
import type { NodeNotificationSettingsUpdate } from '../models/NodeNotificationSettingsUpdate';
import type { NodeOut } from '../models/NodeOut';
import type { NodeUpdate } from '../models/NodeUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class NodesService {
    /**
     * List nodes
     * List nodes.
     *
     * See :class:`NodeListParams` for available query parameters.
     * @param accountId
     * @param sort
     * @param ifNoneMatch
     * @param xAccountId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static listNodesNodesGet(
        accountId: string,
        sort: 'updated_desc' | 'created_desc' | 'created_asc' | 'views_desc' = 'updated_desc',
        ifNoneMatch?: (string | null),
        xAccountId?: (string | null),
    ): CancelablePromise<Array<NodeOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes',
            headers: {
                'If-None-Match': ifNoneMatch,
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
                'sort': sort,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create node
     * @param requestBody
     * @param accountId
     * @param xFeatureFlags
     * @param xAccountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createNodeNodesPost(
        requestBody: NodeCreate,
        accountId?: (string | null),
        xFeatureFlags?: (string | null),
        xAccountId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes',
            headers: {
                'X-Feature-Flags': xFeatureFlags,
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get node
     * @param slug
     * @param accountId
     * @param xAccountId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static readNodeNodesSlugGet(
        slug: string,
        accountId?: (string | null),
        xAccountId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes/{slug}',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update node
     * @param slug
     * @param accountId
     * @param requestBody
     * @param xAccountId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static updateNodeNodesSlugPatch(
        slug: string,
        accountId: string,
        requestBody: NodeUpdate,
        xAccountId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/nodes/{slug}',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete node
     * @param slug
     * @param accountId
     * @param xAccountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteNodeNodesSlugDelete(
        slug: string,
        accountId: string,
        xAccountId?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/nodes/{slug}',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get node notification settings
     * @param nodeId
     * @param accountId
     * @param xAccountId
     * @returns NodeNotificationSettingsOut Successful Response
     * @throws ApiError
     */
    public static getNodeNotificationSettingsNodesNodeIdNotificationSettingsGet(
        nodeId: number,
        accountId: string,
        xAccountId?: (string | null),
    ): CancelablePromise<NodeNotificationSettingsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes/{node_id}/notification-settings',
            path: {
                'node_id': nodeId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update node notification settings
     * @param nodeId
     * @param accountId
     * @param requestBody
     * @param xAccountId
     * @returns NodeNotificationSettingsOut Successful Response
     * @throws ApiError
     */
    public static updateNodeNotificationSettingsNodesNodeIdNotificationSettingsPatch(
        nodeId: number,
        accountId: string,
        requestBody: NodeNotificationSettingsUpdate,
        xAccountId?: (string | null),
    ): CancelablePromise<NodeNotificationSettingsOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/nodes/{node_id}/notification-settings',
            path: {
                'node_id': nodeId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List feedback
     * @param slug
     * @param accountId
     * @param xAccountId
     * @returns FeedbackOut Successful Response
     * @throws ApiError
     */
    public static listFeedbackNodesSlugFeedbackGet(
        slug: string,
        accountId: string,
        xAccountId?: (string | null),
    ): CancelablePromise<Array<FeedbackOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes/{slug}/feedback',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create feedback
     * @param slug
     * @param accountId
     * @param requestBody
     * @param xAccountId
     * @returns FeedbackOut Successful Response
     * @throws ApiError
     */
    public static createFeedbackNodesSlugFeedbackPost(
        slug: string,
        accountId: string,
        requestBody: FeedbackCreate,
        xAccountId?: (string | null),
    ): CancelablePromise<FeedbackOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes/{slug}/feedback',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete feedback
     * @param slug
     * @param feedbackId
     * @param accountId
     * @param xAccountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteFeedbackNodesSlugFeedbackFeedbackIdDelete(
        slug: string,
        feedbackId: string,
        accountId: string,
        xAccountId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/nodes/{slug}/feedback/{feedback_id}',
            path: {
                'slug': slug,
                'feedback_id': feedbackId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List nodes
     * List nodes.
     *
     * See :class:`NodeListParams` for available query parameters.
     * @param accountId
     * @param sort
     * @param ifNoneMatch
     * @param xAccountId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static listNodesAccountsAccountIdNodesGet(
        accountId: string,
        sort: 'updated_desc' | 'created_desc' | 'created_asc' | 'views_desc' = 'updated_desc',
        ifNoneMatch?: (string | null),
        xAccountId?: (string | null),
    ): CancelablePromise<Array<NodeOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/accounts/{account_id}/nodes',
            path: {
                'account_id': accountId,
            },
            headers: {
                'If-None-Match': ifNoneMatch,
                'X-Account-Id': xAccountId,
            },
            query: {
                'sort': sort,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create node
     * @param accountId
     * @param requestBody
     * @param xAccountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createNodeAccountsAccountIdNodesPost(
        accountId: (string | null),
        requestBody: NodeCreate,
        xAccountId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/accounts/{account_id}/nodes',
            path: {
                'account_id': accountId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get node
     * @param slug
     * @param accountId
     * @param xAccountId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static readNodeAccountsAccountIdNodesSlugGet(
        slug: string,
        accountId: (string | null),
        xAccountId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/accounts/{account_id}/nodes/{slug}',
            path: {
                'slug': slug,
                'account_id': accountId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update node
     * @param slug
     * @param accountId
     * @param requestBody
     * @param xAccountId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static updateNodeAccountsAccountIdNodesSlugPatch(
        slug: string,
        accountId: string,
        requestBody: NodeUpdate,
        xAccountId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/accounts/{account_id}/nodes/{slug}',
            path: {
                'slug': slug,
                'account_id': accountId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete node
     * @param slug
     * @param accountId
     * @param xAccountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteNodeAccountsAccountIdNodesSlugDelete(
        slug: string,
        accountId: string,
        xAccountId?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/accounts/{account_id}/nodes/{slug}',
            path: {
                'slug': slug,
                'account_id': accountId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get node notification settings
     * @param nodeId
     * @param accountId
     * @param xAccountId
     * @returns NodeNotificationSettingsOut Successful Response
     * @throws ApiError
     */
    public static getNodeNotificationSettingsAccountsAccountIdNodesNodeIdNotificationSettingsGet(
        nodeId: number,
        accountId: string,
        xAccountId?: (string | null),
    ): CancelablePromise<NodeNotificationSettingsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/accounts/{account_id}/nodes/{node_id}/notification-settings',
            path: {
                'node_id': nodeId,
                'account_id': accountId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update node notification settings
     * @param nodeId
     * @param accountId
     * @param requestBody
     * @param xAccountId
     * @returns NodeNotificationSettingsOut Successful Response
     * @throws ApiError
     */
    public static updateNodeNotificationSettingsAccountsAccountIdNodesNodeIdNotificationSettingsPatch(
        nodeId: number,
        accountId: string,
        requestBody: NodeNotificationSettingsUpdate,
        xAccountId?: (string | null),
    ): CancelablePromise<NodeNotificationSettingsOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/accounts/{account_id}/nodes/{node_id}/notification-settings',
            path: {
                'node_id': nodeId,
                'account_id': accountId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List feedback
     * @param slug
     * @param accountId
     * @param xAccountId
     * @returns FeedbackOut Successful Response
     * @throws ApiError
     */
    public static listFeedbackAccountsAccountIdNodesSlugFeedbackGet(
        slug: string,
        accountId: string,
        xAccountId?: (string | null),
    ): CancelablePromise<Array<FeedbackOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/accounts/{account_id}/nodes/{slug}/feedback',
            path: {
                'slug': slug,
                'account_id': accountId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create feedback
     * @param slug
     * @param accountId
     * @param requestBody
     * @param xAccountId
     * @returns FeedbackOut Successful Response
     * @throws ApiError
     */
    public static createFeedbackAccountsAccountIdNodesSlugFeedbackPost(
        slug: string,
        accountId: string,
        requestBody: FeedbackCreate,
        xAccountId?: (string | null),
    ): CancelablePromise<FeedbackOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/accounts/{account_id}/nodes/{slug}/feedback',
            path: {
                'slug': slug,
                'account_id': accountId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete feedback
     * @param slug
     * @param feedbackId
     * @param accountId
     * @param xAccountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteFeedbackAccountsAccountIdNodesSlugFeedbackFeedbackIdDelete(
        slug: string,
        feedbackId: string,
        accountId: string,
        xAccountId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/accounts/{account_id}/nodes/{slug}/feedback/{feedback_id}',
            path: {
                'slug': slug,
                'feedback_id': feedbackId,
                'account_id': accountId,
            },
            headers: {
                'X-Account-Id': xAccountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
