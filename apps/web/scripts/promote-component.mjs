#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.cwd(), 'apps/web');
const manifestPath = path.join(root, 'ui.manifest.json');
const kitPath = path.join(root, 'ui-kit/src/kit.ts');

const name = process.argv.slice(2).join(' ').trim();
if (!name) {
  console.error('Usage: npm run ui:promote -- <ComponentName>');
  process.exit(1);
}

function readJson(p) { return JSON.parse(fs.readFileSync(p, 'utf8')); }
function writeJson(p, o) { fs.writeFileSync(p, JSON.stringify(o, null, 2) + '\n'); }

const manifest = readJson(manifestPath);
const list = manifest.groups?.['ui-kit'] ?? [];
const item = list.find((x) => x.name.toLowerCase() === name.toLowerCase());
if (!item) {
  console.error(`Component not found in manifest: ${name}`);
  process.exit(1);
}

// Promote in manifest
item.status = 'core';
item.expose = true;
writeJson(manifestPath, manifest);

// Update kit barrel
const kitSrc = fs.readFileSync(kitPath, 'utf8');
const simpleName = item.name.replace(/[^A-Za-z0-9_]/g, '');
const already = new RegExp(`export\\s+\\{[^}]*\\b${simpleName}\\b`).test(kitSrc);
let addition = '';

// known multi-export components
const special = {
  Table: 'export { Table, TBody, TFoot, THead, Th, Tr, Td } from "@/components/ui/Table";\n',
  Pagination: 'export { Pagination, PaginationItems, PaginationNext, PaginationPrevious, PaginationFirst, PaginationLast } from "@/components/ui/Pagination";\n',
  Spinner: 'export { Spinner } from "@/components/ui/Spinner";\n',
};

if (!already) {
  if (special[simpleName]) {
    addition = special[simpleName];
  } else {
    addition = `export { ${simpleName} } from "@/components/ui/${simpleName}";\n`;
  }
  const updated = kitSrc.trimEnd() + '\n' + addition;
  fs.writeFileSync(kitPath, updated);
}

console.log(`Promoted to core: ${item.name}`);
if (addition) console.log('Updated kit barrel with export.');

