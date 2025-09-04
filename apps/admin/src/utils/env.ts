import { confirmDialog } from "../shared/ui";

function getEnv() {
  try {
    return (
      (import.meta as { env?: Record<string, string | undefined> })?.env ||
      {}
    );
  } catch {
    return {};
  }
}

export const ENV_MODE = getEnv().MODE || "";

export const isLocal = ENV_MODE === "local";
export const isPreviewEnv = ["local", "dev", "test"].includes(ENV_MODE);
export const ADMIN_DEV_TOOLS = getEnv().ADMIN_DEV_TOOLS === "1";

export async function confirmWithEnv(message: string): Promise<boolean> {
  return await confirmDialog(`${message}\n\nEnvironment: ${ENV_MODE}`);
}
