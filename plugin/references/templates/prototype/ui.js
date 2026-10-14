// ProtoFlow prototype UI kit — written once by /protoflow-prototype, then preserved.
// Ready-made, domain-neutral components for every page type in .claude/references/prototype-ui.md (any industry: shop, booking,
// HR, finance, support, learning…), styled by app.css and themed with --brand. Screens compose these instead of hand-building markup: a screen is data + handlers + a few kit calls.
// Every builder returns a DOM node (or { el, close } for overlays). Pass `ref` to put a data-ref on the node.
// The API list below is extracted into .slices/_brief.md by protoflow_compile.py — keep one `export` per builder,
// with a one-line `//` comment directly above it.

// h("div", {class: "card", "data-ref": "SCR-001", onclick: fn}, child, "text", …) — null/undefined/false children are
// skipped, 0 is printed: SQLite booleans are 0/1, so write `row.flag ? h(…) : null`, never `row.flag && h(…)`.
export function h(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k.startsWith("on") && typeof v === "function") e.addEventListener(k.slice(2), v);
    else if (k === "value") e.value = v;
    else if (k === "ref") e.setAttribute("data-ref", v);
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat(Infinity)) if (c != null && c !== false) e.append(c.nodeType ? c : document.createTextNode(String(c)));
  return e;
}

const cx = (...c) => c.filter(Boolean).join(" ");
// Native append() prints null/false as text — every kit builder appends through put().
const put = (el, ...kids) => el.append(...kids.flat(Infinity).filter(k => k != null && k !== false));
const clean = kids => kids.flat(Infinity).filter(k => k != null && k !== false);
// Make an element's own append / prepend / replaceChildren skip null/false (for slots that screens re-fill): safe(el) → el.
export function safe(el) {
  for (const m of ["append", "prepend", "replaceChildren"]) { const orig = Element.prototype[m]; el[m] = (...k) => orig.apply(el, clean(k)); }
  return el;
}
const SVG = {
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z"/>',
  cart: '<path d="M3 4h2l2.4 11h10.2L20 8H6.2"/><circle cx="9" cy="19.5" r="1.3"/><circle cx="17" cy="19.5" r="1.3"/>',
  bag: '<path d="M5 8h14l-1 12H6L5 8Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
  left: '<path d="m15 5-7 7 7 7"/>', right: '<path d="m9 5 7 7-7 7"/>', down: '<path d="m5 9 7 7 7-7"/>',
  check: '<path d="m5 12 5 5 9-10"/>', plus: '<path d="M12 5v14M5 12h14"/>', minus: '<path d="M5 12h14"/>',
  trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>', menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  filter: '<path d="M4 5h16l-6 8v6l-4-2v-4L4 5Z"/>', star: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>', edit: '<path d="M4 20h4L19 9l-4-4L4 16v4Z"/>',
  pin: '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11Z"/><circle cx="12" cy="10" r="2.5"/>',
  box: '<path d="M3 7l9-4 9 4v10l-9 4-9-4V7Z"/><path d="M3 7l9 4 9-4M12 11v10"/>',
  truck: '<path d="M3 6h11v10H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/>',
  card: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>', chat: '<path d="M4 5h16v11H9l-5 4V5Z"/>',
  file: '<path d="M6 3h8l4 4v14H6V3Z"/><path d="M14 3v4h4"/>', home: '<path d="M4 11 12 4l8 7v9h-5v-6H9v6H4v-9Z"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1"/>',
  bell: '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4l2-2Z"/><path d="M10 20a2 2 0 0 0 4 0"/>', chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  send: '<path d="M4 12 20 4l-6 16-3-7-7-1Z"/>', lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>', clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
};
// Inline stroke icon: search heart cart bag user close left right down check plus minus trash menu filter star info edit pin box truck card
// calendar chat file home settings bell chart send lock mail clock.
export function icon(name, { fill = false, size } = {}) {
  const s = document.createElement("span");
  s.className = "ico";
  s.innerHTML = `<svg viewBox="0 0 24 24" fill="${fill ? "currentColor" : "none"}" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"${size ? ` width="${size}" height="${size}"` : ""}>${SVG[name] || SVG.info}</svg>`;
  return s;
}

