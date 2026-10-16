// Île Éclair : serveur temps réel + comptes pour Cloudflare Workers (Durable Object, offre gratuite).
import { DurableObject } from 'cloudflare:workers';

const MAX_PLAYERS = 12, MAX_ACCOUNTS = 5000;
const TOPICS = new Set(['shot', 'bs', 'kill', 'wall', 'chest']);
const UR = /^[A-Za-z0-9_-]{3,14}$/, HEX = /^#[0-9a-f]{6}$/i, KEY = /^[0-9a-f]{64}$/;
const enc = new TextEncoder();
const hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, '0')).join('');
const sha = async t => hex(await crypto.subtle.digest('SHA-256', enc.encode(t)));
const rnd = n => hex(crypto.getRandomValues(new Uint8Array(n)));
const same = (a, b) => { if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; };
const int = (v, a, b) => Math.max(a, Math.min(b, Number.isFinite(+v) ? Math.trunc(+v) : a));
const num = v => typeof v === 'number' && Number.isFinite(v);

function cleanP(p) {
  p = p && typeof p === 'object' ? p : {};
  const o = p.own || {}, l = p.look || {}, A = (a, f, n) => Array.isArray(a) ? a.filter(f).slice(0, n) : [];
  return {
    tk: int(p.tk, 0, 1e6), kp: int(p.kp, 0, 2),
    own: { c: A(o.c, x => typeof x === 'string' && HEX.test(x), 30), h: A(o.h, Number.isInteger, 10), k: A(o.k, Number.isInteger, 10), pal: !!o.pal },
    look: { c: HEX.test(l.c) ? l.c : '#3da5ff', s: int(l.s, 0, 5), h: int(l.h, 0, 4), k: int(l.k, 0, 6) }
  };
}
function cleanPatch(p) {
  if (!p || typeof p !== 'object' || Array.isArray(p)) return null;
  const out = {};
  for (const [k, v] of Object.entries(p)) {
    if (v === null) { if (k === 't' || k === 'b') out[k] = null; continue; }
    if (k === 'n') { if (typeof v === 'string') out.n = v.replace(/[\u0000-\u001f<>]/g, '').slice(0, 14); }
    else if (k === 'c') { if (typeof v === 'string' && HEX.test(v)) out.c = v; }
    else if (['s', 'h', 'k', 'w', 'g'].includes(k)) { if (Number.isInteger(v) && v >= 0 && v <= 9) out[k] = v; }
    else if (['x', 'y', 'z', 'a', 'hp', 't'].includes(k)) { if (num(v)) out[k] = v; }
    else if (k === 'b') {
      if (Array.isArray(v) && v.length <= 24 && v.every(r => Array.isArray(r) && r.length <= 5 && r.every(z => num(z) || (typeof z === 'string' && z.length <= 40)))) out.b = v;
    }
  }
  return out;
}
const merge = (t, p) => { for (const k in p) { if (p[k] === null) delete t[k]; else t[k] = p[k]; } };
const trim = pr => { const { b, ...rest } = pr; return rest; };   // le tableau des bots n'est pas gardé pendant la veille

