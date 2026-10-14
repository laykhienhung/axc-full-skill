export const meta = {
  name: 'testforge-batch',
  description: 'Generate verified Playwright specs per screen from a batch plan, N screens in parallel',
  whenToUse: 'Invoked by the testforge-batch skill after the user confirms the plan table',
  phases: [{ title: 'Generate', detail: 'one agent per screen, capped at args.concurrency' }],
}

// args: { plan: <plan.json object>, concurrency: number, repoRoot: string, briefPath: string, packRoot: string }
const plan = args && args.plan
if (!plan || !Array.isArray(plan.screens)) throw new Error('args.plan with screens[] is required')
const repoRoot = args.repoRoot || '.'
// Where the skill pack lives: ".claude" when copied into the repo, the plugin cache dir when installed as a plugin.
const packRoot = args.packRoot || '.claude'
const briefPath = args.briefPath || `${packRoot}/skills/testforge-batch/references/agent-brief.md`
const cap = Math.max(1, Math.floor(Number(args.concurrency) || 5))

const screens = plan.screens
  .map((s) => ({ ...s, cases: s.cases.filter((c) => c.action !== 'skip') }))
  .filter((s) => s.cases.length > 0)
const skipped = plan.screens.length - screens.length
if (skipped) log(`${skipped} screen(s) have only skip cases — not dispatched`)

const RESULT = {
  type: 'object',
  properties: {
    screen: { type: 'string' },
    pomFile: { type: 'string' },
    specFiles: { type: 'array', items: { type: 'string' } },
    fixture: {
      type: 'object',
      properties: { name: { type: 'string' }, class: { type: 'string' }, import: { type: 'string' } },
      required: ['name', 'class', 'import'],
    },
    cases: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          specId: { type: 'string' },
          status: { type: 'string', enum: ['passed', 'failed', 'not-captured'] },
          attempts: { type: 'number' },
          deviations: { type: 'array', items: { type: 'string' } },
          error: { type: 'string' },
        },
        required: ['specId', 'status', 'attempts', 'deviations'],
      },
    },
    notes: { type: 'string' },
  },
  required: ['screen', 'pomFile', 'specFiles', 'fixture', 'cases'],
}

const prompt = (s) => `You are a testforge-batch screen agent. Repo root: ${repoRoot}
Skill pack root: ${packRoot} (paths in the brief written as \`<pack>/…\` or \`.claude/…\` live under it).

Read ${briefPath} and follow it exactly — it defines which files you may touch, how to capture
selectors (probe scripts, NEVER the Playwright MCP), the run/fix loop, cleanup, and your return shape.

Your screen plan entry:
${JSON.stringify(s, null, 2)}`

phase('Generate')
const results = new Array(screens.length).fill(null)
let next = 0
const lane = async () => {
  while (next < screens.length) {
    const i = next++
    const s = screens[i]
    log(`start ${s.screen} (${s.cases.length} case(s))`)
    try {
      results[i] = await agent(prompt(s), { label: `screen:${s.slug}`, phase: 'Generate', schema: RESULT })
    } catch (e) {
      log(`agent for ${s.screen} threw: ${String(e).slice(0, 200)}`) // lane keeps draining the queue
    }
    log(`done ${s.screen}: ${results[i] ? results[i].cases.filter((c) => c.status === 'passed').length + '/' + s.cases.length + ' passed' : 'agent failed'}`)
  }
}
await parallel(Array.from({ length: Math.min(cap, screens.length) }, () => lane))

return {
  concurrency: cap,
  results: results.filter(Boolean),
  failedScreens: screens
    .filter((_, i) => !results[i])
    .map((s) => ({ screen: s.screen, slug: s.slug, cases: s.cases.map((c) => c.specId) })),
}