const hash = s => { let x = 0; for (const c of String(s)) x = (x * 31 + c.charCodeAt(0)) | 0; return Math.abs(x); };
// Placeholder image (no stock photos): a soft two-tone gradient + simple shape picked from `seed`, optional caption.
export function art(seed, { label = "", ratio = "4/5", cls = "" } = {}) {
  const n = hash(seed), hue = n % 360, hue2 = (hue + 40 + (n >> 3) % 60) % 360, shape = (n >> 5) % 4;
  const shapes = ['<circle cx="50" cy="56" r="22"/>', '<rect x="30" y="34" width="40" height="44" rx="8"/>',
    '<path d="M50 28 76 78H24Z"/>', '<ellipse cx="50" cy="58" rx="26" ry="18"/>'];
  const d = h("div", { class: cx("art", cls), style: `aspect-ratio:${ratio}`, role: "img", "aria-label": label || "image" });
  d.innerHTML = `<svg viewBox="0 0 100 125" preserveAspectRatio="xMidYMid slice"><defs><linearGradient id="g${n}" x1="0" y1="0" x2="1" y2="1">` +
    `<stop offset="0" stop-color="hsl(${hue} 45% 88%)"/><stop offset="1" stop-color="hsl(${hue2} 40% 74%)"/></linearGradient></defs>` +
    `<rect width="100" height="125" fill="url(#g${n})"/><g fill="hsl(${hue} 35% 52% / .55)" transform="translate(0 6)">${shapes[shape]}</g></svg>`;
  return d;
}

// Page heading: { title, sub, ref, actions: [node], crumbs: [[label, onclick] | label] }.
export function pageHead({ title, sub, ref, actions = [], crumbs: c } = {}) {
  return h("div", {},
    c ? crumbs(c) : null,
    h("div", { class: "page-head" },
      h("div", { class: "grow" }, h("h1", { ref }, title), sub ? h("p", {}, sub) : null),
      actions.length ? h("div", { class: "actions" }, actions) : null));
}

// Breadcrumbs: [[label, onclick], …, "Current page"].
export function crumbs(items) {
  return h("nav", { class: "crumbs", "aria-label": "Breadcrumb" }, items.map((it, i) => [
    i ? h("span", { class: "sep" }, "/") : null,
    Array.isArray(it) ? h("a", { href: "#", onclick: e => { e.preventDefault(); it[1](); } }, it[0]) : h("span", {}, it)]));
}

// Button: label, onclick, { kind: primary|outline|ghost|danger|link, size: lg|sm, icon, ref, block, type, disabled }.
export function btn(label, onclick, { kind = "primary", size, icon: ic, ref, block, type = "button", disabled, title } = {}) {
  return h("button", { class: cx("btn", kind, size, block && "block"), type, onclick, ref, disabled, title },
    ic ? icon(ic) : null, label);
}

// Round icon button with optional count dot: iconBtn("cart", onclick, { count, label, ref, on }).
export function iconBtn(name, onclick, { count, label, ref, on } = {}) {
  return h("button", { class: cx("icon-btn", on && "on"), type: "button", onclick, ref, "aria-label": label || name, title: label || null },
    icon(name, { fill: !!on }), count ? h("span", { class: "dot" }, count > 99 ? "99+" : count) : null);
}

// Section panel: panel("Title" | null, ...children) — a white card with optional heading.
export function panel(title, ...kids) {
  return h("section", { class: "panel" }, title ? h("h3", {}, title) : null, kids);
}

