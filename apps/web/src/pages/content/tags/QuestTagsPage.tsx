import React from 'react';
import TagsPage, { TagGroupSummary } from './TagsPage';

function matchesQuestScope(group: TagGroupSummary) {
  if (!group?.key) return false;
  const key = group.key.toLowerCase();
  return key.includes('quest') || key.includes('world');
}

export default function QuestTagsPage() {
  return (
    <TagsPage
      context="quests"
      title="Quest tags"
      defaultGroupKey="quests"
      description="Separate vocabulary for quest discovery, world alignment, and live event hooks."
      groupFilter={(group) => matchesQuestScope(group)}
    />
  );
}