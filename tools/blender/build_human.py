"""Génère le personnage réaliste d'Île Éclair (maillage riggé) et ses accessoires de skins, exporte models/human.glb.

blender -b --factory-startup -P <script qui exec ce fichier puis appelle build_human() et export_human()>

Squelette identique à celui de hero-eclair.glb (mêmes noms d'os, tous orientés vers le haut, sans rotation de repos) :
le jeu recopie les poses du corps en blocs sur ces os, donc marche, visée, planeur et emotes marchent tels quels.
Pose en T, face avant = +X, bras le long de ±Y Blender (ArmP du côté -Y). Mètres, ~1,77 m de haut.

Matériaux du corps : Skin, Shirt, Pants, Belt, Shoes, Hair, EyeW, EyeD — le jeu les recolore selon la tenue ou le skin.
Accessoires : un matériau par couleur nommé A_<skin>_<couleur hex>[_<os>] ; le jeu n'affiche que ceux du skin porté
(table KIT dans index.html) et garde la couleur écrite dans le nom. Le suffixe d'os fixe la pièce sur cet os
(bouclier, cape, ailes, sac : sur le dos, ils ne doivent pas suivre les bras).
"""
import bpy, bmesh, math, os
from mathutils import Vector, Euler

OUT_HUMAN = r"C:/Repos/Fortnit/models/human.glb"
COLL_HUMAN = "IleEclair_Human"
COLS = {"Skin": 0xf1c27d, "Shirt": 0x3da5ff, "Pants": 0x2b2b3a, "Belt": 0x1b1b22, "Shoes": 0xf5f5f5,
        "Hair": 0x3b2a1e, "EyeW": 0xffffff, "EyeD": 0x1b1b22}
HEAD_C, HEAD_R = Vector((0.01, 0, 1.64)), 0.115
HC, R = HEAD_C, HEAD_R


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mat(name):
    m = bpy.data.materials.get("H_" + name) or bpy.data.materials.new("H_" + name)
    rgb = [lin((COLS[name] >> s) & 255) for s in (16, 8, 0)]
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None) or nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 0.7
    return m


def link(coll, ob):
    coll.objects.link(ob)
    return ob


# ---------- découpes ----------
def below(z):
    return lambda bm: bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z < z], context="FACES")


def keep(test):
    return lambda bm: bmesh.ops.delete(bm, geom=[f for f in bm.faces if not test(f.calc_center_median())], context="FACES")


def jaw(bm):
    # bas du visage plus étroit, menton légèrement en avant
    for v in bm.verts:
        t = max(0.0, (HEAD_C.z - v.co.z) / (HEAD_R * 1.1))
        v.co.y *= 1 - 0.22 * t
        v.co.x += 0.014 * t * max(0.0, v.co.x - HEAD_C.x) / HEAD_R * 3


hair_cut = keep(lambda c: not ((c.x > 0.045 and c.z < 1.705) or c.z < 1.60 or (abs(c.y) > 0.09 and c.z < 1.64 and c.x > -0.03)))
face_hole = keep(lambda c: not (c.x > 0.055 and 1.56 < c.z < 1.71) and c.z > 1.5)
eye_band = keep(lambda c: not (c.x > 0.04 and 1.635 < c.z < 1.675) and c.z > 1.5)


# ---------- accessoires des skins : (forme, position, demi-tailles, couleur, options) ----------
def cap(col):
    return [("sphere", HC + Vector((-0.004, 0, 0.03)), (R * 1.13, R * 1.05, R * 0.92), col, {"cut": below(HC.z + 0.035), "u": 24, "v": 16}),
            ("sphere", (0.118, 0, 1.676), (0.062, 0.092, 0.009), col, {"cut": keep(lambda c: c.x > 0.085)})]


def helmet(col, k=1.12, cut=1.52):
    return ("sphere", HC + Vector((0, 0, 0.008)), (R * k, R * 0.93 * k, R * 1.02 * k), col, {"cut": below(cut), "u": 24, "v": 16})


def pair(f):
    return [f(s) for s in (1, -1)]


def torso_ring(z, col, h=0.014):
    rx = 0.105 + 0.02 * max(0, min(1, (z - 1.06) / 0.16))
    ry = 0.145 + 0.025 * max(0, min(1, (z - 1.06) / 0.16))
    return ("cyl", (0, 0, z), (rx + 0.006, ry + 0.006, h), col, {"u": 24})