// Responsive card grid: grid(nodes, { cols: 4, min: 180 }) — cols on desktop, collapses by min width.
export function grid(nodes, { cols = 4, min = 180, cls = "" } = {}) {
  return h("div", { class: cx("grid", cls), style: `--cols:${cols};--min:${min}px` }, nodes);
}

// Sideways-scrolling row of cards (home rows, "you may also like"): row(nodes, { min: 200 }).
export function row(nodes, { min = 200 } = {}) {
  return h("div", { class: "row-scroll", style: `--min:${min}px` }, nodes);
}

// Media card (any record with a picture: item, listing, room, course, article): { media: node (art()/img), media2, title, sub, meta: node,
//   tag, tagKind: brand|dark|ok|warn|bad, onclick, corner: node (e.g. a favourite iconBtn), quick: { label, onclick }, dim, ref }.
//   Hover zoom / 2nd image / quick button on desktop only.
export function mediaCard({ media, media2, title, sub, meta, tag, tagKind = "brand", onclick, corner, quick, dim, ref } = {}) {
  const stop = fn => e => { e.stopPropagation(); fn(e); };
  return h("article", { class: cx("mcard", dim && "dim"), onclick, ref, tabindex: onclick ? 0 : null,
    onkeydown: onclick ? e => { if (e.key === "Enter") onclick(e); } : null },
    h("div", { class: cx("media", media2 && "has-alt") },
      media ? h("div", { class: "m main" }, media) : null,
      media2 ? h("div", { class: "m alt" }, media2) : null,
      tag ? h("span", { class: cx("tag", tagKind) }, tag) : null,
      corner ? h("div", { class: "corner", onclick: e => e.stopPropagation() }, corner) : null,
      quick ? h("div", { class: "quick" }, btn(quick.label, stop(quick.onclick), { kind: "dark", block: true })) : null),
    h("div", { class: "body" }, h("div", { class: "title" }, title), sub ? h("div", { class: "sub" }, sub) : null, meta || null));
}

// Amount (price, fee, balance, score): amount(value, { was, fmt, big }) — shows the struck-through previous value when it differs.
export function amount(value, { was, fmt = String, big = false } = {}) {
  const changed = was != null && was !== value;
  return h("div", { class: cx("amount", big && "big") }, h("span", { class: changed ? "now" : null }, fmt(value)), changed ? h("s", {}, fmt(was)) : null);
}

// Label/value list for detail pages: kv([["Status", badge("Open", "ok")], ["Owner", "Ana"]], { cols: 2 }) — null rows are skipped.
export function kv(pairs, { cols = 1, ref } = {}) {
  return h("dl", { class: "kv", style: `--cols:${cols}`, ref }, pairs.filter(Boolean).map(([k, v]) => h("div", {}, h("dt", {}, k), h("dd", {}, v ?? "—"))));
}

// Timeline / history: timeline([{ title, when, text, kind: ok|warn|bad|brand }]) — order is up to the caller.
export function timeline(items, { ref } = {}) {
  return h("ol", { class: "timeline", ref }, items.map(i => h("li", { class: i.kind || null },
    h("div", { class: "t-title" }, i.title, i.when ? h("span", { class: "t-when" }, i.when) : null), i.text ? h("div", { class: "t-text" }, i.text) : null)));
}

// Conversation: chat({ messages: [{ me, who, text }], onsend: text => …, placeholder, ref }) → { el, add(msg), thinking(on) }.
export function chat({ messages = [], onsend, placeholder = "Write a message…", ref } = {}) {
  const list = h("div", { class: "chat" }), box = h("textarea", { rows: 2, placeholder, "aria-label": placeholder });
  const add = m => { list.append(h("div", { class: cx("bubble", m.me ? "me" : "them") }, m.who ? h("div", { class: "who" }, m.who) : null, m.text)); list.lastChild.scrollIntoView?.({ block: "end" }); };
  let dots = null;
  const thinking = on => { dots?.remove(); dots = on ? h("div", { class: "bubble them" }, h("span", { class: "spin" }), " Thinking…") : null; if (dots) list.append(dots); };
  const send = () => { const t = box.value.trim(); if (!t) return; box.value = ""; add({ me: true, text: t }); onsend?.(t); };
  box.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
  messages.forEach(add);
  return { el: h("div", { ref }, list, h("div", { class: "composer" }, box, btn("Send", send, { icon: "send" }))), add, thinking };
}

