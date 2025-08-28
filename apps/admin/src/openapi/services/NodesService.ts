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
import type { NodeTagsUpdate } from '../models/NodeTagsUpdate';
import type { NodeUpdate } from '../models/NodeUpdate';
import type { ReactionUpdate } from '../models/ReactionUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class NodesService {
    /**
     * List nodes
     * @param workspaceId
     * @param tags
     * @param match
     * @param sort
     * @param ifNoneMatch
     * @param xWorkspaceId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static listNodesNodesGet(
        workspaceId: string,
        tags?: (string | null),
        match: string = 'any',
        sort: string = 'updated_desc',
        ifNoneMatch?: (string | null),
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Array<NodeOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes',
            headers: {
                'If-None-Match': ifNoneMatch,
                'X-Workspace-Id': xWorkspaceId,
            },
            query: {
                'workspace_id': workspaceId,
                'tags': tags,
                'match': match,
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
     * @param workspaceId
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createNodeNodesPost(
        requestBody: NodeCreate,
        workspaceId?: (string | null),
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes',
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * Get node
     * @param slug
     * @param workspaceId
     * @param xWorkspaceId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static readNodeNodesSlugGet(
        slug: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes/{slug}',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * Update node
     * @param slug
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static updateNodeNodesSlugPatch(
        slug: string,
        workspaceId: string,
        requestBody: NodeUpdate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/nodes/{slug}',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * Delete node
     * @param slug
     * @param workspaceId
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteNodeNodesSlugDelete(
        slug: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/nodes/{slug}',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * Set node tags
     * @param nodeId
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static setNodeTagsNodesNodeIdTagsPost(
        nodeId: string,
        workspaceId: string,
        requestBody: NodeTagsUpdate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes/{node_id}/tags',
            path: {
                'node_id': nodeId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * Update reactions
     * @param slug
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateReactionsNodesSlugReactionsPost(
        slug: string,
        workspaceId: string,
        requestBody: ReactionUpdate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes/{slug}/reactions',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * Get node notification settings
     * @param nodeId
     * @param workspaceId
     * @param xWorkspaceId
     * @returns NodeNotificationSettingsOut Successful Response
     * @throws ApiError
     */
    public static getNodeNotificationSettingsNodesNodeIdNotificationSettingsGet(
        nodeId: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeNotificationSettingsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes/{node_id}/notification-settings',
            path: {
                'node_id': nodeId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * Update node notification settings
     * @param nodeId
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns NodeNotificationSettingsOut Successful Response
     * @throws ApiError
     */
    public static updateNodeNotificationSettingsNodesNodeIdNotificationSettingsPatch(
        nodeId: string,
        workspaceId: string,
        requestBody: NodeNotificationSettingsUpdate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeNotificationSettingsOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/nodes/{node_id}/notification-settings',
            path: {
                'node_id': nodeId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * List feedback
     * @param slug
     * @param workspaceId
     * @param xWorkspaceId
     * @returns FeedbackOut Successful Response
     * @throws ApiError
     */
    public static listFeedbackNodesSlugFeedbackGet(
        slug: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Array<FeedbackOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nodes/{slug}/feedback',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * Create feedback
     * @param slug
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns FeedbackOut Successful Response
     * @throws ApiError
     */
    public static createFeedbackNodesSlugFeedbackPost(
        slug: string,
        workspaceId: string,
        requestBody: FeedbackCreate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<FeedbackOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes/{slug}/feedback',
            path: {
                'slug': slug,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * Delete feedback
     * @param slug
     * @param feedbackId
     * @param workspaceId
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteFeedbackNodesSlugFeedbackFeedbackIdDelete(
        slug: string,
        feedbackId: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/nodes/{slug}/feedback/{feedback_id}',
            path: {
                'slug': slug,
                'feedback_id': feedbackId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * List nodes
     * @param workspaceId
     * @param tags
     * @param match
     * @param sort
     * @param ifNoneMatch
     * @param xWorkspaceId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static listNodesWorkspacesWorkspaceIdNodesGet(
        workspaceId: string,
        tags?: (string | null),
        match: string = 'any',
        sort: string = 'updated_desc',
        ifNoneMatch?: (string | null),
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Array<NodeOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/workspaces/{workspace_id}/nodes',
            path: {
                'workspace_id': workspaceId,
            },
            headers: {
                'If-None-Match': ifNoneMatch,
                'X-Workspace-Id': xWorkspaceId,
            },
            query: {
                'tags': tags,
                'match': match,
                'sort': sort,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create node
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createNodeWorkspacesWorkspaceIdNodesPost(
        workspaceId: (string | null),
        requestBody: NodeCreate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/workspaces/{workspace_id}/nodes',
            path: {
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * @param workspaceId
     * @param xWorkspaceId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static readNodeWorkspacesWorkspaceIdNodesSlugGet(
        slug: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/workspaces/{workspace_id}/nodes/{slug}',
            path: {
                'slug': slug,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update node
     * @param slug
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static updateNodeWorkspacesWorkspaceIdNodesSlugPatch(
        slug: string,
        workspaceId: string,
        requestBody: NodeUpdate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/workspaces/{workspace_id}/nodes/{slug}',
            path: {
                'slug': slug,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * @param workspaceId
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteNodeWorkspacesWorkspaceIdNodesSlugDelete(
        slug: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/workspaces/{workspace_id}/nodes/{slug}',
            path: {
                'slug': slug,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set node tags
     * @param nodeId
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns NodeOut Successful Response
     * @throws ApiError
     */
    public static setNodeTagsWorkspacesWorkspaceIdNodesNodeIdTagsPost(
        nodeId: string,
        workspaceId: string,
        requestBody: NodeTagsUpdate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/workspaces/{workspace_id}/nodes/{node_id}/tags',
            path: {
                'node_id': nodeId,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update reactions
     * @param slug
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateReactionsWorkspacesWorkspaceIdNodesSlugReactionsPost(
        slug: string,
        workspaceId: string,
        requestBody: ReactionUpdate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/workspaces/{workspace_id}/nodes/{slug}/reactions',
            path: {
                'slug': slug,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get node notification settings
     * @param nodeId
     * @param workspaceId
     * @param xWorkspaceId
     * @returns NodeNotificationSettingsOut Successful Response
     * @throws ApiError
     */
    public static getNodeNotificationSettingsWorkspacesWorkspaceIdNodesNodeIdNotificationSettingsGet(
        nodeId: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeNotificationSettingsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/workspaces/{workspace_id}/nodes/{node_id}/notification-settings',
            path: {
                'node_id': nodeId,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update node notification settings
     * @param nodeId
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns NodeNotificationSettingsOut Successful Response
     * @throws ApiError
     */
    public static updateNodeNotificationSettingsWorkspacesWorkspaceIdNodesNodeIdNotificationSettingsPatch(
        nodeId: string,
        workspaceId: string,
        requestBody: NodeNotificationSettingsUpdate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeNotificationSettingsOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/workspaces/{workspace_id}/nodes/{node_id}/notification-settings',
            path: {
                'node_id': nodeId,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * @param workspaceId
     * @param xWorkspaceId
     * @returns FeedbackOut Successful Response
     * @throws ApiError
     */
    public static listFeedbackWorkspacesWorkspaceIdNodesSlugFeedbackGet(
        slug: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Array<FeedbackOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/workspaces/{workspace_id}/nodes/{slug}/feedback',
            path: {
                'slug': slug,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create feedback
     * @param slug
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns FeedbackOut Successful Response
     * @throws ApiError
     */
    public static createFeedbackWorkspacesWorkspaceIdNodesSlugFeedbackPost(
        slug: string,
        workspaceId: string,
        requestBody: FeedbackCreate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<FeedbackOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/workspaces/{workspace_id}/nodes/{slug}/feedback',
            path: {
                'slug': slug,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
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
     * @param workspaceId
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteFeedbackWorkspacesWorkspaceIdNodesSlugFeedbackFeedbackIdDelete(
        slug: string,
        feedbackId: string,
        workspaceId: string,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/workspaces/{workspace_id}/nodes/{slug}/feedback/{feedback_id}',
            path: {
                'slug': slug,
                'feedback_id': feedbackId,
                'workspace_id': workspaceId,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
