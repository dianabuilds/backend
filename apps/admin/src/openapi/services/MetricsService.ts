/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MetricsService {
  /**
   * Rum Metrics
   * Приёмник простых RUM-событий с фронтенда.
   * Тело: { event: str, ts: int, url: str, data: any }
   * @returns any Successful Response
   * @throws ApiError
   */
  public static rumMetricsMetricsRumPost(): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/metrics/rum',
    });
  }
}