// Status / label pill: badge("In stock", "ok" | "warn" | "bad" | "brand" | "").
export function badge(text, kind = "") { return h("span", { class: cx("badge", kind) }, text); }

// Stat tiles: stats([["Orders", 12], ["Spent", "$420"]]).
export function stats(pairs) {
  return h("div", { class: "stats" }, pairs.map(([k, v]) => h("div", { class: "stat" }, h("div", { class: "k" }, k), h("div", { class: "v" }, v))));
}

// Data table: { cols: [{ key, label, render: row => node|text, align }], rows, onrow: row => …, empty: node, ref }.
export function table({ cols, rows, onrow, empty, ref } = {}) {
  if (!rows.length && empty) return empty;
  return h("div", { class: "table-wrap", ref }, h("table", {},
    h("thead", {}, h("tr", {}, cols.map(c => h("th", { style: c.align ? `text-align:${c.align}` : null }, c.label)))),
    h("tbody", {}, rows.map(r => h("tr", { onclick: onrow ? () => onrow(r) : null, class: onrow ? "click" : null },
      cols.map(c => h("td", { style: c.align ? `text-align:${c.align}` : null }, c.render ? c.render(r) : r[c.key])))))));
}

// Empty state: { icon, title, text, action: node } — always invite the next step.
export function emptyState({ icon: ic = "info", title, text, action } = {}) {
  return h("div", { class: "empty" }, h("div", { class: "empty-ico" }, icon(ic)), h("strong", {}, title), text ? h("p", {}, text) : null, action || null);
}

// Completion page: { icon: "check", title, text, actions: [node], ref } — the end of a flow.
export function result({ icon: ic = "check", title, text, actions = [], ref, children } = {}) {
  return h("div", { class: "result", ref }, h("div", { class: "result-ico" }, icon(ic)), h("h1", {}, title), text ? h("p", {}, text) : null,
    children || null, actions.length ? h("div", { class: "actions" }, actions) : null);
}

// Tabs: { items: [[key, label]], active, onchange: key => … } — pills; re-render on change.
export function tabs({ items, active, onchange } = {}) {
  return h("div", { class: "tabs", role: "tablist" }, items.map(([k, l]) =>
    h("button", { type: "button", role: "tab", class: k === active ? "on" : null, "aria-selected": String(k === active), onclick: () => onchange(k) }, l)));
}

// Side menu (account area, back-office): { items: [{ key, label, count, onclick, danger }], active }.
export function sideMenu({ items, active } = {}) {
  return h("nav", { class: "side-menu" }, items.map(i =>
    h("a", { href: "#", class: cx(i.key === active && "on", i.danger && "danger"), onclick: e => { e.preventDefault(); i.onclick?.(); } },
      i.label, i.count != null ? h("span", { class: "n" }, i.count) : null)));
}

// Two-column layout with a sticky aside: split(aside, main, { aside: 240 }) — stacks on small screens.
export function split(aside, main, { width = 240, right = false } = {}) {
  return h("div", { class: cx("split", right && "right"), style: `--aside:${width}px` }, right ? [main, h("aside", {}, aside)] : [h("aside", {}, aside), main]);
}

// Form field: field("Email", inputNode, { help, error, ref }) — label + control + helper + inline error slot (.err).
export function field(label, control, { help, error, ref } = {}) {
  return h("label", { class: "field", ref }, h("span", { class: "lbl" }, label), control,
    help ? h("span", { class: "help" }, help) : null, h("span", { class: "err" }, error || ""));
}

