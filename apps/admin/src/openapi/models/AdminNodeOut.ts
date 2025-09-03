/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Status } from './Status';
/**
 * Detailed node payload used by the admin UI.
 */
export type AdminNodeOut = {
    title?: (string | null);
    isVisible?: boolean;
    meta?: Record<string, any>;
    premiumOnly?: (boolean | null);
    nftRequired?: (string | null);
    aiGenerated?: (boolean | null);
    allowFeedback?: boolean;
    isRecommendable?: boolean;
    id: number;
    slug: string;
    authorId?: (string | null);
    createdByUserId?: (string | null);
    updatedByUserId?: (string | null);
    views: number;
    createdAt?: (string | null);
    updatedAt?: (string | null);
    popularityScore: number;
    contentId: number;
    nodeId: number;
    workspaceId: string;
    nodeType: string;
    type?: (string | null);
    summary?: (string | null);
    status: Status;
    publishedAt?: (string | null);
    content?: (Record<string, any> | null);
    coverUrl?: (string | null);
    media?: Array<string>;
    isPublic?: boolean;
    reactions?: Record<string, any>;
    tags?: Array<string>;
};

