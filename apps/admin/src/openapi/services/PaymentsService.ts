/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PremiumPurchaseIn } from '../models/PremiumPurchaseIn';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class PaymentsService {
    /**
     * Buy premium
     * Upgrade the current user to premium using a payment token.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static buyPremiumPaymentsPremiumPost(
        requestBody: PremiumPurchaseIn,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/payments/premium',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
