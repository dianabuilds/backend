#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.cwd(), 'apps/web');
const manifestPath = path.join(root, 'ui.manifest.json');
const kitPath = path.join(root, 'ui-kit/src/kit.ts');

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function exists(p) {
  try { fs.statSync(p); return true; } catch { return false; }
}

function hasExport(name, kitSource) {
  const re = new RegExp(`export\\s+\\{[^}]*\\b${name}\\b[^}]*\\}\\s+from`);
  return re.test(kitSource);
}

try {
  const manifest = readJson(manifestPath);
  const items = manifest.groups?.["ui-kit"] ?? [];
  const widgets = manifest.groups?.["widgets"] ?? [];
  const kitSource = exists(kitPath) ? fs.readFileSync(kitPath, 'utf8') : '';

  const byStatus = { core: [], candidate: [], other: [] };
  for (const it of items) {
    (byStatus[it.status] ?? byStatus.other).push(it);
  }

  function rel(p) { return path.join('apps/web', p); }

  console.log('UI Registry:');
  console.log(`  core: ${byStatus.core.length}`);
  console.log(`  candidate: ${byStatus.candidate.length}`);
  const problems = [];

  for (const it of items) {
    const abs = path.join(root, it.path.replace(/\\/g, '/'));
    if (!exists(abs)) problems.push({ type: 'missing', name: it.name, path: rel(it.path) });
    if (it.expose && !hasExport(it.name.replace(/[^A-Za-z0-9_]/g, ''), kitSource)) {
      problems.push({ type: 'not-exported', name: it.name, path: 'ui-kit/src/kit.ts' });
    }
  }

  for (const w of widgets) {
    const abs = path.join(root, w.path);
    if (!exists(abs)) problems.push({ type: 'missing-widget', name: w.name, path: rel(w.path) });
  }

  if (problems.length) {
    console.log('\nIssues:');
    for (const p of problems) {
      console.log(`  - ${p.type}: ${p.name} -> ${p.path}`);
    }
    process.exitCode = 1;
  } else {
    console.log('\nAll good: paths exist and exports match.');
  }
} catch (e) {
  console.error('report-ui failed:', e.message);
  process.exitCode = 1;
}

