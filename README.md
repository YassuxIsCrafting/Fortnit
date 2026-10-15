# Île Éclair 3D

Battle royale 3D en JavaScript (Three.js), jouable dans le navigateur.

- Jeu : `index.html`, `net.js`, `config.js` (publié avec GitHub Pages)
- Serveur multijoueur + comptes : dossier `server/` (à héberger sur Render ou équivalent)

## Multijoueur
1. Héberge `server/` (Node.js, `npm install`, `node server.js`) avec la variable `ALLOWED_ORIGINS=https://yassuxiscrafting.github.io`
2. Mets l'adresse du serveur (en `wss://`) dans `config.js`
3. Chacun ouvre le lien du jeu : https://yassuxiscrafting.github.io/Fortnit/

Sans serveur (`IE_WS` vide), le jeu reste jouable en solo contre les bots.
