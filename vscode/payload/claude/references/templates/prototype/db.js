// ProtoFlow prototype local database — written once by /protoflow-prototype, then preserved.
// SQLite compiled to WASM, loaded from the CDN. Data lives in this browser only
// (localStorage via SQLite's kvvfs, or in memory if that is unavailable). Seed data only.
import sqlite3InitModule from "https://cdn.jsdelivr.net/npm/@sqlite.org/sqlite-wasm@3.46.1-build1/sqlite-wasm/jswasm/sqlite3.mjs";

let db = null;
export let persisted = false;

const hash = s => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return String(h); };

async function sources() {
  const [schema, seed] = await Promise.all(["schema.sql", "seed.sql"].map(f => fetch(new URL(f, import.meta.url)).then(r => r.text())));
  return { schema, seed, version: hash(schema + "\n" + seed) };
}

function dropAll() {
  const names = db.selectValues("select name from sqlite_master where type='table' and name not like 'sqlite_%'");
  db.exec("pragma foreign_keys=off");
  for (const n of names) db.exec(`drop table if exists "${n}"`);
  db.exec("pragma foreign_keys=on");
}

function load({ schema, seed, version }) {
  dropAll();
  db.exec(schema);
  db.exec(seed);
  db.exec("create table _proto_meta(k text primary key, v text)");
  db.exec({ sql: "insert into _proto_meta values('version', ?)", bind: [version] });
}

export async function openDb() {
  const sqlite3 = await sqlite3InitModule({ print: () => {}, printErr: console.error });
  try { db = new sqlite3.oo1.JsStorageDb("local"); persisted = true; }
  catch { db = new sqlite3.oo1.DB(":memory:", "c"); }
  db.exec("pragma foreign_keys=on");
  const src = await sources();
  const has = db.selectValue("select count(*) from sqlite_master where name='_proto_meta'");
  const current = has ? db.selectValue("select v from _proto_meta where k='version'") : null;
  if (current !== src.version) load(src); // schema or seed changed on re-scaffold → reseed
}

// Bind only when there are parameters: SQLite refuses a bind list for a statement without "?".
const b = p => (p && p.length ? p : undefined);
export const query = (sql, params = []) => db.selectObjects(sql, b(params));
export const one = (sql, params = []) => db.selectObject(sql, b(params)) ?? null;
export function run(sql, params = []) { db.exec({ sql, bind: b(params) }); return db.changes(); }
export async function resetDb() { load(await sources()); }
