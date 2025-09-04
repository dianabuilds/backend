import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    coverage: {
      enabled: true,
      provider: "v8",
      reporter: ["text"],
      include: ["src/components/StatusCell.tsx"],
      statements: 80,
      branches: 80,
      functions: 80,
      lines: 80,
    },
  },
});
