#!/usr/bin/env node
import fs from 'node:fs';

const file = process.argv[2];
if (!file) {
  console.error('Usage: check_npm_audit.mjs <report.json>');
  process.exit(2);
}
const data = JSON.parse(fs.readFileSync(file, 'utf8'));
const critical = data?.metadata?.vulnerabilities?.critical ?? 0;
if (critical > 0) {
  console.error(`${critical} critical vulnerabilities found`);
  process.exit(1);
}
console.log('No critical vulnerabilities found');
