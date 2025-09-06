import { useQuery } from "@tanstack/react-query";
import type { ChangeEvent } from "react";

import { useAccount } from "../account/AccountContext";
import { type Account,listAccounts } from "../api/accounts";
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
  const { data: accounts } = useQuery({
    queryKey: ["accounts", "all"],
    queryFn: () => listAccounts(),
  });
  const override = useOverrideStore();

  const onAccountChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    const account = accounts?.find((a) => a.id === id);
    setAccount(account);
  };

  const onRoleToggle = (r: string) => (e: ChangeEvent<HTMLInputElement>) => {
    const next = new Set(roles);
    if (e.target.checked) next.add(r);
    else next.delete(r);
    onRolesChange(Array.from(next));
  };

  const onOverrideToggle = (e: ChangeEvent<HTMLInputElement>) => {
    const enabled = e.target.checked;
    setOverrideState({ enabled, reason: enabled ? override.reason : "" });
  };

  return (
    <div className="flex flex-wrap items-center gap-2" data-testid="scope-controls">
      <select
        value={accountId || ""}
        onChange={onAccountChange}
        className="border rounded px-2 py-1 text-sm"
        data-testid="account-select"
      >
        <option value="">Select account</option>
        {accounts?.map((acc: Account) => (
          <option key={acc.id} value={acc.id}>
            {acc.name || acc.slug || acc.id}
          </option>
        ))}
      </select>
      <select
        value={scopeMode}
        onChange={(e) => onScopeModeChange(e.target.value)}
        className="border rounded px-2 py-1 text-sm"
        data-testid="scope-mode-select"
      >
        <option value="mine">mine</option>
        <option value="member">member</option>
        <option value="invited">invited</option>
        <option value="space">account</option>
        <option value="global">global</option>
      </select>
      <div className="flex items-center gap-2">
        {ROLE_OPTIONS.map((r) => (
          <label key={r} className="flex items-center gap-1 text-xs">
            <input
              type="checkbox"
              checked={roles.includes(r)}
              onChange={onRoleToggle(r)}
              data-testid={`role-${r}`}
            />
            <span>{r}</span>
          </label>
        ))}
      </div>
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

