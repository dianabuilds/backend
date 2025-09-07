import type { ChangeEvent } from "react";

import { useAccount } from "../account/AccountContext";
import { setOverrideState,useOverrideStore } from "../shared/hooks";

interface ScopeControlsProps {
  scopeMode: string;
  onScopeModeChange: (value: string) => void;
  roles: string[];
  onRolesChange: (roles: string[]) => void;
}

const ROLE_OPTIONS = ["reader", "editor", "admin"];

export default function ScopeControls({
  scopeMode,
  onScopeModeChange,
  roles,
  onRolesChange,
}: ScopeControlsProps) {
  const { accountId, setAccount } = useAccount();
  // Accounts domain is optional in this build.
  // We deliberately avoid fetching /admin/accounts to prevent 404 noise.
  const override = useOverrideStore();

  const onRoleToggle = (_r: string) => (_e: ChangeEvent<HTMLInputElement>) => {};

  const onOverrideToggle = (e: ChangeEvent<HTMLInputElement>) => {
    const enabled = e.target.checked;
    setOverrideState({ enabled, reason: enabled ? override.reason : "" });
  };

  return (
    <div className="flex flex-wrap items-center gap-2" data-testid="scope-controls">
      {/* Scope controls are handled by the top buttons in Nodes page.
          Keep only the Admin override toggles here to avoid duplication. */}
      <label className="flex items-center gap-1 text-xs">
        <input
          type="checkbox"
          checked={override.enabled}
          onChange={onOverrideToggle}
          data-testid="override-toggle"
        />
        <span>Admin override</span>
      </label>
      {override.enabled && (
        <input
          type="text"
          value={override.reason}
          onChange={(e) => setOverrideState({ reason: e.target.value })}
          placeholder="Override reason"
          className="border rounded px-2 py-1 text-sm"
          data-testid="override-reason"
        />
      )}
    </div>
  );
}
