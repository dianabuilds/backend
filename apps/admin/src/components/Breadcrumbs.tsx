import { Link, useLocation } from 'react-router-dom';

export default function Breadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split('/').filter(Boolean);

  if (segments.length === 0) return null;

  // Hide container segments that usually have no content pages
  const hidden = new Set(['ops', 'tools', 'settings', 'ai', 'content']);

  // Friendly labels for known segments
  const segmentMap: Record<string, string> = {
    preview: 'Simulation',
    nodes: 'Nodes',
    quests: 'Quests',
    tags: 'Tags',
    profile: 'Profile',
    payments: 'Payments',
    'feature-flags': 'Feature Flags',
    'rate-limit': 'Rate Limit',
    navigation: 'Navigation',
    monitoring: 'Monitoring',
    telemetry: 'Telemetry',
  };

  const items = segments
    .map((segment, index) => {
      const isLast = index === segments.length - 1;
      if (hidden.has(segment) && !isLast) return null; // skip containers except the last
      const to = '/' + segments.slice(0, index + 1).join('/');
      const labelRaw = segmentMap[segment] || segment.replace(/-/g, ' ');
      const text = labelRaw.charAt(0).toUpperCase() + labelRaw.slice(1);
      return { to, text, isLast, segment };
    })
    .filter((i): i is { to: string; text: string; isLast: boolean; segment: string } => Boolean(i))
    // Remove immediate duplicates (e.g. repeated segment labels)
    .filter((item, index, arr) => index === 0 || item.text !== arr[index - 1].text);

  return (
    <nav className="mb-4 text-sm text-gray-600 dark:text-gray-300" aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-1">
        <li>
          <Link to="/" className="hover:underline">
            Dashboard
          </Link>
        </li>
        {items.map((item) => (
          <li key={item.to} className="flex items-center gap-1">
            <span>/</span>
            {item.isLast || hidden.has(item.segment) ? (
              <span aria-current={item.isLast ? 'page' : undefined}>{item.text}</span>
            ) : (
              <Link to={item.to} className="hover:underline">
                {item.text}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
