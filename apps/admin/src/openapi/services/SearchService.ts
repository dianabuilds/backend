/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SearchService {
  /**
   * Search nodes
   * @param q
   * @param tags
   * @param match
   * @param limit
   * @param offset
   * @returns any Successful Response
   * @throws ApiError
   */
  public static searchNodesSearchGet(
    q?: string | null,
    tags?: string | null,
    match: string = 'any',
    limit: number = 20,
    offset?: number,
  ): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/search',
      query: {
        q: q,
        tags: tags,
        match: match,
        limit: limit,
        offset: offset,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Semantic search
   * @param q
   * @param limit
   * @returns any Successful Response
   * @throws ApiError
   */
  public static semanticSearchSearchSemanticGet(
    q: string,
    limit: number = 20,
  ): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/search/semantic',
      query: {
        q: q,
        limit: limit,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
}
