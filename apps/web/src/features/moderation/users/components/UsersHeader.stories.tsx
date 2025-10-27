import type { Meta, StoryObj } from '@storybook/react';
import { UsersHeader } from './UsersHeader';

const meta: Meta<typeof UsersHeader> = {
  title: 'Features/Moderation/Users/UsersHeader',
  component: UsersHeader,
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<typeof UsersHeader>;

export const Default: Story = {
  args: {
    metrics: {
      total: 1280,
      active: 904,
      sanctioned: 37,
      highRisk: 5,
      complaints: 64,
    },
    lastRefreshLabel: 'Updated 2 minutes ago',
    loading: false,
    hasError: false,
    onRefresh: () => {
      /* noop for Storybook */
    },
    onCreateCase: () => {
      /* noop for Storybook */
    },
  },
};
