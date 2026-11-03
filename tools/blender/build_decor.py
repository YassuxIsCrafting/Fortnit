"""Génère le décor de Fortnit (arbres, rochers, buissons, coffres, véhicules) et exporte models/decor.glb.

Lancer dans Blender :  exec(open(r"C:/Repos/Fortnit/tools/blender/build_decor.py", encoding="utf-8").read(), {"__name__": "decor"})

Mêmes conventions que build_items.py (unités et axes du jeu). Contraintes du moteur :
- arbres : feuillage en blanc pur (teinté par instance dans le jeu), tronc en couleur ; pied en y = 0 ;
- rochers et buissons : taille unité, blancs (couleur et échelle données par instance) ;
- couvercles de coffres : repère de la charnière, comme gChestL / gAmmoL ;
- voiture : carrosserie en magenta 0xff00ff, remplacé dans le jeu par chaque couleur de CARC.
"""
import bpy, math, os

exec(open(r"C:/Repos/Fortnit/tools/blender/build_items.py", encoding="utf-8").read(), globals())

OUT_DECOR = r"C:/Repos/Fortnit/models/decor.glb"
COLL_DECOR = "Fortnit_Decor"
LEAF, BARK, BODY = 0xffffff, 0x6b4423, 0xff00ff
GLASS, TYRE = 0x9fdcff, 0x1b1b1f


def pine():
    it = Item("T0")
    it.cyl(8, 6, 0, 3, 0, BARK, r2=5, seg=7, bev=0)
    it.cyl(5, 40, 0, 26, 0, BARK, axis="Y", r2=3.2, seg=7, bev=0)
    for (r, h, y) in ((34, 40, 52), (28, 38, 76), (21, 34, 98), (13, 28, 118)):
        it.cyl(r, h, 0, y, 0, LEAF, axis="Y", r2=0, seg=8, bev=0)
    return it


def oak():
    it = Item("T1")
    it.cyl(9, 50, 0, 25, 0, BARK, axis="Y", r2=6, seg=7, bev=0)
    it.cyl(3, 22, 9, 50, 0, BARK, axis="Y", r2=2, seg=5, bev=0, rz=-0.7)
    it.cyl(3, 22, -8, 54, 2, BARK, axis="Y", r2=2, seg=5, bev=0, rz=0.7)
    it.ico(34, 0, 80, 0, LEAF, sub=2, sy=0.85, jit=0.12, seed=1)
    it.ico(22, 21, 66, 4, LEAF, sub=1, jit=0.1, seed=2)
    it.ico(22, -21, 70, -4, LEAF, sub=1, jit=0.1, seed=3)
    it.ico(22, 3, 103, 0, LEAF, sub=1, jit=0.1, seed=4)
    return it


def palm():
    it = Item("T2")
    pts = [(0, 0), (1.5, 15), (3.5, 30), (5.5, 45), (7.5, 60), (9, 74), (10, 88)]
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        r = 4.6 - k * 0.3
        it.cyl(r + 0.4, math.hypot(x1 - x0, y1 - y0) + 1, (x0 + x1) / 2, (y0 + y1) / 2, 0,
               0x9a7b4f if k % 2 else 0x846640, axis="Y", r2=r, seg=6, bev=0, rz=-math.atan2(x1 - x0, y1 - y0))
    for k in range(6):
        it.horn((0, 0), (20, 10), (44, -16), 1.5, 0.15, LEAF, depth=4.0, seg=5, sides=4, at=(10, 88, 0), ry=k * math.pi / 3 + 0.3)
    for k in range(3):
        a = k * 2.1
        it.ico(3, 10 + math.cos(a) * 3.5, 84, math.sin(a) * 3.5, 0x5e3b1c, sub=1)
    return it


def birch():
    it = Item("T3")
    it.cyl(5, 70, 0, 35, 0, 0xe8e4d8, axis="Y", r2=3, seg=7, bev=0)
    for (y, a) in ((14, 0.4), (27, 2.6), (40, 4.4), (55, 1.2)):
        r = 5 - y / 70 * 2
        it.box(4, 1.6, 1.2, math.cos(a) * r, y, -math.sin(a) * r, 0x34302b, bev=0, ry=a + math.pi / 2)
    it.ico(28, 0, 84, 0, LEAF, sub=2, sy=1.1, jit=0.12, seed=5)
    it.ico(20, 10, 108, 3, LEAF, sub=1, jit=0.1, seed=6)
    it.ico(18, -11, 66, -2, LEAF, sub=1, jit=0.1, seed=7)
    return it