ACC = {
    "robot": [("cube", (0.012, 0, 1.645), (0.135, 0.12, 0.135), 0xaab4c2, {}),
              ("cube", (0.144, 0, 1.655), (0.006, 0.085, 0.022), 0x00e5ff, {}),
              ("cyl", (0, 0, 1.81), (0.006, 0.006, 0.03), 0x2a2a33, {}),
              ("sphere", (0, 0, 1.85), (0.014, 0.014, 0.014), 0xff4d4d, {}),
              ("cube", (0.128, 0, 1.27), (0.01, 0.055, 0.04), 0x00e5ff, {})]
             + pair(lambda s: ("cube", (0, 0.19 * s, 1.45), (0.06, 0.055, 0.035), 0x2a2a33, {}))
             + pair(lambda s: ("cube", (0.01, 0.126 * s, 1.645), (0.03, 0.01, 0.03), 0xff4d4d, {})),
    "ninja": [("sphere", HC + Vector((0, 0, 0.003)), (R * 1.06, R * 0.97, R * 1.12), 0x15151f, {"cut": eye_band, "u": 24, "v": 18}),
              ("cyl", (0.005, 0, 1.69), (R * 1.1, R * 1.0, 0.012), 0xff2d95, {"u": 24})]
             + pair(lambda s: ("cube", (-0.14, 0.025 * s, 1.665), (0.045, 0.006, 0.01), 0xff2d95, {"rot": (0, 15, 20 * s)})),
    "astro": [("sphere", HC + Vector((0, 0, 0.005)), (R * 1.4, R * 1.32, R * 1.35), 0xf2f2f2,
               {"cut": keep(lambda c: not (c.x > 0.05 and 1.575 < c.z < 1.735) and c.z > 1.5), "u": 28, "v": 18}),
              ("sphere", HC + Vector((0.004, 0, 0.005)), (R * 1.37, R * 1.29, R * 1.32), 0x7fb8e6,
               {"cut": keep(lambda c: c.x > 0.05 and 1.575 < c.z < 1.735), "u": 28, "v": 18}),
              ("cyl", (0, 0, 1.50), (0.1, 0.1, 0.02), 0xcfcfcf, {"u": 20}),
              ("cube", (-0.165, 0, 1.24), (0.05, 0.12, 0.16), 0xdedede, {"pin": "Spine"}),
              ("cube", (0.135, 0, 1.25), (0.015, 0.055, 0.04), 0x3a3d47, {})],
    "knight": [helmet(0xe6b422),
               ("cube", (0.137, 0, 1.655), (0.006, 0.075, 0.007), 0x1b1b22, {}),
               ("cone", (-0.01, 0, 1.83), (0.025, 0.025, 0.06), 0xd62828, {"r2": 0.1}),
               ("cube", (-0.167, 0, 1.24), (0.008, 0.13, 0.16), 0x2b4cc2, {"pin": "Spine"}),
               ("cube", (-0.157, 0, 1.24), (0.008, 0.14, 0.17), 0xe6b422, {"pin": "Spine"})]
              + pair(lambda s: ("sphere", (0, 0.19 * s, 1.445), (0.075, 0.075, 0.05), 0xe6b422, {})),
    "dino": [("sphere", HC + Vector((0, 0, 0.01)), (R * 1.15, R * 1.06, R * 1.15), 0x3fae49, {"cut": face_hole, "u": 24, "v": 18}),
             ("cube", (0.08, 0, 1.775), (0.075, 0.06, 0.03), 0x3fae49, {}),
             ("cube", (0.152, 0, 1.748), (0.003, 0.05, 0.005), 0xffffff, {}),
             ("cone", (-0.24, 0, 0.88), (0.06, 0.06, 0.13), 0x3fae49, {"r2": 0.15, "rot": (0, -110, 0), "pin": "Hips"})]
            + pair(lambda s: ("sphere", (0.06, 0.045 * s, 1.81), (0.016, 0.016, 0.016), 0xffffff, {}))
            + pair(lambda s: ("sphere", (0.073, 0.05 * s, 1.815), (0.008, 0.008, 0.008), 0x111111, {}))
            + [("cone", (-0.135 - 0.01 * (i == 0), 0, z), (0.03, 0.012, 0.035), 0xff9f1c, {"rot": (0, -90, 0), "r2": 0, "pin": "Spine"})
               for i, z in enumerate((1.36, 1.22, 1.08))],
    "ghost": [("sphere", HC + Vector((0, 0, 0.01)), (R * 1.2, R * 1.12, R * 1.2), 0xf5f7ff, {"cut": below(1.5), "u": 24, "v": 18}),
              ("cone", (0, 0, 0.95), (0.24, 0.24, 0.5), 0xf5f7ff, {"r2": 0.55, "pin": "Hips", "u": 20}),
              ("sphere", (0.14, 0, 1.6), (0.01, 0.02, 0.018), 0x111111, {})]
             + pair(lambda s: ("sphere", (0.135, 0.042 * s, 1.665), (0.012, 0.022, 0.03), 0x111111, {})),
    "pirate": [("cyl", (0, 0, 1.755), (0.16, 0.16, 0.01), 0x1b1b22, {"u": 24}),
               ("cyl", (0, 0, 1.79), (0.1, 0.1, 0.035), 0x1b1b22, {"r2": 0.85, "u": 20}),
               ("cyl", (0, 0, 1.772), (0.102, 0.102, 0.008), 0xffd23f, {"u": 20}),
               ("cube", (0.124, 0.037, 1.656), (0.004, 0.02, 0.017), 0x111111, {})],
    "chef": [("cyl", (0, 0, 1.80), (0.095, 0.095, 0.06), 0xffffff, {"u": 20}),
             ("sphere", (0, 0, 1.89), (0.12, 0.12, 0.06), 0xffffff, {}),
             ("cube", (0.075, 0, 1.475), (0.03, 0.07, 0.018), 0xe63946, {}),
             ("cube", (0.134, 0, 1.06), (0.008, 0.12, 0.19), 0xffffff, {"pin": "Hips"})]
            + [("sphere", (0.128, y, z), (0.008, 0.008, 0.008), 0x3a3a3a, {}) for y in (-0.05, 0.05) for z in (1.3, 1.36)],
    "fire": [("sphere", HC + Vector((-0.005, 0, 0.02)), (R * 1.13, R * 1.05, R * 1.0), 0xd62828, {"cut": below(1.665), "u": 24, "v": 16}),
             ("cyl", (-0.01, 0, 1.665), (0.15, 0.14, 0.008), 0xd62828, {"u": 24}),
             ("cube", (0.13, 0, 1.72), (0.006, 0.025, 0.025), 0xffd23f, {})]
            + [("cube", (x, 0, z), (0.006, 0.15, 0.012), 0xd9e1e8, {}) for x in (0.127, -0.125) for z in (1.15, 1.32)]
            + pair(lambda s: ("cyl", (0.005, 0.095 * s, 0.3), (0.05, 0.05, 0.01), 0xd9e1e8, {"u": 16})),
    "mummy": [torso_ring(z, 0xcfc2a2) for z in (1.08, 1.18, 1.3)]
             + [("cyl", HC + Vector((0, 0, dz)), (R * 1.02, R * 0.94, 0.01), 0xcfc2a2, {"u": 24}) for dz in (-0.04, 0.05)]
             + [("cyl", (0.005, 0.095 * s, z), (0.064, 0.064, 0.01), 0xcfc2a2, {"u": 16}) for s in (1, -1) for z in (0.7, 0.35)]
             + [("cyl", (0, y * s, 1.42), (0.047, 0.047, 0.01), 0xcfc2a2, {"rot": (90, 0, 0), "u": 16}) for s in (1, -1) for y in (0.3, 0.55)],
    "pumpkin": [("sphere", HC + Vector((0, 0, 0.02)), (0.165, 0.15, 0.14), 0xf28c28, {"u": 24, "v": 16}),
                ("cyl", (0, 0, 1.80), (0.015, 0.015, 0.03), 0x3b7d3a, {"u": 10}),
                ("cube", (0.172, 0, 1.62), (0.006, 0.07, 0.012), 0x111111, {})]
               + pair(lambda s: ("sphere", HC + Vector((0, 0.07 * s, 0.02)), (0.13, 0.07, 0.135), 0xe07b16, {}))
               + pair(lambda s: ("cone", (0.172, 0.05 * s, 1.68), (0.022, 0.022, 0.01), 0x111111, {"u": 3, "r2": 0, "rot": (0, 90, 0)})),
    "bee": [torso_ring(1.1, 0x1b1b22, 0.03), torso_ring(1.26, 0x1b1b22, 0.03)]
           + pair(lambda s: ("cyl", (0.03, 0.035 * s, 1.80), (0.004, 0.004, 0.05), 0x1b1b22, {"rot": (-15 * s, 0, 0), "u": 8}))
           + pair(lambda s: ("sphere", (0.03, 0.05 * s, 1.86), (0.013, 0.013, 0.013), 0x1b1b22, {}))
           + pair(lambda s: ("sphere", (-0.15, 0.09 * s, 1.32), (0.01, 0.08, 0.13), 0xe6f3ff, {"rot": (-20 * s, 0, 0), "pin": "Spine"})),
    "yeti": [("sphere", HC + Vector((-0.01, 0, 0.02)), (R * 1.1, R * 1.02, R * 1.05), 0xeef6ff, {"cut": face_hole, "u": 24, "v": 16}),
             ("sphere", (0.11, 0, 1.32), (0.05, 0.1, 0.06), 0xeef6ff, {})]
            + pair(lambda s: ("cone", (0, 0.085 * s, 1.75), (0.02, 0.02, 0.045), 0xf5f0e0, {"r2": 0.1, "rot": (-25 * s, 0, 0)}))
            + pair(lambda s: ("sphere", (0, 0.17 * s, 1.47), (0.07, 0.07, 0.05), 0xeef6ff, {})),
    "viking": [("sphere", HC + Vector((0, 0, 0.015)), (R * 1.1, R * 1.02, R * 1.0), 0x9aa3ad, {"cut": below(1.665), "u": 24, "v": 16}),
               ("cube", (0.13, 0, 1.67), (0.006, 0.008, 0.03), 0x9aa3ad, {}),
               ("sphere", (0.09, 0, 1.555), (0.06, 0.075, 0.065), 0xc0602b, {})]
              + pair(lambda s: ("cone", (0, 0.12 * s, 1.73), (0.022, 0.022, 0.06), 0xf5f0e0, {"r2": 0.1, "rot": (-60 * s, 0, 0)}))
              + pair(lambda s: ("sphere", (0, 0.16 * s, 1.45), (0.08, 0.08, 0.05), 0x6b4a2b, {})),
    "crystal": [("cone", (0, 0, 1.79), (0.03, 0.03, 0.06), 0xd1c4ff, {"u": 4, "r2": 0}),
                ("cone", (-0.13, 0, 1.3), (0.03, 0.03, 0.06), 0xd1c4ff, {"u": 4, "r2": 0, "rot": (0, -90, 0), "pin": "Spine"})]
               + pair(lambda s: ("cone", (-0.03, 0.06 * s, 1.76), (0.022, 0.022, 0.05), 0xd1c4ff, {"u": 4, "r2": 0, "rot": (-30 * s, 0, 0)}))
               + pair(lambda s: ("cone", (0, 0.18 * s, 1.48), (0.03, 0.03, 0.06), 0xd1c4ff, {"u": 4, "r2": 0, "rot": (-35 * s, 0, 0)})),
    # Kaiju des Marais : monstre original (tête de reptile à museau, cornes en os, crête de plaques ambrées, longue queue).
    "kaiju": [("sphere", HC + Vector((-0.005, 0, 0.0)), (R * 1.12, R * 1.0, R * 1.08), 0x4a6b2f, {"u": 24, "v": 16}),
              ("sphere", (0.125, 0, 1.625), (0.1, 0.078, 0.058), 0x4a6b2f, {"u": 20, "v": 12}),
              ("sphere", (0.118, 0, 1.565), (0.09, 0.066, 0.026), 0x2f4520, {"u": 18, "v": 10}),
              ("cube", (0.12, 0, 1.588), (0.075, 0.056, 0.006), 0x8a1f1f, {}),
              ("cube", (0.065, 0, 1.69), (0.06, 0.085, 0.018), 0x2f4520, {"rot": (0, 12, 0)})]
             + pair(lambda s: ("sphere", (0.098, 0.068 * s, 1.665), (0.02, 0.016, 0.014), 0xffd23f, {}))
             + pair(lambda s: ("sphere", (0.114, 0.072 * s, 1.665), (0.006, 0.006, 0.011), 0x111111, {}))
             + pair(lambda s: ("sphere", (0.215, 0.022 * s, 1.645), (0.007, 0.006, 0.005), 0x111111, {}))
             + pair(lambda s: ("cone", (-0.03, 0.075 * s, 1.75), (0.022, 0.022, 0.07), 0xe8dcc0, {"r2": 0, "rot": (-25 * s, -45, 0)}))
             + [("cone", (0.17 - 0.035 * i, 0.05 * s, 1.578), (0.006, 0.006, 0.012), 0xf5f0e0, {"r2": 0})
                for i in range(3) for s in (1, -1)]
             # crête : grande sur la nuque, puis de plus en plus petite le long du dos
             + [("cone", (-0.13 - 0.01 * (i == 0), 0, z), (0.05 * k, 0.009, 0.055 * k), 0xff8c1a, {"rot": (0, -90, 0), "r2": 0, "pin": "Spine"})
                for i, (z, k) in enumerate(((1.6, 1.0), (1.47, 1.2), (1.34, 1.1), (1.21, 0.95), (1.08, 0.8)))]
             # queue épaisse qui traîne vers le sol, avec ses petites plaques
             + [("cone", (-0.31, 0, 0.76), (0.095, 0.095, 0.27), 0x4a6b2f, {"r2": 0.12, "rot": (0, -118, 0), "pin": "Hips", "u": 16})]
             + [("cone", (-0.12 - 0.17 * t, 0, 0.94 - 0.12 * t), (0.038 * (1 - 0.45 * t), 0.008, 0.04 * (1 - 0.45 * t)), 0xff8c1a,
                 {"rot": (0, -62, 0), "r2": 0, "pin": "Hips"}) for t in (0.15, 0.55, 0.95, 1.35)]
             + pair(lambda s: ("sphere", (0, 0.19 * s, 1.45), (0.07, 0.07, 0.05), 0x4a6b2f, {"u": 12, "v": 8}))
             + pair(lambda s: ("cone", (-0.01, 0.2 * s, 1.5), (0.014, 0.014, 0.04), 0xe8dcc0, {"r2": 0, "rot": (-30 * s, 0, 0)}))
             + [("cone", (0.13, 0.095 * s + 0.025 * j, 0.03), (0.008, 0.008, 0.025), 0xe8dcc0, {"r2": 0, "rot": (0, 90, 0)})
                for s in (1, -1) for j in (-1, 0, 1)],
    # Corsaire des Récifs : pirate original (bandana bleu noué derrière, anneau d'or, écharpe rouge en travers, sabre à la hanche).
    "corsaire": [("sphere", HC + Vector((-0.004, 0, 0.03)), (R * 1.14, R * 1.08, R * 1.0), 0x1f6fb2, {"cut": below(HC.z + 0.025), "u": 24, "v": 16}),
                 ("sphere", (-0.13, 0, 1.672), (0.024, 0.032, 0.024), 0x1f6fb2, {}),
                 ("sphere", (0.0, 0.118, 1.6), (0.009, 0.004, 0.009), 0xffd23f, {}),
                 ("cube", (0.127, 0, 1.3), (0.006, 0.026, 0.19), 0xb8322a, {"rot": (38, 0, 0)}),
                 torso_ring(1.07, 0xb8322a, 0.022),
                 ("cube", (0.03, 0.168, 0.84), (0.005, 0.013, 0.13), 0xd9e1e8, {"rot": (0, 12, 0), "pin": "Hips"}),
                 ("cube", (0.0, 0.168, 0.975), (0.022, 0.028, 0.006), 0xffd23f, {"pin": "Hips"}),
                 ("cube", (-0.004, 0.168, 1.01), (0.008, 0.008, 0.03), 0x5a3a24, {"pin": "Hips"})]
                + pair(lambda s: ("cube", (-0.158, 0.018 * s, 1.63), (0.035, 0.007, 0.012), 0x1f6fb2, {"rot": (0, 55, 15 * s), "pin": "Head"})),
    "golem": [("sphere", (-0.01, 0, 1.75), (0.09, 0.08, 0.05), 0x3a3030, {"u": 7, "v": 5}),
              ("cube", (0.127, 0.03, 1.2), (0.004, 0.008, 0.07), 0xff7a1a, {"rot": (25, 0, 0)}),
              ("cube", (0.126, -0.05, 1.32), (0.004, 0.04, 0.006), 0xff7a1a, {}),
              ("cube", (-0.125, 0, 1.25), (0.004, 0.006, 0.09), 0xff7a1a, {"rot": (-20, 0, 0)})]
             + pair(lambda s: ("sphere", (0, 0.18 * s, 1.46), (0.08, 0.08, 0.06), 0x3a3030, {"u": 7, "v": 5}))
             + pair(lambda s: ("cube", (0.06, 0.095 * s, 0.62), (0.004, 0.006, 0.06), 0xff7a1a, {}))
             + pair(lambda s: ("sphere", (0.118, 0.037 * s, 1.655), (0.012, 0.014, 0.012), 0xff7a1a, {})),
    "recruit": cap(0x2e6fd6)
               + [("cube", (0.129, 0.008, 1.3), (0.005, 0.012, 0.035), 0x2e6fd6, {"rot": (30, 0, 0)}),
                  ("cube", (0.129, -0.008, 1.24), (0.005, 0.012, 0.035), 0x2e6fd6, {"rot": (30, 0, 0)})]
               + pair(lambda s: ("cube", (0, 0.19 * s, 1.45), (0.05, 0.05, 0.03), 0x2e6fd6, {})),
    "bknight": [helmet(0xc9d3e0),
                ("cube", (0.137, 0, 1.655), (0.007, 0.08, 0.012), 0x00e5ff, {})]
               + [("cone", (-0.02 - 0.03 * i, 0, 1.80 - 0.012 * i), (0.012, 0.012, 0.04), 0xffd23f, {"r2": 0, "rot": (0, -25 * i, 0)}) for i in range(3)]
               + pair(lambda s: ("sphere", (0, 0.19 * s, 1.445), (0.072, 0.072, 0.048), 0xc9d3e0, {})),
    "agent": [("cube", (0.118, 0, 1.656), (0.014, 0.1, 0.016), 0xc27bff, {})]
             + pair(lambda s: ("cube", (0, 0.19 * s, 1.45), (0.055, 0.05, 0.03), 0x1b1430, {})),
    "king": [("cyl", (0, 0, 1.775), (0.085, 0.08, 0.02), 0xffd23f, {"u": 20}),
             ("cube", (-0.145, 0, 1.12), (0.01, 0.16, 0.32), 0xd62828, {"pin": "Spine"}),
             ("cyl", (0, 0, 1.465), (0.11, 0.12, 0.02), 0xffd23f, {"u": 20})]
            + [("cone", (0.075 * math.cos(a), 0.072 * math.sin(a), 1.81), (0.012, 0.012, 0.022), 0xffd23f, {"r2": 0, "u": 6})
               for a in (i * math.pi / 3 for i in range(6))],
    "soldier": cap(0x4b5320)
               + [("cube", (0.112, 0, 1.25), (0.032, 0.15, 0.14), 0x3d4a2a, {}),
                  ("cube", (-0.108, 0, 1.26), (0.03, 0.15, 0.14), 0x3d4a2a, {"pin": "Spine"}),
                  ("cube", (-0.165, 0, 1.24), (0.045, 0.12, 0.15), 0x3d4a2a, {"pin": "Spine"}),
                  ("sphere", (-0.165, 0, 1.39), (0.05, 0.12, 0.03), 0x3d4a2a, {"pin": "Spine", "u": 16, "v": 8})]
               + [("cube", (0.152, y, 1.17), (0.016, 0.03, 0.04), 0x3d4a2a, {}) for y in (-0.075, 0, 0.075)]
               + pair(lambda s: ("cube", (0.0, 0.1 * s, 1.425), (0.13, 0.03, 0.012), 0x3d4a2a, {}))
               + pair(lambda s: ("sphere", (0.055, 0.095 * s, 0.50), (0.022, 0.05, 0.055), 0x3d4a2a, {"u": 14, "v": 10}))
               + pair(lambda s: ("cube", (0.02, 0.15 * s, 0.97), (0.04, 0.025, 0.045), 0x3d4a2a, {}))
               + pair(lambda s: ("cyl", (0.0, 0.095 * s, 0.16), (0.05, 0.05, 0.04), 0x1f1f1f, {"u": 16})),
}


