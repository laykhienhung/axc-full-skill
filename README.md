# axc-full-skill

Claude Code skills for the whole delivery flow, installed with one command:

```
ProtoFlow (BA discovery → spec + prototype)  →  DevSpec (spec-driven build)  →  TestForge (Playwright E2E)
```

## Install

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

```bash
npm version patch
npm publish
```
