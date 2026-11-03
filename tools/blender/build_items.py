"""Génère les armes et le butin de Fortnit dans Blender, puis exporte models/items.glb.

Lancer dans Blender :  exec(open(r"C:/Repos/Fortnit/tools/blender/build_items.py").read())

Les cotes sont données en unités du jeu (repère three.js : X = longueur, Y = haut, Z = épaisseur)
et converties vers Blender (Z haut). Chaque objet a la même origine que l'ancien modèle procédural
de index.html (poignée en 0 pour les armes, centre pour le butin) : la main et le butin restent calés.
"""
import bpy, bmesh, math, os
from mathutils import Matrix, Vector

OUT = r"C:/Repos/Fortnit/models/items.glb"
COLL = "Fortnit_Items"

DARK, DARK2, STEEL, GREY, BLACK = 0x2a2a33, 0x3a3d47, 0x4a4f5a, 0x9aa3ad, 0x16161c
WOOD, WOOD_L, WOOD_D, LENS, GOLD = 0x7a512b, 0x9c6b3c, 0x5e3b1c, 0x66ccff, 0xd9a441
WCOL = [0xb9c0c8, 0x5fd35f, 0x4aa8ff, 0xc27bff, 0x6fa8dc]


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def material(hexc):
    name = "C_%06x" % hexc
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    rgb = [lin((hexc >> s) & 255) for s in (16, 8, 0)]
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None) or nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 0.55
    return m


G2B = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # jeu (Y haut) -> Blender (Z haut)


class Item:
    """Un objet = un seul mesh, une couleur par slot de matériau."""

    def __init__(self, name):
        self.name, self.bm, self.mats = name, bmesh.new(), []

    def _add(self, bm, col, x, y, z, rz=0.0, rx=0.0, ry=0.0):
        if col not in self.mats:
            self.mats.append(col)
        mi = self.mats.index(col)
        # rotations exprimées dans le repère du jeu, autour de l'origine de la pièce
        rot = Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(rx, 4, "X")
        bmesh.ops.transform(bm, matrix=G2B @ Matrix.Translation((x, y, z)) @ rot @ G2B.inverted(), verts=bm.verts)
        for f in bm.faces:
            f.material_index = mi
        me = bpy.data.meshes.new("tmp")
        bm.to_mesh(me)
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        bm.free()

    # --- primitives (cotes jeu : w = X, h = Y, d = Z) ---
    def box(self, w, h, d, x, y, z, col, rz=0.0, bev=0.45, **k):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
        b = min(bev, min(w, h, d) * 0.3)
        if b > 0.01:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=b, segments=2, affect="EDGES", profile=0.5, clamp_overlap=True)
        self._add(bm, col, x, y, z, rz, **k)

    def cyl(self, r, l, x, y, z, col, axis="X", r2=None, seg=16, rz=0.0, bev=0.2, **k):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=l)
        b = min(bev, l * 0.25, r * 0.3)
        if b > 0.01:
            caps = [e for e in bm.edges if not e.is_wire and all(abs(abs(v.co.z) - l / 2) < 1e-4 for v in e.verts)]
            bmesh.ops.bevel(bm, geom=caps, offset=b, segments=2, affect="EDGES", profile=0.5, clamp_overlap=True)
        # cône Blender le long de Z -> axe du jeu demandé
        m = {"X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Identity(4), "Z": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
        self._add(bm, col, x, y, z, rz, **k)

    def ball(self, r, x, y, z, col, sx=1, sy=1, sz=1, seg=16):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2 + 2, radius=r)
        bmesh.ops.scale(bm, vec=(sx, sz, sy), verts=bm.verts)
        self._add(bm, col, x, y, z)

    def ring(self, R, r, x, y, z, col, arc=2 * math.pi, a0=0.0, axis="Z", seg=20, tube=8):
        """Tore (ou arc de tore) dans le plan perpendiculaire à l'axe du jeu donné."""
        bm = bmesh.new()
        full = arc >= 2 * math.pi - 1e-6
        n = seg if full else seg + 1
        rings = []
        for i in range(n):
            a = a0 + arc * i / seg
            c, s = math.cos(a), math.sin(a)
            rings.append([bm.verts.new(((R + r * math.cos(b)) * c, (R + r * math.cos(b)) * s, r * math.sin(b)))
                          for b in (2 * math.pi * j / tube for j in range(tube))])
        for i in range(seg if full else seg):
            A, B = rings[i], rings[(i + 1) % n]
            for j in range(tube):
                bm.faces.new((A[j], B[j], B[(j + 1) % tube], A[(j + 1) % tube]))
        if not full:
            for rr in (rings[0], rings[-1]):
                bm.faces.new(rr)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # tore construit autour de l'axe Z Blender (= Y du jeu)
        m = {"Z": Matrix.Rotation(math.pi / 2, 4, "X"), "Y": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y")}[axis]
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
        self._add(bm, col, x, y, z)

    def horn(self, p0, p1, p2, r0, r1, col, depth=1.0, seg=10, sides=8, t0=0.0, t1=1.0):
        """Pointe courbe (Bézier quadratique dans le plan XY du jeu), section qui s'affine."""
        bm = bmesh.new()
        P = [Vector((p[0], p[1], 0)) for p in (p0, p1, p2)]
        pt = lambda t: (1 - t) ** 2 * P[0] + 2 * (1 - t) * t * P[1] + t * t * P[2]
        tg = lambda t: (2 * (1 - t) * (P[1] - P[0]) + 2 * t * (P[2] - P[1])).normalized()
        rings = []
        for i in range(seg + 1):
            t = t0 + (t1 - t0) * i / seg
            c, d, r = pt(t), tg(t), r0 + (r1 - r0) * t
            nrm = Vector((-d.y, d.x, 0))
            rings.append([bm.verts.new(c + nrm * (r * math.cos(a)) + Vector((0, 0, r * depth * math.sin(a))))
                          for a in (2 * math.pi * j / sides for j in range(sides))])
        for A, B in zip(rings, rings[1:]):
            for j in range(sides):
                bm.faces.new((A[j], B[j], B[(j + 1) % sides], A[(j + 1) % sides]))
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.transform(bm, matrix=G2B, verts=bm.verts)
        self._add(bm, col, 0, 0, 0)

    def done(self, coll, slot):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-4)
        self.bm.to_mesh(me)
        self.bm.free()
        for c in self.mats:
            me.materials.append(material(c))
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(38))
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        ob.location = (slot[0], 0, slot[1])  # vitrine dans Blender ; le jeu recentre chaque objet
        return ob


