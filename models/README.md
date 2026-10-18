# Modèles 3D des skins

Chaque skin « modèle 3D » de la boutique lit un fichier `.glb` dans ce dossier.
Tant qu'un fichier manque, le skin s'affiche en version blocs (aucune erreur).

## Comment les récupérer

1. Connecte-toi sur [sketchfab.com](https://sketchfab.com) (compte gratuit).
2. Ouvre le lien du modèle ci-dessous, clique sur **Download 3D Model**.
3. Choisis le format **glTF** puis la version **.glb** (« Autoconverted format (glb) »).
4. Renomme le fichier exactement comme indiqué et place-le dans ce dossier `models/`.

| Fichier à créer | Skin dans le jeu | Modèle d'origine | Auteur | Licence |
|---|---|---|---|---|
| `scout-girl.glb` | Éclaireuse | [Low Poly Scout Girl (Apocalypse \| Rigged)](https://sketchfab.com/3d-models/low-poly-scout-girl-apocalypse-rigged-e388c7898cb7465ab43d0cd2a53cd91a) | micaelsampaio | CC BY 4.0 |
| `plague-doctor.glb` | Docteur peste | [Plague Doctor](https://sketchfab.com/3d-models/plague-doctor-41f7a1dfd6984135b876f334908e3ca4) | BeardenInc | CC BY 4.0 |
| `skeleton-lord.glb` | Seigneur squelette | [Skeleton Lord](https://sketchfab.com/3d-models/skeleton-lord-a3f7b44275cf4c489ad62c535268ac16) | DJMaesen (compte bumstrum) | CC BY 4.0 |
| `elf-guardian.glb` | Gardienne elfe | [Low poly Character animated - Elf guardian](https://sketchfab.com/3d-models/low-poly-character-animated-elf-guardian-c3fbde75977e421bb78e0e7c7fd7a0a3) | Karthik Naidu | CC BY 4.0 |
| `jumpsuit-striker.glb` | Striker | [Jumpsuit Low Poly Game Ready (Striker14)](https://sketchfab.com/3d-models/jumpsuit-low-poly-game-ready-striker14-da288adbddf949aa85962968732f0999) | DanlyVostok | CC BY 4.0 |
| `suavio.glb` | Suavio | [Suavio (animated character)](https://sketchfab.com/3d-models/suavio-animated-character-7bb4d68c63714217a718b64306790193) | Jungle Jim | CC BY 4.0 |
| `rabbit-warrior.glb` | Guerrier lapin | [Rabbit Man Warrior (Animated)](https://sketchfab.com/3d-models/rabbit-man-warrior-animated-7dd8546fb8a444de817ec42d5a8e22a7) | Jungle Jim | CC BY 4.0 |
| `bull-warrior.glb` | Guerrier taureau | [Stylized Epic Bull Man Warrior (animated)](https://sketchfab.com/3d-models/stylized-epic-bull-man-warrior-animated-c888523f5d5748799170e94e701987aa) | Jungle Jim | CC BY 4.0 |

Les crédits de chaque auteur s'affichent dans le jeu (bouton **📜 Crédits** du lobby) et
dans la boutique. Ne retire pas ces crédits : la licence CC BY l'exige.

## Ajouter un autre modèle

N'utilise que des modèles **originaux** (pas de fan-art de personnages de jeux, films ou séries)
sous licence **CC0** ou **CC BY** (pas « NonCommercial »). Ajoute-le ensuite à la liste `MODELS`
dans `index.html` avec son lien, son auteur et sa licence.

Les modèles très détaillés (plus de 50 000 faces) peuvent ralentir le jeu sur mobile.

## Format des crédits (recommandé par Sketchfab)

Les crédits du jeu suivent ce modèle :

> "Titre du modèle" (lien) by Auteur is licensed under Creative Commons Attribution (http://creativecommons.org/licenses/by/4.0/).

Exemple :

> "Stylized Epic Bull Man Warrior (animated)" (https://skfb.ly/p9GOM) by Jungle Jim is licensed under Creative Commons Attribution (http://creativecommons.org/licenses/by/4.0/).

Sketchfab fournit ce texte, avec un lien court `skfb.ly`, quand on télécharge un modèle. Pour les autres
modèles, le lien complet est utilisé tant que le lien court n'est pas renseigné (champ `short` dans `MODELS`).

## Compression

Les fichiers de ce dossier sont compressés pour le web avec [glTF Transform](https://gltf-transform.dev)
(textures en WebP 1024 px, expressions du visage et animations d'origine retirées, car le jeu utilise
ses propres animations). Les originaux sont gardés dans `models/originaux/` (non suivi par git).

Pour compresser un nouveau modèle (Node.js requis) :

```bash
npx @gltf-transform/cli optimize originaux/mon-modele.glb mon-modele.glb --compress false --flatten false --join false --instance false --palette false --simplify false --sparse false --texture-compress webp --texture-size 1024
```
