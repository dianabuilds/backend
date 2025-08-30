import { Link, useLocation } from "react-router-dom";

export default function Breadcrumbs() {
  const location = useLocation();
  const pathnames = location.pathname.split("/").filter(Boolean);

  if (pathnames.length === 0) {
    return null;
  }

  const segmentMap: Record<string, string> = {
    preview: "Simulation",
  };

  const items = pathnames
    .map((segment, index) => {
      const to = "/" + pathnames.slice(0, index + 1).join("/");
      const label = segmentMap[segment] || segment.replace(/-/g, " ");
      const text = label.charAt(0).toUpperCase() + label.slice(1);
      return { to, text };
    })
    // Remove duplicated segments to avoid repeated breadcrumbs
    .filter((item, index, arr) => index === 0 || item.text !== arr[index - 1].text);

  return (
    <nav className="mb-4 text-sm text-gray-600 dark:text-gray-300">
      <ol className="flex flex-wrap items-center gap-1">
        <li>
          <Link to="/" className="hover:underline">
            Dashboard
          </Link>
        </li>
        {items.map((item, index) => (
          <li key={item.to} className="flex items-center gap-1">
            <span>/</span>
            {index === items.length - 1 ? (
              <span>{item.text}</span>
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
