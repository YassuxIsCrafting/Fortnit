// Worker « ile-eclair » : l'ancienne adresse du site renvoie vers le jeu sur GitHub Pages.
//  - Navigateurs : redirection 301 vers https://yassuxiscrafting.github.io/Fortnit/ (même chemin, même ?salon=…).
//  - Applis Android (WebView) et Windows (Electron) : elles n'acceptent que l'adresse ile-eclair, donc le worker
//    leur sert les fichiers de GitHub Pages sans changer d'adresse (pas besoin de recompiler les applis).
// Publier : npx wrangler deploy cloudflare-redirect/worker.js --name ile-eclair --compatibility-date 2026-11-02
const SITE = 'https://yassuxiscrafting.github.io/Fortnit';

export default {
  async fetch(req) {
    const u = new URL(req.url);
    const target = SITE + u.pathname + u.search;
    const ua = req.headers.get('User-Agent') || '';
    const app = /; wv\)|Electron\//.test(ua) || u.searchParams.has('app');
    if (!app) return Response.redirect(target, 301);
    const r = await fetch(target, { method: req.method, headers: { 'User-Agent': ua }, redirect: 'follow' });
    const h = new Headers(r.headers);
    h.delete('content-security-policy');
    return new Response(r.body, { status: r.status, headers: h });
  }
};
