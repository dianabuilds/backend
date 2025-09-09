/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class PremiumService {
  /**
   * My Limits
   * @returns any Successful Response
   * @throws ApiError
   */
  public static myLimitsPremiumMeLimitsGet(): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/premium/me/limits',
    });
  }
}
