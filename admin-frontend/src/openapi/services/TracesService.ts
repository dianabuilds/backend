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
     * Create trace
     * @param requestBody
     * @returns NodeTraceOut Successful Response
     * @throws ApiError
     */
    public static createTraceTracesPost(
        requestBody: NodeTraceCreate,
    ): CancelablePromise<NodeTraceOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/traces',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List traces
     * @param nodeId
     * @param visibleTo
     * @returns NodeTraceOut Successful Response
     * @throws ApiError
     */
    public static listTracesTracesGet(
        nodeId: string,
        visibleTo: string = 'all',
    ): CancelablePromise<Array<NodeTraceOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/traces',
            query: {
                'node_id': nodeId,
                'visible_to': visibleTo,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
