// ProtoFlow prototype router + screen context — written once by /protoflow-prototype, then preserved.
// Routes: /<feature>/<SCR-id>[?key=value] (History API). Screens are listed in the generated screens.js.
// Requires serve.py's SPA fallback — it serves index.html for any path with no matching file,
// so a deep link or refresh on a route still resolves (there is no real file at that path).
import { openDb, query, one, run, resetDb, persisted } from "./db.js";
import * as S from "./screens.js";
import { h, closeOverlays } from "./ui.js";

const { FEATURES, SCREENS } = S;
const WALKS = S.WALKS ?? [];
const $ = s => document.querySelector(s);
// Review notes for every open item (ASSUMPTION / UNKNOWN / CONFLICT) of each screen — written by protoflow_compile.py
// --notes into notes.js and rendered under the page (review mode only). Screens add ctx.note() only for extras.
const NOTES = await import("./notes.js").then(m => m.NOTES).catch(() => ({}));
export { h };

function toast(msg, kind = "", ref = null) {
  const d = h("div", { class: kind, "data-ref": ref }, msg);
  $("#toast").append(d);
  setTimeout(() => d.remove(), 5000);
}

function parse() {
  const path = location.pathname.replace(/^\/|\/$/g, "");
  const [feature, scr] = path.split("/");
  return { feature, scr, params: Object.fromEntries(new URLSearchParams(location.search)) };
}

function go(scr, params = {}) {
  const f = FEATURES.find(x => x.screens.some(s => s.id === scr));
  const qs = new URLSearchParams(params).toString();
  const url = `/${f ? f.id : "_"}/${scr}${qs ? "?" + qs : ""}`;
  history.pushState(null, "", url);
  render();
}

function nav(active) {
  const n = $("#nav");
  n.replaceChildren();
  for (const f of FEATURES) {
    n.append(h("h3", {}, f.title));
    for (const s of f.screens)
      n.append(h("a", { href: `/${f.id}/${s.id}`, class: s.id === active ? "on" : null, "data-ref": s.id }, s.title));
  }
}

async function render() {
  const { scr, params } = parse();
  if (!scr || !SCREENS[scr]) {
    const first = FEATURES[0]?.screens[0];
    if (first) return go(first.id);
    return $("#main").replaceChildren(h("div", { class: "state empty" }, "No screens specified yet."));
  }
  nav(scr);
  closeOverlays();
  const main = $("#main");
  try {
    const mod = (await SCREENS[scr]()).default;
    main.replaceChildren();
    const ctx = {
      h, query, one, run, go, params, toast,
      // Append children to the page, skipping null/false (native append would print "null").
      add: (...kids) => main.append(...kids.flat(Infinity).filter(k => k != null && k !== false).map(k => (k.nodeType ? k : String(k)))),
      // Review-only note for ASSUMPTION / UNKNOWN / CONFLICT / simulated parts: hidden in the customer view.
      note: (kind, text, ref) => h("div", { class: "review-only", "data-ref": ref || null }, `${kind}: ${text}`),
      ok: msg => toast(msg, "ok"),
      // A business-rule check failed: show it citing the rule id, so the customer sees which BR fired.
      // msg is customer guidance; the rule id travels in data-ref only (visible with "show ids").
      violate: (br, msg) => { toast(msg, "bad", br); return h("div", { class: "violation", "data-ref": br }, msg); },
      rerender: render,
    };
    await mod.render(main, ctx);
    const notes = NOTES[scr] || [];
    if (notes.length) main.append(h("div", { class: "review-notes" }, notes.map(n => ctx.note(n.kind, n.text, n.ref))));
    reveal();
  } catch (e) {
    console.error(e);
    main.replaceChildren(h("div", { class: "state error" }, `Screen ${scr} failed to render: ${e.message}`));
  }
}

