#!/usr/bin/env node
// Prepare vscode/ for packaging: copy the payload (.claude/ → payload/claude/), the shared installer
// (lib/ → payload/lib/) and LICENSE, and sync the version from the root package.json.
// Then:  cd vscode && npx @vscode/vsce package   (or `publish`)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const EXT = path.join(ROOT, 'vscode');
const PAYLOAD = path.join(EXT, 'payload');
const skip = (src) => !/[\\/](__pycache__|\.DS_Store)$/.test(src);

fs.rmSync(PAYLOAD, { recursive: true, force: true });
fs.cpSync(path.join(ROOT, '.claude'), path.join(PAYLOAD, 'claude'), { recursive: true, filter: skip });
fs.cpSync(path.join(ROOT, 'lib'), path.join(PAYLOAD, 'lib'), { recursive: true, filter: skip });
if (fs.existsSync(path.join(ROOT, 'LICENSE'))) fs.copyFileSync(path.join(ROOT, 'LICENSE'), path.join(EXT, 'LICENSE'));

const root = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));
const extPkgFile = path.join(EXT, 'package.json');
const ext = JSON.parse(fs.readFileSync(extPkgFile, 'utf8'));
ext.version = root.version;
if (root.repository) ext.repository = root.repository;
fs.writeFileSync(extPkgFile, JSON.stringify(ext, null, 2) + '\n');

console.log(`Prepared vscode/ (${ext.publisher}.${ext.name} v${ext.version})`);
