// Île Éclair : serveur temps réel + comptes pour Cloudflare Workers (Durable Object, offre gratuite).
import { DurableObject } from 'cloudflare:workers';

const MAX_PLAYERS = 12, MAX_ACCOUNTS = 5000;
const TOPICS = new Set(['shot', 'bs', 'kill', 'wall', 'chest', 'rev', 'chat', 'fx']);   // fx : effets des gadgets
const MAX_FRIENDS = 60;
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
    cr: p.cr ? 1 : 0, cw: int(p.cw, 0, 1e6), wins: int(p.wins, 0, 1e6), cs: typeof p.cs === 'string' && /^\d{4}-\d{2}$/.test(p.cs) ? p.cs : '',
    own: { c: A(o.c, x => typeof x === 'string' && HEX.test(x), 30), h: A(o.h, Number.isInteger, 10), k: A(o.k, Number.isInteger, 10), u: A(o.u, Number.isInteger, 10), pal: !!o.pal },
    look: { c: HEX.test(l.c) ? l.c : '#3da5ff', s: int(l.s, 0, 5), h: int(l.h, 0, 4), k: int(l.k, 0, 40), u: int(l.u, 0, 9) }
  };
}
function cleanPatch(p) {
  if (!p || typeof p !== 'object' || Array.isArray(p)) return null;
  const out = {};
  for (const [k, v] of Object.entries(p)) {
    if (v === null) { if (k === 't' || k === 'b') out[k] = null; continue; }
    if (k === 'n') { if (typeof v === 'string') out.n = v.replace(/[\u0000-\u001f<>]/g, '').slice(0, 14); }
    else if (k === 'c') { if (typeof v === 'string' && HEX.test(v)) out.c = v; }
    else if (['s', 'h', 'k', 'u', 'w', 'g', 'cr', 'kn', 'em', 'md', 'vr', 'iv'].includes(k)) { if (Number.isInteger(v) && v >= 0 && v <= (k === 'k' ? 40 : k === 'vr' ? 20 : 9)) out[k] = v; }   // vr : règle spéciale, iv : camouflage
    else if (['x', 'y', 'z', 'a', 'hp', 't', 'v', 'pt', 'tm', 'en'].includes(k)) { if (num(v)) out[k] = v; }
    else if (k === 'b') {
      if (Array.isArray(v) && v.length <= 128 && v.every(r => Array.isArray(r) && r.length <= 5 && r.every(z => num(z) || (typeof z === 'string' && z.length <= 40)))) out.b = v;
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
      if (a && a.id) { this.ids.set(ws, a.id); if (!a.aux) this.pres.set(a.id, a.pr || {}); this.meta.set(a.id, { key: a.key || null, ip: a.ip || '', saved: Date.now(), aux: !!a.aux }); }
    }
    ctx.storage.sql.exec('CREATE TABLE IF NOT EXISTS acc (k TEXT PRIMARY KEY, u TEXT, salt TEXT, hash TEXT, toks TEXT, p TEXT)');
    ctx.storage.sql.exec('CREATE TABLE IF NOT EXISTS fr (a TEXT, b TEXT, st INTEGER, PRIMARY KEY (a, b))');   // a demande b ; st 0 = en attente, 1 = amis
  }

  socketsOf(key) { return this.ctx.getWebSockets().filter(w => { const m = this.meta.get(this.idOf(w)); return m && m.key === key; }); }
  push(key, obj) { const s = JSON.stringify(obj); for (const w of this.socketsOf(key)) { try { w.send(s); } catch {} } }
  nameOf(key) { const r = this.ctx.storage.sql.exec('SELECT u FROM acc WHERE k = ?', key).toArray()[0]; return r ? r.u : key; }
  links(key) { return this.ctx.storage.sql.exec('SELECT a, b, st FROM fr WHERE a = ? OR b = ?', key, key).toArray(); }
  notifyFriends(key) { for (const l of this.links(key)) this.push(l.a === key ? l.b : l.a, { t: 'fnote' }); }
  flist(key) {
    const out = { friends: [], inc: [], out: [] };
    for (const l of this.links(key)) {
      const o = l.a === key ? l.b : l.a, u = this.nameOf(o);
      if (l.st === 1) { const w = this.socketsOf(o)[0]; out.friends.push({ u, on: !!w, pid: w ? this.idOf(w) : null }); }
      else if (l.b === key) out.inc.push(u); else out.out.push(u);
    }
    return out;
  }

  idOf(ws) { let id = this.ids.get(ws); if (!id) { const a = ws.deserializeAttachment(); id = a && a.id; if (id) this.ids.set(ws, id); } return id; }
  bcast(fromId, obj) {
    const s = JSON.stringify(obj);
    for (const w of this.ctx.getWebSockets()) { const i = this.idOf(w); if (i !== fromId && !(this.meta.get(i) || {}).aux) { try { w.send(s); } catch {} } }
  }
  persist(ws, id, force) {
    const m = this.meta.get(id); if (!m) return;
    if (!force && Date.now() - m.saved < 2000) return;
    m.saved = Date.now();
    try { ws.serializeAttachment({ id, key: m.key, ip: m.ip, aux: m.aux ? 1 : 0, pr: trim(this.pres.get(id) || {}) }); } catch {}
  }

  async fetch(req) {
    if (req.headers.get('Upgrade') !== 'websocket') return new Response('Île Éclair : serveur OK', { headers: { 'content-type': 'text/plain; charset=utf-8' } });
    const pair = new WebSocketPair(), client = pair[0], server = pair[1];
    // aux=1 : connexion « comptes » d'un joueur qui est dans un salon privé (comptes et amis restent ici).
    // Elle ne prend pas de place, n'a pas de présence et ne reçoit pas le trafic de la partie publique.
    const aux = new URL(req.url).searchParams.get('aux') === '1';
    if (!aux && this.ctx.getWebSockets().filter(w => !(this.meta.get(this.idOf(w)) || {}).aux).length >= MAX_PLAYERS) {
      server.accept(); server.send(JSON.stringify({ t: 'full' })); server.close(1013, 'complet');
      return new Response(null, { status: 101, webSocket: client });
    }
    const id = rnd(4), ip = req.headers.get('CF-Connecting-IP') || '';
    this.ctx.acceptWebSocket(server);
    this.ids.set(server, id); if (!aux) this.pres.set(id, {}); this.meta.set(id, { key: null, ip, saved: 0, aux });
    this.persist(server, id, true);
    const peers = {}; if (!aux) for (const [k, v] of this.pres) if (k !== id) peers[k] = v;
    server.send(JSON.stringify({ t: 'init', id, peers }));
    if (!aux) this.bcast(id, { t: 'join', id });
    return new Response(null, { status: 101, webSocket: client });
  }

  blocked(ip) { const f = this.fails.get(ip); return f && f.until > Date.now(); }
  // Anti-essais par adresse : 12 mauvais mots de passe en 10 min bloquent 5 min. Les échecs plus vieux que 10 min sont oubliés
  // (avant, le compteur ne redescendait jamais : des joueurs sur le même wifi finissaient bloqués à force de petites erreurs).
  fail(ip) { const now = Date.now(); let f = this.fails.get(ip); if (!f || now - f.first > 10 * 60e3) f = { n: 0, first: now, until: f ? f.until : 0 }; if (++f.n >= 12) { f.until = now + 5 * 60e3; f.n = 0; f.first = now; } this.fails.set(ip, f); }
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
      if ((m.t === 'pr' || m.t === 'ev') && meta.aux) return;
      if (m.t === 'pr') {
        const p = cleanPatch(m.patch); if (!p) return;
        const pr = this.pres.get(id) || {}; merge(pr, p); this.pres.set(id, pr);
        this.bcast(id, { t: 'pr', id, patch: p });
        this.persist(ws, id, ['n', 'c', 's', 'h', 'k', 'g'].some(k => k in p));
      } else if (m.t === 'ping') {
        reply({ ok: true }); // mesure du ping côté joueur
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
        const token = rnd(24), toks = [...JSON.parse(a.toks || '[]'), await sha(token)].slice(-10);   // 10 appareils connectés en même temps (avant 5)
        this.ctx.storage.sql.exec('UPDATE acc SET toks = ? WHERE k = ?', JSON.stringify(toks), key);
        meta.key = key; this.meta.set(id, meta); this.persist(ws, id, true); this.notifyFriends(key);
        reply({ ok: true, u: a.u, token, p: JSON.parse(a.p) });
      } else if (m.t === 'resume') {
        const key = String(m.u || '').toLowerCase(), a = this.row(key);
        if (!a || !JSON.parse(a.toks || '[]').includes(await sha(String(m.token || '')))) return reply({ ok: false, err: 'Session expirée.' });   // pas compté comme essai : un jeton de 48 caractères ne se devine pas
        meta.key = key; this.meta.set(id, meta); this.persist(ws, id, true); this.notifyFriends(key);
        reply({ ok: true, u: a.u, p: JSON.parse(a.p) });
      } else if (m.t === 'save') {
        if (!meta.key || !this.row(meta.key)) return reply({ ok: false, err: 'Non connecté.' });
        this.ctx.storage.sql.exec('UPDATE acc SET p = ? WHERE k = ?', JSON.stringify(cleanP(m.p)), meta.key);
        reply({ ok: true });
      } else if (['flist', 'fadd', 'facc', 'fdel', 'pinv', 'pans'].includes(m.t)) {
        const me = meta.key; if (!me || !this.row(me)) return reply({ ok: false, err: 'Connecte-toi pour gérer tes amis.' });
        if (m.t === 'flist') return reply({ ok: true, ...this.flist(me) });
        const u = String(m.u || ''), o = u.toLowerCase(), sql = this.ctx.storage.sql;
        if (!UR.test(u) || o === me) return reply({ ok: false, err: 'Nom invalide.' });
        const mine = sql.exec('SELECT st FROM fr WHERE a = ? AND b = ?', me, o).toArray()[0], theirs = sql.exec('SELECT st FROM fr WHERE a = ? AND b = ?', o, me).toArray()[0];
        if (m.t === 'fadd') {
          if (!this.row(o)) return reply({ ok: false, err: 'Joueur introuvable.' });
          if (mine || (theirs && theirs.st === 1)) return reply({ ok: true });
          if (theirs) sql.exec('UPDATE fr SET st = 1 WHERE a = ? AND b = ?', o, me);
          else { if (this.links(me).length >= MAX_FRIENDS) return reply({ ok: false, err: 'Liste d\'amis pleine.' }); sql.exec('INSERT INTO fr (a, b, st) VALUES (?, ?, 0)', me, o); }
        } else if (m.t === 'facc') { if (!theirs) return reply({ ok: false, err: 'Aucune demande.' }); sql.exec('UPDATE fr SET st = 1 WHERE a = ? AND b = ?', o, me); }
        else if (m.t === 'fdel') sql.exec('DELETE FROM fr WHERE (a = ? AND b = ?) OR (a = ? AND b = ?)', me, o, o, me);
        else {
          if (!((mine && mine.st === 1) || (theirs && theirs.st === 1))) return reply({ ok: false, err: 'Vous n\'êtes pas amis.' });
          this.push(o, m.t === 'pinv' ? { t: 'pinv', from: this.nameOf(me), pid: id } : { t: 'pans', from: this.nameOf(me), ok: !!m.ok, pid: id });
          return reply({ ok: true });
        }
        this.push(o, { t: 'fnote' }); reply({ ok: true });
      }
    } catch (e) { if (m.r) reply({ ok: false, err: 'Erreur serveur.' }); }
  }

  leave(ws) { const id = this.idOf(ws); if (!id) return; const mt = this.meta.get(id) || {}, k = mt.key; this.pres.delete(id); this.meta.delete(id); if (k) try { this.notifyFriends(k); } catch {} this.buckets.delete(id); if (!mt.aux) this.bcast(id, { t: 'leave', id }); }
  async webSocketClose(ws, code, reason) { try { ws.close(code, reason); } catch {} this.leave(ws); }
  async webSocketError(ws) { this.leave(ws); }
}

export default {
  async fetch(req, env) {
    if (req.headers.get('Upgrade') === 'websocket') {
      const allowed = (env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim().replace(/\/$/, '')).filter(Boolean);
      const origin = (req.headers.get('Origin') || '').replace(/\/$/, '');
      if (allowed.length && !allowed.includes(origin)) return new Response('origine refusée', { status: 403 });
      // Salons privés : /s/CODE (5 à 8 lettres ou chiffres) = une salle à part ; sinon la salle publique « principale ».
      const sm = new URL(req.url).pathname.match(/^\/s\/([A-Z0-9]{4,8})$/);
      return env.ROOM.get(env.ROOM.idFromName(sm ? 's:' + sm[1] : 'principale')).fetch(req);
    }
    return new Response('Île Éclair : serveur OK', { headers: { 'content-type': 'text/plain; charset=utf-8' } });
  }
};