// Scroll effects: elements with class "reveal" fade in once they enter the viewport (purely visual, never blocks clicks).
const io = "IntersectionObserver" in window ? new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { rootMargin: "0px 0px -8% 0px" }) : null;
function reveal() { document.querySelectorAll(".reveal:not(.in)").forEach(n => (io ? io.observe(n) : n.classList.add("in"))); }

$("#refsToggle").addEventListener("change", e => document.body.classList.toggle("refs", e.target.checked));
// Review mode (BA only): screen list + review notes. Off by default so the customer sees the product.
const setReview = on => { document.body.classList.toggle("review", on); $("#reviewToggle").checked = on; try { localStorage.setItem("proto.review", on ? "1" : ""); } catch {} };
$("#reviewToggle").addEventListener("change", e => setReview(e.target.checked));
try { setReview(localStorage.getItem("proto.review") === "1"); } catch { setReview(false); }
$("#resetBtn").addEventListener("click", async () => { await resetDb(); toast("Data reset.", "ok"); render(); });
window.addEventListener("popstate", render);

document.addEventListener("click", e => {
  const a = e.target.closest("a[href]");
  if (!a || a.target || a.hasAttribute("download")) return;
  if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  const url = new URL(a.href, location.href);
  if (url.origin !== location.origin) return;
  e.preventDefault();
  if (url.pathname + url.search !== location.pathname + location.search) {
    history.pushState(null, "", url.pathname + url.search);
    render();
  }
});

function setDevPanel(open) {
  $("#devPanel").hidden = !open;
  $("#devTab").setAttribute("aria-expanded", String(open));
}
$("#devTab").addEventListener("click", () => setDevPanel($("#devPanel").hidden));
document.addEventListener("keydown", e => {
  const t = e.target;
  if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
  if (e.key === "`" && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); setDevPanel($("#devPanel").hidden); }
  else if (e.key === "Escape" && !$("#devPanel").hidden) setDevPanel(false);
});

