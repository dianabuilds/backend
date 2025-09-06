/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NotificationOut } from '../models/NotificationOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class NotificationsService {
    /**
     * List notifications
     * @param accountId
     * @returns NotificationOut Successful Response
     * @throws ApiError
     */
    public static listNotificationsNotificationsGet(
        accountId: string,
    ): CancelablePromise<Array<NotificationOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/notifications',
            query: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Mark notification read
     * @param notificationId
     * @param accountId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static markReadNotificationsNotificationIdReadPost(
        notificationId: string,
        accountId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/notifications/{notification_id}/read',
            path: {
                'notification_id': notificationId,
            },
            query: {
                'account_id': accountId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
