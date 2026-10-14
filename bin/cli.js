#!/usr/bin/env node
// axc-full-skill — installs the DevSpec + ProtoFlow + TestForge Claude Code skills into <repo>/.claude/
// Zero dependencies. Install logic lives in lib/installer.mjs (shared with the VS Code extension).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { install, listInstalled, summary } from '../lib/installer.mjs';

const PKG_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PKG = JSON.parse(fs.readFileSync(path.join(PKG_DIR, 'package.json'), 'utf8'));
const PAYLOAD = path.join(PKG_DIR, '.claude');

const HELP = `${PKG.name} v${PKG.version}

Usage: npx ${PKG.name} <command> [options]

Commands:
  init      Install skills, commands and references into ./.claude/
  update    Upgrade a previous install (keeps files you edited)
  list      Show what is installed

Options:
  --dir <path>   Target repo (default: current directory)
  --force        Overwrite files you edited / files not installed by ${PKG.name}
  --dry-run      Show what would change, write nothing
  -h, --help     Show this help
  -v, --version  Show version
`;

function parseArgs(argv) {
  const opts = { cmd: null, dir: process.cwd(), force: false, dryRun: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dir') opts.dir = path.resolve(argv[++i] ?? '.');
    else if (a === '--force') opts.force = true;
    else if (a === '--dry-run') opts.dryRun = true;
    else if (a === '-h' || a === '--help') opts.cmd = 'help';
    else if (a === '-v' || a === '--version') opts.cmd = 'version';
    else if (!a.startsWith('-') && !opts.cmd) opts.cmd = a;
    else fail(`Unknown argument: ${a}`);
  }
  return opts;
}

function fail(msg) {
  console.error(`error: ${msg}\n\n${HELP}`);
  process.exit(1);
}

function runInstall(opts, mode) {
  let result;
  try {
    result = install({ payload: PAYLOAD, targetDir: opts.dir, name: PKG.name, version: PKG.version, mode, ...opts });
  } catch (e) {
    fail(e.message);
  }
  const { stats, claudeDir, fromVersion } = result;
  if (mode === 'init' && fromVersion) console.log(`Found an existing install (v${fromVersion}) — updated it.\n`);

  const show = (label, list) => {
    if (!list.length) return;
    console.log(`${label} (${list.length}):`);
    for (const f of list.slice(0, 15)) console.log(`  ${f}`);
    if (list.length > 15) console.log(`  … and ${list.length - 15} more`);
  };
  show('Added', stats.added);
  show('Updated', stats.updated);
  show('Removed', stats.removed);
  show('Skipped — edited locally or not installed by this package (use --force to overwrite)', stats.skipped);
  show('Kept — dropped upstream but edited locally', stats.kept);

  const prefix = opts.dryRun ? '[dry-run] would have: ' : '';
  const ver = fromVersion && fromVersion !== PKG.version ? `v${fromVersion} → v${PKG.version}` : `v${PKG.version}`;
  console.log(`\n${prefix}${PKG.name} ${ver} in ${claudeDir}\n${summary(stats)}`);
  if (!opts.dryRun && (stats.added.length || stats.updated.length)) {
    console.log('\nRestart Claude Code (or start a new session) to pick up the new skills.');
  }
}

function list(opts) {
  let info;
  try {
    info = listInstalled(opts.dir);
  } catch (e) {
    fail(e.message);
  }
  if (!info) {
    console.log(`Not installed in ${path.join(opts.dir, '.claude')}. Run: npx ${PKG.name} init`);
    return;
  }
  console.log(`${PKG.name} v${info.version} in ${info.claudeDir} (${info.fileCount} files)\n`);
  for (const [pack, skills] of Object.entries(info.packs)) {
    if (skills.length) console.log(`${pack} (${skills.length}): ${skills.join(', ')}`);
  }
  if (info.version !== PKG.version) console.log(`\nv${PKG.version} is available: npx ${PKG.name}@latest update`);
}

const opts = parseArgs(process.argv.slice(2));
switch (opts.cmd) {
  case 'init':
  case 'install':
    runInstall(opts, 'init');
    break;
  case 'update':
  case 'upgrade':
    runInstall(opts, 'update');
    break;
  case 'list':
  case 'ls':
    list(opts);
    break;
  case 'version':
    console.log(PKG.version);
    break;
  case 'help':
  case null:
    console.log(HELP);
    break;
  default:
    fail(`Unknown command: ${opts.cmd}`);
}
