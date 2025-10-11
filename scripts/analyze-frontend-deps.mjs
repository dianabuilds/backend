#!/usr/bin/env node
import fs from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const args = process.argv.slice(2);
const checkMode = args.includes('--check') || args.includes('--ci');
const quietMode = args.includes('--quiet');

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');
const appRoot = path.join(repoRoot, 'apps', 'web');
const srcRoot = path.join(appRoot, 'src');
const outputDir = path.join(repoRoot, 'var', 'frontend-deps');
const tsConfigPath = path.join(appRoot, 'tsconfig.json');

const require = createRequire(import.meta.url);
const ts = require(path.join(appRoot, 'node_modules', 'typescript'));

const layerRank = {
  layout: 4,
  pages: 3,
  widgets: 2,
  features: 2,
  entities: 1,
  shared: 1,
};

const knownLayers = new Set(['layout', 'pages', 'widgets', 'features', 'entities', 'shared']);

function toPosix(p) {
  return p.split(path.sep).join('/');
}

function detectLayer(relativePath) {
  const normalized = toPosix(relativePath);
  const [first, second] = normalized.split('/');
  if (!first) return null;
  if (first === 'shared' && second === 'entities') {
    return 'entities';
  }
  if (knownLayers.has(first)) {
    return first;
  }
  return null;
}

function loadTsConfig(configPath) {
  const configFile = ts.readConfigFile(configPath, ts.sys.readFile);
  if (configFile.error) {
    throw new Error(
      ts.formatDiagnosticsWithColorAndContext([configFile.error], {
        getCanonicalFileName: (f) => f,
        getCurrentDirectory: ts.sys.getCurrentDirectory,
        getNewLine: () => ts.sys.newLine,
      }),
    );
  }
  const parsed = ts.parseJsonConfigFileContent(
    configFile.config,
    ts.sys,
    path.dirname(configPath),
    undefined,
    configPath,
  );
  return parsed;
}

function createLayerMatrix() {
  return new Map();
}

