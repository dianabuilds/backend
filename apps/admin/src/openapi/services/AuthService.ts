/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChangePasswordIn } from '../models/ChangePasswordIn';
import type { EVMVerify } from '../models/EVMVerify';
import type { LoginResponse } from '../models/LoginResponse';
import type { SignupSchema } from '../models/SignupSchema';
import type { Token } from '../models/Token';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuthService {
    /**
     * Login
     * @param requestBody
     * @returns LoginResponse Successful Response
     * @throws ApiError
     */
    public static loginAuthLoginPost(
        requestBody: {
            login: string;
            password: string;
        },
    ): CancelablePromise<LoginResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/login',
            body: requestBody,
            mediaType: 'application/json',
        });
    }
    /**
     * Refresh
     * @param requestBody
     * @returns LoginResponse Successful Response
     * @throws ApiError
     */
    public static refreshAuthRefreshPost(
        requestBody?: Token,
    ): CancelablePromise<LoginResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/refresh',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Signup
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static signupAuthSignupPost(
        requestBody: SignupSchema,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/signup',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Verify Email
     * @param token
     * @returns any Successful Response
     * @throws ApiError
     */
    public static verifyEmailAuthVerifyGet(
        token?: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/verify',
            query: {
                'token': token,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Change Password
     * @param requestBody
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static changePasswordAuthChangePasswordPost(
        requestBody: ChangePasswordIn,
        authorization: string = '',
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/change-password',
            headers: {
                'authorization': authorization,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Logout
     * @returns any Successful Response
     * @throws ApiError
     */
    public static logoutAuthLogoutPost(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/logout',
        });
    }
    /**
     * Evm Nonce
     * @param userId User ID
     * @returns any Successful Response
     * @throws ApiError
     */
    public static evmNonceAuthEvmNonceGet(
        userId?: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/auth/evm/nonce',
            query: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Evm Verify
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static evmVerifyAuthEvmVerifyPost(
        requestBody: EVMVerify,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/auth/evm/verify',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Refresh
     * @param requestBody
     * @returns LoginResponse Successful Response
     * @throws ApiError
     */
    public static refreshRefreshPost(
        requestBody?: Token,
    ): CancelablePromise<LoginResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/refresh',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