def trig(it, x, y, rz=0.2):
    it.ring(2.6, 0.5, x, y - 0.4, 0, DARK2, arc=math.pi, a0=math.pi)
    it.box(0.8, 2.4, 1.0, x - 0.3, y + 0.6, 0, BLACK, rz=rz, bev=0.2)


def pistol(ac):
    it = Item("W0")
    it.box(19, 4.4, 4.2, 10.5, 3.3, 0, DARK, bev=0.6)
    for i in range(5):
        it.box(0.45, 3.0, 4.4, 2.2 + i * 1.0, 3.6, 0, BLACK, bev=0.1)
    it.box(15, 2.2, 4.0, 9.5, 0.4, 0, DARK2)
    it.box(12, 0.9, 4.5, 12, 5.4, 0, ac, bev=0.3)
    it.cyl(1.5, 2.0, 20.6, 3.2, 0, GREY)
    it.cyl(0.8, 0.4, 21.7, 3.2, 0, BLACK, bev=0)
    it.box(1.0, 1.1, 1.0, 19.2, 5.9, 0, BLACK, bev=0.2)
    it.box(1.4, 1.2, 3.0, 2.4, 5.9, 0, BLACK, bev=0.2)
    it.box(1.2, 1.6, 1.6, 0.5, 5.0, 0, GREY, rz=0.4, bev=0.3)
    it.box(5.0, 10.5, 4.0, 3.0, -3.8, 0, DARK2, rz=-0.25, bev=1.0)
    it.box(3.4, 7.0, 4.4, 3.2, -4.0, 0, STEEL, rz=-0.25, bev=0.6)
    it.box(4.8, 1.0, 4.2, 1.6, -9.0, 0, ac, rz=-0.25, bev=0.3)
    trig(it, 8.2, -0.8)
    return it


