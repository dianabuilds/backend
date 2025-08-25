export const ENV_MODE =
  (import.meta as { env?: Record<string, string | undefined> }).env?.MODE ||
  "";

export const isLocal = ENV_MODE === "local";
export const isPreviewEnv = ["local", "dev", "test"].includes(ENV_MODE);

export function confirmWithEnv(message: string) {
  return window.confirm(`${message}\n\nEnvironment: ${ENV_MODE}`);
}
