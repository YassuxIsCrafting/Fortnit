# Île Éclair 3D

Battle royale 3D (Three.js) jouable dans le navigateur, en solo contre des bots ou en multijoueur.

```
index.html, net.js, config.js   -> le jeu (publié par GitHub Pages)
cloudflare/                     -> le serveur multijoueur + comptes (Cloudflare Workers, offre gratuite)
```

Jeu : https://yassuxiscrafting.github.io/Fortnit/

## Activer le multijoueur et les comptes (gratuit, sans carte bancaire)

### 1. Mettre le serveur sur Cloudflare
1. Crée un compte gratuit sur https://dash.cloudflare.com (e-mail + mot de passe).
2. Dans le menu, ouvre **Workers & Pages**, puis **Create** et **Import a repository** (« Get started »).
3. Connecte ton compte GitHub et choisis le dépôt `Fortnit`.
4. Dans la configuration du projet :
   - **Nom du Worker** : `ile-eclair` (doit être le même que `name` dans `cloudflare/wrangler.jsonc`)
   - **Root directory** : `cloudflare`
   - **Deploy command** : `npx wrangler deploy` (valeur par défaut)
   - pas de build command
5. Clique sur **Save and Deploy**. À la fin, Cloudflare affiche l'adresse du Worker :
   `https://ile-eclair.TON-SOUS-DOMAINE.workers.dev` (ouvre-la : tu dois lire « Île Éclair : serveur OK »).

Variante avec un terminal (Node.js installé) : `cd cloudflare && npx wrangler login && npx wrangler deploy`.

### 2. Brancher le jeu sur le serveur
Dans GitHub, ouvre `config.js`, clique sur le crayon et remplace le contenu par :

```js
window.IE_WS = 'wss://ile-eclair.TON-SOUS-DOMAINE.workers.dev';
```

(`wss://` et pas `https://`, sans `/` à la fin.) Fais **Commit changes** : GitHub Pages se met à jour en une ou deux minutes.

### 3. Tester
Ouvre le jeu dans deux onglets : vous devez vous voir dans le lobby.

## À savoir
- `cloudflare/wrangler.jsonc` limite l'accès au serveur au site `https://yassuxiscrafting.github.io`. Si tu changes
  d'adresse de site, modifie `ALLOWED_ORIGINS` dedans.
- Les comptes sont conservés dans la base du Worker (elle survit aux redémarrages et aux mises à jour).
- Quota gratuit (estimation) : environ 25 heures de jeu cumulées par jour, tous joueurs confondus. Au-delà, le serveur
  peut refuser les connexions jusqu'au lendemain ; le jeu reste jouable en solo.
- Une seule salle de 12 joueurs maximum. Chaque joueur calcule ses propres dégâts : la triche reste possible.
- Le mot de passe ne quitte jamais le navigateur : seule une clé dérivée (PBKDF2) est envoyée au serveur.
