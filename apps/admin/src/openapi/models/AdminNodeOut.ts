/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Status } from './Status';
/**
 * Detailed node payload used by the admin UI.
 */
export type AdminNodeOut = {
    aiGenerated?: (boolean | null);
    allowFeedback?: boolean;
    authorId?: (string | null);
    content?: (Record<string, any> | null);
    contentId: number;
    coverUrl?: (string | null);
    createdAt?: (string | null);
    createdByUserId?: (string | null);
    id: number;
    isPublic: boolean;
    isRecommendable?: boolean;
    isVisible?: boolean;
    media?: Array<string>;
    meta?: Record<string, any>;
    nftRequired?: (string | null);
    nodeId: number;
    nodeType: string;
    popularityScore?: number;
    premiumOnly?: (boolean | null);
    publishedAt?: (string | null);
    reactions?: Record<string, any>;
    slug: string;
    status: Status;
    summary?: (string | null);
    tags?: Array<string>;
    title?: (string | null);
    type?: (string | null);
    updatedAt?: (string | null);
    updatedByUserId?: (string | null);
    views?: number;
    workspaceId: string;
};

