"""Génère les parties du corps des personnages d'Île Éclair et exporte models/character.glb.

Lancer dans Blender :  exec(open(r"C:/Repos/Fortnit/tools/blender/build_character.py", encoding="utf-8").read(), {"__name__": "chr"})

Le jeu anime un corps en pièces (mkChar) et y accroche skins, chapeaux et visage : chaque pièce garde
le centre et l'encombrement de l'ancienne géométrie (gBody, gHead, gLeg, gFoot, gArm, gHand).
Une seule couleur par pièce (le matériau vient du jeu), le relief fait tout le détail. Face avant = +X.
"""
import bpy, math, os

exec(open(r"C:/Repos/Fortnit/tools/blender/build_items.py", encoding="utf-8").read(), globals())

OUT_CHR = r"C:/Repos/Fortnit/models/character.glb"
COLL_CHR = "IleEclair_Character"
W = 0xffffff


def body():
    # reste dans le cône d'origine (rayon 10 en bas -> 12,5 en haut) pour que les bandes des skins restent visibles
    it = Item("C_body")
    it.lathe([(0, -11), (8.4, -11), (9.5, -10.5), (10.1, -9.4), (10.5, -6), (11.0, -2), (11.6, 2), (12.1, 5.5),
              (12.3, 8.2), (11.8, 10), (10.4, 11), (7.6, 11.5), (5.4, 11.9), (5.0, 12.8), (0, 12.8)], 0, 0, 0, W, seg=24, sz=0.94)
    return it


def head():
    it = Item("C_head")
    it.ball(11, 0, 0, 0, W, seg=28)
    return it


def leg():
    it = Item("C_leg")
    it.lathe([(0, -8.5), (3.0, -8.5), (3.25, -7.2), (3.35, -4.5), (3.6, -1.6), (3.95, 0.2), (3.75, 2.2), (3.9, 4.6),
              (4.0, 7.0), (3.5, 8.3), (0, 8.7)], 0, 0, 0, W, seg=14)
    return it


def foot():
    it = Item("C_foot")
    it.box(11.4, 1.4, 8.2, 0, -1.3, 0, W, bev=0.6)
    it.box(9.0, 3.0, 7.2, -0.9, 0.4, 0, W, bev=1.4)
    it.ball(3.7, 3.5, -0.3, 0, W, sx=1.15, sy=0.72, sz=1.0, seg=14)
    for x in (-0.6, 1.4):
        it.box(1.0, 0.6, 4.2, x, 1.95, 0, W, bev=0.25)
    return it


def arm():
    it = Item("C_arm")
    it.lathe([(0, -8.2), (2.3, -8.0), (2.55, -6.2), (2.75, -2.6), (3.05, -0.6), (2.85, 1.2), (3.05, 4.0),
              (3.3, 6.4), (2.9, 7.8), (0, 8.3)], 0, 0, 0, W, seg=12)
    return it


def hand():
    it = Item("C_hand")
    it.ball(3.3, 0, -0.2, 0, W, sx=0.85, sy=1.1, sz=0.95, seg=14)
    it.ball(1.4, 2.0, 0.9, 0, W, sx=1.0, sy=1.5, sz=1.0, seg=10)
    return it


MAKERS = [body, head, leg, foot, arm, hand]


def build_character():
    coll = bpy.data.collections.get(COLL_CHR) or bpy.data.collections.new(COLL_CHR)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for ob in list(coll.objects):
        me = ob.data
        bpy.data.objects.remove(ob)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    # vitrine : le corps assemblé comme dans mkChar (tête y=46, torse y=27, hanches y=17, épaules y=35)
    place = {"C_body": (0, 27, 0), "C_head": (0, 46, 0), "C_leg": (0, 8.5, 5.5), "C_foot": (2, 2, 5.5),
             "C_arm": (0, 27, 12), "C_hand": (0, 18.5, 12)}
    stats = {}
    for mk in MAKERS:
        ob = mk().done(coll, (0, 0))
        x, y, z = place[ob.name]
        ob.location = (x + 2000, -z, y)
        stats[ob.name] = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return coll, stats


def export_character(coll):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in coll.objects:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=OUT_CHR, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_normals=True, export_texcoords=False, export_animations=False)
    bpy.ops.object.select_all(action="DESELECT")
    return os.path.getsize(OUT_CHR)
