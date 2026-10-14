#!/usr/bin/env node
// Runs one throwaway probe script with the repo's node_modules and .env available.
// A single fixed entry point, so one permission rule covers every probe:
//   node .claude/skills/testforge-batch/scripts/run_probe.js <tmp>/testforge-probe/<slug>/probe-N.js
const path = require('path');
const Module = require('module');

const probe = process.argv[2];
if (!probe) {
  console.error('usage: node run_probe.js <probe-file.js>');
  process.exit(2);
}

const repoRoot = path.resolve(__dirname, '../../../..');
// Resolve require('@playwright/test') etc. from the repo although the probe lives in tmp.
process.env.NODE_PATH = [path.join(repoRoot, 'node_modules'), process.env.NODE_PATH]
  .filter(Boolean)
  .join(path.delimiter);
Module._initPaths();
process.env.REPO_ENV = process.env.REPO_ENV || path.join(repoRoot, '.env');

require(path.resolve(probe));
