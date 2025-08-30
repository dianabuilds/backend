import { spawn } from "child_process";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const tsconfig = resolve(__dirname, "../apps/admin/tsconfig.json");

const child = spawn("npx", ["ts-unused-exports", tsconfig], {
  stdio: "inherit",
});
child.on("close", (code) => process.exit(code ?? 0));
