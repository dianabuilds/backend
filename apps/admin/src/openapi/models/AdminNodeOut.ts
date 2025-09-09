/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Status } from './Status';
/**
 * Detailed node payload used by the admin UI.
 */
export type AdminNodeOut = {
  id: number;
  contentId: number;
  nodeId: number;
  accountId: string;
  nodeType: string;
  type?: string | null;
  slug: string;
  title?: string | null;
  summary?: string | null;
  status: Status;
  meta?: Record<string, any>;
  content?: Record<string, any> | null;
  coverUrl?: string | null;
  media?: Array<string>;
  isPublic: boolean;
  isVisible?: boolean;
  allowFeedback?: boolean;
  isRecommendable?: boolean;
  premiumOnly?: boolean | null;
  nftRequired?: string | null;
  aiGenerated?: boolean | null;
  authorId?: string | null;
  createdByUserId?: string | null;
  updatedByUserId?: string | null;
  views?: number;
  reactions?: Record<string, any>;
  popularityScore?: number;
  publishedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  tags?: Array<string>;
};
