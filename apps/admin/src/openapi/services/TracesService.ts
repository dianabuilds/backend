/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTraceCreate } from '../models/NodeTraceCreate';
import type { NodeTraceOut } from '../models/NodeTraceOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TracesService {
    /**
     * List traces
     * @param nodeId
     * @param visibleTo
     * @param xWorkspaceId
     * @returns NodeTraceOut Successful Response
     * @throws ApiError
     */
    public static listTracesTracesGet(
        nodeId?: string,
        visibleTo: string = 'all',
        xWorkspaceId?: (string | null),
    ): CancelablePromise<Array<NodeTraceOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/traces',
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            query: {
                'node_id': nodeId,
                'visible_to': visibleTo,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create trace
     * @param requestBody
     * @param xWorkspaceId
     * @returns NodeTraceOut Successful Response
     * @throws ApiError
     */
    public static createTraceTracesPost(
        requestBody: NodeTraceCreate,
        xWorkspaceId?: (string | null),
    ): CancelablePromise<NodeTraceOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/traces',
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
}
