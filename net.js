/* Île Éclair : client réseau pour un hébergement statique (Netlify, GitHub Pages...).
   Reproduit la petite API "room" + "auth" utilisée par le jeu, au-dessus d'un WebSocket. */
(function () {
  var URL_ = window.IE_WS;
  if (window.claude || !URL_) return;               // déjà fourni par la plateforme, ou pas de serveur : mode solo
  var ws = null, myId = null, mine = {}, peers = new Map(), hs = {}, cbs = [], reqs = new Map(), rn = 0, gotInit = false, readyRes;
  var ready = new Promise(function (r) { readyRes = r; });
  var wait = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  function send(o) { if (ws && ws.readyState === 1) ws.send(JSON.stringify(o)); }
  function notify() { cbs.forEach(function (f) { try { f(); } catch (e) {} }); }
  function merge(t, p) { for (var k in p) { if (p[k] === null) delete t[k]; else t[k] = p[k]; } }

  function connect() {
    try { ws = new WebSocket(URL_); } catch (e) { setTimeout(connect, 3000); return; }
    ws.onmessage = function (e) {
      var m; try { m = JSON.parse(e.data); } catch (x) { return; }
      if (m.t === 'init') {
        myId = m.id; peers = new Map();
        for (var k in m.peers) peers.set(k, m.peers[k]);
        if (Object.keys(mine).length) send({ t: 'pr', patch: mine });   // après une reconnexion
        if (!gotInit) { gotInit = true; readyRes(); }
        notify();
      } else if (m.t === 'join') { peers.set(m.id, {}); notify(); }
      else if (m.t === 'leave') { peers.delete(m.id); notify(); }
      else if (m.t === 'pr') { var o = peers.get(m.id); if (!o) { o = {}; peers.set(m.id, o); } merge(o, m.patch || {}); notify(); }
      else if (m.t === 'ev') {
        (hs[m.topic] || []).forEach(function (f) { try { f({ topic: m.topic, data: m.data, peer: m.id, isMe: false, sameTab: false }); } catch (x) {} });
      } else if (m.t === 'res') {
        var q = reqs.get(m.r); if (q) { reqs.delete(m.r); if (m.ok) q.res(m); else q.rej(m.err || 'Erreur'); }
      }
    };
    ws.onclose = function () {
      peers = new Map(); notify();
      reqs.forEach(function (q) { q.rej('Connexion perdue.'); }); reqs.clear();
      setTimeout(connect, 2000);
    };
    ws.onerror = function () {};
  }
  connect();

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

  function call(o) {
    return Promise.race([ready, wait(8000)]).then(function () {
      return new Promise(function (res, rej) {
        if (!ws || ws.readyState !== 1) return rej('Serveur injoignable. Réessaie dans un instant.');
        var r = ++rn; o.r = r; reqs.set(r, { res: res, rej: rej }); send(o);
        setTimeout(function () { if (reqs.delete(r)) rej('Le serveur ne répond pas.'); }, 10000);
      });
    });
  }
  var auth = {
    register: function (u, pw, p) { return call({ t: 'reg', u: u, pw: pw, p: p }); },
    login: function (u, pw) { return call({ t: 'login', u: u, pw: pw }); },
    resume: function (u, token) { return call({ t: 'resume', u: u, token: token }); },
    save: function (p) { return call({ t: 'save', p: p }); }
  };

  window.claude = {
    use: function (n) {
      if (n === 'room') return Promise.race([ready, wait(6000)]).then(function () { return myId ? room : null; });
      if (n === 'auth') return Promise.resolve(auth);
      return Promise.resolve(null);
    }
  };
})();
