import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

interface Command {
  cmd: string;
  name: string;
  path: string;
}

const COMMANDS: Command[] = [
  { cmd: "ws", name: "Workspaces", path: "/workspaces" },
  { cmd: "sim", name: "Simulation", path: "/preview" },
  { cmd: "trace", name: "Traces", path: "/traces" },
  { cmd: "node:new", name: "New node", path: "/nodes/new" },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
        setQuery("");
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

  const matches = COMMANDS.filter(
    (c) =>
      c.cmd.startsWith(query.toLowerCase()) ||
      c.name.toLowerCase().includes(query.toLowerCase()),
  );

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cmd = matches[0];
    if (cmd) onSelect(cmd.path);
  };

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-24">
      <div className="w-80 rounded-lg bg-white shadow dark:bg-gray-800 p-2">
        <form onSubmit={onSubmit}>
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command..."
            className="w-full mb-2 px-2 py-1 border rounded bg-gray-50 dark:bg-gray-700"
          />
        </form>
        {matches.map((cmd) => (
          <button
            key={cmd.path}
            onClick={() => onSelect(cmd.path)}
            className="block w-full px-2 py-1 text-left hover:bg-gray-100 dark:hover:bg-gray-700 text-sm"
          >
            <span className="font-mono mr-2">{cmd.cmd}</span>
            {cmd.name}
          </button>
        ))}
        {matches.length === 0 && (
          <div className="px-2 py-1 text-sm text-gray-500">No commands</div>
        )}
      </div>
    </div>
  );
}