function incrementMatrix(matrix, fromLayer, toLayer) {
  if (!fromLayer) return;
  const target = toLayer ?? 'unknown';
  if (!matrix.has(fromLayer)) {
    matrix.set(fromLayer, new Map());
  }
  const inner = matrix.get(fromLayer);
  inner.set(target, (inner.get(target) ?? 0) + 1);
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

function resolveModule(moduleName, containingFile, options, host, cache, fallbackOptions) {
  const cacheKey = `${containingFile}:::${moduleName}`;
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
  }
  const primary = ts.resolveModuleName(moduleName, containingFile, options, host);
  let resolved = primary.resolvedModule ?? null;
  if (!resolved && fallbackOptions) {
    const fallback = ts.resolveModuleName(moduleName, containingFile, fallbackOptions, host);
    resolved = fallback.resolvedModule ?? null;
  }
  cache.set(cacheKey, resolved);
  return resolved;
}
function resolveStyleModule(spec, fromAbsolute) {
  const queryIndex = spec.indexOf('?');
  const cleanSpec = queryIndex >= 0 ? spec.slice(0, queryIndex) : spec;
  if (!cleanSpec.endsWith('.css')) {
    return null;
  }
  const fromDir = path.dirname(fromAbsolute);
  let resolvedPath = null;
  if (cleanSpec.startsWith('./') || cleanSpec.startsWith('../')) {
    resolvedPath = path.resolve(fromDir, cleanSpec);
  } else if (cleanSpec.startsWith('/')) {
    resolvedPath = path.join(appRoot, cleanSpec.slice(1));
  } else {
    try {
      resolvedPath = require.resolve(cleanSpec, { paths: [fromDir, appRoot] });
    } catch {
      return null;
    }
  }
  if (!resolvedPath || !existsSync(resolvedPath)) {
    return null;
  }
  return {
    resolvedFileName: resolvedPath,
    extension: path.extname(resolvedPath),
    isExternalLibraryImport: resolvedPath.includes('node_modules'),
  };
}
async function main() {
  const parsedConfig = loadTsConfig(tsConfigPath);
  const fallbackOptions = {
    ...parsedConfig.options,
    moduleResolution: ts.ModuleResolutionKind.NodeJs,
  };
  const compilerHost = ts.createCompilerHost(parsedConfig.options, true);
  const program = ts.createProgram({
    rootNames: parsedConfig.fileNames,
    options: parsedConfig.options,
    host: compilerHost,
  });

  const importCache = new Map();
  const edges = [];
  const unresolved = [];

  const sourceFiles = program
    .getSourceFiles()
    .filter((sf) => toPosix(sf.fileName).startsWith(toPosix(srcRoot)));

  for (const sourceFile of sourceFiles) {
    const fromAbsolute = sourceFile.fileName;
    const fromWithinSrc = path.relative(srcRoot, fromAbsolute);
    if (fromWithinSrc.startsWith('..')) {
      continue;
    }
    const fromNormalized = toPosix(fromWithinSrc);
    const fromLayer = detectLayer(fromWithinSrc);
    const seenForSource = new Set();

    function recordEdge(entry) {
      const key = `${entry.from}:::${entry.to ?? entry.importPath}`;
      if (seenForSource.has(key)) return;
      seenForSource.add(key);
      edges.push(entry);
    }

    function handleModuleSpecifier(moduleText, kind) {
      if (!moduleText) return;
      const spec = moduleText.trim();
      if (!spec || spec.startsWith('data:')) return;
      let resolved = resolveModule(
        spec,
        fromAbsolute,
        parsedConfig.options,
        compilerHost,
        importCache,
        fallbackOptions,
      );
      if (!resolved) {
        resolved = resolveStyleModule(spec, fromAbsolute);
      }
      if (!resolved) {
        unresolved.push({
          from: `src/${fromNormalized}`,
          importPath: spec,
          kind,
        });
        return;
      }
      if (resolved.isExternalLibraryImport || /node_modules/.test(resolved.resolvedFileName)) {
        return;
      }
      const targetAbsolute = path.resolve(resolved.resolvedFileName);
      let targetKind = 'internal';
      let targetRelative;
      let toLayer = null;
      if (toPosix(targetAbsolute).startsWith(toPosix(srcRoot))) {
        targetRelative = toPosix(path.relative(appRoot, targetAbsolute));
        const relWithinSrc = path.relative(srcRoot, targetAbsolute);
        toLayer = detectLayer(relWithinSrc);
      } else if (toPosix(targetAbsolute).startsWith(toPosix(path.join(appRoot, 'vendor')))) {
        targetKind = 'vendor';
        targetRelative = toPosix(path.relative(appRoot, targetAbsolute));
      } else {
        targetKind = 'local';
        targetRelative = toPosix(path.relative(repoRoot, targetAbsolute));
      }

      recordEdge({
        from: `src/${fromNormalized}`,
        fromLayer,
        to: targetRelative,
        toLayer,
        toKind: targetKind,
        importPath: spec,
        kind,
      });
    }

    function walk(node) {
      if (ts.isImportDeclaration(node) && node.moduleSpecifier) {
        const moduleText = node.moduleSpecifier.getText(sourceFile).replace(/^['"]|['"]$/g, '');
        handleModuleSpecifier(moduleText, 'import');
      } else if (
        ts.isExportDeclaration(node) &&
        node.moduleSpecifier &&
        ts.isStringLiteralLike(node.moduleSpecifier)
      ) {
        const moduleText = node.moduleSpecifier.text;
        handleModuleSpecifier(moduleText, 'export');
      } else if (
        ts.isCallExpression(node) &&
        node.expression.kind === ts.SyntaxKind.ImportKeyword &&
        node.arguments.length === 1 &&
        ts.isStringLiteralLike(node.arguments[0])
      ) {
        handleModuleSpecifier(node.arguments[0].text, 'dynamic-import');
      }
      ts.forEachChild(node, walk);
    }

    walk(sourceFile);
  }

  const layerMatrix = createLayerMatrix();
  const violations = [];

  for (const edge of edges) {
    if (edge.fromLayer) {
      incrementMatrix(layerMatrix, edge.fromLayer, edge.toLayer ?? edge.toKind);
    }
    if (edge.toKind === 'vendor') {
      violations.push({ ...edge, reason: 'Imports vendor module' });
      continue;
    }
    if (!edge.fromLayer || !edge.toLayer) {
      continue;
    }
    const fromRank = layerRank[edge.fromLayer];
    const toRank = layerRank[edge.toLayer];
    if (typeof fromRank === 'number' && typeof toRank === 'number' && fromRank < toRank) {
      violations.push({ ...edge, reason: `Disallowed upward import ${edge.fromLayer} -> ${edge.toLayer}` });
    }
  }

  const matrixObject = {};
  for (const [fromLayer, targets] of layerMatrix.entries()) {
    matrixObject[fromLayer] = {};
    for (const [toLayer, count] of targets.entries()) {
      matrixObject[fromLayer][toLayer] = count;
    }
  }

  const generatedAt = new Date().toISOString();
  const summary = `Dependency analysis: ${edges.length} edges, ${violations.length} violation(s), ${unresolved.length} unresolved import(s).`;

  if (!checkMode) {
    await ensureDir(outputDir);
    await fs.writeFile(
      path.join(outputDir, 'dependency-edges.json'),
      `${JSON.stringify({ generatedAt, edges, unresolved }, null, 2)}\n`,
      'utf8',
    );
    await fs.writeFile(
      path.join(outputDir, 'layer-matrix.json'),
      `${JSON.stringify({ generatedAt, matrix: matrixObject }, null, 2)}\n`,
      'utf8',
    );
    await fs.writeFile(
      path.join(outputDir, 'violations.json'),
      `${JSON.stringify({ generatedAt, violations }, null, 2)}\n`,
      'utf8',
    );
  }

  if (!quietMode) {
    if (checkMode) {
      console.log(summary);
    } else {
      console.log(`${summary} Report saved to ${path.relative(repoRoot, outputDir)}.`);
    }
  }

  if (unresolved.length > 0 && !quietMode) {
    console.warn(`[frontend-deps] Found ${unresolved.length} unresolved import(s). First:`, unresolved[0]);
  }

  if (violations.length > 0) {
    const header = `[frontend-deps] Found ${violations.length} layering violation(s).`;
    const details = violations.slice(0, 10).map((violation) => ` - ${violation.from} -> ${violation.to} (${violation.reason})`);
    const message = [header, ...details, violations.length > 10 ? ' - ...' : null].filter(Boolean).join('\n');
    console.error(message);
    if (checkMode) {
      process.exitCode = 1;
    }
  } else if (!quietMode) {
    console.log('[frontend-deps] No layering violations detected.');
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

