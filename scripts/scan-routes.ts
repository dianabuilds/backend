import { readdirSync } from "fs";
import { join, resolve } from "path";

function walk(dir: string, matcher: (file: string) => boolean, acc: string[]) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) walk(full, matcher, acc);
    else if (entry.isFile() && matcher(full)) acc.push(full);
  }
}

const root = resolve(process.argv[2] ?? "apps/admin/src");
const routes: string[] = [];
walk(root, (file) => /route\.(t|j)sx?$/.test(file), routes);
for (const route of routes) console.log(route);
