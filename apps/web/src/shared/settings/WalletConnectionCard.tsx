import React from 'react';
import { Card, Button, Badge, Spinner, CopyButton } from '../ui';
import { CheckCircle2, Copy as CopyIcon } from '../icons';
import { useWalletConnection } from './useWalletConnection';

type WalletConnectionCardProps = {
  initialWalletAddress?: string | null;
  initialWalletChainId?: string | null;
  className?: string;
  onWalletChange?: (address: string | null) => void;
  title?: string;
  description?: string | null;
  showChain?: boolean;
};

export function WalletConnectionCard({
  initialWalletAddress,
  initialWalletChainId,
  className = '',
  onWalletChange,
  title = 'Wallet connection',
  description = 'Bind an EVM wallet to receive payouts and sign sensitive actions.',
  showChain = true,
}: WalletConnectionCardProps) {
  const {
    wallet,
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
  } = useWalletConnection({ initialWalletAddress, initialWalletChainId, onWalletChange });

  const composedClassName = `space-y-4 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm ${className}`.trim();

  return (
    <Card className={composedClassName}>
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
          {description && <p className="text-xs text-gray-500">{description}</p>}
        </div>
        <Badge color={isConnected ? 'success' : 'neutral'} variant="soft">
          {isConnected ? 'Connected' : 'Not connected'}
        </Badge>
      </div>

      {loading && (
        <div className="flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-500">
          <Spinner size="sm" /> Checking wallet status...
        </div>
      )}

      {status && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">{status}</div>
      )}
      {error && (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</div>
      )}

      <div className="rounded-xl border border-gray-200 bg-white/70 px-4 py-3 text-sm text-gray-600">
        {isConnected ? (
          <div className="space-y-2">
            <CopyButton value={wallet ?? ''}>
              {({ copy, copied }) => (
                <button
                  type="button"
                  onClick={copy}
                  className="group inline-flex items-center gap-2 font-mono text-sm text-gray-900"
                  title="Copy wallet address"
                >
                  <span className="truncate">{shortAddress}</span>
                  {copied ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  ) : (
                    <CopyIcon className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
                  )}
                </button>
              )}
            </CopyButton>
            {showChain && chainLabel && <div className="text-xs text-gray-500">Chain ID: {chainLabel}</div>}
          </div>
        ) : (
          'No wallet connected yet.'
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" size="sm" color="primary" onClick={connectWallet} disabled={busy}>
          {busy ? 'Connecting...' : isConnected ? 'Reconnect wallet' : 'Connect wallet'}
        </Button>
        {isConnected && (
          <Button type="button" size="sm" variant="ghost" color="neutral" onClick={disconnectWallet} disabled={busy}>
            Disconnect
          </Button>
        )}
        <Button type="button" size="sm" variant="ghost" color="neutral" onClick={() => void loadWallet()} disabled={busy || loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      <p className="text-[11px] text-gray-400">
        We attempt to use MetaMask when available. Install a compatible wallet extension if your browser cannot detect a provider.
      </p>
    </Card>
  );
}