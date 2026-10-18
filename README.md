# Hesse Fortnite (Île Éclair 3D)

Battle royale 3D jouable dans le navigateur (three.js), en solo contre des bots ou en multijoueur,
sur PC et sur mobile.

> Projet de fan non officiel, gratuit et sans but commercial. Il n'est ni affilié, ni approuvé, ni
> sponsorisé par Epic Games ou Fortnite.

- Jeu en ligne : https://yassuxiscrafting.github.io/Fortnit/
- Appli Android : `HesseFortnite.apk` dans la version « Application Android » du dépôt (voir plus bas).

## Le jeu

- **100 joueurs** par partie : les vrais joueurs (12 maximum), complétés par des bots.
- **Île de départ** : 1 minute d'attente avec les autres joueurs, puis tout le monde monte dans le bus.
- **Bus** qui traverse la carte : saute quand tu veux (Espace), chute libre puis planeur.
- **Carte de 8000 × 8000** : 225 bâtiments, 10 lieux nommés, arbres, coffres, caisses de munitions, 50 voitures.
- **Tempête** en 9 phases : elle apparaît 1 minute après le saut, la zone se décale à chaque phase,
  se referme complètement à la fin et ignore le bouclier.
- **Armes** à raretés (Commun → Légendaire) avec chargeurs : pistolet, fusil d'assaut, pompe, sniper,
  et la pioche pour récolter du bois.
- **Construction** de murs et d'escaliers, dégâts de chute, soins (minipot, grosse potion, medkit).
- **Modes Solo et Duo** : en Duo, on joue avec un ami (groupe) ou un coéquipier bot, on peut être à terre
  et se faire relever. Les bots jouent aussi en binômes.
- **Couronne** : un Top 1 donne une couronne pour la partie suivante (éliminations comptées double).
- **Emotes** sur une roue (touche B), jouables en partie et dans le lobby.
- **Amis** entre comptes, avec invitations en duo.
- **Paramètres** (touche P) : qualité des skins (Bien / Potato), ombres, résolution, distance d'affichage,
  sensibilité, champ de vision, axe inversé, volume général, musique et effets sonores.

## Commandes

**PC** : ZQSD bouger · Souris viser · Clic pioche / tirer · Clic droit viser · 1 pioche · 2-5 armes ·
6-7-8 soins · F coffre / caisse · E voiture (ou relever un équipier) · Espace sauter (et quitter le bus) ·
A (Q en QWERTY) mur · R escalier · M carte · B roue des emotes · P paramètres

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
| Skins | 24 | 1 000 |
| Emotes | 24 | 237 |
| Accessoires | 4 | 15 |
| Tenues (couleurs) | 9 | 14 |
| Outils (palette libre) | 1 | 5 |
| **Toute la boutique** | **62** | **1 271 Kill Tokens** |

Pour tout acheter, il faut donc 1 271 Kill Tokens, soit environ :

- **3 813 éliminations** sans couronne (1 token pour 3 éliminations),
- ou **128 Top 1** (10 tokens chacun),
- ou un mélange des deux (par exemple 60 Top 1 + 2 013 éliminations).

Gratuits dès le départ : le skin Normal, la tenue bleue, les emotes Couronnes, Palmarès, Salut, Bravo et
Pouce levé.

## Jouer en local

Double-clique sur `index.html` pour jouer en solo. Pour voir les skins en modèles 3D, il faut un petit
serveur local (le navigateur bloque le chargement des modèles sinon) :

```bash
npx serve .
```

Puis ouvre l'adresse indiquée (en général http://localhost:3000). En local, le multijoueur et les comptes
sont désactivés : le serveur n'accepte que le site en ligne.

## Skins en modèles 3D

Les fichiers `.glb` vont dans `models/`. La liste des modèles, les liens de téléchargement et les
noms de fichiers sont dans [models/README.md](models/README.md). Tant qu'un fichier manque, le skin
s'affiche en version blocs. Les animations d'origine des modèles sont remplacées par celles du jeu.

## Structure

```
index.html, net.js, config.js   -> le jeu (publié par GitHub Pages)
models/                         -> modèles 3D des skins (.glb) et leur liste
cloudflare/                     -> serveur multijoueur, comptes et amis (Cloudflare Workers)
android/                        -> appli Android (WebView) compilée par GitHub Actions
.github/workflows/android.yml   -> compilation de l'APK et publication
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

À chaque modification du dossier `android/`, GitHub Actions compile l'APK et le publie dans la version
`android-latest` du dépôt (« Application Android »). L'appli ouvre le jeu en ligne en plein écran ;
il faut Internet. Pour l'installer : télécharger `HesseFortnite.apk` sur le téléphone, l'ouvrir et
autoriser l'installation depuis cette source.

## Crédits

L'écran **📜 Crédits** du lobby liste tout le détail. En résumé :

- Conception et direction : Yasser (YassuxIsCrafting). Code écrit avec l'aide de Claude (Anthropic).
- Modèles 3D des skins : auteurs Sketchfab sous licence CC BY 4.0 (voir [models/README.md](models/README.md)).
- [three.js](https://threejs.org) (licence MIT), police [Bungee](https://fonts.google.com/specimen/Bungee)
  (SIL Open Font License).
- Services : GitHub (code, Pages, Actions), Cloudflare (Workers, Durable Objects), cdnjs, jsDelivr,
  Google Fonts, Sketchfab.
- Les autres skins, emotes, armes, véhicules, bâtiments, musiques et effets sonores sont des créations
  originales du projet.
