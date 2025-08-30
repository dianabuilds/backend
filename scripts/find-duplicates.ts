import { readFileSync } from "fs";

const file = process.argv[2];
if (!file) {
  console.error("Usage: tsx scripts/find-duplicates.ts <file>");
  process.exit(1);
}

const lines = readFileSync(file, "utf-8")
  .split(/\r?\n/)
  .filter(Boolean);

const counts = new Map<string, number>();
for (const line of lines) counts.set(line, (counts.get(line) ?? 0) + 1);

for (const [line, count] of counts) {
  if (count > 1) console.log(`${line}: ${count}`);
}
