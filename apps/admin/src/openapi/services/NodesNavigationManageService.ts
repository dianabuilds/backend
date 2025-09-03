/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTransitionCreate } from '../models/NodeTransitionCreate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class NodesNavigationManageService {
    /**
     * Create transition
     * @param slug
     * @param workspaceId
     * @param requestBody
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createTransitionNodesSlugTransitionsPost(
        slug: string,
        workspaceId: string,
        requestBody: NodeTransitionCreate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes/{slug}/transitions',
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
     * Record visit
     * @param slug
     * @param toSlug
     * @param workspaceId
     * @param source
     * @param channel
     * @param xWorkspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static recordVisitNodesSlugVisitToSlugPost(
        slug: string,
        toSlug: string,
        workspaceId: string,
        source?: (string | null),
        channel?: (string | null),
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/nodes/{slug}/visit/{to_slug}',
            path: {
                'slug': slug,
                'to_slug': toSlug,
            },
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            query: {
                'workspace_id': workspaceId,
                'source': source,
                'channel': channel,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