// Input/select/textarea: input({ name, type, value, placeholder, required, options: [[value, label]], rows, min, max, oninput }).
export function input({ options, rows, ...a } = {}) {
  if (options) return h("select", a, options.map(([v, l]) => h("option", { value: v, selected: String(v) === String(a.value) ? true : null }, l)));
  if (rows) return h("textarea", { rows, ...a });
  return h("input", { type: "text", ...a });
}

// Show / clear an inline field error: fieldError(inputEl, "Enter a valid email" | node | "").
export function fieldError(el, msg) {
  const f = el.closest(".field");
  el.setAttribute("aria-invalid", msg ? "true" : "false");
  if (f) f.querySelector(".err").replaceChildren(msg || "");
  return !msg;
}

// Form: form({ onsubmit, ref, narrow: true }, ...fields, actions) — submit handler gets (event, formData object).
export function form({ onsubmit, ref, narrow = true, cls } = {}, ...kids) {
  return h("form", { class: cx("form", narrow && "form-narrow", cls), ref, novalidate: true,
    onsubmit: e => { e.preventDefault(); onsubmit?.(e, Object.fromEntries(new FormData(e.target))); } }, kids);
}

// Submitting state: const done = busy(button, "Saving…"); … done(); — disables the button with a spinner + label.
export function busy(button, label = "Working…") {
  const old = [...button.childNodes];
  button.disabled = true;
  button.replaceChildren(h("span", { class: "spin" }), label);
  return () => { button.disabled = false; button.replaceChildren(...old); };
}

// Number stepper (quantity, seats, guests, days): stepper({ value, min: 1, max, onchange: v => …, small }) — buttons disable at the limits.
export function stepper({ value = 1, min = 1, max = 99, onchange, small, ref } = {}) {
  const out = h("span", {}, value);
  const dec = h("button", { type: "button", "aria-label": "Decrease" }, "−"), inc = h("button", { type: "button", "aria-label": "Increase" }, "+");
  // "+" stays clickable at the max (dimmed) so a press can explain the limit via onchange(value + 1, "max").
  const set = v => { value = v; out.textContent = v; dec.disabled = v <= min; inc.classList.toggle("at-max", v >= max); };
  dec.onclick = () => { if (value > min) { set(value - 1); onchange?.(value); } };
  inc.onclick = () => { if (value < max) { set(value + 1); onchange?.(value); } else onchange?.(value + 1, "max"); };
  set(value);
  return h("div", { class: cx("stepper", small && "small"), ref }, dec, out, inc);
}

// Option pills (single choice: size, plan, time slot, level): pills({ options: [{ value, label, out }], selected, onpick, ref }) — `out` = unavailable, struck through.
export function pills({ options, selected, onpick, ref } = {}) {
  return h("div", { class: "pills", ref }, options.map(o => h("button", { type: "button", class: cx("pill", o.value === selected && "on", o.out && "out"),
    "aria-pressed": String(o.value === selected), title: o.out ? `${o.label} — unavailable` : o.label, onclick: () => onpick(o.value, o) }, o.label)));
}

// Visual swatches (colour, theme, label colour): swatches({ options: [{ value, label, hex, out }], selected (value or Set), onpick }).
export function swatches({ options, selected, onpick, ref } = {}) {
  const on = v => (selected instanceof Set ? selected.has(v) : v === selected);
  return h("div", { class: "swatches", ref }, options.map(o => h("button", { type: "button", class: cx("swatch", on(o.value) && "on", o.out && "out"),
    "aria-pressed": String(on(o.value)), title: o.label, onclick: () => onpick(o.value, o) }, h("i", { style: `background:${o.hex}` }), h("span", {}, o.label))));
}