export class Room extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.pres = new Map();   // id -> présence
    this.meta = new Map();   // id -> { key, ip, saved }
    this.ids = new WeakMap();
    this.buckets = new Map();
    this.fails = new Map();
    for (const ws of ctx.getWebSockets()) {        // reconstruction après une veille
      const a = ws.deserializeAttachment();
      if (a && a.id) { this.ids.set(ws, a.id); this.pres.set(a.id, a.pr || {}); this.meta.set(a.id, { key: a.key || null, ip: a.ip || '', saved: Date.now() }); }
    }
    ctx.storage.sql.exec('CREATE TABLE IF NOT EXISTS acc (k TEXT PRIMARY KEY, u TEXT, salt TEXT, hash TEXT, toks TEXT, p TEXT)');
  }

  idOf(ws) { let id = this.ids.get(ws); if (!id) { const a = ws.deserializeAttachment(); id = a && a.id; if (id) this.ids.set(ws, id); } return id; }
  bcast(fromId, obj) {
    const s = JSON.stringify(obj);
    for (const w of this.ctx.getWebSockets()) { if (this.idOf(w) !== fromId) { try { w.send(s); } catch {} } }
  }
  persist(ws, id, force) {
    const m = this.meta.get(id); if (!m) return;
    if (!force && Date.now() - m.saved < 2000) return;
    m.saved = Date.now();
    try { ws.serializeAttachment({ id, key: m.key, ip: m.ip, pr: trim(this.pres.get(id) || {}) }); } catch {}
  }

  async fetch(req) {
    if (req.headers.get('Upgrade') !== 'websocket') return new Response('Île Éclair : serveur OK', { headers: { 'content-type': 'text/plain; charset=utf-8' } });
    const pair = new WebSocketPair(), client = pair[0], server = pair[1];
    if (this.ctx.getWebSockets().length >= MAX_PLAYERS) {
      server.accept(); server.send(JSON.stringify({ t: 'full' })); server.close(1013, 'complet');
      return new Response(null, { status: 101, webSocket: client });
    }
    const id = rnd(4), ip = req.headers.get('CF-Connecting-IP') || '';
    this.ctx.acceptWebSocket(server);
    this.ids.set(server, id); this.pres.set(id, {}); this.meta.set(id, { key: null, ip, saved: 0 });
    this.persist(server, id, true);
    const peers = {}; for (const [k, v] of this.pres) if (k !== id) peers[k] = v;
    server.send(JSON.stringify({ t: 'init', id, peers }));
    this.bcast(id, { t: 'join', id });
    return new Response(null, { status: 101, webSocket: client });
  }

  blocked(ip) { const f = this.fails.get(ip); return f && f.until > Date.now(); }
  fail(ip) { const f = this.fails.get(ip) || { n: 0, until: 0 }; if (++f.n >= 8) { f.until = Date.now() + 5 * 60e3; f.n = 0; } this.fails.set(ip, f); }
  row(key) { return this.ctx.storage.sql.exec('SELECT * FROM acc WHERE k = ?', key).toArray()[0]; }

  async webSocketMessage(ws, raw) {
    if (typeof raw !== 'string' || raw.length > 16384) return;
    const id = this.idOf(ws); if (!id) return;
    const now = Date.now(), b = this.buckets.get(id) || { t: 300, l: now };
    b.t = Math.min(300, b.t + (now - b.l) * 0.15); b.l = now; this.buckets.set(id, b);
    if (b.t < 1) return; b.t--;
    let m; try { m = JSON.parse(raw); } catch { return; }
    if (!m || typeof m !== 'object') return;
    const meta = this.meta.get(id) || { key: null, ip: '', saved: 0 };
    const reply = o => { try { ws.send(JSON.stringify({ t: 'res', r: m.r, ...o })); } catch {} };
    try {
      if (m.t === 'pr') {
        const p = cleanPatch(m.patch); if (!p) return;
        const pr = this.pres.get(id) || {}; merge(pr, p); this.pres.set(id, pr);
        this.bcast(id, { t: 'pr', id, patch: p });
        this.persist(ws, id, ['n', 'c', 's', 'h', 'k', 'g'].some(k => k in p));
      } else if (m.t === 'ev') {
        if (!TOPICS.has(m.topic) || JSON.stringify(m.data ?? null).length > 2048) return;
        this.bcast(id, { t: 'ev', id, topic: m.topic, data: m.data });
      } else if (m.t === 'reg') {
        if (this.blocked(meta.ip)) return reply({ ok: false, err: 'Trop d\'essais. Réessaie dans quelques minutes.' });
        const u = String(m.u || ''), pw = String(m.pw || ''), key = u.toLowerCase();
        if (!UR.test(u)) return reply({ ok: false, err: 'Nom invalide.' });
        if (!KEY.test(pw)) return reply({ ok: false, err: 'Mot de passe invalide.' });
        if (this.row(key)) return reply({ ok: false, err: 'Ce nom est déjà pris.' });
        if (this.ctx.storage.sql.exec('SELECT COUNT(*) AS c FROM acc').one().c >= MAX_ACCOUNTS) return reply({ ok: false, err: 'Serveur complet.' });
        const salt = rnd(16), token = rnd(24), hash = await sha(salt + ':' + pw), th = await sha(token), p = cleanP(m.p);
        try { this.ctx.storage.sql.exec('INSERT INTO acc (k,u,salt,hash,toks,p) VALUES (?,?,?,?,?,?)', key, u, salt, hash, JSON.stringify([th]), JSON.stringify(p)); }
        catch { return reply({ ok: false, err: 'Ce nom est déjà pris.' }); }
        meta.key = key; this.meta.set(id, meta); this.persist(ws, id, true);
        reply({ ok: true, u, token, p });
      } else if (m.t === 'login') {
        if (this.blocked(meta.ip)) return reply({ ok: false, err: 'Trop d\'essais. Réessaie dans quelques minutes.' });
        const key = String(m.u || '').toLowerCase(), a = this.row(key), bad = 'Nom ou mot de passe incorrect.', pw = String(m.pw || '');
        if (!a || !KEY.test(pw)) { this.fail(meta.ip); return reply({ ok: false, err: bad }); }
        if (!same(await sha(a.salt + ':' + pw), a.hash)) { this.fail(meta.ip); return reply({ ok: false, err: bad }); }
        const token = rnd(24), toks = [...JSON.parse(a.toks || '[]'), await sha(token)].slice(-5);
        this.ctx.storage.sql.exec('UPDATE acc SET toks = ? WHERE k = ?', JSON.stringify(toks), key);
        meta.key = key; this.meta.set(id, meta); this.persist(ws, id, true);
        reply({ ok: true, u: a.u, token, p: JSON.parse(a.p) });
      } else if (m.t === 'resume') {
        const key = String(m.u || '').toLowerCase(), a = this.row(key);
        if (!a || !JSON.parse(a.toks || '[]').includes(await sha(String(m.token || '')))) { this.fail(meta.ip); return reply({ ok: false, err: 'Session expirée.' }); }
        meta.key = key; this.meta.set(id, meta); this.persist(ws, id, true);
        reply({ ok: true, u: a.u, p: JSON.parse(a.p) });
      } else if (m.t === 'save') {
        if (!meta.key || !this.row(meta.key)) return reply({ ok: false, err: 'Non connecté.' });
        this.ctx.storage.sql.exec('UPDATE acc SET p = ? WHERE k = ?', JSON.stringify(cleanP(m.p)), meta.key);
        reply({ ok: true });
      }
    } catch (e) { if (m.r) reply({ ok: false, err: 'Erreur serveur.' }); }
  }

  leave(ws) { const id = this.idOf(ws); if (!id) return; this.pres.delete(id); this.meta.delete(id); this.buckets.delete(id); this.bcast(id, { t: 'leave', id }); }
  async webSocketClose(ws, code, reason) { try { ws.close(code, reason); } catch {} this.leave(ws); }
  async webSocketError(ws) { this.leave(ws); }
}

export default {
  async fetch(req, env) {
    if (req.headers.get('Upgrade') === 'websocket') {
      const allowed = (env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim().replace(/\/$/, '')).filter(Boolean);
      const origin = (req.headers.get('Origin') || '').replace(/\/$/, '');
      if (allowed.length && !allowed.includes(origin)) return new Response('origine refusée', { status: 403 });
      return env.ROOM.get(env.ROOM.idFromName('principale')).fetch(req);
    }
    return new Response('Île Éclair : serveur OK', { headers: { 'content-type': 'text/plain; charset=utf-8' } });
  }
};
