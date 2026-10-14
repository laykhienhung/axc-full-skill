# Generated code conventions (match this repo's basecode)

Load before writing any `.ts`. The generated code MUST look like it belongs in this repo.

## Read the basecode first — do not assume

Before generating, read the current pattern (it evolves):
- `tests/pages/base.page.ts`      — Page Object base class
- `tests/pages/*.page.ts`         — existing POM style (locators in constructor)
- `tests/fixtures/test-fixtures.ts` — how POMs are exposed as fixtures
- `tests/e2e/*.spec.ts`           — spec style
- `playwright.config.ts`          — baseURL, projects, auth setup

## The three-file shape per feature

1. **Page Object** `tests/pages/<feature>.page.ts`
   - `extends BasePage`. All locators declared `readonly` and built in the constructor.
   - Actions are methods. NO raw selectors, coordinates, or class suffixes leak past this file.
2. **Fixture** — add one property to `tests/fixtures/test-fixtures.ts`:
   ```ts
   type Pages = { loginPage: LoginPage; <feature>Page: <Feature>Page; };
   // ...
   <feature>Page: async ({ page }, use) => { await use(new <Feature>Page(page)); },
   ```
3. **Spec** `tests/e2e/<module-slug>/<CASE-ID>.spec.ts`
   - Folder = the feature name kebab-cased (e.g. `Authentication` → `authentication/`).
     Reuse the folder if it exists so same-module cases group together; only create it when missing.
   - Import `{ test, expect }` from `../../fixtures/test-fixtures` (the extended test, never `@playwright/test` directly).
   - POMs arrive as fixtures — NO `new PageClass()` in the spec.
   - One `test()` per case. Map every case step to a POM call; comment step ranges
     (`// Steps 6–8: navigate`).
   - **Naming is UPPERCASE.** Spec filename uses the uppercase case id under its module folder
     (`tests/e2e/authentication/CARISDO-TC-1.spec.ts`).
     The `test()` title is the fully uppercase id + title:
     `test('CARISDO-TC-1: LOGIN THEN CREATE A PACKAGE CODE', ...)`. Page Object class/file names
     stay conventional (`PackageCodePage` / `package-code.page.ts`).

## Hard rules

- **No raw selectors in specs.** If you're tempted, add a method to the POM.
- **Assert on observable state** via `expect(...).toPass({timeout})` for grids/async UI,
  not fixed `waitForTimeout`.
- **Secrets (user, password, token, API key): env-only, NO literal fallback.**
  `const USER = process.env.TEST_USER; if (!USER) throw new Error('Set TEST_USER in .env');`
  A `?? '<case value>'` fallback for a secret bakes a plaintext credential into the repo — never do it.
  Non-secrets (baseURL, tenant, codes) MAY default: `process.env.BASE_URL ?? '<value>'`.
  The app loads `.env` via `dotenv/config` in `playwright.config.ts`; `.env` is gitignored.
- **Re-runnability:** if a step creates a record with a fixed unique key that already exists
  server-side, generate a unique value per run (e.g. `Date.now().toString(36)`), and say so in
  a comment. A literal re-run that hits a duplicate is a broken test, not a real failure.
- **Token-lean output:** no restating-the-code comments; comment only the non-obvious
  (grid quirks, deviations from the test case, why a value is randomized).

## Deviations from the test case

When reality differs from the written steps (missing dialog, different button label,
duplicate key), encode what actually works AND surface the deviation to the user in your
summary. Never silently follow a step that will hang or fail.