// ---------------------------------------------------------------- self-test (review layer)
// window.protoSelftest() renders every screen sample listed in screens.js (`samples: [{ as, params }]`, default one
// visit as the current persona) and reports what the customer view must never show (.claude/references/prototype-ui.md):
// spec ids/words, raw enum codes (read from schema.sql check constraints), null/undefined/NaN/[object …], ISO
// timestamps, stray 0/true/false text, sideways scroll, an empty page, render errors and console errors.
// Data is reset before and after. Run it at each width the project supports (desktop; 375px too unless the prototype is desktop-only).
// protoSelftest({ only: ["SCR-003", …] }) checks just those screens: their samples + every walk that starts at or reaches them.
async function protoSelftest({ only } = {}) {
  const pick = id => !only || only.includes(id);
  const schema = await fetch("/schema.sql").then(r => r.text()).catch(() => "");
  const codes = [...new Set([...schema.matchAll(/check\s*\(\s*\w+\s+in\s*\(([^)]*)\)/gi)]
    .flatMap(m => m[1].match(/'([A-Z][A-Z0-9_]+)'/g) || []).map(c => c.slice(1, -1)))];
  const B = w => String.raw`\b(?:${w})\b`;   // whole word
  const LEAK = new RegExp([B(String.raw`(?:SCR|REQ|BR|FLOW|UC|ENT|AC)-\d+`), B("null|undefined|NaN"), String.raw`\[object`,
    String.raw`\d{4}-\d\d-\d\dT\d`, B("prototype|seed|Open question|Assumed|Conflict|Simulated|screens?|flows?|entit(?:y|ies)|requirements?"),
    ...codes.map(c => B(c))].join("|"), "g");
  const errors = [], origErr = console.error;
  console.error = (...a) => { errors.push(a.map(String).join(" ")); origErr(...a); };
  window.addEventListener("error", e => errors.push(e.message));
  const keep = { persona: localStorage.getItem("proto.persona"), review: document.body.classList.contains("review"), path: location.pathname + location.search };
  document.body.classList.remove("review");
  await resetDb();
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  // wait until redirects are done and the page has content: same URL and text for 300 ms (max ~3 s)
  const settle = async () => {
    let last = "";
    for (let i = 0; i < 30; i++) {
      await sleep(100);
      const now = location.href + "|" + $("#main").innerText.length;
      if (now === last && $("#main").innerText.trim().length >= 20 && i >= 3) return;
      last = now;
    }
  };
  const results = [];
  for (const f of FEATURES) for (const s of f.screens.filter(x => pick(x.id))) for (const smp of s.samples ?? [{}]) {
    await resetDb();                                      // every sample starts from the seed, independent of the others
    if (smp.as) try { localStorage.setItem("proto.persona", smp.as); } catch {}
    const qs = new URLSearchParams(smp.params || {}).toString();
    history.pushState(null, "", `/${f.id}/${s.id}${qs ? "?" + qs : ""}`);
    $("#toast").replaceChildren();
    await render(); await settle();
    const clone = h("div", {}, $("#main").cloneNode(true), [...document.querySelectorAll("[data-overlay]")].map(n => n.cloneNode(true)));
    clone.querySelectorAll(".review-only,[hidden],script,style").forEach(n => n.remove());
    // join text nodes with a separator — textContent glues "+" "null" "Add" into one word and hides the leak
    const parts = [], tw0 = document.createTreeWalker(h("div", {}, clone, $("#toast").cloneNode(true)), NodeFilter.SHOW_TEXT);
    for (let n = tw0.nextNode(); n; n = tw0.nextNode()) parts.push(n.data);
    const text = parts.join(" | ");
    const stray = [];
    const tw = document.createTreeWalker(clone, NodeFilter.SHOW_TEXT);
    for (let n = tw.nextNode(); n; n = tw.nextNode()) if (/^\s*(0|1|true|false)\s*$/.test(n.data) && !n.parentElement.closest(".v,.n,.stat,td,button,.stepper,.dot")) stray.push(n.data.trim());
    results.push({
      screen: s.id, as: smp.as ?? keep.persona ?? "", url: `/${f.id}/${s.id}${qs ? "?" + qs : ""}`, landed: location.pathname + location.search,
      leaks: [...new Set(text.match(LEAK) || [])].concat(stray.map(x => `stray "${x}"`)),
      hscroll: document.documentElement.scrollWidth > innerWidth + 1,
      empty: $("#main").innerText.trim().length < 20,
      failed: /failed to render/.test($("#main").innerText),
      errors: errors.splice(0),
    });
  }
  // Scripted walks (screens.js WALKS): click through each flow's happy path and trigger each rule, like the BA would.
  const walks = [];
  for (const w of WALKS.filter(w => pick(w.at) || (w.steps || []).some(st => st.expectAt && pick(st.expectAt)))) walks.push({ name: w.name, ...(await walk(w, settle)), errors: errors.splice(0) });
  console.error = origErr;
  await resetDb();
  try { keep.persona == null ? localStorage.removeItem("proto.persona") : localStorage.setItem("proto.persona", keep.persona); } catch {}
  document.body.classList.toggle("review", keep.review);
  history.pushState(null, "", keep.path); await render();
  const bad = results.filter(r => r.leaks.length || r.hscroll || r.empty || r.failed || r.errors.length);
  const badWalks = walks.filter(w => !w.ok || w.errors.length);
  return { width: innerWidth, visited: results.length, walks: walks.length, ok: !bad.length && !badWalks.length,
    problems: bad, walkProblems: badWalks, walked: walks.map(w => w.name) };
}

