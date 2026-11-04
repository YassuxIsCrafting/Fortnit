"""Génère les pièces des bâtiments d'Île Éclair et exporte models/buildings.glb.

Lancer dans Blender :  exec(open(r"C:/Repos/Fortnit/tools/blender/build_buildings.py", encoding="utf-8").read(), {"__name__": "bld"})

Les bâtiments du jeu sont assemblés à partir de pièces instanciées ; on refait les pièces, pas l'assemblage :
- B_wall : bloc de mur 60³ centré (murs des maisons et constructions du joueur), blanc, teinté par instance ;
- B_winF : cadre, appui et volets autour de la vitre (plan 32×30 en z = 0, tourné vers +Z) ;
- B_door : porte ouverte et son encadrement (mêmes cotes que gDoor) ;
- R_gable / R_pyr : toits à l'échelle du monde (258 × 46 × 258). Le jeu les ramène à l'unité ;
  le blanc pur est teinté par la couleur du toit, les autres couleurs (faîtage, cheminée, pignons) restent telles quelles.
"""
import bpy, math, os

exec(open(r"C:/Repos/Fortnit/tools/blender/build_items.py", encoding="utf-8").read(), globals())

OUT_BLD = r"C:/Repos/Fortnit/models/buildings.glb"
COLL_BLD = "IleEclair_Buildings"
TINT, TRIM, FRAME = 0xffffff, 0x5a3a24, 0xf5f5f5
RW, RH = 129, 46  # demi-largeur et hauteur des toits


def wall():
    it = Item("B_wall")
    it.box(60, 60, 60, 0, 0, 0, TINT, bev=2.2, seg=1)
    return it


def window_frame():
    it = Item("B_winF")
    for y in (16.6, -16.6):
        it.box(38.6, 3.6, 3, 0, y, 0.9, FRAME, bev=0.6, seg=1)
    for x in (17.5, -17.5):
        it.box(3.6, 36.8, 3, x, 0, 0.9, FRAME, bev=0.6, seg=1)
    it.box(43, 2.6, 6.5, 0, -19.4, 2.6, FRAME, bev=0.6, seg=1)
    it.box(40, 1.4, 4, 0, -21.2, 1.4, 0xd6d0c4, bev=0.3, seg=1)
    for s in (1, -1):
        it.box(11, 33, 1.2, 25.6 * s, 0, 0.1, TRIM, bev=0.4, seg=1)
        for y in range(-12, 13, 6):
            it.box(10, 1.2, 1.6, 25.6 * s, y, 0.6, 0x7a512b, bev=0)
        it.box(1.2, 2.6, 1.6, 20.4 * s, 8 * (1 if s > 0 else -1), 0.9, BLACK, bev=0)
    return it


def door():
    it = Item("B_door")
    for x in (27, -27):
        it.box(6.4, 58, 6.4, x, 29, 0, TRIM, bev=0.8, seg=1)
        it.box(8.4, 3, 8, x, 1.5, 0, 0x4a2f1c, bev=0.6, seg=1)
    it.box(66, 7, 7.4, 0, 57.5, 0, TRIM, bev=1.0, seg=1)
    it.box(8, 9.5, 8.4, 0, 58, 0, 0x7a512b, bev=0.8, seg=1)
    it.box(3, 52, 24, 24, 26, 14, 0x8b5a2b, bev=0.6, seg=1)
    for y in (13, 38):
        it.box(3.8, 18, 16, 24, y, 14, 0x7a4e26, bev=0.8, seg=1)
    for y in (8, 44):
        it.box(4, 2.4, 3, 24, y, 2.6, BLACK, bev=0.3, seg=1)
    for x in (21.8, 26.2):
        it.ball(1.6, x, 25, 22, 0xffd23f, seg=10)
    it.box(56, 1.6, 4, 0, 0.8, 0, 0x4a2f1c, bev=0.4, seg=1)
    return it


def gable():
    it = Item("R_gable")
    a = math.atan2(RH, RW)
    L = math.hypot(RW, RH)
    for s in (1, -1):
        it.box(L + 6, 4, 264, s * RW / 2, RH / 2 + 1.5, 0, TINT, rz=-a * s, bev=1.0, seg=1)
        for k in range(5):
            t = (k + 0.5) / 5
            it.box(L / 5.4, 1.8, 266, s * RW * (1 - t), RH * t + 3.9, 0, TINT, rz=-a * s, bev=0.6, seg=1)
        it.box(4, 3.4, 266, s * (RW + 2.5), -0.6, 0, TRIM, bev=0.8, seg=1)
    it.cyl(3.6, 268, 0, RH + 2.4, 0, 0x4a4f57, axis="Z", seg=8, bev=0.6)
    for z in (127.5, -127.5):
        it.prism([(-RW + 4, 0), (RW - 4, 0), (0, RH - 2)], 3, 0, 0, z, 0x8b5a2b)
        it.cyl(6, 1.2, 0, 16, z * 1.013, 0x34302b, axis="Z", seg=12, bev=0)
        it.cyl(7.2, 1.0, 0, 16, z * 1.008, FRAME, axis="Z", seg=12, bev=0)
    it.box(16, 36, 16, 55, 30, 60, 0xb5654a, bev=1.0, seg=1)
    it.box(20, 3, 20, 55, 49, 60, 0x4a4f57, bev=0.8, seg=1)
    return it


def pyramid():
    it = Item("R_pyr")
    R = (RW + 4) * math.sqrt(2)
    for k in range(5):
        y0 = k * 8.6
        rb, rt = R * (1 - y0 / RH), R * (1 - (y0 + 10) / RH)
        it.cyl(rb, 10, 0, y0 + 5, 0, TINT, axis="Y", r2=rt, seg=4, bev=0, ry=math.pi / 4)
    it.cyl(R * (1 - 43 / RH) + 2, 6, 0, 45, 0, 0x4a4f57, axis="Y", r2=1.5, seg=4, bev=0, ry=math.pi / 4)
    it.cyl(1.2, 8, 0, 51, 0, 0x4a4f57, axis="Y", seg=8, bev=0)
    it.ball(3, 0, 56, 0, 0xffd23f, seg=12)
    it.cyl(R + 3, 3, 0, -0.2, 0, TRIM, axis="Y", r2=R + 1.6, seg=4, bev=0, ry=math.pi / 4)
    return it


MAKERS = [wall, window_frame, door, gable, pyramid]


def build_buildings():
    coll = bpy.data.collections.get(COLL_BLD) or bpy.data.collections.new(COLL_BLD)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for ob in list(coll.objects):
        me = ob.data
        bpy.data.objects.remove(ob)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    slots = [(0, 0), (90, 0), (180, 0), (0, 120), (300, 120)]
    stats = {}
    for mk, sl in zip(MAKERS, slots):
        ob = mk().done(coll, (sl[0] + 1400, sl[1]))
        stats[ob.name] = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return coll, stats


def export_buildings(coll):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in coll.objects:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=OUT_BLD, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_normals=True, export_texcoords=False, export_animations=False)
    bpy.ops.object.select_all(action="DESELECT")
    return os.path.getsize(OUT_BLD)
