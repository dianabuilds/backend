import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const COMMANDS = [
  { name: "Status", path: "/system/health" },
  { name: "Limits", path: "/ops/limits" },
  { name: "Trace", path: "/traces" },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  const onSelect = (path: string) => {
    setOpen(false);
    navigate(path);
  };

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-24">
      <div className="w-80 rounded-lg bg-white shadow dark:bg-gray-800">
        {COMMANDS.map((cmd) => (
          <button
            key={cmd.path}
            onClick={() => onSelect(cmd.path)}
            className="block w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {cmd.name}
          </button>
        ))}
      </div>
    </div>
  );
}
