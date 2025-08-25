import PageLayout from "./_shared/PageLayout";
import { seedDatabase, resetDatabase } from "../api/devtools";
import { confirmWithEnv, isLocal } from "../utils/env";
import { useToast } from "../components/ToastProvider";

export default function GettingStarted() {
  const { addToast } = useToast();
  if (!isLocal) return null;

  const seed = async () => {
    if (!confirmWithEnv("Seed database?")) return;
    try {
      await seedDatabase();
      addToast({ title: "Seed triggered", variant: "success" });
    } catch (e) {
      addToast({
        title: "Seed failed",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const reset = async () => {
    if (!confirmWithEnv("Reset database?")) return;
    try {
      await resetDatabase();
      addToast({ title: "Reset triggered", variant: "success" });
    } catch (e) {
      addToast({
        title: "Reset failed",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  return (
    <PageLayout title="Getting Started" subtitle="Local environment helpers">
      <div className="space-y-4">
        <div className="flex gap-2">
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white"
            onClick={seed}
          >
            Seed
          </button>
          <button
            className="px-3 py-1 rounded bg-red-600 text-white"
            onClick={reset}
          >
            Reset DB
          </button>
        </div>
        <ul className="list-disc ml-6 space-y-1">
          <li>
            <a
              href="http://localhost:8025"
              className="text-blue-600 hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              Mailhog
            </a>
          </li>
          <li>
            <a
              href="http://localhost:9000"
              className="text-blue-600 hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              MinIO
            </a>
          </li>
          <li>
            <a
              href="http://localhost:3000"
              className="text-blue-600 hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              Grafana
            </a>
          </li>
        </ul>
      </div>
    </PageLayout>
  );
}
