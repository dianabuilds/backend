interface Props {
  role: string;
}

export default function RoleBadge({ role }: Props) {
  const map: Record<string, string> = {
    owner: 'bg-blue-200 text-blue-800',
    editor: 'bg-green-200 text-green-800',
    viewer: 'bg-gray-200 text-gray-800',
  };
  const cls = map[role] || 'bg-gray-200 text-gray-800';
  return <span className={`px-2 py-0.5 rounded text-xs capitalize ${cls}`}>{role}</span>;
}