def rifle(ac):
    it = Item("W1")
    it.box(22, 6, 5, 8, 2, 0, DARK, bev=0.6)
    it.box(20, 1.2, 3, 10, 5.6, 0, DARK2, bev=0.3)
    for i in range(9):
        it.box(0.8, 0.8, 3.3, 1.5 + i * 2.2, 6.4, 0, BLACK, bev=0.15)
    it.box(14, 5.5, 5.8, 25, 2.5, 0, ac, bev=0.9)
    for x in (21, 25, 29):
        it.box(2.2, 1.6, 6.0, x, 2.6, 0, DARK, bev=0.4)
    it.cyl(1.4, 12, 37, 3.5, 0, STEEL)
    it.cyl(2.0, 4.5, 43.5, 3.5, 0, DARK, bev=0.4)
    for x in (42.8, 44.2):
        it.box(0.6, 1.0, 4.3, x, 3.5, 0, BLACK, bev=0)
    it.cyl(0.9, 0.3, 45.8, 3.5, 0, BLACK, bev=0)
    it.box(1.0, 3.0, 1.0, 31, 6.4, 0, DARK, bev=0.2)
    it.box(5.5, 3.2, 3.2, 12, 8.2, 0, DARK, bev=0.6)
    it.cyl(1.1, 0.3, 14.85, 8.4, 0, LENS, bev=0)
    it.cyl(1.1, 0.3, 9.15, 8.4, 0, 0xff4d4d, bev=0)
    for (x, y, r) in ((12, -3.5, 0.1), (12.9, -7.5, 0.25), (14.2, -11.2, 0.4)):
        it.box(5.0, 4.6, 4.0, x, y, 0, DARK2, rz=r, bev=0.5)
    it.box(5.4, 1.2, 4.4, 15.2, -13.4, 0, ac, rz=0.4, bev=0.3)
    it.box(4, 8, 4, 0, -5, 0, DARK, rz=-0.2, bev=0.8)
    trig(it, 4.6, -0.9)
    it.box(13, 4.5, 4, -8, 1.3, 0, DARK, rz=0.05, bev=0.7)
    it.box(8, 1.0, 4.2, -8, 3.5, 0, ac, rz=0.05, bev=0.3)
    it.box(2.5, 7.0, 4.4, -15, 0.6, 0, BLACK, bev=0.6)
    it.box(2.0, 1.0, 6.0, 2, 4.5, 0, GREY, bev=0.3)
    return it


def shotgun(ac):
    it = Item("W2")
    it.cyl(2.0, 34, 22, 3.5, 0, DARK2)
    it.cyl(1.6, 26, 18, 0.4, 0, DARK)
    it.cyl(2.4, 1.5, 39, 3.5, 0, GREY)
    it.cyl(1.2, 0.3, 39.8, 3.5, 0, BLACK, bev=0)
    it.box(24, 0.6, 1.2, 25, 5.7, 0, GREY, bev=0.2)
    it.ball(0.65, 38.4, 6.1, 0, GOLD, seg=10)
    it.cyl(2.8, 13, 18, -0.6, 0, WOOD, seg=18, bev=0.6)
    for x in (13.5, 16.5, 19.5, 22.5):
        it.cyl(2.95, 0.6, x, -0.6, 0, WOOD_D, seg=18, bev=0)
    it.box(14, 6.5, 5, 4, 1.6, 0, DARK, bev=0.7)
    it.box(10, 3.0, 5.3, 4, 1.8, 0, ac, bev=0.4)
    it.box(16, 5.5, 4.4, -11.5, 0.6, 0, WOOD, rz=0.12, bev=0.9)
    it.box(2.0, 7.5, 4.6, -19.5, -0.4, 0, BLACK, rz=0.12, bev=0.5)
    it.box(8.5, 4.0, 0.6, -11, 1.0, 2.4, DARK, rz=0.12, bev=0.2)
    for x in (-13.5, -11, -8.5):
        it.cyl(0.9, 3.2, x, 1.0 + (x + 11) * 0.12, 2.9, 0xe0392b, axis="Y", seg=10)
        it.cyl(0.95, 0.8, x, -0.4 + (x + 11) * 0.12, 2.9, GOLD, axis="Y", seg=10, bev=0.1)
    it.box(4, 8, 4.2, -1, -5, 0, DARK, rz=-0.2, bev=0.8)
    trig(it, 3.4, -1.2)
    return it


