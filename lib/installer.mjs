// Shared install/update logic for the npm CLI (bin/cli.js) and the VS Code extension (vscode/extension.js).
// Owns only the files it installed, tracked in <repo>/.claude/.axc-full-skill.json.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export const SECTIONS = ['skills', 'commands', 'references'];
export const MANIFEST = '.axc-full-skill.json';
export const PACKS = { DevSpec: /^devspec-/, ProtoFlow: /^protoflow-/, TestForge: /^testforge-/ };

const sha = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const toAbs = (root, rel) => path.join(root, ...rel.split('/'));

// Payload files as posix-style paths relative to the payload root (manifest keys are OS-independent).
export function payloadFiles(payload) {
  const out = [];
  const walk = (dir, rel) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      if (e.name === '__pycache__' || e.name === '.DS_Store') continue;
      const r = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) walk(path.join(dir, e.name), r);
      else out.push(r);
    }
  };
  for (const s of SECTIONS) if (fs.existsSync(path.join(payload, s))) walk(path.join(payload, s), s);
  return out.sort();
}

export function readManifest(claudeDir) {
  const f = path.join(claudeDir, MANIFEST);
  if (!fs.existsSync(f)) return null;
  try {
    return JSON.parse(fs.readFileSync(f, 'utf8'));
  } catch {
    throw new Error(`${f} is not valid JSON — fix or delete it, then re-run with --force`);
  }
}

// Remove now-empty parent dirs up to (not including) the section root.
function pruneEmpty(claudeDir, rel) {
  const parts = rel.split('/');
  for (let n = parts.length - 1; n > 1; n--) {
    const d = toAbs(claudeDir, parts.slice(0, n).join('/'));
    if (fs.existsSync(d) && fs.readdirSync(d).length === 0) fs.rmdirSync(d);
    else break;
  }
}

/**
 * Install or update the payload into <targetDir>/.claude/.
 * @param {{payload: string, targetDir: string, name: string, version: string,
 *          mode?: 'init'|'update', force?: boolean, dryRun?: boolean}} o
 * @returns {{stats: Record<string,string[]>, claudeDir: string, fromVersion: string|null}}
 */
export function install({ payload, targetDir, name, version, mode = 'init', force = false, dryRun = false }) {
  const claudeDir = path.join(targetDir, '.claude');
  const old = readManifest(claudeDir);
  if (mode === 'update' && !old) throw new Error(`no previous install found in ${claudeDir} — run "init" first`);

  const oldFiles = old?.files ?? {};
  const files = payloadFiles(payload);
  const next = {};
  const stats = { added: [], updated: [], unchanged: [], skipped: [], removed: [], kept: [] };

  for (const rel of files) {
    const src = toAbs(payload, rel);
    const dest = toAbs(claudeDir, rel);
    const srcHash = sha(src);
    let action;
    if (!fs.existsSync(dest)) action = 'added';
    else {
      const destHash = sha(dest);
      if (destHash === srcHash) action = 'unchanged';
      else if (oldFiles[rel] === destHash || force) action = 'updated'; // ours and untouched, or forced
      else action = 'skipped'; // edited by the user, or a file we never installed
    }
    stats[action].push(rel);
    if (action === 'skipped') {
      if (oldFiles[rel]) next[rel] = oldFiles[rel]; // still ours; keep tracking the old hash so it stays "edited"
      continue;
    }
    next[rel] = srcHash;
    if ((action === 'added' || action === 'updated') && !dryRun) {
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.copyFileSync(src, dest);
    }
  }

  // Files we installed before that the new version no longer ships.
  for (const rel of Object.keys(oldFiles)) {
    if (rel in next || files.includes(rel)) continue;
    const dest = toAbs(claudeDir, rel);
    if (!fs.existsSync(dest)) continue;
    if (sha(dest) === oldFiles[rel] || force) {
      stats.removed.push(rel);
      if (!dryRun) {
        fs.rmSync(dest);
        pruneEmpty(claudeDir, rel);
      }
    } else stats.kept.push(rel);
  }

  if (!dryRun) {
    fs.mkdirSync(claudeDir, { recursive: true });
    const manifest = { name, version, installedAt: new Date().toISOString(), files: next };
    fs.writeFileSync(path.join(claudeDir, MANIFEST), JSON.stringify(manifest, null, 2) + '\n');
  }

  return { stats, claudeDir, fromVersion: old?.version ?? null };
}

/** Installed skills grouped by pack, or null when nothing is installed. */
export function listInstalled(targetDir) {
  const claudeDir = path.join(targetDir, '.claude');
  const m = readManifest(claudeDir);
  if (!m) return null;
  const skills = [...new Set(Object.keys(m.files).filter((f) => f.startsWith('skills/')).map((f) => f.split('/')[1]))];
  const packs = {};
  for (const [pack, re] of Object.entries(PACKS)) packs[pack] = skills.filter((s) => re.test(s));
  return { claudeDir, version: m.version, fileCount: Object.keys(m.files).length, packs };
}

export function summary(stats) {
  return (
    `added ${stats.added.length}, updated ${stats.updated.length}, unchanged ${stats.unchanged.length}, ` +
    `skipped ${stats.skipped.length}, removed ${stats.removed.length}`
  );
}