def acc_mat(acc, col, pin):
    return "A_%s_%06x" % (acc, col) + ("_" + pin if pin else "")


for _acc, _specs in ACC.items():
    for _s in _specs:
        _n = acc_mat(_acc, _s[3], _s[4].get("pin"))
        COLS[_n] = _s[3]
MATS = list(COLS)


def part(coll, name, prim, loc, scale, matname, **kw):
    bm = bmesh.new()
    if prim == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=kw.get("u", 20), v_segments=kw.get("v", 14), radius=1)
    elif prim in ("cone", "cyl"):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=kw.get("u", 12), radius1=1,
                              radius2=1 if prim == "cyl" and "r2" not in kw else kw.get("r2", 0), depth=2)
    else:
        bmesh.ops.create_cube(bm, size=2)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    if kw.get("rot"):
        bmesh.ops.rotate(bm, verts=bm.verts, matrix=Euler([math.radians(a) for a in kw["rot"]]).to_matrix())
    bmesh.ops.translate(bm, vec=loc, verts=bm.verts)
    if kw.get("cut"):
        kw["cut"](bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in MATS:
        me.materials.append(mat(m))
    for f in me.polygons:
        f.use_smooth = prim == "sphere"
        f.material_index = MATS.index(matname)
    return link(coll, bpy.data.objects.new(name, me))


def body_mesh(coll):
    """Corps d'un seul tenant : chaîne de sommets + modificateur Skin, puis subdivision."""
    P = [((0, 0, 0.95), (0.12, 0.16)), ((0, 0, 1.06), (0.105, 0.145)), ((0, 0, 1.22), (0.125, 0.17)),
         ((0, 0, 1.36), (0.11, 0.165)), ((0, 0, 1.46), (0.058, 0.058)), ((0, 0, 1.54), (0.05, 0.05))]
    E = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
    for s in (1, -1):
        b = len(P)
        P += [((0, 0.17 * s, 1.42), (0.056, 0.056)), ((0, 0.44 * s, 1.42), (0.041, 0.041)), ((0, 0.68 * s, 1.42), (0.031, 0.029)),
              ((0, 0.765 * s, 1.42), (0.046, 0.018)), ((0.01, 0.84 * s, 1.415), (0.036, 0.015))]
        E += [(3, b), (b, b + 1), (b + 1, b + 2), (b + 2, b + 3), (b + 3, b + 4)]
        b = len(P)
        P += [((0, 0.09 * s, 0.90), (0.088, 0.088)), ((0.005, 0.095 * s, 0.50), (0.058, 0.058)), ((0, 0.095 * s, 0.09), (0.042, 0.042)),
              ((0.15, 0.095 * s, 0.04), (0.036, 0.046)), ((-0.05, 0.095 * s, 0.04), (0.036, 0.04))]
        E += [(0, b), (b, b + 1), (b + 1, b + 2), (b + 2, b + 3), (b + 2, b + 4)]
    me = bpy.data.meshes.new("H_body")
    me.from_pydata([p for p, _ in P], E, [])
    ob = link(coll, bpy.data.objects.new("H_body", me))
    mod = ob.modifiers.new("skin", "SKIN")
    mod.branch_smoothing = 0.6
    mod.use_smooth_shade = True
    for i, (_, r) in enumerate(P):
        sv = me.skin_vertices[0].data[i]
        sv.radius = r
        sv.use_root = i == 0
    sub = ob.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 2
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.view_layer.objects:
        o.select_set(o == ob)
    bpy.ops.object.modifier_apply(modifier="skin")
    bpy.ops.object.modifier_apply(modifier="sub")
    me = ob.data
    # coupes nettes aux ourlets (chaussures, ceinture, manches, col) avant d'attribuer les matériaux par zone
    bm = bmesh.new()
    bm.from_mesh(me)
    for co, no in (((0, 0, 0.13), (0, 0, 1)), ((0, 0, 0.965), (0, 0, 1)), ((0, 0, 1.02), (0, 0, 1)),
                   ((0, 0.36, 0), (0, 1, 0)), ((0, -0.36, 0), (0, 1, 0)),
                   ((0, 0, 1.445), (0, 0, 1)), ((0, 0.11, 0), (0, 1, 0)), ((0, -0.11, 0), (0, 1, 0))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)
    bm.to_mesh(me)
    bm.free()
    for m in MATS:
        me.materials.append(mat(m))
    for f in me.polygons:
        c = f.center
        if c.z < 0.13:
            k = "Shoes"
        elif 0.965 < c.z < 1.02 and abs(c.y) < 0.2:
            k = "Belt"
        elif c.z < 0.99:
            k = "Pants"
        elif c.z < 1.47 and abs(c.y) < 0.36 and not (c.z > 1.445 and abs(c.y) < 0.11):
            k = "Shirt"
        else:
            k = "Skin"
        f.material_index = MATS.index(k)
        f.use_smooth = True
    return ob


def head_parts(coll):
    obs = [part(coll, "H_head", "sphere", HC, (R, R * 0.9, R * 1.1), "Skin", u=24, v=18, cut=jaw),
           part(coll, "H_hair", "sphere", HC + Vector((-0.008, 0, 0.018)), (R * 1.07, R * 0.98, R * 1.1), "Hair", u=24, v=18, cut=hair_cut),
           part(coll, "H_nose", "sphere", (0.123, 0, 1.622), (0.017, 0.014, 0.026), "Skin", u=12, v=8)]
    for s in (1, -1):
        obs += [part(coll, "H_ear", "sphere", (0.0, 0.1 * s, 1.635), (0.018, 0.012, 0.03), "Skin", u=12, v=8),
                part(coll, "H_eyeW", "sphere", (0.104, 0.037 * s, 1.655), (0.017, 0.017, 0.015), "EyeW", u=12, v=8),
                part(coll, "H_eyeD", "sphere", (0.119, 0.037 * s, 1.654), (0.006, 0.009, 0.009), "EyeD", u=10, v=6),
                part(coll, "H_brow", "cube", (0.117, 0.038 * s, 1.684), (0.004, 0.017, 0.0035), "Hair")]
    obs.append(part(coll, "H_mouth", "cube", (0.13, 0, 1.584), (0.003, 0.017, 0.0028), "EyeD"))
    return obs


def acc_parts(coll):
    obs = []
    for acc, specs in ACC.items():
        for i, (prim, loc, scale, col, opt) in enumerate(specs):
            kw = {k: v for k, v in opt.items() if k != "pin"}
            obs.append(part(coll, "A_%s_%d" % (acc, i), prim, loc, scale, acc_mat(acc, col, opt.get("pin")), **kw))
    return obs


BONES = [("Hips", None, (0, 0, 0.92), 0.13), ("Spine", "Hips", (0, 0, 1.05), 0.41), ("Head", "Spine", (0, 0, 1.50), 0.27),
         ("ArmP", "Spine", (0, -0.17, 1.42), 0.18), ("ForeP", "ArmP", (0, -0.44, 1.42), 0.18),
         ("ArmN", "Spine", (0, 0.17, 1.42), 0.18), ("ForeN", "ArmN", (0, 0.44, 1.42), 0.18),
         ("LegP", "Hips", (0, -0.09, 0.90), 0.18), ("ShinP", "LegP", (0, -0.095, 0.50), 0.18),
         ("LegN", "Hips", (0, 0.09, 0.90), 0.18), ("ShinN", "LegN", (0, 0.095, 0.50), 0.18)]


def ramp(v, a, b):
    return max(0.0, min(1.0, (v - a) / (b - a)))


def weights(co):
    x, y, z = co
    ay, s = abs(y), ("P" if y < 0 else "N")
    if z > 1.49:
        t = ramp(z, 1.47, 1.53)
        return {"Head": t, "Spine": 1 - t}
    if z > 1.28 and ay > 0.13:
        a = ramp(ay, 0.13, 0.22)
        f = ramp(ay, 0.41, 0.47)
        return {"Spine": 1 - a, "Arm" + s: a * (1 - f), "Fore" + s: a * f}
    if z < 0.97 and ay > 0.015:
        l = ramp(z, 0.97, 0.84) * ramp(ay, 0.015, 0.05)
        k = ramp(z, 0.54, 0.46)
        return {"Hips": 1 - l, "Leg" + s: l * (1 - k), "Shin" + s: l * k}
    t = ramp(z, 1.0, 1.12)
    return {"Hips": 1 - t, "Spine": t}


def build_human():
    coll = bpy.data.collections.get(COLL_HUMAN) or bpy.data.collections.new(COLL_HUMAN)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for ob in list(coll.objects):
        d = ob.data
        bpy.data.objects.remove(ob)
        if d is not None and d.users == 0:
            (bpy.data.meshes if isinstance(d, bpy.types.Mesh) else bpy.data.armatures).remove(d)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    body = body_mesh(coll)
    parts = head_parts(coll) + acc_parts(coll)
    # fusion par l'API de données (l'opérateur join ne marche pas toujours en arrière-plan) ;
    # chaque pièce porte les matériaux dans l'ordre de MATS, donc les index restent justes
    bm = bmesh.new()
    bm.from_mesh(body.data)
    for o in parts:
        o.data.transform(o.matrix_world)
        bm.from_mesh(o.data)
        d = o.data
        bpy.data.objects.remove(o)
        bpy.data.meshes.remove(d)
    bm.to_mesh(body.data)
    bm.free()
    body.name = body.data.name = "Human"
    me = body.data

    arm = bpy.data.armatures.new("Armature")
    rig = link(coll, bpy.data.objects.new("Armature", arm))
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.view_layer.objects:
        o.select_set(o == rig)
    bpy.ops.object.mode_set(mode="EDIT")
    for n, p, h, l in BONES:
        b = arm.edit_bones.new(n)
        b.head = h
        b.tail = (h[0], h[1], h[2] + l)
        b.roll = 0
        if p:
            b.parent = arm.edit_bones[p]
    bpy.ops.object.mode_set(mode="OBJECT")

    body.parent = rig
    md = body.modifiers.new("Armature", "ARMATURE")
    md.object = rig
    groups = {n: body.vertex_groups.new(name=n) for n, *_ in BONES}
    pin = {}  # sommets des pièces fixées sur un os (suffixe du matériau)
    for f in me.polygons:
        n = MATS[f.material_index]
        if n.startswith("A_") and n.split("_")[-1] in groups:
            for v in f.vertices:
                pin[v] = n.split("_")[-1]
    for v in me.vertices:
        for n, w in ({pin[v.index]: 1.0} if v.index in pin else weights(v.co)).items():
            if w > 1e-4:
                groups[n].add([v.index], w, "REPLACE")
    rig.location = (2600, 0, 0)
    return coll, {"verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons), "mats": len(MATS)}


def export_human(coll, out=OUT_HUMAN):
    rig = next(o for o in coll.objects if o.type == "ARMATURE")
    loc = tuple(rig.location)
    rig.location = (0, 0, 0)
    bpy.ops.object.select_all(action="DESELECT")
    for ob in coll.objects:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_apply=False,
                              export_yup=True, export_normals=True, export_texcoords=False, export_animations=False,
                              export_skins=True)
    rig.location = loc
    bpy.ops.object.select_all(action="DESELECT")
    return os.path.getsize(out)
