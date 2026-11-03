# Hesse Fortnite (Île Éclair 3D)

Battle royale 3D jouable dans le navigateur (three.js), en solo contre des bots ou en multijoueur,
sur PC et sur mobile.

> Projet de fan non officiel, gratuit et sans but commercial. Il n'est ni affilié, ni approuvé, ni
> sponsorisé par Epic Games ou Fortnite.

- Jeu en ligne : https://fortnit-jeu.yasser-mobiarchitects.workers.dev/
- Appli Android : `HesseFortnite.apk`, à compiler depuis le dossier `android/` (voir plus bas).
- Appli Windows : `Fortnit.exe`, à compiler depuis le dossier `desktop/`, toujours à jour (voir plus bas).

## Le jeu

- **Cinématique d'entrée** (environ 30 s, touche, clic ou manette pour passer) : survol de l'île, lieux, tempête, bus et saut, filmés dans le vrai décor.
- **Parapluies** : 8 planeurs à motifs dans la boutique, inspirés de l'ambiance des shonens (motifs originaux, sans nom ni logo repris).
- **Skin Héros Éclair** offert : personnage 3D animé (`models/hero-eclair.glb`, maillage généré avec Higgsfield, squelette fait main).
- **Ambiance** : la partie va du matin au crépuscule, le ciel vire au violet avec la tempête, pluie, orage et brouillard
  au matin (tirés au sort, identiques pour tous les joueurs). Rendu cartoon, contours noirs, ombres de contact, éclat
  lumineux, rayons et reflets du soleil (Paramètres, qualité Élevée ; tout est coupé en Potato).
- **Décor** : collines et falaises, vrai lac au Lac Miroir, vagues et écume, plusieurs espèces d'arbres, herbe dense autour
  du joueur, toits, fenêtres qui s'allument la nuit, enseignes, un style et un repère par lieu (grue et conteneurs aux Docks,
  statue à Cité Éclair, moulin à la Ferme, colonnes aux Ruines, éoliennes à la Crête...), oiseaux, papillons, feuilles.
- **Personnages** : les bots utilisent le modèle 3D de près, en blocs de loin ; course, recul, rechargement, atterrissage,
  chute, chute du corps à l'élimination, clignement et grimace. Les autres skins restent en blocs.
- **Effets** : flash, traînées, douilles, impacts selon la matière, murs qui apparaissent et volent en morceaux, chiffres de
  dégâts, tremblement de caméra, éclairs dans la tempête, ralenti et cinématique de fin, poussière, sillage, traînée du planeur.
- **Interface** : lobby en scène de concert, cartes de boutique selon la rareté, coffre doré dont les objets jaillissent,
  écran de chargement avec astuces, carte dessinée à la main.
- **100 joueurs** par partie : les vrais joueurs (12 maximum), complétés par des bots.
- **Île de départ** : 1 minute d'attente avec les autres joueurs, puis tout le monde monte dans le bus.
- **Bus** qui traverse la carte : saute quand tu veux (Espace), chute libre puis planeur.
- **Carte de 8000 × 8000** : 247 bâtiments, 10 lieux nommés, arbres, coffres, caisses de munitions, 50 voitures.
- **Tempête** en 9 phases : elle apparaît 1 minute après le saut, la zone se décale à chaque phase,
  se referme complètement à la fin et ignore le bouclier.
- **Armes** à raretés (Commun → Légendaire) avec chargeurs : pistolet, fusil d'assaut, pompe, sniper,
  et la pioche pour récolter du bois.
- **Construction** de murs et d'escaliers, dégâts de chute, soins (minipot, grosse potion, medkit).
- **Modes Solo et Duo** : en Duo, on joue avec un ami (groupe) ou un coéquipier bot, on peut être à terre
  et se faire relever. Les bots jouent aussi en binômes.
- **Mode Reload** : dans le lobby, glisse vers le haut sur le sélecteur de mode (molette, flèche haut ou
  joystick vers le haut marchent aussi ; vers le bas pour revenir). Duo à 40 joueurs, zone de départ plus petite et
  tempête plus rapide. Éliminé, tu réapparais en chute libre près de ton équipier au bout de 10 s (pioche, pistolet
  commun, 60 munitions, 100 bois) tant qu’il est en vie. À partir de la 5e phase de tempête, les éliminations
  sont définitives.
