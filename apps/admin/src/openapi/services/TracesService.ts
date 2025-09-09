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
   * @param xAccountId
   * @returns NodeTraceOut Successful Response
   * @throws ApiError
   */
  public static createTraceTracesPost(
    requestBody: NodeTraceCreate,
    xAccountId?: string | null,
  ): CancelablePromise<NodeTraceOut> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/traces',
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
   * List traces
   * @param nodeId
   * @param visibleTo
   * @param xAccountId
   * @returns NodeTraceOut Successful Response
   * @throws ApiError
   */
  public static listTracesTracesGet(
    nodeId?: string,
    visibleTo: string = 'all',
    xAccountId?: string | null,
  ): CancelablePromise<Array<NodeTraceOut>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/traces',
      headers: {
        'X-Account-Id': xAccountId,
      },
      query: {
        node_id: nodeId,
        visible_to: visibleTo,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