def sniper(ac):
    it = Item("W3")
    it.cyl(1.3, 36, 35, 3.5, 0, DARK)
    it.cyl(1.8, 8, 21, 3.5, 0, STEEL)
    it.cyl(2.3, 6, 56, 3.5, 0, DARK, bev=0.4)
    for x in (55, 57):
        it.box(0.7, 1.2, 4.8, x, 3.5, 0, BLACK, bev=0)
    for z in (-1.3, 1.3):
        it.cyl(0.5, 12, 31, 1.4, z, GREY, seg=8)
    it.box(22, 5, 4.6, 6, 2, 0, DARK, bev=0.6)
    it.box(12, 1.2, 4.8, 8, 4.8, 0, ac, bev=0.3)
    it.box(5, 4, 3.8, 8, -2.2, 0, DARK2, bev=0.5)
    it.cyl(2.0, 14, 10, 9.2, 0, BLACK, seg=18)
    it.cyl(2.0, 3.2, 18.6, 9.2, 0, BLACK, r2=2.9, seg=18)
    it.cyl(2.0, 2.6, 1.6, 9.2, 0, BLACK, r2=2.6, seg=18, ry=math.pi)
    it.cyl(2.65, 0.3, 20.3, 9.2, 0, LENS, seg=18, bev=0)
    it.cyl(2.35, 0.3, 0.2, 9.2, 0, LENS, seg=18, bev=0)
    it.cyl(1.1, 2.2, 10, 11.6, 0, ac, axis="Y", seg=12)
    it.cyl(1.0, 1.8, 10, 9.2, 2.6, ac, axis="Z", seg=12)
    for x in (5, 14):
        it.box(2, 4, 2.6, x, 6.5, 0, GREY, bev=0.4)
    it.cyl(0.5, 3.6, 1, 4.0, 3.0, GREY, axis="Z", seg=8)
    it.ball(1.0, 1, 4.0, 4.9, DARK, seg=10)
    it.box(18, 6, 4, -12, 0, 0, WOOD, rz=0.1, bev=0.9)
    it.box(10, 1.6, 4.2, -11, 3.5, 0, WOOD_L, rz=0.1, bev=0.6)
    it.box(2, 7.5, 4.4, -21, -0.9, 0, BLACK, rz=0.1, bev=0.5)
    it.box(4, 8, 4.4, 0, -5, 0, DARK, rz=-0.2, bev=0.8)
    trig(it, 4.4, -1.0)
    return it


def pickaxe(ac):
    it = Item("W4")
    a = 0.25
    on = lambda t: (8 + t * math.cos(a), 4 + t * math.sin(a))
    it.cyl(1.7, 30, 8, 4, 0, WOOD, rz=a, seg=12)
    x, y = on(-9)
    it.cyl(1.9, 8, x, y, 0, WOOD_D, rz=a, seg=12, bev=0.3)
    for t in (-13, -9, -5):
        x, y = on(t)
        it.cyl(2.05, 1.2, x, y, 0, DARK, rz=a, seg=12, bev=0.2)
    x, y = on(-15.6)
    it.ball(2.4, x, y, 0, ac, seg=12)
    x, y = on(15.4)
    it.cyl(1.5, 2, x, y, 0, GREY, rz=a, seg=12)
    it.box(6, 7, 5, 22, 9, 0, STEEL, rz=-0.15, bev=0.9)
    it.cyl(1.0, 5.8, 22, 9, 0, GREY, axis="Z", seg=10)
    up, lo = ((22.3, 11.5), (24.6, 18), (21.4, 23.5)), ((21.8, 6.5), (24.2, 1.0), (20.4, -4.0))
    for p in (up, lo):
        it.horn(*p, 2.6, 0.25, ac, depth=0.75, t1=0.78)
        it.horn(*p, 2.6, 0.25, GREY, depth=0.75, t0=0.76)
    return it


def mini():
    it = Item("L_mini")
    it.ball(6.5, 0, -1.5, 0, 0x4aa8ff, seg=20)
    it.ball(1.4, 2.6, 1.4, 4.6, 0xdff3ff, sx=0.8, sy=1.4, sz=0.6, seg=10)
    it.ring(6.25, 0.6, 0, -1.2, 0, 0xf5f5f5, axis="Y", seg=24)
    it.cyl(2.2, 3.6, 0, 5.6, 0, 0x9fd4ff, axis="Y", seg=14)
    it.cyl(2.7, 1.0, 0, 7.2, 0, 0x9fd4ff, axis="Y", seg=14)
    it.cyl(1.9, 2.4, 0, 8.6, 0, 0xb0773a, axis="Y", r2=2.1, seg=12)
    return it


