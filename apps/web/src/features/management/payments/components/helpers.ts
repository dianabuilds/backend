import type {
  BillingContract,
  BillingProvider,
  BillingProviderNetworks,
  BillingProviderTokens,
  BillingTransaction,
} from '@shared/types/management';

export type ProviderFormState = {
  slug: string;
  type: string;
  enabled: boolean;
  priority: string;
  contractSlug: string;
  networks: string;
  supportedTokens: string;
  defaultNetwork: string;
  extraConfig: string;
};

export const DEFAULT_PROVIDER_FORM: ProviderFormState = {
  slug: '',
  type: 'custom',
  enabled: true,
  priority: '100',
  contractSlug: '',
  networks: '',
  supportedTokens: '',
  defaultNetwork: '',
  extraConfig: '',
};

export const toListString = (value: unknown): string => {
  if (Array.isArray(value)) {
    return value
      .map((item) => String(item ?? ''))
      .filter(Boolean)
      .join(', ');
  }
  if (value && typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return '';
    }
  }
  if (typeof value === 'string') return value;
  return '';
};

export const providerToForm = (provider: BillingProvider): ProviderFormState => {
  const baseConfig =
    provider.config && typeof provider.config === 'object'
      ? { ...(provider.config as Record<string, unknown>) }
      : {};

  const linkedContract =
    typeof baseConfig.linked_contract === 'string'
      ? String(baseConfig.linked_contract)
      : '';
  const networksValue = provider.networks ?? baseConfig.networks;
  const tokensValue = provider.supported_tokens ?? baseConfig.supported_tokens;
  const defaultNetwork =
    provider.default_network ??
    (typeof baseConfig.default_network === 'string'
      ? String(baseConfig.default_network)
      : '');

  delete baseConfig.linked_contract;
  delete baseConfig.networks;
  delete baseConfig.supported_tokens;
  delete baseConfig.default_network;

  const extraConfig = Object.keys(baseConfig).length
    ? JSON.stringify(baseConfig, null, 2)
    : '';

  return {
    slug: provider.slug ?? '',
    type: provider.type ?? 'custom',
    enabled: Boolean(provider.enabled),
    priority: provider.priority != null ? String(provider.priority) : '100',
    contractSlug: provider.contract_slug ?? linkedContract ?? '',
    networks: toListString(networksValue),
    supportedTokens: toListString(tokensValue),
    defaultNetwork: defaultNetwork ?? '',
    extraConfig,
  };
};

export const parseStructuredList = (
  value: string,
): BillingProviderNetworks | null => {
  const trimmed = value.trim();
  if (!trimmed) return null;
  try {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed) || (parsed && typeof parsed === 'object')) {
      return parsed as BillingProviderNetworks;
    }
  } catch {
    // ignore — fallback to CSV
  }
  const list = trimmed
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
  return list.length ? list : null;
};

export const parseStructuredTokens = (
  value: string,
): BillingProviderTokens | null => {
  const trimmed = value.trim();
  if (!trimmed) return null;
  try {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed) || (parsed && typeof parsed === 'object')) {
      return parsed as BillingProviderTokens;
    }
  } catch {
    // ignore — fallback to CSV
  }
  const list = trimmed
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
  return list.length ? list : null;
};

export const centsToUsd = (value: number | null | undefined) => {
  const amount = (value ?? 0) / 100;
  return '$' + amount.toFixed(2);
};

export const formatDate = (value?: string | null) => {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

export const txExplorerUrl = (chain?: string | null, tx?: string | null) => {
  if (!tx) return '';
  if (chain === 'polygon') return 'https://polygonscan.com/tx/' + tx;
  if (chain === 'bsc') return 'https://bscscan.com/tx/' + tx;
  if (chain === 'ethereum') return 'https://etherscan.io/tx/' + tx;
  return '';
};

export const getTxStatusMeta = (status?: string | null) => {
  const value = String(status || '').toLowerCase();
  if (['succeeded', 'success', 'captured', 'completed'].includes(value)) {
    return { label: 'успешно', color: 'success' as const };
  }
  if (['pending', 'processing'].includes(value)) {
    return { label: 'ожидает', color: 'warning' as const };
  }
  if (['failed', 'error', 'declined'].includes(value)) {
    return { label: 'ошибка', color: 'error' as const };
  }
  return { label: status || '—', color: 'neutral' as const };
};

export const getContractStats = (contracts: BillingContract[]) => {
  const total = contracts.length;
  const enabled = contracts.filter((item) => item.enabled).length;
  const testnet = contracts.filter((item) => item.testnet).length;
  const mainnet = total - testnet;
  return { total, enabled, testnet, mainnet };
};

export const getNetworkOptions = (transactions: BillingTransaction[]) => {
  const set = new Set<string>();
  transactions.forEach((tx) => {
    if (tx.network) set.add(tx.network);
  });
  return Array.from(set).sort();
};
