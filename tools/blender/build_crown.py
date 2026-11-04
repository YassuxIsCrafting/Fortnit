"""Génère la couronne des gagnants d'Île Éclair et exporte models/crown.glb.

blender -b --factory-startup -P tools/blender/build_crown.py

Même encombrement que l'ancienne couronne d'addCrown (rayon ~10-11, posée à y = 56 sur la tête) :
origine au centre du bandeau, bas du bandeau en y = -5. Couleurs cuites en couleurs de sommets par le jeu.
"""
import bpy, math, os

exec(open(r"C:/Repos/Fortnit/tools/blender/build_items.py", encoding="utf-8").read(), globals())

OUT_CROWN = r"C:/Repos/Fortnit/models/crown.glb"
GOLD, GOLD_D, GOLD_L, VELVET = 0xffc83d, 0xd99a1e, 0xffe680, 0xa8161b
GEMS = [0xd62828, 0x2e6fd6, 0x2fbf5a, 0x2e6fd6]


def crown():
    it = Item("CROWN")
    # bandeau creux (paroi extérieure bombée, paroi intérieure droite)
    it.lathe([(9.0, -5), (9.8, -5), (10.4, -4.4), (10.5, -1.9), (10.4, 0.6), (9.8, 1.2), (9.0, 1.2), (9.0, -5)],
             0, 0, 0, GOLD, seg=32)
    it.ring(10.35, 0.55, 0, -4.5, 0, GOLD_D, axis="Y", seg=32, tube=8)
    it.ring(10.05, 0.5, 0, 1.0, 0, GOLD_D, axis="Y", seg=32, tube=8)
    it.ball(8.9, 0, -0.6, 0, VELVET, sy=0.55, seg=20)  # velours à l'intérieur
    for i in range(8):
        a = i * math.pi / 4
        c, s = math.cos(a), math.sin(a)
        # grande pointe surmontée d'une perle
        it.cyl(1.9, 6.2, c * 9.6, 4.2, s * 9.6, GOLD, axis="Y", r2=0.45, seg=10, bev=0)
        it.ball(1.15, c * 9.5, 7.7, s * 9.5, GOLD_L, seg=12)
        # petite fleur entre deux pointes
        a2 = a + math.pi / 8
        it.cyl(1.3, 3.2, math.cos(a2) * 9.7, 2.7, math.sin(a2) * 9.7, GOLD_D, axis="Y", r2=0.3, seg=8, bev=0)
        # pierre sur le bandeau
        it.ball(1.35, c * 10.55, -1.9, s * 10.55, GEMS[i % 4], sx=1 - 0.55 * abs(c), sz=1 - 0.55 * abs(s), sy=1.25, seg=12)
    return it


bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.data.collections.new("IleEclair_Crown")
bpy.context.scene.collection.children.link(coll)
it = crown()
ob = it.done(coll, (0, 0))
ob.location = (0, 0, 0)
tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT_CROWN, export_format="GLB", use_selection=True, export_apply=True,
                          export_yup=True, export_normals=True, export_texcoords=False, export_animations=False)
print("RESULT", {"tris": tris, "bytes": os.path.getsize(OUT_CROWN)})
