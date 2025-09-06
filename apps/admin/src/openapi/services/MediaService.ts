/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_upload_media_media_post } from '../models/Body_upload_media_media_post';
import type { Body_upload_media_workspaces__account_id__media_post } from '../models/Body_upload_media_workspaces__account_id__media_post';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MediaService {
    /**
     * Upload Media
     * Accept an uploaded image and return its public URL.
     * @param xWorkspaceId
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static uploadMediaMediaPost(
        xWorkspaceId?: (string | null),
        formData?: Body_upload_media_media_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/media',
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Upload Media
     * Accept an uploaded image and return its public URL.
     * @param xWorkspaceId
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static uploadMediaWorkspacesAccountIdMediaPost(
        xWorkspaceId?: (string | null),
        formData?: Body_upload_media_workspaces__account_id__media_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/workspaces/{account_id}/media',
            headers: {
                'X-Workspace-Id': xWorkspaceId,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
