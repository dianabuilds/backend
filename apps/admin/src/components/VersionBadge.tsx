interface Props {
  version: number;
}

export default function VersionBadge({ version }: Props) {
  return <span className="px-2 py-0.5 rounded text-xs bg-blue-200 text-blue-800">v{version}</span>;
}
