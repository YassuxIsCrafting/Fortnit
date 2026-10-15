'use strict';
// Île Éclair : serveur WebSocket (salle de jeu + comptes).
const http = require('http'), crypto = require('crypto'), fs = require('fs'), path = require('path'), util = require('util');
const { WebSocketServer } = require('ws');
const scrypt = util.promisify(crypto.scrypt);

const PORT = +process.env.PORT || 8080;
const ORIGINS = (process.env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim().replace(/\/$/, '')).filter(Boolean);
const DATA = process.env.DATA_FILE || path.join(__dirname, 'data', 'accounts.json');
const MAX_PLAYERS = +process.env.MAX_PLAYERS || 12;
const MAX_ACCOUNTS = 5000;
const TOPICS = new Set(['shot', 'bs', 'kill', 'wall', 'chest']);
const UR = /^[A-Za-z0-9_-]{3,14}$/, HEX = /^#[0-9a-f]{6}$/i;

// ---------- comptes (fichier JSON) ----------
let acc = {};
try { acc = JSON.parse(fs.readFileSync(DATA, 'utf8')); } catch { /* premier lancement */ }
let timer = null;
function persist() {
  clearTimeout(timer);
  timer = setTimeout(() => {
    try {
      fs.mkdirSync(path.dirname(DATA), { recursive: true });
      fs.writeFileSync(DATA + '.tmp', JSON.stringify(acc));
      fs.renameSync(DATA + '.tmp', DATA);
    } catch (e) { console.error('sauvegarde impossible :', e.message); }
  }, 400);
}
const sha = t => crypto.createHash('sha256').update(t).digest('hex');
const hashPw = async (pw, salt) => (await scrypt(pw, salt, 32)).toString('hex');
const int = (v, a, b) => Math.max(a, Math.min(b, Number.isFinite(+v) ? Math.trunc(+v) : a));
function cleanP(p) {
  p = p && typeof p === 'object' ? p : {};
  const o = p.own || {}, l = p.look || {}, A = (a, f, n) => Array.isArray(a) ? a.filter(f).slice(0, n) : [];
  return {
    tk: int(p.tk, 0, 1e6), kp: int(p.kp, 0, 2),
    own: { c: A(o.c, x => typeof x === 'string' && HEX.test(x), 30), h: A(o.h, Number.isInteger, 10), k: A(o.k, Number.isInteger, 10), pal: !!o.pal },
    look: { c: HEX.test(l.c) ? l.c : '#3da5ff', s: int(l.s, 0, 5), h: int(l.h, 0, 4), k: int(l.k, 0, 6) }
  };
}

// ---------- présence : on n'accepte que les champs du jeu ----------
const num = v => typeof v === 'number' && Number.isFinite(v);
function cleanPatch(p) {
  if (!p || typeof p !== 'object' || Array.isArray(p)) return null;
  const out = {};
  for (const [k, v] of Object.entries(p)) {
    if (v === null) { if (k === 't' || k === 'b') out[k] = null; continue; }
    if (k === 'n') { if (typeof v === 'string') out.n = v.replace(/[\u0000-\u001f<>]/g, '').slice(0, 14); }
    else if (k === 'c') { if (typeof v === 'string' && HEX.test(v)) out.c = v; }
    else if (['s', 'h', 'k', 'w', 'g'].includes(k)) { if (Number.isInteger(v) && v >= 0 && v <= 9) out[k] = v; }
    else if (['x', 'y', 'a', 'hp', 't'].includes(k)) { if (num(v)) out[k] = v; }
    else if (k === 'b') {
      if (Array.isArray(v) && v.length <= 24 && v.every(r => Array.isArray(r) && r.length <= 5 && r.every(z => num(z) || (typeof z === 'string' && z.length <= 40)))) out.b = v;
    }
  }
  return out;
}
const merge = (t, p) => { for (const k in p) { if (p[k] === null) delete t[k]; else t[k] = p[k]; } };

// ---------- serveur ----------
const server = http.createServer((req, res) => { res.writeHead(200, { 'content-type': 'text/plain; charset=utf-8' }); res.end('Île Éclair : serveur OK'); });
const wss = new WebSocketServer({
  server, maxPayload: 16 * 1024,
  verifyClient: (info, cb) => (!ORIGINS.length || ORIGINS.includes((info.origin || '').replace(/\/$/, ''))) ? cb(true) : cb(false, 403, 'origine refusée')
});
const clients = new Map(), fails = new Map();
const send = (ws, o) => { if (ws.readyState === 1) ws.send(JSON.stringify(o)); };
const bcast = (from, o) => { const s = JSON.stringify(o); for (const [k, c] of clients) if (k !== from && c.ws.readyState === 1) c.ws.send(s); };
const blocked = ip => { const f = fails.get(ip); return f && f.until > Date.now(); };
const fail = ip => { const f = fails.get(ip) || { n: 0, until: 0 }; if (++f.n >= 8) { f.until = Date.now() + 5 * 60e3; f.n = 0; } fails.set(ip, f); };

