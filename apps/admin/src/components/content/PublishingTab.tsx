import PublishControls from '../publish/PublishControls';

interface PublishingTabProps {
  workspaceId: string;
  nodeId: number;
  onChanged?: () => void;
}

export default function PublishingTab({
  workspaceId,
  nodeId,
  onChanged,
}: PublishingTabProps) {
  return (
    <PublishControls
      workspaceId={workspaceId}
      nodeId={nodeId}
      onChanged={onChanged}
    />
  );
}
