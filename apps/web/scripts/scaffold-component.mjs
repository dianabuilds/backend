#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const webRoot = path.resolve(process.cwd(), 'apps/web');
const srcRoot = path.join(webRoot, 'ts/demo/src');

const [type, name, domain] = process.argv.slice(2);
if (!type || !name) {
  console.log('Usage: npm run scaffold -- <ui|shared|page> <Name> [domain|path]');
  process.exit(1);
}

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }); }
function write(p, c) { fs.writeFileSync(p, c, 'utf8'); }

const pascal = (s) => s.replace(/(^|[-_\s]+)([a-zA-Z])/g, (_, __, c) => c.toUpperCase());
const comp = pascal(name);

if (type === 'ui') {
  const dir = path.join(srcRoot, 'components/ui', comp);
  ensureDir(dir);
  const file = path.join(dir, 'index.tsx');
  write(file, `/**\n * @group: ui-kit\n * @component: ${comp}\n * @status: draft\n */\nimport clsx from "clsx";\nimport { ReactNode } from "react";\n\nexport function ${comp}({ className, children }: { className?: string; children?: ReactNode }) {\n  return <div className={clsx("${name.toLowerCase()}", className)}>{children}</div>;\n}\n`);
  console.log('Created UI component at', path.relative(webRoot, file));
} else if (type === 'shared') {
  if (!domain) { console.error('Provide shared domain, e.g., shared profile ProfileCard'); process.exit(1); }
  const dir = path.join(srcRoot, 'components/shared', domain, comp);
  ensureDir(dir);
  const file = path.join(dir, 'index.tsx');
  write(file, `/**\n * @group: shared\n * @component: ${comp}\n * @status: draft\n */\nimport { ReactNode } from "react";\n\nexport function ${comp}({ children }: { children?: ReactNode }) {\n  return <div>{children}</div>;\n}\n`);
  console.log('Created shared component at', path.relative(webRoot, file));
} else if (type === 'page') {
  const relPath = domain || comp; // accept path-like input
  const dir = path.join(srcRoot, 'app/pages', relPath);
  ensureDir(dir);
  const file = path.join(dir, 'index.tsx');
  write(file, `// Page: ${relPath}\nexport default function Page() {\n  return <div className="p-4">${comp} page</div>;\n}\n`);
  console.log('Created page at', path.relative(webRoot, file));
} else {
  console.error('Unknown type:', type);
  process.exit(1);
}

