/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_upload_media_asset_admin_media_post } from '../models/Body_upload_media_asset_admin_media_post';
import type { Body_upload_media_asset_workspaces__workspace_id__admin_media_post } from '../models/Body_upload_media_asset_workspaces__workspace_id__admin_media_post';
import type { MediaAssetOut } from '../models/MediaAssetOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdminMediaService {
    /**
     * Upload media asset
     * @param workspaceId
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static uploadMediaAssetAdminMediaPost(
        workspaceId: string,
        formData?: Body_upload_media_asset_admin_media_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/admin/media',
            query: {
                'workspace_id': workspaceId,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List media assets
     * @param workspaceId
     * @param limit
     * @param offset
     * @returns MediaAssetOut Successful Response
     * @throws ApiError
     */
    public static listMediaAssetsAdminMediaGet(
        workspaceId: string,
        limit: number = 100,
        offset?: number,
    ): CancelablePromise<Array<MediaAssetOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/admin/media',
            query: {
                'workspace_id': workspaceId,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Upload media asset
     * @param workspaceId
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static uploadMediaAssetWorkspacesWorkspaceIdAdminMediaPost(
        workspaceId: string,
        formData?: Body_upload_media_asset_workspaces__workspace_id__admin_media_post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/workspaces/{workspace_id}/admin/media',
            path: {
                'workspace_id': workspaceId,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List media assets
     * @param workspaceId
     * @param limit
     * @param offset
     * @returns MediaAssetOut Successful Response
     * @throws ApiError
     */
    public static listMediaAssetsWorkspacesWorkspaceIdAdminMediaGet(
        workspaceId: string,
        limit: number = 100,
        offset?: number,
    ): CancelablePromise<Array<MediaAssetOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/workspaces/{workspace_id}/admin/media',
            path: {
                'workspace_id': workspaceId,
            },
            query: {
                'limit': limit,
                'offset': offset,
            },
            errors: {
                401: `Unauthorized`,
                403: `Forbidden`,
                422: `Validation Error`,
            },
        });
    }
}
