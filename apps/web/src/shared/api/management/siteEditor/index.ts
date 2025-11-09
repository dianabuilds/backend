export * from './types';

export {
  fetchSitePages,
  fetchSitePage,
  fetchSitePageDraft,
  fetchSitePageSharedBindings,
  assignSharedBinding,
  deleteSharedBinding,
  createSitePage,
  updateSitePage,
  deleteSitePage,
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
  fetchSiteBlocks,
  fetchSiteBlock,
  createSiteBlock,
  saveSiteBlock,
  publishSiteBlock,
  archiveSiteBlock,
  fetchSiteBlockHistory,
  fetchSiteBlockVersion,
  restoreSiteBlockVersion,
  fetchBlockTemplates,
  fetchBlockTemplate,
  fetchBlockTemplateByKey,
  createBlockTemplate,
  updateBlockTemplate,
  previewSiteBlock,
} from './blocks';

export {
  fetchComponentCatalog,
  fetchComponent,
  fetchComponentSchema,
} from './components';

export { fetchSitePageMetrics, fetchSiteBlockMetrics } from './metrics';

export { fetchSiteAudit } from './audit';

import {
  fetchSitePages,
  fetchSitePage,
  fetchSitePageDraft,
  fetchSitePageSharedBindings,
  assignSharedBinding,
  deleteSharedBinding,
  createSitePage,
  updateSitePage,
  deleteSitePage,
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
  fetchSiteBlocks,
  fetchSiteBlock,
  createSiteBlock,
  saveSiteBlock,
  publishSiteBlock,
  archiveSiteBlock,
  fetchSiteBlockHistory,
  fetchSiteBlockVersion,
  restoreSiteBlockVersion,
  fetchBlockTemplates,
  fetchBlockTemplate,
  fetchBlockTemplateByKey,
  createBlockTemplate,
  updateBlockTemplate,
  previewSiteBlock,
} from './blocks';
import { fetchSitePageMetrics, fetchSiteBlockMetrics } from './metrics';
import { fetchSiteAudit } from './audit';
import {
  fetchComponentCatalog,
  fetchComponent,
  fetchComponentSchema,
} from './components';

export const managementSiteEditorApi = {
  fetchSitePages,
  fetchSitePage,
  fetchSitePageDraft,
  fetchSitePageSharedBindings,
  assignSharedBinding,
  deleteSharedBinding,
  createSitePage,
  updateSitePage,
  deleteSitePage,
  saveSitePageDraft,
  publishSitePage,
  fetchSitePageHistory,
  fetchSitePageVersion,
  fetchSitePageMetrics,
  validateSitePageDraft,
  diffSitePageDraft,
  previewSitePage,
  restoreSitePageVersion,
  fetchSiteBlocks,
  fetchSiteBlock,
  createSiteBlock,
  saveSiteBlock,
  publishSiteBlock,
  archiveSiteBlock,
  fetchSiteBlockHistory,
  fetchSiteBlockVersion,
  fetchSiteBlockMetrics,
  restoreSiteBlockVersion,
  previewSiteBlock,
  fetchBlockTemplates,
  fetchBlockTemplate,
  fetchBlockTemplateByKey,
  createBlockTemplate,
  updateBlockTemplate,
  fetchSiteAudit,
  fetchComponentCatalog,
  fetchComponent,
  fetchComponentSchema,
};


