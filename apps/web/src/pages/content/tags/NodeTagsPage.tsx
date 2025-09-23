import React from 'react';
import TagsPage, { TagGroupSummary } from './TagsPage';

function matchesNodeScope(group: TagGroupSummary) {
  if (!group?.key) return false;
  const key = group.key.toLowerCase();
  return key.includes('node') || key.includes('graph');
}

export default function NodeTagsPage() {
  return (
    <TagsPage
      context="nodes"
      title="Node tags"
      defaultGroupKey="nodes"
      description="Taxonomy for narrative nodes only: keep the discovery graph tidy and relations meaningful."
      groupFilter={(group) => matchesNodeScope(group)}
    />
  );
}