wss.on('connection', (ws, req) => {
  if (clients.size >= MAX_PLAYERS) { send(ws, { t: 'full' }); ws.close(); return; }
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket.remoteAddress;
  const id = crypto.randomBytes(4).toString('hex');
  const c = { ws, id, pr: {}, key: null, tokens: 300, last: Date.now(), alive: true };
  clients.set(id, c);
  const peers = {}; for (const [k, o] of clients) if (k !== id) peers[k] = o.pr;
  send(ws, { t: 'init', id, peers });
  bcast(id, { t: 'join', id });
  ws.on('pong', () => { c.alive = true; });
  ws.on('error', () => {});
  ws.on('close', () => { clients.delete(id); bcast(id, { t: 'leave', id }); });
  ws.on('message', async raw => {
    const now = Date.now();
    c.tokens = Math.min(300, c.tokens + (now - c.last) * 0.15); c.last = now;   // ~150 messages/s
    if (c.tokens < 1) return; c.tokens--;
    let m; try { m = JSON.parse(raw); } catch { return; }
    if (!m || typeof m !== 'object') return;
    const reply = o => send(ws, { t: 'res', r: m.r, ...o });
    try {
      if (m.t === 'pr') {
        const p = cleanPatch(m.patch); if (!p) return;
        merge(c.pr, p); bcast(id, { t: 'pr', id, patch: p });
      } else if (m.t === 'ev') {
        if (!TOPICS.has(m.topic) || JSON.stringify(m.data ?? null).length > 2048) return;
        bcast(id, { t: 'ev', id, topic: m.topic, data: m.data });
      } else if (m.t === 'reg') {
        if (blocked(ip)) return reply({ ok: false, err: 'Trop d\'essais. Réessaie dans quelques minutes.' });
        const u = String(m.u || ''), pw = String(m.pw || ''), key = u.toLowerCase();
        if (!UR.test(u)) return reply({ ok: false, err: 'Nom invalide.' });
        if (pw.length < 6 || pw.length > 100) return reply({ ok: false, err: 'Mot de passe : 6 à 100 caractères.' });
        if (acc[key]) return reply({ ok: false, err: 'Ce nom est déjà pris.' });
        if (Object.keys(acc).length >= MAX_ACCOUNTS) return reply({ ok: false, err: 'Serveur complet.' });
        const salt = crypto.randomBytes(16).toString('hex'), token = crypto.randomBytes(24).toString('hex');
        const hash = await hashPw(pw, salt);
        if (acc[key]) return reply({ ok: false, err: 'Ce nom est déjà pris.' });
        acc[key] = { u, salt, hash, toks: [sha(token)], p: cleanP(m.p) }; persist(); c.key = key;
        reply({ ok: true, u, token, p: acc[key].p });
      } else if (m.t === 'login') {
        if (blocked(ip)) return reply({ ok: false, err: 'Trop d\'essais. Réessaie dans quelques minutes.' });
        const key = String(m.u || '').toLowerCase(), a = acc[key], bad = 'Nom ou mot de passe incorrect.';
        if (!a) { fail(ip); return reply({ ok: false, err: bad }); }
        const h = Buffer.from(await hashPw(String(m.pw || ''), a.salt), 'hex'), ref = Buffer.from(a.hash, 'hex');
        if (h.length !== ref.length || !crypto.timingSafeEqual(h, ref)) { fail(ip); return reply({ ok: false, err: bad }); }
        const token = crypto.randomBytes(24).toString('hex');
        a.toks = [...(a.toks || []), sha(token)].slice(-5); persist(); c.key = key;
        reply({ ok: true, u: a.u, token, p: a.p });
      } else if (m.t === 'resume') {
        const key = String(m.u || '').toLowerCase(), a = acc[key];
        if (!a || !(a.toks || []).includes(sha(String(m.token || '')))) { fail(ip); return reply({ ok: false, err: 'Session expirée.' }); }
        c.key = key; reply({ ok: true, u: a.u, p: a.p });
      } else if (m.t === 'save') {
        if (!c.key || !acc[c.key]) return reply({ ok: false, err: 'Non connecté.' });
        acc[c.key].p = cleanP(m.p); persist(); reply({ ok: true });
      }
    } catch (e) { console.error(e.message); if (m.r) reply({ ok: false, err: 'Erreur serveur.' }); }
  });
});
setInterval(() => { for (const c of clients.values()) { if (!c.alive) { c.ws.terminate(); continue; } c.alive = false; try { c.ws.ping(); } catch {} } }, 30000).unref();
server.listen(PORT, () => console.log('Île Éclair : serveur prêt sur le port ' + PORT + (ORIGINS.length ? ' (origines : ' + ORIGINS.join(', ') + ')' : ' (toutes origines acceptées)')));
