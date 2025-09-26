import React from 'react';
import { apiDelete, apiGet, apiPost } from '../api/client';
import { extractErrorMessage } from '../utils/errors';
import { makeIdempotencyKey } from '../utils/idempotency';
import { useSettingsIdempotencyHeader } from './';

type WalletInfo = {
  wallet?: {
    address?: string | null;
    chain_id?: string | null;
  } | null;
};

type UseWalletConnectionOptions = {
  initialWalletAddress?: string | null;
  initialWalletChainId?: string | null;
  onWalletChange?: (address: string | null) => void;
};

export function shortenAddress(address: string | null | undefined): string {
  if (!address) return '-';
  const trimmed = address.trim();
  if (trimmed.length <= 12) return trimmed;
  return `${trimmed.slice(0, 6)}...${trimmed.slice(-4)}`;
}

function describeChain(chainId: string | null | undefined): string | null {
  if (!chainId) return null;
  const trimmed = chainId.trim();
  if (!trimmed) return null;
  if (trimmed.startsWith('0x')) {
    const decimal = Number.parseInt(trimmed, 16);
    if (!Number.isNaN(decimal)) {
      return `${trimmed} (${decimal})`;
    }
  }
  return trimmed;
}

export function useWalletConnection({ initialWalletAddress, initialWalletChainId, onWalletChange }: UseWalletConnectionOptions = {}) {
  const [wallet, setWallet] = React.useState<string | null | undefined>(initialWalletAddress);
  const [chainId, setChainId] = React.useState<string | null>(initialWalletChainId ?? null);
  const [loading, setLoading] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<string | null>(null);
  const idempotencyHeader = useSettingsIdempotencyHeader();

  const shouldFetch = typeof initialWalletAddress === 'undefined';

  const loadWallet = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const profile = (await apiGet('/v1/profile/me')) as WalletInfo;
      const nextAddress = profile?.wallet?.address ?? null;
      const nextChain = profile?.wallet?.chain_id ?? null;
      setWallet(nextAddress);
      setChainId(nextChain);
      setStatus(null);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load wallet status'));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (shouldFetch) {
      void loadWallet();
    } else {
      setWallet(initialWalletAddress ?? null);
      setChainId(initialWalletChainId ?? null);
    }
  }, [shouldFetch, loadWallet, initialWalletAddress, initialWalletChainId]);

  const connectWallet = React.useCallback(async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const ethereum = (window as any)?.ethereum;
      if (!ethereum || typeof ethereum.request !== 'function') {
        setError('Wallet provider not detected. Install MetaMask or a compatible wallet and try again.');
        return;
      }

      const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
      const list = Array.isArray(accounts) ? accounts : [accounts];
      const firstAccount = list.find(Boolean);
      if (!firstAccount) {
        throw new Error('No wallet account returned from provider.');
      }
      const address = String(firstAccount);

      const providerChainId = await ethereum.request({ method: 'eth_chainId' }).catch(() => null);
      const normalizedChain = typeof providerChainId === 'string' ? providerChainId : null;

      let signature: string | null = null;
      try {
        const message = `Connect wallet to Caves at ${new Date().toISOString()}`;
        signature = await ethereum.request({
          method: 'personal_sign',
          params: [message, address],
        });
      } catch {
        signature = null;
      }

      const payload: Record<string, string | null> = {
        address,
        chain_id: normalizedChain,
        signature,
      };

      const headers: Record<string, string> = { [idempotencyHeader]: makeIdempotencyKey() };
      const result = (await apiPost('/v1/profile/me/wallet', payload, { headers })) as WalletInfo;
      const nextAddress = result?.wallet?.address ?? address;
      const nextChain = result?.wallet?.chain_id ?? normalizedChain;

      setWallet(nextAddress || null);
      setChainId(nextChain || null);
      setStatus('Wallet connected.');
      onWalletChange?.(nextAddress ?? null);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to connect wallet'));
    } finally {
      setBusy(false);
    }
  }, [busy, idempotencyHeader, onWalletChange]);

  const disconnectWallet = React.useCallback(async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const result = (await apiDelete('/v1/profile/me/wallet')) as WalletInfo;
      const nextAddress = result?.wallet?.address ?? null;
      const nextChain = result?.wallet?.chain_id ?? null;
      setWallet(nextAddress);
      setChainId(nextChain);
      setStatus('Wallet disconnected.');
      onWalletChange?.(nextAddress ?? null);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to disconnect wallet'));
    } finally {
      setBusy(false);
    }
  }, [busy, onWalletChange]);

  const chainLabel = React.useMemo(() => describeChain(chainId), [chainId]);
  const shortAddress = React.useMemo(() => shortenAddress(wallet ?? null), [wallet]);
  const isConnected = Boolean(wallet);

  return {
    wallet: wallet ?? null,
    chainId,
    chainLabel,
    shortAddress,
    isConnected,
    loading,
    busy,
    error,
    status,
    loadWallet,
    connectWallet,
    disconnectWallet,
  };
}