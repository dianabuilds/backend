import React from 'react';
import { NavLink } from 'react-router-dom';
import { ContentLayout } from '../ContentLayout';
import { Card } from '../../../shared/ui';

const questActions = (
  <div className="flex flex-wrap items-center gap-2">
    <NavLink
      to="/quests/new"
      className="btn-base btn h-9 rounded-full bg-primary-600 px-4 text-sm font-medium text-white shadow-sm transition hover:bg-primary-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/70"
    >
      New Quest
    </NavLink>
    <NavLink
      to="/quests/worlds/new"
      className="btn-base btn h-9 rounded-full bg-white px-4 text-sm font-medium text-primary-600 shadow-sm ring-1 ring-primary-200 transition hover:bg-primary-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/70"
    >
      New World
    </NavLink>
  </div>
);

export default function QuestAIStudioPage() {
  return (
    <ContentLayout
      context="quests"
      title="AI quest studio"
      description="Kick off automated quest ideas, evaluate generated outlines, and promote the strongest drafts into the main pipeline."
      actions={questActions}
    >
      <Card className="space-y-4 p-6">
        <h2 className="text-base font-semibold text-gray-800 dark:text-dark-50">Coming soon</h2>
        <p className="text-sm text-gray-600 dark:text-dark-200">
          The AI studio will let you generate quest skeletons from world templates, validate constraints, and export selected runs straight into the library.
        </p>
        <p className="text-sm text-gray-600 dark:text-dark-200">
          Until we plug in the generation endpoints keep your prompts and evaluation rubrics handy. This placeholder intentionally lives in the navigation so the team can iterate on UX flows early.
        </p>
      </Card>
    </ContentLayout>
  );
}