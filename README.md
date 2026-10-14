# axc-full-skill

Claude Code skills for the whole delivery flow, installed with one command:

```
ProtoFlow (BA discovery → spec + prototype)  →  DevSpec (spec-driven build)  →  TestForge (Playwright E2E)
```

## Install

Three ways — pick one per repo (installing two gives you duplicate skills).

| Way | Command | Skills live in |
|---|---|---|
| npm / pnpm | `npx axc-full-skill init` | the repo's `.claude/` (commit it to share with the team) |
| Claude Code plugin | `/plugin install axc-full-skill --marketplace laykhienhung/axc-full-skill` | Claude Code's plugin cache (per user) |
| VS Code extension | **AXC Skills: Install Skills into Workspace** | the workspace's `.claude/` |

### Claude Code plugin

Inside Claude Code (terminal or the VS Code extension):

```
/plugin marketplace add laykhienhung/axc-full-skill
/plugin install axc-full-skill@axc-full-skill
```

As a plugin, skills are namespaced, e.g. `/axc-full-skill:devspec-plan` (the bare `/devspec-plan` also works when nothing else uses that name). Update with `/plugin marketplace update axc-full-skill`.

### VS Code extension

Install **AXC Full Skill for Claude Code** from the Extensions view, then run **AXC Skills: Install Skills into Workspace** from the Command Palette.

### npm / pnpm

Run in the root of the repo you want the skills in:

```bash
npx axc-full-skill init
```

```bash
pnpm dlx axc-full-skill init
```

This writes `.claude/skills/`, `.claude/commands/` and `.claude/references/` into the repo. It never touches anything else in `.claude/` (your `settings.json`, `CLAUDE.md`, or other skills). Restart Claude Code afterwards so it picks up the new skills.

Install it **per repo**, not in `~/.claude`: the skills address their shared files as `.claude/references/…` relative to the repo root.

## Update

```bash
npx axc-full-skill@latest update
```

A manifest (`.claude/.axc-full-skill.json`) records what was installed. On update:

- files you haven't edited are replaced with the new version
- files you **have** edited are kept, and listed as skipped (`--force` overwrites them)
- files dropped in the new version are removed if you never edited them

## Commands

| Command | Does |
|---|---|
| `init` | Install into `./.claude/` (an existing install is updated) |
| `update` | Upgrade a previous install |
| `list` | Show the installed version and skills |

Options: `--dir <path>` (target repo), `--force`, `--dry-run`.

## What's inside

| Pack | Skills / commands |
|---|---|
| **ProtoFlow** — for BAs | `/protoflow-new`, `-interview`, `-ground`, `-explore`, `-spec`, `-prototype`, `-status`, `-handoff`, `-guide` |
| **DevSpec** — spec-driven dev | `/devspec-init`, `-explore`, `-db-design`, `-ui-mockup`, `-capture`, `-plan`, `-work`, `-verify`, `-amend`, `-archive`, `-improve`, `-report`, `-caveman` |
| **TestForge** — E2E tests | `/testforge-gen`, `-batch`, `-convert`, `-extract` |

## Prerequisites

The skills are plain files; some of them call tools you set up per repo:

| Needed for | What |
|---|---|
| DevSpec `db-design` | Postgres MCP server + `DATABASE_URI` |
| DevSpec `verify`, TestForge `gen`/`batch` | Playwright MCP server (`@playwright/mcp`), `agent-browser` for verify |
| ProtoFlow scripts, TestForge scripts | Python 3 |
| DevSpec `init`/`explore` (optional) | A code-graph MCP (`code-review-graph` or `gitnexus`) |

## Releasing (maintainers)

`.claude/` is the source. The plugin (`plugin/`) and the extension payload (`vscode/payload/`) are generated from it — never edit them by hand.

```bash
npm version patch          # bump the version
npm run build              # regenerate plugin/ and vscode/payload/, sync versions
npm publish                # npm
git commit -am "release" && git push   # plugin marketplace (users get it on /plugin marketplace update)
cd vscode && npx @vscode/vsce publish  # VS Code Marketplace
```

| Path | What |
|---|---|
| `.claude/` | Skill source (npm payload) |
| `lib/installer.mjs` | Install/update logic shared by the CLI and the extension |
| `bin/cli.js` | npm CLI |
| `.claude-plugin/marketplace.json` | Claude Code marketplace (this repo) |
| `plugin/` | Generated Claude Code plugin — paths rewritten to `${CLAUDE_PLUGIN_ROOT}` |
| `vscode/` | VS Code extension (`payload/` is generated) |
| `scripts/` | `build-plugin.mjs`, `build-vscode.mjs` |
