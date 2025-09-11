#!/usr/bin/env node
/*
  Simple encoding utilities:
  - scan: prints files with BOM or U+FFFD characters
  - strip-bom: removes UTF-8 BOM from text files
*/
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', 'src');
const TEXT_EXT = new Set([
  '.ts',
  '.tsx',
  '.js',
  '.jsx',
  '.json',
  '.css',
  '.md',
  '.txt',
  '.svg',
  '.html',
]);

function isTextFile(p) {
  const ext = path.extname(p).toLowerCase();
  return TEXT_EXT.has(ext);
}

function walk(dir) {
  const res = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) res.push(...walk(p));
    else if (entry.isFile()) res.push(p);
  }
  return res;
}

function hasBOM(buf) {
  return buf.length >= 3 && buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf;
}

function scan() {
  const files = walk(ROOT).filter(isTextFile);
  const bom = [];
  const replacement = [];
  for (const f of files) {
    const buf = fs.readFileSync(f);
    if (hasBOM(buf)) bom.push(f);
    // scan for U+FFFD (EF BF BD)
    for (let i = 0; i < buf.length - 2; i++) {
      if (buf[i] === 0xef && buf[i + 1] === 0xbf && buf[i + 2] === 0xbd) {
        replacement.push(f);
        break;
      }
    }
  }
  if (bom.length) {
    console.log('Files with BOM:');
    bom.forEach((f) => console.log(' -', path.relative(ROOT, f)));
  } else {
    console.log('No BOM found');
  }
  if (replacement.length) {
    console.log('Files containing U+FFFD:');
    replacement.forEach((f) => console.log(' -', path.relative(ROOT, f)));
  } else {
    console.log('No U+FFFD found');
  }
  console.log(`Scanned ${files.length} files`);
}

function stripBOM() {
  const files = walk(ROOT).filter(isTextFile);
  let count = 0;
  for (const f of files) {
    const buf = fs.readFileSync(f);
    if (hasBOM(buf)) {
      fs.writeFileSync(f, buf.slice(3));
      count++;
    }
  }
  console.log(`Removed BOM from ${count} files`);
}

const cmd = process.argv[2] || 'scan';
if (cmd === 'scan') scan();
else if (cmd === 'strip-bom') stripBOM();
else {
  console.error('Unknown command:', cmd);
  process.exit(2);
}
