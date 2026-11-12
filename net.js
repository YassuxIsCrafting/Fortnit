/* Île Éclair : client réseau pour un hébergement statique (site Cloudflare, Netlify...).
   Reproduit la petite API "room" + "auth" utilisée par le jeu, au-dessus d'un WebSocket. */
(function () {
  var URL_ = window.IE_WS;
  if (window.claude || !URL_) return;               // déjà fourni par la plateforme, ou pas de serveur : mode solo
  // Salons privés : un code de 4 à 8 lettres/chiffres (adresse ?salon=CODE, ou gardé dans le navigateur).
  // Dans un salon, la partie passe par la salle /s/CODE du serveur, et les comptes/amis par une 2e connexion
  // « aux » vers la salle publique (sans place prise ni présence). Sans code : une seule connexion, comme avant.
  var norm = function (c) { c = String(c || '').toUpperCase().replace(/[^A-Z0-9]/g, ''); return c.length >= 4 && c.length <= 8 ? c : ''; };
  var CODE = '';
  try { var qs = new URLSearchParams(location.search).get('salon'); if (qs !== null) { CODE = norm(qs); if (CODE) localStorage.setItem('ie_salon', CODE); } else CODE = norm(localStorage.getItem('ie_salon')); } catch (e) {}
  window.IE_SALON = CODE;
  window.IE_setSalon = function (c) {
    c = norm(c); try { if (c) localStorage.setItem('ie_salon', c); else localStorage.removeItem('ie_salon'); } catch (e) {}
    try { var u = new URL(location.href); u.searchParams.delete('salon'); location.replace(u.toString()); } catch (e) { location.reload(); }
  };
  var BASE = URL_.replace(/\/+$/, '');
  var ws = null, gs = null, myId = null, mine = {}, peers = new Map(), hs = {}, cbs = [], reqs = new Map(), rn = 0, readyRes, readyGRes, gotA = false, gotG = false;
  var full = false;   // salle publique pleine (12 joueurs) : on garde quand même les comptes via une connexion « aux »
  var ready = new Promise(function (r) { readyRes = r; }), readyG = new Promise(function (r) { readyGRes = r; });
  var wait = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  function sendOn(s, o) { if (s && s.readyState === 1) s.send(JSON.stringify(o)); }
  function send(o) { sendOn(CODE ? gs : ws, o); }      // partie (présence, événements)
  function sendA(o) { sendOn(ws, o); }                  // comptes, amis, ping
  function notify() { cbs.forEach(function (f) { try { f(); } catch (e) {} }); }
  function merge(t, p) { for (var k in p) { if (p[k] === null) delete t[k]; else t[k] = p[k]; } }

  function onGame(m) {
    if (m.t === 'init') {
      myId = m.id; peers = new Map();
      for (var k in m.peers) peers.set(k, m.peers[k]);
      if (Object.keys(mine).length) send({ t: 'pr', patch: mine });   // après une reconnexion
      if (!gotG) { gotG = true; readyGRes(); }
      notify();
    } else if (m.t === 'join') { peers.set(m.id, {}); notify(); }
    else if (m.t === 'leave') { peers.delete(m.id); notify(); }
    else if (m.t === 'pr') { var o = peers.get(m.id); if (!o) { o = {}; peers.set(m.id, o); } merge(o, m.patch || {}); notify(); }
    else if (m.t === 'ev') {
      (hs[m.topic] || []).forEach(function (f) { try { f({ topic: m.topic, data: m.data, peer: m.id, isMe: false, sameTab: false }); } catch (x) {} });
    }
  }
  function onAux(m) {
    if (m.t === 'full' && !CODE) { full = true; return; }   // le serveur va fermer : la reconnexion passera en « aux »
    if (m.t === 'init' && !gotA) { gotA = true; readyRes(); }
    if (m.t === 'fnote' || m.t === 'pinv' || m.t === 'pans') {
      var h = window.IE_onSocial; if (h) try { h(m); } catch (x) {}
    } else if (m.t === 'res') {
      var q = reqs.get(m.r); if (q) { reqs.delete(m.r); if (m.ok) q.res(m); else q.rej(m.err || 'Erreur'); }
    } else if (!CODE && !full) onGame(m);
  }
  function open(url, onMsg, set, onClose) {
    var s; try { s = new WebSocket(typeof url === 'function' ? url() : url); } catch (e) { setTimeout(function () { open(url, onMsg, set, onClose); }, 3000); return; }
    set(s);
    s.onmessage = function (e) { var m; try { m = JSON.parse(e.data); } catch (x) { return; } onMsg(m); };
    s.onclose = function () { onClose(); setTimeout(function () { open(url, onMsg, set, onClose); }, 2000); };
    s.onerror = function () {};
  }
  var lostG = function () { peers = new Map(); notify(); };
  open(function () { return CODE || full ? BASE + '/?aux=1' : URL_; }, onAux, function (s) { ws = s; }, function () {
    if (!CODE) lostG();
    reqs.forEach(function (q) { q.rej('Connexion perdue.'); }); reqs.clear();
  });
  if (CODE) open(BASE + '/s/' + CODE, onGame, function (s) { gs = s; }, lostG);
  else readyG = ready;

  var room = {
    peers: function () {
      var a = [];
      if (myId) a.push({ peer: myId, isMe: true, sameTab: true, kind: 'viewer', presence: mine });
      peers.forEach(function (p, k) { a.push({ peer: k, isMe: false, sameTab: false, kind: 'viewer', presence: p }); });
      return a;
    },
    onPeers: function (f) { cbs.push(f); },
    on: function (t, f) { (hs[t] = hs[t] || []).push(f); },
    emit: function (t, d) { send({ t: 'ev', topic: t, data: d }); return Promise.resolve(); },
    presence: function (p) { merge(mine, p); send({ t: 'pr', patch: p }); return Promise.resolve(); }
  };

  // Attend que la connexion « comptes » soit ouverte (jusqu'à ms) : sur mobile elle se coupe souvent
  // (appli en arrière-plan, réseau qui change) et se rouvre 2 s plus tard, il ne faut pas échouer pendant ce temps.
  function whenOpen(ms) {
    var t0 = Date.now();
    return new Promise(function (res) { (function chk() { if (gotA && ws && ws.readyState === 1) return res(true); if (Date.now() - t0 > ms) return res(false); setTimeout(chk, 150); })(); });
  }
  function call1(o) {
    return whenOpen(10000).then(function (ok) {
      return new Promise(function (res, rej) {
        if (!ok) return rej('Serveur injoignable. Vérifie ta connexion et réessaie.');
        var r = ++rn, q = {}; for (var k in o) q[k] = o[k]; q.r = r; reqs.set(r, { res: res, rej: rej }); sendA(q);
        setTimeout(function () { if (reqs.delete(r)) rej('Le serveur ne répond pas.'); }, 10000);
      });
    });
  }
  // Une 2e chance automatique si la connexion a sauté pendant la demande
  function call(o) {
    return call1(o).catch(function (e) { if (e === 'Connexion perdue.' || e === 'Le serveur ne répond pas.') return wait(500).then(function () { return call1(o); }); throw e; });
  }
  // Le mot de passe n'est jamais envoyé tel quel : le navigateur en dérive une clé (PBKDF2, 150 000 tours)
  // avec le nom d'utilisateur comme sel, et c'est cette clé que le serveur vérifie.
  function derive(u, pw) {
    var C = typeof crypto !== 'undefined' ? crypto : window.crypto;
    if (!C || !C.subtle) return Promise.reject('Navigateur non compatible avec les comptes.');
    var enc = new TextEncoder();
    return C.subtle.importKey('raw', enc.encode(pw), 'PBKDF2', false, ['deriveBits']).then(function (k) {
      return C.subtle.deriveBits({ name: 'PBKDF2', salt: enc.encode('ile-eclair|' + String(u).toLowerCase()), iterations: 150000, hash: 'SHA-256' }, k, 256);
    }).then(function (b) {
      return Array.prototype.map.call(new Uint8Array(b), function (x) { return ('0' + x.toString(16)).slice(-2); }).join('');
    });
  }
  var auth = {
    // Si la création a réussi mais que la réponse s'est perdue, la 2e tentative dit « déjà pris » : on essaie alors de se connecter avec le même mot de passe
    register: function (u, pw, p) { return derive(u, pw).then(function (k) { return call1({ t: 'reg', u: u, pw: k, p: p }).catch(function (e) {
      if (e !== 'Connexion perdue.' && e !== 'Le serveur ne répond pas.') throw e;
      return wait(500).then(function () { return call1({ t: 'reg', u: u, pw: k, p: p }); }).catch(function (e2) { if (e2 === 'Ce nom est déjà pris.') return call1({ t: 'login', u: u, pw: k }).catch(function () { throw e2; }); throw e2; });
    }); }); },
    login: function (u, pw) { return derive(u, pw).then(function (k) { return call({ t: 'login', u: u, pw: k }); }); },
    resume: function (u, token) { return call({ t: 'resume', u: u, token: token }); },
    save: function (p) { return call({ t: 'save', p: p }); },
    friends: function () { return call({ t: 'flist' }); },
    social: function (t, u, ok) { return call({ t: t, u: u, ok: ok }); },
    // Ping : temps d'un aller-retour avec le serveur, en millisecondes.
    ping: function () { var t0 = performance.now(); return call({ t: 'ping' }).then(function () { return performance.now() - t0; }); }
  };

  window.claude = {
    use: function (n) {
      if (n === 'room') return Promise.race([readyG, wait(6000)]).then(function () { return myId ? room : null; });
      if (n === 'auth') return Promise.resolve(auth);
      return Promise.resolve(null);
    }
  };
})();
