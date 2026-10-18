@echo off
rem Lance le jeu et le serveur multijoueur en local (Node.js requis).
rem Jeu : http://localhost:3000   -   Autres appareils du réseau : http://ADRESSE-DE-CE-PC:3000
cd /d "%~dp0"
start "Hesse Fortnite - serveur multijoueur" cmd /k "cd cloudflare && npx --yes wrangler dev --ip 0.0.0.0 --port 8787"
start "Hesse Fortnite - jeu" cmd /k "npx --yes serve -l 3000 ."
timeout /t 6 >nul
start "" http://localhost:3000
