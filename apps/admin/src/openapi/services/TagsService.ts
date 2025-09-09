/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TagCreate } from '../models/TagCreate';
import type { TagOut } from '../models/TagOut';
import type { TagUpdate } from '../models/TagUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TagsService {
  /**
   * List tags
   * Retrieve available tags with optional search and popularity filter.
   * @param accountId
   * @param q
   * @param popular
   * @param limit
   * @param offset
   * @returns TagOut Successful Response
   * @throws ApiError
   */
  public static listTagsTagsTagsGet(
    accountId: string,
    q?: string | null,
    popular: boolean = false,
    limit: number = 10,
    offset?: number,
  ): CancelablePromise<Array<TagOut>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/tags/tags/',
      query: {
        account_id: accountId,
        q: q,
        popular: popular,
        limit: limit,
        offset: offset,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Create tag
   * @param accountId
   * @param requestBody
   * @returns TagOut Successful Response
   * @throws ApiError
   */
  public static createTagTagsTagsPost(
    accountId: string,
    requestBody: TagCreate,
  ): CancelablePromise<TagOut> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/tags/tags/',
      query: {
        account_id: accountId,
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Get tag
   * @param slug
   * @param accountId
   * @returns TagOut Successful Response
   * @throws ApiError
   */
  public static getTagTagsTagsSlugGet(slug: string, accountId: string): CancelablePromise<TagOut> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/tags/tags/{slug}',
      path: {
        slug: slug,
      },
      query: {
        account_id: accountId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Update tag
   * @param slug
   * @param accountId
   * @param requestBody
   * @returns TagOut Successful Response
   * @throws ApiError
   */
  public static updateTagTagsTagsSlugPut(
    slug: string,
    accountId: string,
    requestBody: TagUpdate,
  ): CancelablePromise<TagOut> {
    return __request(OpenAPI, {
      method: 'PUT',
      url: '/tags/tags/{slug}',
      path: {
        slug: slug,
      },
      query: {
        account_id: accountId,
      },
      body: requestBody,
      mediaType: 'application/json',
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Delete tag
   * @param slug
   * @param accountId
   * @returns any Successful Response
   * @throws ApiError
   */
  public static deleteTagTagsTagsSlugDelete(
    slug: string,
    accountId: string,
  ): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: 'DELETE',
      url: '/tags/tags/{slug}',
      path: {
        slug: slug,
      },
      query: {
        account_id: accountId,
      },
      errors: {
        422: `Validation Error`,
      },
    });
  }
  /**
   * Tags Health
   * @returns string Successful Response
   * @throws ApiError
   */
  public static tagsHealthTagsHealthGet(): CancelablePromise<Record<string, string>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/tags/_health',
    });
  }
}