// Checkbox list (filters): checkList({ options: [{ value, label, count, child }], selected: Set, onchange: (value, checked) => … }).
export function checkList({ options, selected = new Set(), onchange } = {}) {
  return h("div", { class: "checks" }, options.map(o => h("label", { class: cx("check", o.child && "child") },
    h("input", { type: "checkbox", checked: selected.has(o.value) ? true : null, onchange: e => onchange(o.value, e.target.checked) }),
    h("span", {}, o.label), o.count != null ? h("span", { class: "n" }, o.count) : null)));
}

// Two-thumb range slider: range({ min, max, value: [lo, hi], step, fmt, onchange: ([lo, hi]) => … }) — fires on release.
export function range({ min, max, value = [min, max], step = 1, fmt = String, onchange } = {}) {
  const [a, b] = [h("input", { type: "range", min, max, step, value: value[0] }), h("input", { type: "range", min, max, step, value: value[1] })];
  const fill = h("div", { class: "fill" }), lab = h("div", { class: "range-lab" });
  const sync = () => {
    let lo = +a.value, hi = +b.value; if (lo > hi) [lo, hi] = [hi, lo];
    const p = v => ((v - min) / (max - min || 1)) * 100;
    fill.style.left = p(lo) + "%"; fill.style.right = 100 - p(hi) + "%";
    lab.replaceChildren(h("span", {}, fmt(lo)), h("span", {}, fmt(hi)));
    return [lo, hi];
  };
  a.oninput = b.oninput = sync; a.onchange = b.onchange = () => onchange?.(sync());
  sync();
  return h("div", {}, h("div", { class: "range" }, h("div", { class: "track" }), fill, a, b), lab);
}

// Filter sidebar: filters([{ title, body: node }], { onclear }) — titled groups, sticky on desktop.
export function filters(groups, { onclear } = {}) {
  return h("div", { class: "filters" }, groups.map(g => h("div", { class: "fgroup" }, h("h4", {}, g.title), g.body)),
    onclear ? btn("Clear all filters", onclear, { kind: "link" }) : null);
}

// Removable chip: chip("Status: Open", onremove, { key: true }) — key chips are highlighted (e.g. the search keyword).
export function chip(label, onremove, { key } = {}) {
  return h("button", { type: "button", class: cx("fchip", key && "key"), onclick: onremove, title: "Remove" }, label, onremove ? icon("close") : null);
}

// Toolbar row: toolbar(left nodes…, null, right nodes…) — a null entry pushes what follows to the right.
export function toolbar(...kids) { return h("div", { class: "toolbar" }, kids.map(k => (k === null ? h("div", { class: "grow" }) : k))); }

// Load-more footer: loadMore({ shown, total, onmore, noun: "items" }) — "Showing 24 of 60" + progress bar + button.
export function loadMore({ shown, total, onmore, noun = "items", label = "Load more" } = {}) {
  return h("div", { class: "more" }, h("div", {}, `Showing ${Math.min(shown, total)} of ${total} ${noun}`),
    h("div", { class: "bar" }, h("i", { style: `width:${Math.round((Math.min(shown, total) / (total || 1)) * 100)}%` })),
    shown < total ? btn(label, onmore, { kind: "outline" }) : null);
}

// Image gallery (photos, documents): gallery({ images: [node], start, ref }) — big image with fade, arrows, thumbnails, ←/→ keys.
export function gallery({ images, start = 0, ref } = {}) {
  let i = start;
  const big = h("div", { class: "g-big" }), thumbs = h("div", { class: "g-thumbs" });
  const show = n => {
    i = (n + images.length) % images.length;
    big.querySelector(".g-img")?.remove();
    big.prepend(h("div", { class: "g-img" }, images[i].cloneNode(true)));
    [...thumbs.children].forEach((t, k) => t.classList.toggle("on", k === i));
  };
  images.forEach((img, k) => thumbs.append(h("button", { type: "button", class: "g-thumb", "aria-label": `Image ${k + 1}`, onclick: () => show(k) }, img.cloneNode(true))));
  if (images.length > 1) big.append(h("button", { type: "button", class: "g-arrow l", "aria-label": "Previous image", onclick: () => show(i - 1) }, icon("left")),
    h("button", { type: "button", class: "g-arrow r", "aria-label": "Next image", onclick: () => show(i + 1) }, icon("right")));
  const el = h("div", { class: "gallery", ref, tabindex: 0, onkeydown: e => { if (e.key === "ArrowLeft") show(i - 1); if (e.key === "ArrowRight") show(i + 1); } },
    big, images.length > 1 ? thumbs : null);
  show(i);
  return el;
}

