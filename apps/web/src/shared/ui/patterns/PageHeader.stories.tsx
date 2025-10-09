import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { PageHeader } from './PageHeader';
import { Button } from '@ui';

const meta: Meta<typeof PageHeader> = {
  title: 'Patterns/PageHeader',
  component: PageHeader,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj<typeof PageHeader>;

export const Highlight: Story = {
  args: {
    title: 'РЈРїСЂР°РІР»РµРЅРёРµ РїР»Р°С‚С„РѕСЂРјРѕР№',
    description: 'РќР°СЃС‚СЂРѕР№РєР° С‚Р°СЂРёС„РѕРІ, РёРЅС‚РµРіСЂР°С†РёР№ Рё СЃРµСЂРІРёСЃРЅС‹С… РєРѕРјРїРѕРЅРµРЅС‚. РР· СЌС‚РѕРіРѕ СЂР°Р·РґРµР»Р° РЅР°С‡РёРЅР°РµС‚СЃСЏ РµР¶РµРґРЅРµРІРЅР°СЏ СЂР°Р±РѕС‚Р° Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂРѕРІ.',
    kicker: 'Control center',
    breadcrumbs: [
      { label: 'Dashboard', to: '/' },
      { label: 'Platform' },
    ],
    actions: (
      <div className="flex items-center gap-2">
        <Button variant="ghost">Р­РєСЃРїРѕСЂС‚</Button>
        <Button>Р”РѕР±Р°РІРёС‚СЊ Р·Р°РїРёСЃСЊ</Button>
      </div>
    ),
    stats: [
      { label: 'РђРєС‚РёРІРЅС‹Рµ РёРЅС‚РµРіСЂР°С†РёРё', value: '18', hint: 'РёР· 22 РґРѕСЃС‚СѓРїРЅС‹С…' },
      { label: 'РћС€РёР±РєР° Р·Р° СЃСѓС‚РєРё', value: '3', hint: 'СЂР°Р·СЂРµС€РµРЅРѕ 5' },
    ],
  },
};

export const Radiant: Story = {
  args: {
    ...Highlight.args,
    pattern: 'radiant',
    title: 'Observability',
    description: 'РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚Рё API Рё РєР»РёРµРЅС‚СЃРєРёС… РїСЂРёР»РѕР¶РµРЅРёР№.',
    stats: [
      { label: 'Р’СЂРµРјСЏ РѕС‚РєР»РёРєР°', value: '142 РјСЃ' },
      { label: 'РћС€РёР±РєРё 5xx', value: '0.3%' },
      { label: 'LLM Р·Р°РїСЂРѕСЃС‹', value: '12 480' },
    ],
  },
};

