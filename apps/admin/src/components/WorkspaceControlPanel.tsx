import { useEffect, useState } from "react";

import WorkspaceSelector from "./WorkspaceSelector";
import { safeLocalStorage } from "../utils/safeStorage";

export default function WorkspaceControlPanel() {
  const [plan, setPlan] = useState(() => safeLocalStorage.getItem("plan") || "");
  const [language, setLanguage] = useState(
    () => safeLocalStorage.getItem("language") || "",
  );

  useEffect(() => {
    try {
      if (plan) safeLocalStorage.setItem("plan", plan);
      else safeLocalStorage.removeItem("plan");
    } catch {
      /* ignore */
    }
  }, [plan]);

  useEffect(() => {
    try {
      if (language) safeLocalStorage.setItem("language", language);
      else safeLocalStorage.removeItem("language");
    } catch {
      /* ignore */
    }
  }, [language]);

  return (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      <WorkspaceSelector />
      <input
        className="border rounded px-2 py-1"
        placeholder="plan"
        value={plan}
        onChange={(e) => setPlan(e.target.value)}
      />
      <input
        className="border rounded px-2 py-1"
        placeholder="language"
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
      />
    </div>
  );
}

