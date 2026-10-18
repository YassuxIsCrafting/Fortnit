// Adresse du serveur temps réel d'Île Éclair.
//  - En ligne (GitHub Pages, appli Android) : le serveur Cloudflare.
//  - En local (localhost, réseau de la maison, ou fichier ouvert par double-clic) : le serveur local
//    lancé par jouer-en-local.bat (wrangler dev, port 8787).
//  - Mets '' pour forcer le mode solo contre les bots.
(function () {
  var h = location.hostname, local = location.protocol === 'file:' || h === 'localhost' || h === '127.0.0.1' ||
    /^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/.test(h);
  window.IE_WS = local ? 'ws://' + (h || 'localhost') + ':8787' : 'wss://fortnit.yasser-mobiarchitects.workers.dev';
})();
