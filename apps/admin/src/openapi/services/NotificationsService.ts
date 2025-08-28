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
     * @param workspaceId
     * @returns NotificationOut Successful Response
     * @throws ApiError
     */
    public static listNotificationsNotificationsGet(
        workspaceId: string,
    ): CancelablePromise<Array<NotificationOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/notifications',
            query: {
                'workspace_id': workspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Mark notification read
     * @param notificationId
     * @param workspaceId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static markReadNotificationsNotificationIdReadPost(
        notificationId: string,
        workspaceId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/notifications/{notification_id}/read',
            path: {
                'notification_id': notificationId,
            },
            query: {
                'workspace_id': workspaceId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
