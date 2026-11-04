"""Génère les objets 3D de la boutique d'Île Éclair (chapeaux, planeur, parapluies) et exporte models/shop.glb.

blender -b --factory-startup -P tools/blender/build_shop.py

Repère du corps en blocs (tête : centre y = 46, rayon 11, face avant +X) ; le jeu réduit les chapeaux sur le perso réaliste.
- HATn_t : parties à la couleur de la tenue (la couleur du maillage est ignorée), HATn_f : parties à couleur fixe ;
  la couronne de la boutique reprend crown.glb ;
- G_glider : aile delta du planeur par défaut (remplace gGlider) ;
- U_canopy : toile des parapluies, avec UV (u = tour, v = 1 en haut) pour garder les motifs dessinés par le jeu,
  origine au bord de la toile (y = 96 dans mkUmb) ; U_ribs : baleines et embouts (enfant de la toile, tourne avec elle) ;
  U_handle : poignée en J, posée sur la main le long du manche (axe +Y).
"""
import bpy, bmesh, math, os
from mathutils import Vector

exec(open(r"C:/Repos/Fortnit/tools/blender/build_items.py", encoding="utf-8").read(), globals())

OUT_SHOP = r"C:/Repos/Fortnit/models/shop.glb"
W = 0xffffff
RIM, TOPY, RCAN = 0.0, 31.0, 50.0  # toile : bord en y = 0, sommet en y = 31, rayon 50


def cap():
    t, f = Item("HAT1_t"), Item("HAT1_f")
    t.ball(11.9, 0, 49.5, 0, W, sy=0.78, seg=24)
    t.ball(8.6, 11.2, 51.0, 0, W, sx=1.0, sy=0.12, sz=1.12, seg=20)  # visière
    f.ring(11.75, 0.45, 0, 50.0, 0, 0x1b1b22, axis="Y", seg=28)
    f.ball(1.2, 0, 58.7, 0, 0x1b1b22, seg=10)
    for a in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
        f.ball(0.55, math.cos(a) * 8.6, 55.6, math.sin(a) * 8.6, 0x1b1b22, seg=8)
    return t, f


def helmet():
    f = Item("HAT3_f")
    f.ball(12.8, 0, 47.5, 0, 0x7d8a6a, sy=0.86, seg=24)
    f.lathe([(12.4, 47.4), (14.8, 46.9), (15.2, 46.2), (12.6, 46.4)], 0, 0, 0, 0x6b775a, seg=28)
    f.ring(12.9, 0.7, 0, 48.6, 0, 0x4b5320, axis="Y", seg=28)
    f.box(2.2, 2.6, 0.8, 12.4, 52.0, 0, 0xffd23f, bev=0.3)
    for s in (1, -1):
        f.box(1.2, 9.0, 1.4, 0, 42.5, 11.6 * s, 0x2b2b2b, bev=0.3)
    return f


def antenna():
    f = Item("HAT4_f")
    f.ring(11.4, 1.0, 0, 52.0, 0, 0x2a2a33, axis="Y", seg=28)
    f.ring(11.4, 1.0, 0, 50.0, 0, 0x2a2a33, axis="X", seg=28, arc=math.pi, a0=0)
    f.cyl(1.6, 2.0, 0, 57.4, 0, 0x9aa3ad, axis="Y", seg=12)
    for k in range(5):
        f.ring(1.3, 0.35, 0, 59.4 + k * 1.6, 0, 0xc9d3e0, axis="Y", seg=12, tube=6)
    f.cyl(0.55, 6, 0, 65.5, 0, 0x9aa3ad, axis="Y", seg=8)
    f.ball(3.4, 0, 71.0, 0, 0xff4d4d, seg=16)
    f.ball(1.2, 1.4, 72.2, 1.2, 0xffb3b3, seg=10)
    return f