def rock():
    it = Item("D_rock")
    it.ico(1, 0, 0, 0, LEAF, sub=2, jit=0.2, seed=11, flat=0.45)
    return it


def bush():
    it = Item("D_bush")
    it.ico(1, 0, 0, 0, LEAF, sub=2, jit=0.14, seed=12, flat=0.6)
    return it


CHW, CHG, CHD = 0x8b5a2b, 0xffd23f, 0x5e3b1c


def chest_base():
    it = Item("D_chestB")
    it.box(32, 16, 22, 0, 8, 0, CHW, bev=0.8)
    for y in (5.4, 10.8):
        it.box(32.3, 0.5, 22.3, 0, y, 0, CHD, bev=0)
    for x in (-9, 9):
        it.box(3.4, 17, 23, x, 8.5, 0, CHG, bev=0.5)
    for x in (-15.2, 15.2):
        it.box(2.2, 16.6, 22.8, x, 8.3, 0, CHG, bev=0.5)
    return it


def chest_lid():
    it = Item("D_chestL")
    it.box(32, 8, 22, 0, 4, 11, CHW, bev=2.4)
    for x in (-9, 9):
        it.box(3.6, 9, 23, x, 4.5, 11, CHG, bev=1.2)
    it.box(5, 6, 2, 0, -1, 22.5, CHG, bev=0.6)
    it.box(1.2, 2.4, 0.6, 0, -1.6, 23.6, BLACK, bev=0.2)
    return it


def ammo_base():
    it = Item("D_ammoB")
    it.box(26, 12, 16, 0, 6, 0, 0x5d6b4e, bev=0.8)
    for x in (-8, 0, 8):
        it.box(1.2, 12.2, 16.4, x, 6, 0, 0x4d5a40, bev=0.2)
    it.box(27, 3, 17, 0, 10, 0, 0x3f4a35, bev=0.5)
    it.box(8, 5, 1, 0, 6, 8.5, 0xd9c27a, bev=0.3)
    for x in (-13.6, 13.6):
        it.box(1.2, 2, 6, x, 7, 0, GREY, bev=0.3)
    return it


def ammo_lid():
    it = Item("D_ammoL")
    it.box(26, 4, 16, 0, 2, 8, 0x6b7a5a, bev=0.8)
    it.box(3, 3.4, 1, 0, 0.8, 16.4, GREY, bev=0.3)
    return it


def wheel(it, x, y, z, r, w):
    it.cyl(r, w, x, y, z, TYRE, axis="Z", seg=16, bev=min(1.5, r * 0.2))
    it.cyl(r * 0.5, 0.6, x, y, z + (w / 2 + 0.2) * (1 if z > 0 else -1), GREY, axis="Z", seg=12, bev=0)


def car():
    it = Item("D_car")
    it.box(72, 14, 36, 0, 15, 0, BODY, bev=3)
    it.box(38, 14, 32, -6, 29, 0, BODY, bev=3)
    it.box(1.5, 12, 28.5, 12.6, 29, 0, GLASS, rz=0.35, bev=0.4)
    it.box(1.5, 11, 28, -24.6, 29, 0, GLASS, rz=-0.25, bev=0.4)
    for s in (1, -1):
        it.box(14, 9.5, 1, 3, 29.5, 16.1 * s, GLASS, bev=0.3)
        it.box(14, 9.5, 1, -14, 29.5, 16.1 * s, GLASS, bev=0.3)
        it.box(3, 2.2, 3, 13, 23, 18.2 * s, BODY, bev=0.5)
        it.cyl(2.6, 1, 36.3, 17, 11 * s, 0xfff6b0, seg=12, bev=0)
        it.box(1, 3, 7, -36.2, 17, 11 * s, 0xff3b3b, bev=0.3)
        for x in (22, -22):
            wheel(it, x, 7, 17.5 * s, 7, 6)
    it.box(0.6, 12.5, 36.4, -4, 15, 0, 0x55555f, bev=0)
    it.box(4, 6, 37, 36.5, 10, 0, 0x333333, bev=1)
    it.box(4, 6, 37, -36.5, 10, 0, 0x333333, bev=1)
    it.box(1, 5, 16, 37, 14.5, 0, 0x222228, bev=0.3)
    return it


