#!/usr/bin/env node
// Build the Claude Code plugin (plugin/) from the repo-install payload (.claude/).
//
// .claude/ is written for being copied into a repo, so its files address each other as `.claude/…`.
// A plugin lives in Claude Code's plugin cache instead, so paths are rewritten:
//   - SKILL.md and commands/*.md (Claude Code substitutes variables in these) → `${CLAUDE_PLUGIN_ROOT}/…`
//   - other docs (read later with the Read tool, no substitution)          → `<pack>/…`, and every
//     SKILL.md gets a line saying what `<pack>` is.
// Scripts and templates are copied unchanged. Re-run after every change to .claude/:  npm run build:plugin
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, '.claude');
const OUT = path.join(ROOT, 'plugin');
const PKG = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));
const SECTIONS = ['skills', 'commands', 'references'];
const VAR = '${CLAUDE_PLUGIN_ROOT}';

const PACK_NOTE =
  `> **Pack root:** \`${VAR}\`. In this pack's reference files, a path written as \`<pack>/…\` is under that root; ` +
  `project files (\`devspec/\`, \`protoflow/\`, \`tests/\`) stay relative to the working repo.\n`;

const isLoaded = (rel) => /^skills\/[^/]+\/SKILL\.md$/.test(rel) || /^commands\/[^/]+\.md$/.test(rel);
const isTemplate = (rel) => rel.startsWith('references/templates/');

function rewrite(rel, text) {
  if (isLoaded(rel)) {
    text = text
      .replace(/(^|[^\w./-])\.claude\/(references|skills)\//g, `$1${VAR}/$2/`)
      .replace(/\.\.\/\.\.\/references\//g, `${VAR}/references/`)
      .replace(/packRoot: "\.claude"/g, `packRoot: "${VAR}"`);
    if (rel.endsWith('SKILL.md')) text = text.replace(/^(---\r?\n[\s\S]*?\r?\n---\r?\n)/, `$1\n${PACK_NOTE}`);
    return text;
  }
  return text.replace(/(^|[^\w./-])\.claude\/(references|skills)\//g, '$1<pack>/$2/');
}

function copyDir(srcDir, rel) {
  for (const e of fs.readdirSync(srcDir, { withFileTypes: true })) {
    if (e.name === '__pycache__' || e.name === '.DS_Store') continue;
    const r = `${rel}/${e.name}`;
    const src = path.join(srcDir, e.name);
    const dest = path.join(OUT, ...r.split('/'));
    if (e.isDirectory()) {
      copyDir(src, r);
      continue;
    }
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    if (r.endsWith('.md') && !isTemplate(r)) fs.writeFileSync(dest, rewrite(r, fs.readFileSync(src, 'utf8')));
    else fs.copyFileSync(src, dest);
  }
}

fs.rmSync(OUT, { recursive: true, force: true });
for (const s of SECTIONS) copyDir(path.join(SRC, s), s);

const manifest = {
  name: PKG.name,
  version: PKG.version,
  description: PKG.description,
  author: PKG.author,
  homepage: PKG.homepage,
  repository: PKG.repository?.url ?? PKG.repository,
  license: PKG.license,
  keywords: PKG.keywords,
};
fs.mkdirSync(path.join(OUT, '.claude-plugin'), { recursive: true });
fs.writeFileSync(path.join(OUT, '.claude-plugin', 'plugin.json'), JSON.stringify(manifest, null, 2) + '\n');

// Keep the marketplace entry's version in step with the package.
const mpFile = path.join(ROOT, '.claude-plugin', 'marketplace.json');
const mp = JSON.parse(fs.readFileSync(mpFile, 'utf8'));
for (const p of mp.plugins) if (p.name === PKG.name) Object.assign(p, { version: PKG.version, description: PKG.description });
fs.writeFileSync(mpFile, JSON.stringify(mp, null, 2) + '\n');

// Anything still pointing at `.claude/…` outside templates would break inside the plugin cache.
const leftovers = [];
const scan = (dir, rel) => {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const r = rel ? `${rel}/${e.name}` : e.name;
    if (e.isDirectory()) scan(path.join(dir, e.name), r);
    else if (r.endsWith('.md') && !isTemplate(r) && /(^|[^\w./-])\.claude\/(references|skills)\//m.test(fs.readFileSync(path.join(dir, e.name), 'utf8')))
      leftovers.push(r);
  }
};
scan(OUT, '');
if (leftovers.length) {
  console.error(`Unrewritten .claude/ paths in:\n  ${leftovers.join('\n  ')}`);
  process.exit(1);
}
console.log(`Built plugin/ (${PKG.name} v${PKG.version})`);
