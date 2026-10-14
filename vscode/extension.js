// VS Code extension: installs the axc-full-skill Claude Code skills into the open workspace's .claude/.
// The install logic is the same module the npm CLI uses (payload/lib/installer.mjs, copied in by build-vscode).
const vscode = require('vscode');
const path = require('path');
const { pathToFileURL } = require('url');

const PAYLOAD = path.join(__dirname, 'payload', 'claude');
const NAME = 'axc-full-skill';
let out;

const loadInstaller = () => import(pathToFileURL(path.join(__dirname, 'payload', 'lib', 'installer.mjs')).href);

async function pickFolder() {
  const folders = vscode.workspace.workspaceFolders ?? [];
  if (folders.length === 0) {
    vscode.window.showErrorMessage('AXC Skills: open a folder first — skills are installed per repo.');
    return null;
  }
  if (folders.length === 1) return folders[0];
  return vscode.window.showWorkspaceFolderPick({ placeHolder: 'Install AXC skills into which folder?' });
}

async function run(ctx, mode, force = false) {
  const folder = await pickFolder();
  if (!folder) return;
  const { install, summary } = await loadInstaller();
  const version = ctx.extension.packageJSON.version;
  let result;
  try {
    result = install({ payload: PAYLOAD, targetDir: folder.uri.fsPath, name: NAME, version, mode, force });
  } catch (e) {
    vscode.window.showErrorMessage(`AXC Skills: ${e.message}`);
    return;
  }
  const { stats, claudeDir, fromVersion } = result;
  out.appendLine(`[${new Date().toLocaleTimeString()}] ${mode}${force ? ' --force' : ''} → ${claudeDir}`);
  for (const key of ['added', 'updated', 'removed', 'skipped', 'kept']) {
    for (const f of stats[key]) out.appendLine(`  ${key.padEnd(8)} ${f}`);
  }
  out.appendLine(`  ${summary(stats)}\n`);

  const ver = fromVersion && fromVersion !== version ? `v${fromVersion} → v${version}` : `v${version}`;
  const msg = `AXC Skills ${ver}: ${summary(stats)}.`;
  const actions = ['Show details'];
  if (stats.skipped.length) actions.unshift('Overwrite edited files');
  const changed = stats.added.length + stats.updated.length + stats.removed.length > 0;
  const pick = await vscode.window.showInformationMessage(
    changed ? `${msg} Start a new Claude Code session to load them.` : msg,
    ...actions,
  );
  if (pick === 'Show details') out.show();
  if (pick === 'Overwrite edited files') {
    const ok = await vscode.window.showWarningMessage(
      `Overwrite ${stats.skipped.length} file(s) you edited or that weren't installed by AXC Skills?`,
      { modal: true },
      'Overwrite',
    );
    if (ok === 'Overwrite') await run(ctx, mode, true);
  }
}

async function list() {
  const folder = await pickFolder();
  if (!folder) return;
  const { listInstalled } = await loadInstaller();
  const info = listInstalled(folder.uri.fsPath);
  if (!info) {
    const pick = await vscode.window.showInformationMessage('AXC Skills are not installed in this folder.', 'Install');
    if (pick === 'Install') vscode.commands.executeCommand('axcSkills.install');
    return;
  }
  out.appendLine(`${NAME} v${info.version} in ${info.claudeDir} (${info.fileCount} files)`);
  for (const [pack, skills] of Object.entries(info.packs)) {
    if (skills.length) out.appendLine(`  ${pack} (${skills.length}): ${skills.join(', ')}`);
  }
  out.appendLine('');
  out.show();
}

function activate(ctx) {
  out = vscode.window.createOutputChannel('AXC Skills');
  ctx.subscriptions.push(
    out,
    vscode.commands.registerCommand('axcSkills.install', () => run(ctx, 'init')),
    vscode.commands.registerCommand('axcSkills.update', () => run(ctx, 'update')),
    vscode.commands.registerCommand('axcSkills.list', list),
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