- **Rareté** des armes : Commun, Peu commun, Rare, Épique, Légendaire et Mythique (très rare, seulement dans
  les coffres). Les cosmétiques ont aussi une rareté, purement visuelle.
- **Couronne** : un Top 1 donne une couronne pour la partie suivante (éliminations comptées double).
- **Emotes** sur une roue (touche B), jouables en partie et dans le lobby.
- **Amis** entre comptes, avec invitations en duo.
- **Paramètres** (touche P) : qualité graphique (Élevée / Potato), effets visuels, rendu cartoon, cycle jour / nuit, météo, tremblements de caméra, ombres, résolution, distance d'affichage,
  sensibilité, champ de vision, axe inversé, volume général, musique et effets sonores.

## Commandes

**Sprint** : Maj sur PC, joystick poussé à fond vers l'avant sur mobile, clic du joystick gauche (L3) à la manette.

**PC** : ZQSD bouger · Souris viser · Clic pioche / tirer · Clic droit viser · 1 pioche · 2-5 armes ·
6-7-8 soins · F coffre / caisse · E voiture (ou relever un équipier) · Espace sauter (et quitter le bus) ·
A (Q en QWERTY) mur · R escalier · M carte · B roue des emotes · G chat · P paramètres

**Mobile** : joystick à gauche pour bouger, glisser à droite pour viser, boutons 🔥 tirer · 🎯 viser ·
⤒ sauter · ✋ action · 🧱 mur · 🪜 escalier · 🗺️ carte · 💃 emotes · ⚙️ paramètres. Touche la barre du
bas pour changer d'arme ou te soigner. Joue en mode paysage.

**Manette PS5 (DualSense)**, en USB ou en Bluetooth : joystick gauche bouger · joystick droit viser · R2 tirer ·
L2 viser · Croix sauter (et quitter le bus) · Rond mur · Carré action (coffre, voiture, relever) · Triangle pioche ·
R1 / L1 arme suivante / précédente · croix directionnelle haut escalier, bas roue d'emotes, gauche / droite soins ·
Créer carte · Options paramètres. Dans le lobby : Croix pour jouer, Options pour les paramètres. La manette vibre
quand tu tires et quand tu prends des dégâts.

**Manette Xbox** (USB, Bluetooth ou adaptateur sans fil) : mêmes emplacements que la PS5 avec les noms Xbox :
RT tirer · LT viser · A sauter · B mur · X action · Y pioche · RB / LB changer d'arme · croix directionnelle
haut escalier, bas emotes, gauche / droite soins · Affichage carte · Menu paramètres. Dans le lobby : A pour jouer.

## Boutique et Kill Tokens

On gagne **1 Kill Token toutes les 3 éliminations** (2 « éliminations » par kill quand on porte la
couronne) et **10 Kill Tokens par Top 1** (partie de plus de 20 secondes).

| Catégorie | Objets payants | Coût total |
|---|---|---|
| Skins | 16 | 620 |
| Emotes | 24 | 237 |
| Accessoires | 4 | 15 |
| Parapluies | 8 | 220 |
| Tenues (couleurs) | 9 | 14 |
| Outils (palette libre) | 1 | 5 |
| **Toute la boutique** | **62** | **1 111 Kill Tokens** |

Pour tout acheter, il faut donc 1 111 Kill Tokens, soit environ :

- **3 333 éliminations** sans couronne (1 token pour 3 éliminations),
- ou **112 Top 1** (10 tokens chacun),
- ou un mélange des deux (par exemple 60 Top 1 + 1 533 éliminations).

Gratuits dès le départ : le skin Normal, la tenue bleue, les emotes Couronnes, Palmarès, Salut, Bravo et
Pouce levé.

## Passe de combat et quêtes

- **XP de saison** : chaque partie rapporte de l'XP (partie jouée, temps de survie, 50 XP par élimination,
  bonus de classement : top 25, top 10, top 5, Victoire royale), et les quêtes en rapportent beaucoup plus.
  1 000 XP = 1 niveau, 50 niveaux par saison.
- **Passe de combat** (onglet PASSE) : une piste gratuite (Kill Tokens, le skin Recrue Éclair, l'emote
  La Vague) et une piste premium à 95 Kill Tokens (skins Chevalier Éclair, Agent Tempête, Roi des Cimes,
  4 emotes et plus de Kill Tokens que son prix). Les récompenses arrivent automatiquement à chaque niveau,
  y compris celles des niveaux déjà atteints quand on achète le passe premium.
