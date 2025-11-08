import React from 'react';
import { useParams } from 'react-router-dom';
import { ManagementSiteBlockDetail } from '../../features/management';

export default function SiteBlockDetailPage(): React.ReactElement {
  const params = useParams<{ blockId?: string }>();
  return <ManagementSiteBlockDetail blockId={params.blockId} />;
}
