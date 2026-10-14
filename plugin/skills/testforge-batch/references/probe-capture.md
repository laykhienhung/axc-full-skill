# Probe capture: selectors without the MCP

Screen agents run in parallel, and the Playwright MCP is a single shared browser, so batch agents capture selectors with **throwaway Node scripts** that launch their own headless browser. The rules are the same as `testforge-gen/references/playwright-capture.md` (role/label first, visible-only, confirm each effect, no DOM dumps). Only the driver differs.

## Where

`<os.tmpdir()>/testforge-probe/<slug>/probe-<n>.js` (CommonJS). Never inside the repo. Delete the whole `<slug>` directory before you return.

Run it from the repo root through the runner. The runner makes the repo's `node_modules` and `.env` resolvable from the temp dir:

```bash
node <pack>/skills/testforge-batch/scripts/run_probe.js "<tmp>/testforge-probe/<slug>/probe-1.js"
```

Always use exactly this form: no `NODE_PATH=` prefix, no `cd`, no `&&` chaining. The project permission rule matches this command only, and any other form falls back to the auto-mode classifier, which may block it.

## Template

```js
// probe-1.js — throwaway; answers "what locator addresses step N?"
require('dotenv').config({ path: process.env.REPO_ENV || '.env' });
const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const out = {};
  try {
    // login: same steps as tests/pages/login.page.ts
    await page.goto(process.env.BASE_URL);
    await page.getByPlaceholder(/^(enter )?username$/i).fill(process.env.TEST_USER);
    await page.getByPlaceholder(/^(enter )?password$/i).fill(process.env.TEST_PASS);
    await page.getByPlaceholder(/^(enter )?company code$/i).fill(process.env.TEST_TENANT);
    const loggedIn = page.waitForResponse(
      (r) => r.request().method() === 'POST' && /login/i.test(r.url()),
    );
    await page.getByRole('button', { name: /^log ?in$/i }).click();
    await loggedIn;
    await page.getByRole('menu').first().waitFor();

    // --- navigate to the screen, then test candidate locators ---
    const candidates = {
      search: page.getByRole('button', { name: /search/i }),
      bkgNo: page.getByLabel(/system bkg/i),
    };
    for (const [k, loc] of Object.entries(candidates)) {
      const n = await loc.count();
      const visible = [];
      for (let i = 0; i < n; i++) visible.push(await loc.nth(i).isVisible());
      out[k] = { count: n, visible };
    }

    // small, targeted DOM facts only — never page.content()
    out.buttons = await page.evaluate(() =>
      [...document.querySelectorAll('button')]
        .filter((b) => b.offsetWidth > 0 && b.offsetHeight > 0)
        .map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim())
        .filter(Boolean)
        .slice(0, 60),
    );
  } catch (e) {
    out.error = String(e).slice(0, 500);
    await page.screenshot({ path: __dirname + '/fail.png' });
  } finally {
    console.log(JSON.stringify(out));
    await browser.close();
  }
})();
```

## Rules

- **Small JSON out.** Counts, visibility, inner text, attribute values, capped lists. Never `page.content()` or a full accessibility tree. It overflows context the same way a full MCP snapshot does.
- **One question per probe.** Probe, read the JSON, decide, then write the next probe. Each probe re-logs in, which is expected and allowed.
- **Confirm effects.** After an action, probe the resulting state (a toast visible, a field value changed) before encoding the step.
- **Visible-only.** Hidden stale duplicates exist (see `devspec/improve/gotchas.md`). Reuse `clickFirstVisible()` / `fieldByLabel()` from `tests/common/locators.ts` in the POM. In a probe, check `isVisible()` per match.
- **Sidebar.** Use the `BasePage.navigateSidebar(top, submenu)` sequence. Set a wide viewport (1600×1000) if the submenu is off-screen.
- **Screenshots** of failures go in the probe directory only. Read one with the Read tool if the JSON isn't enough.
- **Grids** (IBSheet / ag-Grid): follow `testforge-gen/references/custom-grids.md`. Probe `window.IBSheet` / grid APIs via `page.evaluate` returning small objects. If, after 3 attempts, you can't drive the grid, mark the case `not-captured` with what you tried.