// Steps indicator (wizard / checkout): progress(["Shipping", "Payment", "Review"], 1).
export function progress(steps, at = 0) {
  return h("ol", { class: "progress" }, steps.map((s, k) => h("li", { class: cx(k < at && "done", k === at && "on") }, h("span", { class: "n" }, k < at ? icon("check") : k + 1), s)));
}

// Skeleton placeholders while loading: skeleton("card" | "line" | "row", count).
export function skeleton(kind = "card", n = 4) {
  const one = { card: () => h("div", { class: "sk-card" }, h("div", { class: "sk sk-media" }), h("div", { class: "sk sk-line" }), h("div", { class: "sk sk-line short" })),
    line: () => h("div", { class: "sk sk-line" }), row: () => h("div", { class: "sk sk-row" }) }[kind] || (() => h("div", { class: "sk sk-line" }));
  return h("div", { class: cx("skel", kind === "card" && "grid"), style: kind === "card" ? "--cols:4;--min:180px" : null, "aria-busy": "true" }, Array.from({ length: n }, one));
}

// Loading state: await loading(slot, skeleton("card", 8), () => content(), 350) — skeleton for `ms`, then the content.
export async function loading(slot, placeholder, build, ms = 350) {
  slot.replaceChildren(placeholder);
  await delay(ms);
  slot.replaceChildren(...[await build()].flat().filter(Boolean));
}

// Simulated latency for fake externals (payment, email, AI): await delay(800).
export const delay = ms => new Promise(r => setTimeout(r, ms));

// ---- overlays: appended to <body>, closed by Esc / backdrop / close button, and closed on every route change ----
function layer(cls, inner, { onclose, dismiss = true } = {}) {
  const wrap = h("div", { class: cx("layer", cls), "data-overlay": "" });
  let closed = false;
  const close = (why) => {
    if (closed) return; closed = true;
    wrap.classList.add("leaving");
    document.removeEventListener("keydown", esc);
    setTimeout(() => wrap.remove(), 180);
    onclose?.(why);
  };
  const esc = e => { if (e.key === "Escape" && dismiss) close("esc"); };
  wrap.addEventListener("mousedown", e => { if (e.target === wrap && dismiss) close("backdrop"); });
  document.addEventListener("keydown", esc);
  wrap.append(inner);
  document.body.append(wrap);
  wrap._close = close;
  return { el: inner, close };
}
const closeBtn = close => h("button", { type: "button", class: "icon-btn x", "aria-label": "Close", onclick: () => close("x") }, icon("close"));

// Slide-in drawer: drawer({ title, body, foot, side: "right"|"left", width, onclose, ref }) → { el, close, body, foot } (re-fill body/foot).
export function drawer({ title, body, foot, side = "right", width = 420, onclose, ref } = {}) {
  const b = safe(h("div", { class: "dr-body" }, body)), f = safe(h("div", { class: "dr-foot" }, foot));   // screens re-fill these
  const panelEl = h("div", { class: cx("drawer", side), style: `--w:${width}px`, ref, role: "dialog", "aria-label": title });
  const o = layer("dim", panelEl, { onclose });
  put(panelEl, h("div", { class: "dr-head" }, h("h2", {}, title), closeBtn(o.close)), b, f);   // foot hidden while empty (CSS)
  return { ...o, body: b, foot: f };
}