// One walk: { name, as, at: "SCR-002", params, steps: [ {click: "Add to cart" | "css:.mcard"}, {fill: {"Email": "x"}},
//   {expect: "text"}, {expectRule: "BR-006"}, {expectAt: "SCR-005"}, {wait: 300} ] }. Text matches are case-insensitive and
// prefer the top-most open overlay. Returns { ok } or { ok: false, step, error } — step is the index that failed.
async function walk(w, settle) {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const scope = () => [...[...document.querySelectorAll("[data-overlay]")].reverse(), $("#main"), document.body];
  const visible = n => !!(n.offsetWidth || n.offsetHeight || n.getClientRects().length) && !n.closest(".review-only,.dev-panel,#nav,.top,.dev-tab");
  const label = e => ((e.innerText || "").trim() || e.getAttribute("aria-label") || e.getAttribute("title") || "").toLowerCase();
  const find = q => {
    for (const root of scope()) {
      if (q.startsWith("css:")) { const n = [...root.querySelectorAll(q.slice(4))].find(visible); if (n) return n; continue; }
      const want = q.toLowerCase();
      const els = [...root.querySelectorAll("button,a,[role=button],[role=tab],label,article,[tabindex]")].filter(visible);
      const n = els.find(e => label(e) === want) || els.find(e => (e.getAttribute("aria-label") || "").toLowerCase() === want)
        || els.find(e => label(e).includes(want));
      if (n) return n;
    }
    return null;
  };
  const until = async (fn, ms = 2500) => { for (let t = 0; t < ms; t += 100) { if (fn()) return true; await sleep(100); } return !!fn(); };
  try {
    await resetDb();
    if (w.as) try { localStorage.setItem("proto.persona", w.as); } catch {}
    const f = FEATURES.find(x => x.screens.some(s => s.id === w.at));
    const qs = new URLSearchParams(w.params || {}).toString();
    history.pushState(null, "", `/${f ? f.id : "_"}/${w.at}${qs ? "?" + qs : ""}`);
    $("#toast").replaceChildren();
    await render(); await settle();
    for (const [i, st] of (w.steps || []).entries()) {
      const fail = error => ({ ok: false, step: i, error });
      if (st.click) {
        let n = null; await until(() => (n = find(st.click)));
        if (!n) return fail(`nothing to click: "${st.click}"`);
        n.click(); await sleep(st.wait ?? 400);
      } else if (st.fill) {
        for (const [k, v] of Object.entries(st.fill)) {
          let el = k.startsWith("css:") ? document.querySelector(k.slice(4)) : null;
          if (!el) for (const root of scope()) {
            const lab = [...root.querySelectorAll("label")].filter(visible)
              .find(l => (l.querySelector(".lbl")?.innerText || l.innerText || "").trim().toLowerCase().startsWith(k.toLowerCase()));
            el = lab?.querySelector("input,select,textarea") || root.querySelector(`[name="${k}"],[placeholder="${k}"]`);
            if (el) break;
          }
          if (!el) return fail(`no field "${k}"`);
          if (el.type === "checkbox") el.checked = !!v; else el.value = v;
          el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true }));
        }
        await sleep(150);
      } else if (st.expect) {
        const want = st.expect.toLowerCase();
        if (!(await until(() => scope().some(r => (r.innerText || "").toLowerCase().includes(want)))))
          return fail(`expected text "${st.expect}"`);
      } else if (st.expectRule) {
        if (!(await until(() => document.querySelector(`[data-ref="${st.expectRule}"]`)))) return fail(`rule ${st.expectRule} did not fire`);
      } else if (st.expectAt) {
        if (!(await until(() => location.pathname.endsWith("/" + st.expectAt) || document.querySelector(`[data-ref="${st.expectAt}"]`))))
          return fail(`expected ${st.expectAt}, at ${location.pathname}`);
      } else if (st.wait) await sleep(st.wait);
    }
    return { ok: true };
  } catch (e) { return { ok: false, error: String(e.message || e) }; }
}
window.protoSelftest = protoSelftest;

try {
  await openDb();
  if (!persisted) toast("Browser storage unavailable — data resets on reload.");
  render();
} catch (e) {
  console.error(e);
  $("#main").replaceChildren(h("div", { class: "state error" },
    "Could not start the local database. Serve this folder over http (python serve.py) and check the internet connection — SQLite-WASM loads from cdn.jsdelivr.net."));
}
