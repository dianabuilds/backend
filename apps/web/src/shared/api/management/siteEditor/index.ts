export * from './types';

export {
  fetchSitePages,
  fetchSitePage,
  fetchSitePageDraft,
  saveSitePageDraft,
  publishSitePage,
  fetchSitePageHistory,
  fetchSitePageVersion,
  validateSitePageDraft,
  diffSitePageDraft,
  previewSitePage,
  restoreSitePageVersion,
} from './pages';

export {
  fetchSiteGlobalBlocks,
  fetchSiteGlobalBlock,
  createSiteGlobalBlock,
  saveSiteGlobalBlock,
  publishSiteGlobalBlock,
  fetchSiteGlobalBlockHistory,
  fetchSiteGlobalBlockVersion,
  restoreSiteGlobalBlockVersion,
  previewSiteBlock,
} from './blocks';

export { fetchSitePageMetrics, fetchSiteGlobalBlockMetrics } from './metrics';

export { fetchSiteAudit } from './audit';

import {
  fetchSitePages,
  fetchSitePage,
  fetchSitePageDraft,
  saveSitePageDraft,
  publishSitePage,
  fetchSitePageHistory,
  fetchSitePageVersion,
  validateSitePageDraft,
  diffSitePageDraft,
  previewSitePage,
  restoreSitePageVersion,
} from './pages';
import {
  fetchSiteGlobalBlocks,
  fetchSiteGlobalBlock,
  createSiteGlobalBlock,
  saveSiteGlobalBlock,
  publishSiteGlobalBlock,
  fetchSiteGlobalBlockHistory,
  fetchSiteGlobalBlockVersion,
  restoreSiteGlobalBlockVersion,
  previewSiteBlock,
} from './blocks';
import { fetchSitePageMetrics, fetchSiteGlobalBlockMetrics } from './metrics';
import { fetchSiteAudit } from './audit';

export const managementSiteEditorApi = {
  fetchSitePages,
  fetchSitePage,
  fetchSitePageDraft,
  saveSitePageDraft,
  publishSitePage,
  fetchSitePageHistory,
  fetchSitePageVersion,
  fetchSitePageMetrics,
  validateSitePageDraft,
  diffSitePageDraft,
  previewSitePage,
  restoreSitePageVersion,
  fetchSiteGlobalBlocks,
  fetchSiteGlobalBlock,
  createSiteGlobalBlock,
  saveSiteGlobalBlock,
  publishSiteGlobalBlock,
  fetchSiteGlobalBlockHistory,
  fetchSiteGlobalBlockVersion,
  fetchSiteGlobalBlockMetrics,
  restoreSiteGlobalBlockVersion,
  previewSiteBlock,
  fetchSiteAudit,
};