// Centered modal: modal({ title, body, width, onclose, ref, dismiss }) → { el, close }.
export function modal({ title, body, width = 460, onclose, ref, dismiss = true } = {}) {
  const box = h("div", { class: "modal", style: `--w:${width}px`, ref, role: "dialog", "aria-label": title });
  const o = layer("dim center", box, { onclose, dismiss });
  put(box, h("div", { class: "modal-head" }, title ? h("h2", {}, title) : h("span"), closeBtn(o.close)), body);
  return o;
}

// Yes/no decision: if (await confirm({ title, text, ok: "Remove", cancel: "Keep", danger: true, ref })) … — resolves true/false.
export function confirm({ title, text, ok = "Confirm", cancel = "Cancel", danger, ref } = {}) {
  return new Promise(res => {
    const box = h("div", { class: "modal confirm", ref, role: "alertdialog" });
    const o = layer("dim center", box, { onclose: why => res(why === "ok") });
    put(box, h("h3", {}, title), text ? h("p", {}, text) : null,
      h("div", { class: "actions" }, btn(cancel, () => o.close("cancel"), { kind: "outline" }), btn(ok, () => o.close("ok"), { kind: danger ? "danger" : "primary" })));
  });
}

// Drop-down sheet from the top (search overlay): sheet({ body, onclose, ref }) → { el, close }.
export function sheet({ body, onclose, ref } = {}) {
  const box = h("div", { class: "sheet", ref });
  const o = layer("dim from-top", box, { onclose });
  put(box, h("div", { class: "sheet-inner" }, closeBtn(o.close), body));
  return o;
}

// Rich toast card (e.g. "Added" / "Booked" with thumbnail + next-step buttons): toastCard({ title, body, actions: [node], ms: 4000, ref }) → { el, close }.
export function toastCard({ title, body, actions = [], ms = 4000, ref, icon: ic = "check" } = {}) {
  document.querySelectorAll(".tcard-layer").forEach(n => n._close?.());
  const box = h("div", { class: "tcard", ref, role: "status" });
  const wrap = h("div", { class: "tcard-layer", "data-overlay": "" }, box);
  let t;
  const close = () => { clearTimeout(t); wrap.classList.add("leaving"); setTimeout(() => wrap.remove(), 180); };
  wrap._close = close;
  put(box, h("div", { class: "tc-head" }, h("span", { class: "tc-ok" }, icon(ic)), h("strong", {}, title), closeBtn(close)),
    body ? h("div", { class: "tc-body" }, body) : null, actions.length ? h("div", { class: "tc-actions" }, actions) : null);
  box.addEventListener("click", e => { if (e.target.closest("button:not(.x)")) close(); });
  box.addEventListener("mouseenter", () => clearTimeout(t));
  box.addEventListener("mouseleave", () => { t = setTimeout(close, ms); });
  document.body.append(wrap);
  t = setTimeout(close, ms);
  return { el: box, close };
}

// Close every open overlay (drawer, modal, sheet, toast card) — the router calls this on each navigation.
export function closeOverlays() { document.querySelectorAll("[data-overlay]").forEach(n => (n._close ? n._close("route") : n.remove())); }

// Little "pop" animation for instant feedback (heart, badge): pop(node).
export function pop(node) { node.classList.remove("pop"); void node.offsetWidth; node.classList.add("pop"); return node; }

// Site footer: footer({ brand, columns: [[title, [label…]]], note }) — links are decorative ("coming soon" via onclick).
export function footer({ brand, columns = [], note, onlink } = {}) {
  return h("footer", { class: "foot" },
    h("div", { class: "foot-brand" }, brand),
    columns.map(([t, links]) => h("div", {}, h("h4", {}, t), links.map(l => h("a", { href: "#", onclick: e => { e.preventDefault(); onlink?.(l); } }, l)))),
    note ? h("div", { class: "foot-note" }, note) : null);
}
