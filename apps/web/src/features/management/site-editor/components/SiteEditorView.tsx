import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { Tabs } from '@ui';
import { managementSiteEditorApi } from '@shared/api/management';
import type { SitePageListResponse, SiteGlobalBlockListResponse } from '@shared/types/management';

import SitePagesCatalog from './SitePagesCatalog';
import SiteGlobalBlocksCatalog from './SiteGlobalBlocksCatalog';

type SummaryState = {
  pages: number | null;
  blocks: number | null;
};

export default function SiteEditorView(): React.ReactElement {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get('tab');
  const activeTab = tabParam === 'blocks' ? 'blocks' : 'pages';

  const [summary, setSummary] = React.useState<SummaryState>({
    pages: null,
    blocks: null,
  });

  React.useEffect(() => {
    const controller = new AbortController();
    let isMounted = true;
    async function loadSummary() {
      try {
        const [pages, blocks] = await Promise.all([
          managementSiteEditorApi.fetchSitePages(
            { pageSize: 1 },
            { signal: controller.signal },
          ) as Promise<SitePageListResponse>,
          managementSiteEditorApi.fetchSiteGlobalBlocks(
            { pageSize: 1 },
            { signal: controller.signal },
          ) as Promise<SiteGlobalBlockListResponse>,
        ]);
        if (!isMounted) {
          return;
        }
        setSummary({
          pages: pages.total ?? pages.items.length,
          blocks: blocks.total ?? blocks.items.length,
        });
      } catch (error) {
        if (controller.signal.aborted || !isMounted) {
          return;
        }
        if (process.env.NODE_ENV !== 'production') {
          // eslint-disable-next-line no-console
          console.warn('Не удалось загрузить сводку редактора сайта', error);
        }
        setSummary({
          pages: null,
          blocks: null,
        });
      }
    }

    loadSummary();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, []);

  const tabItems = React.useMemo(
    () => [
      {
        key: 'pages',
        label: `Страницы${summary.pages != null ? ` (${summary.pages})` : ''}`,
      },
      {
        key: 'blocks',
        label: `Глобальные блоки${summary.blocks != null ? ` (${summary.blocks})` : ''}`,
      },
    ],
    [summary.blocks, summary.pages],
  );

  const handleTabChange = React.useCallback(
    (key: string) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('tab', key);
        return next;
      });
    },
    [setSearchParams],
  );

  return (
    <div className="space-y-6 pb-12">
      <Tabs items={tabItems} value={activeTab} onChange={handleTabChange} className="pt-2" />

      {activeTab === 'blocks' ? <SiteGlobalBlocksCatalog /> : <SitePagesCatalog />}
    </div>
  );
}
