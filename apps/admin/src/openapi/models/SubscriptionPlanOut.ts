/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type SubscriptionPlanOut = {
    slug: string;
    title: string;
    description: (string | null);
    price_cents: (number | null);
    currency: (string | null);
    is_active: boolean;
    order: number;
    monthly_limits: (Record<string, number> | null);
    features: (Record<string, any> | null);
    id: string;
    created_at: string;
    updated_at: string;
};

