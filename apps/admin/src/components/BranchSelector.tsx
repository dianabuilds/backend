import { useWorkspace } from "../workspace/WorkspaceContext";

export default function BranchSelector() {
  const { branch, setBranch } = useWorkspace();

  return (
    <input
      className="border rounded px-2 py-1"
      placeholder="branch"
      value={branch}
      onChange={(e) => setBranch(e.target.value)}
    />
  );
}

