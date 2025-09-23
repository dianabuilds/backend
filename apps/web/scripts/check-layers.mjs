#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const webRoot = path.resolve(process.cwd(), 'apps/web');
const cfgPath = path.join(webRoot, 'layers.config.json');

function loadJson(p) { return JSON.parse(fs.readFileSync(p, 'utf8')); }
function readFile(p) { return fs.readFileSync(p, 'utf8'); }
function exists(p) { try { fs.statSync(p); return true; } catch { return false; } }

const cfg = loadJson(cfgPath);
const root = path.join(webRoot, cfg.root);
const aliasMap = Object.fromEntries(Object.entries(cfg.aliases).map(([k, v]) => [k, path.join(webRoot, v)]));

// Build layer detector
function classifyLayer(rel) {
  for (const l of cfg.layers) {
    for (const g of l.globs) {
      // naive glob: prefix match before ** or */
      const base = g.replace('/**', '').replace('**', '').replace('*', '');
      if (rel.startsWith(base)) return l.name;
    }
  }
  return 'unknown';
}

// Build quick resolver for imports
function resolveImport(fromFile, spec) {
  if (spec.startsWith('.')) {
    const abs = path.resolve(path.dirname(fromFile), spec);
    return resolveWithExtensions(abs);
  }
  // alias resolution
  const hit = Object.keys(aliasMap).find(a => spec === a || spec.startsWith(a + '/'));
  if (hit) {
    const tail = spec.slice(hit.length + (spec.length > hit.length ? 1 : 0));
    const abs = path.join(aliasMap[hit], tail);
    return resolveWithExtensions(abs);
  }
  // external or unknown
  return null;
}

const exts = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.mts', '.cts', '/index.ts', '/index.tsx', '/index.js'];
function resolveWithExtensions(abs) {
  for (const e of exts) {
    const p = abs.endsWith(e) ? abs : abs + e;
    if (exists(p)) return p;
  }
  return null;
}

// Scan files
function* walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else if (/\.(ts|tsx|js|jsx|mjs|cjs|mts|cts)$/.test(e.name)) yield p;
  }
}

const files = Array.from(walk(root));
const rules = new Map(cfg.rules.map(r => [r.from, new Set(r.allow)]));
const overrides = (cfg.overrides || []).map(o => ({
  re: new RegExp(o.file.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')),
  allowAlso: new Set(o.allowAlso || [])
}));
const problems = [];

const importRe = /import\s+(?:[^{'"`]*?\{?[^'"`]*?\}?\s+from\s+)?["'`]([^"'`]+)["'`]/g;
const dynImportRe = /import\(\s*["'`]([^"'`]+)["'`]\s*\)/g;

for (const f of files) {
  const rel = path.relative(path.join(webRoot, cfg.root), f).replace(/\\/g, '/');
  const fromLayer = classifyLayer(rel);
  if (fromLayer === 'unknown') continue;
  const allowed = new Set([...(rules.get(fromLayer) || [])]);
  // file-based overrides
  const relFile = path.relative(path.join(webRoot, cfg.root), f).replace(/\\/g, '/');
  for (const o of overrides) {
    if (o.re.test(relFile)) {
      for (const a of o.allowAlso) allowed.add(a);
    }
  }
  if (!allowed) continue; // unknown or unrestricted

  const src = readFile(f);
  const specs = new Set();
  for (const re of [importRe, dynImportRe]) {
    re.lastIndex = 0;
    let m; while ((m = re.exec(src))) specs.add(m[1]);
  }

  for (const spec of specs) {
    const target = resolveImport(f, spec);
    if (!target) continue; // external or unresolved
    const tRel = path.relative(path.join(webRoot, cfg.root), target).replace(/\\/g, '/');
    const toLayer = classifyLayer(tRel);
    if (toLayer === 'unknown') continue;
    if (!allowed.has(toLayer)) {
      problems.push({
        file: path.relative(webRoot, f),
        layer: fromLayer,
        import: spec,
        targetLayer: toLayer,
      });
    }
  }
}

if (problems.length) {
  console.log('Layer violations:');
  for (const p of problems) {
    console.log(`- [${p.layer}] ${p.file} -> (${p.targetLayer}) ${p.import}`);
  }
  process.exitCode = 1;
} else {
  console.log('Layers check: OK');
}