def van():
    it = Item("D_van")
    it.box(96, 40, 50, 0, 26, 0, 0xe8eef5, bev=3)
    it.box(34, 28, 48, 40, 17, 0, 0xe8eef5, bev=3)
    it.box(1.5, 13, 40, 56.6, 25, 0, GLASS, rz=0.3, bev=0.4)
    it.box(97, 5, 50.6, 0, 12, 0, 0x2e7de0, bev=0.8)
    it.box(96.6, 3, 50.6, 0, 42, 0, 0x2e7de0, bev=0.8)
    it.box(2, 34, 50.4, -47.6, 25, 0, 0xcfd8e3, bev=0.5)
    for s in (1, -1):
        it.box(20, 12, 1, 42, 25, 24.2 * s, GLASS, bev=0.3)
        it.cyl(2.6, 1, 57.2, 14, 17 * s, 0xfff6b0, seg=12, bev=0)
        for x in (-30, 34):
            wheel(it, x, 8, 24 * s, 8, 7)
    it.box(4, 6, 50, 58, 6, 0, 0x333333, bev=1)
    it.cyl(2.5, 24, -20, 58, 0, 0x6b7280, axis="Y", seg=10)
    it.cyl(3, 5, -20, 72, 0, 0xcfd8e3, axis="Y", r2=14, seg=18, bev=0.3)
    it.ball(2, -20, 76, 0, 0x4aa8ff, seg=10)
    return it


def busbody():
    it = Item("D_bus")
    it.box(220, 70, 84, 0, 0, 0, 0x2e7de0, bev=6)
    it.box(222, 10, 86, 0, 28, 0, 0xffd23f, bev=2)
    it.box(222, 4, 86, 0, -24, 0, 0xffd23f, bev=1)
    for s in (1, -1):
        for x in (-70, -35, 0, 35, 70):
            it.box(26, 22, 1.5, x, 8, 42 * s, GLASS, bev=1)
        it.cyl(4.5, 2, 110.5, -16, 30 * s, 0xfff6b0, seg=14, bev=0)
        it.box(2, 6, 10, -110.5, -16, 30 * s, 0xff3b3b, bev=0.5)
        for x in (-70, 70):
            wheel(it, x, -36, 40 * s, 15, 10)
    it.box(2, 30, 72, 110.5, 10, 0, GLASS, bev=1)
    it.box(6, 8, 86, 112, -31, 0, 0x333333, bev=2)
    it.box(6, 8, 86, -112, -31, 0, 0x333333, bev=2)
    for z in (-36, 36):
        it.box(180, 2, 2, 0, 37, z, 0x9aa3ad, bev=0.5)
    return it


MAKERS = [pine, oak, palm, birch, rock, bush, chest_base, chest_lid, ammo_base, ammo_lid, car, van, busbody]


def build_decor():
    coll = bpy.data.collections.get(COLL_DECOR) or bpy.data.collections.new(COLL_DECOR)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for ob in list(coll.objects):
        me = ob.data
        bpy.data.objects.remove(ob)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    # vitrine : arbres, puis petits objets, puis véhicules ; les rochers/buissons (taille 1) sont agrandis pour la vue
    slots = [(0, 0), (90, 0), (180, 0), (270, 0), (360, 0), (420, 0), (0, -80), (0, -80), (70, -80), (70, -80),
             (160, -80), (300, -80), (180, -260)]
    stats = {}
    for mk, sl in zip(MAKERS, slots):
        ob = mk().done(coll, (sl[0] + 600, sl[1]))
        if ob.name in ("D_rock", "D_bush"):
            ob.scale = (20, 20, 20)
        stats[ob.name] = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return coll, stats


def export_decor(coll):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in coll.objects:
        ob.select_set(True)
    scales = {ob.name: tuple(ob.scale) for ob in coll.objects}
    for ob in coll.objects:
        ob.scale = (1, 1, 1)
    bpy.ops.export_scene.gltf(filepath=OUT_DECOR, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_normals=True, export_texcoords=False, export_animations=False)
    for ob in coll.objects:
        ob.scale = scales[ob.name]
    bpy.ops.object.select_all(action="DESELECT")
    return os.path.getsize(OUT_DECOR)