def big():
    it = Item("L_big")
    it.cyl(6, 9, 0, -2.5, 0, 0x00e5ff, axis="Y", seg=22, bev=1.6)
    it.cyl(5.5, 3, 0, 3.4, 0, 0x00c4dd, axis="Y", r2=2.5, seg=22, bev=0.4)
    it.cyl(2.3, 2.4, 0, 5.9, 0, 0x00c4dd, axis="Y", seg=14)
    it.cyl(2.9, 2.6, 0, 8.0, 0, 0x2b2b3a, axis="Y", seg=14, bev=0.5)
    for y in (-6.0, 1.2):
        it.ring(6.0, 0.55, 0, y, 0, 0x2b2b3a, axis="Y", seg=26)
    for s in (1, -1):
        it.box(4.4, 3.6, 0.8, 0, -1.6, 6.0 * s, 0xffffff, bev=0.3)
        it.box(3.1, 3.1, 0.8, 0, -3.2, 6.0 * s, 0xffffff, rz=math.pi / 4, bev=0.3)
        it.box(1.0, 3.0, 0.9, 0, -2.0, 6.25 * s, 0x00a8c8, bev=0.2)
    it.ball(1.2, 3.4, 0.2, 4.6, 0xe6fdff, sx=0.7, sy=1.6, sz=0.5, seg=10)
    return it


def medkit():
    it = Item("L_med")
    it.box(20, 12, 11, 0, -1, 0, 0xf5f5f5, bev=1.4)
    it.box(20.3, 0.8, 11.3, 0, 1.2, 0, 0xd6d6d6, bev=0.3)
    for s in (1, -1):
        it.box(7, 2.2, 0.6, 0, -1.4, 5.55 * s, 0xff4d4d, bev=0.2)
        it.box(2.2, 7, 0.6, 0, -1.4, 5.55 * s, 0xff4d4d, bev=0.2)
        it.box(1.6, 2.6, 11.6, 6.5 * s, 1.2, 0, GREY, bev=0.3)
    it.ring(3.4, 0.8, 0, 5.0, 0, 0xff4d4d, arc=math.pi, axis="Z", seg=14)
    for s in (1, -1):
        it.box(2.0, 1.0, 2.0, 3.4 * s, 5.2, 0, DARK, bev=0.3)
    return it


def ammo():
    it = Item("L_ammo")
    it.box(16, 8, 10, 0, -3, 0, 0x55663a, bev=0.8)
    it.box(16.4, 2, 10.4, 0, -3.5, 0, 0xffd23f, bev=0.4)
    it.box(16.6, 1.4, 10.6, 0, 1.3, 0, 0x3c4a25, bev=0.4)
    for s in (1, -1):
        it.box(1.4, 3, 1.0, 5.6 * s, -1.4, 5.3, GREY, bev=0.2)
    for i in range(5):
        x = -6 + i * 3
        it.cyl(1.1, 4.0, x, 4.0, 0, GOLD, axis="Y", seg=12, bev=0.15)
        it.cyl(1.1, 2.2, x, 7.1, 0, 0xc8742e, axis="Y", r2=0.15, seg=12, bev=0)
    return it


def wood():
    it = Item("L_wood")
    for (y, z) in ((-2.8, -3.0), (-2.8, 3.0), (1.9, 0.0)):
        it.cyl(2.8, 18, 0, y, z, WOOD, seg=14, bev=0.3)
        it.cyl(2.3, 18.3, 0, y, z, 0xd9a066, seg=14, bev=0)
        it.ring(2.32, 0.12, 9.18, y, z, WOOD_D, axis="X", seg=14, tube=4)
        it.ring(2.32, 0.12, -9.18, y, z, WOOD_D, axis="X", seg=14, tube=4)
    return it


def build():
    coll = bpy.data.collections.get(COLL) or bpy.data.collections.new(COLL)
    if coll.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(coll)
    for ob in list(coll.objects):
        me = ob.data
        bpy.data.objects.remove(ob)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    makers = [lambda: pistol(WCOL[0]), lambda: rifle(WCOL[1]), lambda: shotgun(WCOL[2]), lambda: sniper(WCOL[3]),
              lambda: pickaxe(WCOL[4]), mini, big, medkit, ammo, wood]
    stats = {}
    for i, mk in enumerate(makers):
        ob = mk().done(coll, (0, -i * 30) if i < 5 else (90, -(i - 5) * 30))
        stats[ob.name] = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return coll, stats


def export(coll):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in coll.objects:
        ob.select_set(True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_normals=True, export_texcoords=False, export_animations=False)
    return os.path.getsize(OUT)
