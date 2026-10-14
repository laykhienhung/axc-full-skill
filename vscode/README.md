# AXC Full Skill for Claude Code

Installs a set of [Claude Code](https://claude.com/claude-code) skills into the folder you have open, covering the whole delivery flow:

```
ProtoFlow (BA discovery → spec + prototype)  →  DevSpec (spec-driven build)  →  TestForge (Playwright E2E)
```

## Usage

Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run:

| Command | Does |
|---|---|
| **AXC Skills: Install Skills into Workspace** | Writes `.claude/skills/`, `.claude/commands/` and `.claude/references/` into the open folder |
| **AXC Skills: Update Installed Skills** | Upgrades a previous install to this extension's version |
| **AXC Skills: Show Installed Skills** | Lists the installed version and skills |

Then start a new Claude Code session in that folder (terminal or the Claude Code extension) and the skills are available, e.g. `/devspec-explore`, `/protoflow-new`, `/testforge-gen`.

The extension never touches anything else in `.claude/` (`settings.json`, `CLAUDE.md`, your own skills). On update, files you edited are kept; you're offered to overwrite them.

## What's inside

| Pack | Commands |
|---|---|
| **ProtoFlow** — for BAs | `/protoflow-new`, `-interview`, `-ground`, `-explore`, `-spec`, `-prototype`, `-status`, `-handoff`, `-guide` |
| **DevSpec** — spec-driven dev | `/devspec-init`, `-explore`, `-db-design`, `-ui-mockup`, `-capture`, `-plan`, `-work`, `-verify`, `-amend`, `-archive`, `-improve`, `-report`, `-caveman` |
| **TestForge** — E2E tests | `/testforge-gen`, `-batch`, `-convert`, `-extract` |

## Other ways to install

- npm: `npx axc-full-skill init`
- Claude Code plugin: see the project README.