def glider_mesh():
    """Aile delta : nez (25,102,0), saumons (-15,98.5,±46), fuite au centre (-11,103,0)."""
    import bmesh as _b
    g = Item("G_glider")
    for s in (1, -1):
        bm = _b.new()
        P = [Vector(p) for p in ((25, 102, 0), (-15, 98.5, 46 * s), (-11, 103, 0))]
        top = [bm.verts.new((p.x, -p.z, p.y + 0.6)) for p in P]
        bot = [bm.verts.new((p.x, -p.z, p.y - 0.6)) for p in P]
        bm.faces.new(top)
        bm.faces.new(bot[::-1])
        for i in range(3):
            j = (i + 1) % 3
            bm.faces.new((top[i], bot[i], bot[j], top[j]))
        _b.ops.recalc_face_normals(bm, faces=bm.faces)
        g._add(bm, 0xff5d8f, 0, 0, 0)
        bm = _b.new()  # bande jaune près du bord d'attaque
        Q = [Vector(p) for p in ((22, 102.2, 0), (-11, 98.9, 40 * s), (-13.5, 98.8, 43.5 * s), (16, 102.3, 0))]
        q = [bm.verts.new((p.x, -p.z, p.y + 0.75)) for p in Q]
        qb = [bm.verts.new((p.x, -p.z, p.y + 0.55)) for p in Q]
        bm.faces.new(q)
        bm.faces.new(qb[::-1])
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((q[i], qb[i], qb[j], q[j]))
        _b.ops.recalc_face_normals(bm, faces=bm.faces)
        g._add(bm, 0xffd23f, 0, 0, 0)
    g.cyl(0.8, 40, 5, 101.6, 0, 0x2a2a33, seg=8)  # quille
    g.cyl(0.9, 3, 26.2, 101.8, 0, 0xffd23f, seg=8)
    for s in (1, -1):  # trapèze : montants et barre de contrôle
        a, b = Vector((5, 100.5, 0)), Vector((3, 74, 16 * s))
        d = (a - b).normalized()  # axe Y du cylindre -> d : Rx puis Rz (ordre de Item._add)
        rx = math.asin(d.z)
        rz = -math.asin(max(-1, min(1, d.x / max(1e-6, math.cos(rx)))))
        g.cyl(0.6, (a - b).length, (a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2, 0x333333, axis="Y", seg=8, bev=0, rz=rz, rx=rx)
    g.cyl(0.65, 32, 3, 74, 0, 0x333333, axis="Z", seg=8, bev=0)
    return g


def canopy_mesh():
    """Toile festonnée à 8 panneaux, avec UV pour les motifs du jeu."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    N, T = 64, 12
    rows = []
    for it in range(T + 1):
        t = it / T
        row = []
        for ip in range(N + 1):
            phi = 2 * math.pi * ip / N
            sp = (phi % (math.pi / 4)) / (math.pi / 4)
            m = math.sin(math.pi * sp)
            r = RCAN * math.sin(t * math.pi / 2) * (1 - 0.07 * m * t)
            y = TOPY * math.cos(t * math.pi / 2) + 4.5 * m * t * t
            x, z = -math.cos(phi) * r, math.sin(phi) * r
            row.append((bm.verts.new((x, -z, y)), (ip / N, 1 - t)))
        rows.append(row)
    for a, b in zip(rows, rows[1:]):
        for i in range(N):
            f = bm.faces.new((a[i][0], b[i][0], b[i + 1][0], a[i + 1][0]))
            for loop, (_, u) in zip(f.loops, (a[i], b[i], b[i + 1], a[i + 1])):
                loop[uv].uv = u
    bmesh.ops.remove_doubles(bm, verts=[r[0] for r in rows[0]], dist=1e-4)  # sommet
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:  # normales vers l'extérieur de la toile
        if f.normal.dot(f.calc_center_median() - Vector((0, 0, -20))) < 0:
            f.normal_flip()
    me = bpy.data.meshes.new("U_canopy")
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    me.materials.append(material(0xffffff))
    return me


def ribs():
    r = Item("U_ribs")
    for k in range(8):
        a = k * math.pi / 4
        r.horn((0, TOPY + 0.4), (RCAN * 0.78, TOPY + 0.6), (RCAN + 0.4, RIM + 0.2), 0.45, 0.4, 0x2a2a33, depth=1, seg=10, sides=5,
               at=(0, 0, 0), ry=a)
        r.ball(0.95, math.cos(a) * (RCAN + 0.6), RIM - 0.1, -math.sin(a) * (RCAN + 0.6), 0xffd23f, seg=8)
    r.cyl(1.8, 3.2, 0, TOPY + 1.0, 0, 0x2a2a33, axis="Y", seg=12)
    return r


def handle():
    h = Item("U_handle")
    h.cyl(1.55, 8, 0, 3.5, 0, 0x7a512b, axis="Y", seg=12)
    h.ring(3.2, 1.15, 3.2, -0.6, 0, 0x7a512b, arc=math.pi, a0=math.pi, axis="Z", seg=16, tube=8)
    h.ball(1.2, 6.4, -0.6, 0, 0x5e3b1c, seg=10)
    return h


bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.data.collections.new("Shop")
bpy.context.scene.collection.children.link(coll)
obs, stats = [], {}
t, f = cap()
for it in (t, f, helmet(), antenna(), glider_mesh(), ribs(), handle()):
    ob = it.done(coll, (0, 0))
    ob.location = (0, 0, 0)
    obs.append(ob)
me = canopy_mesh()
can = bpy.data.objects.new("U_canopy", me)
coll.objects.link(can)
obs.append(can)
for ob in obs:
    stats[ob.name] = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT_SHOP, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                          export_normals=True, export_texcoords=True, export_animations=False)
print("RESULT", {"tris": stats, "bytes": os.path.getsize(OUT_SHOP)})