- **Quêtes** (onglet QUÊTES) :
  - quêtes du jour : 3 emplacements au maximum, une nouvelle quête par jour, et une quête remplaçable
    par jour ;
  - quêtes de la semaine : 5 nouvelles quêtes chaque lundi ;
  - paliers : objectifs de toute la saison en 5 étapes (éliminations, coffres, parties, victoires,
    constructions, dégâts).

## Jouer en local

Double-clique sur `index.html` pour jouer en solo contre les bots. Pour le multijoueur en local
(plusieurs joueurs sur le même réseau), lance `jouer-en-local.bat` : il démarre le serveur multijoueur
local (port 8787) et le jeu sur http://localhost:3000. Les autres appareils du réseau ouvrent
http://ADRESSE-DE-CE-PC:3000.

## Structure

```
index.html, net.js, config.js   -> le jeu (site publié sur Cloudflare Workers, worker fortnit-jeu)
models/                         -> modèles 3D du jeu (générés par tools/blender)
cloudflare/                     -> serveur multijoueur, comptes et amis (Cloudflare Workers)
android/                        -> appli Android (WebView)
desktop/                        -> appli Windows (Electron)
```

## Site du jeu (Cloudflare)

Le site est le worker `fortnit-jeu`, qui ne sert que des fichiers statiques. Pour le mettre à jour, copier
`index.html`, `config.js`, `net.js` et les modèles utilisés par le jeu (`models/*.glb` sauf les fichiers bruts
listés dans `.gitignore`) dans un dossier, puis :

```bash
npx wrangler deploy --name fortnit-jeu --assets <dossier> --compatibility-date 2026-11-02
```

## Serveur multijoueur (Cloudflare)

Le serveur s'appelle `fortnit` (`cloudflare/wrangler.jsonc`). Pour le mettre à jour, avec Node.js installé :

```bash
cd cloudflare
npx wrangler login
npx wrangler deploy
```

L'adresse du serveur est dans `config.js` (`wss://fortnit.yasser-mobiarchitects.workers.dev`), et le
serveur n'accepte que les connexions venant du site (`ALLOWED_ORIGINS`).

## Appli Android

L'appli ouvre le jeu en ligne (https://fortnit-jeu.yasser-mobiarchitects.workers.dev/) en plein écran ;
il faut Internet. Pour la compiler : ouvrir le dossier `android/` dans Android Studio, puis
Build > Build APK(s). Pour l'installer : copier `HesseFortnite.apk` sur le téléphone, l'ouvrir et
autoriser l'installation depuis cette source.

## Appli Windows

`Fortnit.exe` (dossier `desktop/`, Electron) ouvre en plein écran le jeu en ligne
https://fortnit-jeu.yasser-mobiarchitects.workers.dev/. Le jeu n'est pas dans l'exe : chaque mise à jour du site
arrive toute seule au prochain lancement, sans rien retélécharger. Il faut Internet.

- Pas d'installation : double-clic sur `Fortnit.exe` pour jouer.
- L'exe n'est pas signé : au premier lancement, Windows affiche « Windows a protégé votre ordinateur ».
  Cliquer sur « Informations complémentaires » puis « Exécuter quand même ».
- Dans l'appli : F11 plein écran, F5 recharger.
- Compiler soi-même : `cd desktop`, `npm install`, `npm run build` → `desktop/dist/Fortnit.exe`.
  `npm run icon` régénère l'icône à partir de `desktop/build/icon.svg`.

## Crédits

L'écran **📜 Crédits** du lobby liste tout le détail. En résumé :

- Conception et direction : Yasser (YassuxIsCrafting). Code écrit avec l'aide de Claude (Anthropic).
- [three.js](https://threejs.org) (licence MIT), police [Bungee](https://fonts.google.com/specimen/Bungee)
  (SIL Open Font License).
- Services : Cloudflare (Workers pour le site et le serveur, Durable Objects), cdnjs, Google Fonts.
- Les skins, emotes, véhicules, bâtiments, musiques et effets sonores sont des créations originales du
  projet. Le pistolet, le fusil d'assaut, le pompe et le coffre sont des modèles Sketchfab sous licence
  CC BY 4.0, crédités dans le jeu.
