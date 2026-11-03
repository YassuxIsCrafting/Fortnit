"""Génère le personnage réaliste de Fortnit (maillage riggé) et exporte models/human.glb.

Lancer dans Blender :  exec(open(r"C:/Repos/Fortnit/tools/blender/build_human.py", encoding="utf-8").read(), {"__name__": "human"})

Squelette identique à celui de hero-eclair.glb (mêmes noms d'os, tous orientés vers le haut, sans rotation de repos) :
le jeu recopie les poses du corps en blocs sur ces os (heroSync), donc marche, visée, planeur et emotes marchent tels quels.
Pose en T, face avant = +X, bras le long de ±Y Blender (ArmP du côté -Y). Mètres, ~1,77 m de haut.
Matériaux nommés Skin, Shirt, Pants, Belt, Shoes, Hair, EyeW, EyeD : le jeu les recolore (tenue, peau...).
"""
import bpy, bmesh, math, os
from mathutils import Vector

OUT_HUMAN = r"C:/Repos/Fortnit/models/human.glb"
COLL_HUMAN = "Fortnit_Human"
COLS = {"Skin": 0xf1c27d, "Shirt": 0x3da5ff, "Pants": 0x2b2b3a, "Belt": 0x1b1b22, "Shoes": 0xf5f5f5,
        "Hair": 0x3b2a1e, "EyeW": 0xffffff, "EyeD": 0x1b1b22, "Cap": 0x4b5320, "Gear": 0x3d4a2a}
BOOT = [0.13]  # hauteur des chaussures (0.22 : rangers du soldat)
HEAD_C, HEAD_R = Vector((0.01, 0, 1.64)), 0.115


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


MATS = list(COLS)


def link(coll, ob):
    coll.objects.link(ob)
    return ob


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
    # coupes nettes aux ourlets (chaussures, ceinture, manches) avant d'attribuer les matériaux par zone
    bm = bmesh.new()
    bm.from_mesh(me)
    for co, no in (((0, 0, BOOT[0]), (0, 0, 1)), ((0, 0, 0.965), (0, 0, 1)), ((0, 0, 1.02), (0, 0, 1)),
                   ((0, 0.36, 0), (0, 1, 0)), ((0, -0.36, 0), (0, 1, 0)),
                   ((0, 0, 1.445), (0, 0, 1)), ((0, 0.11, 0), (0, 1, 0)), ((0, -0.11, 0), (0, 1, 0))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no)
    bm.to_mesh(me)
    bm.free()
    for m in MATS:
        me.materials.append(mat(m))
    for f in me.polygons:
        c = f.center
        if c.z < BOOT[0]:
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


def part(coll, name, prim, loc, scale, matname, **kw):
    bm = bmesh.new()
    if prim == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=kw.get("u", 20), v_segments=kw.get("v", 14), radius=1)
    else:
        bmesh.ops.create_cube(bm, size=2)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
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


def jaw(bm):
    # bas du visage plus étroit, menton légèrement en avant
    for v in bm.verts:
        t = max(0.0, (HEAD_C.z - v.co.z) / (HEAD_R * 1.1))
        v.co.y *= 1 - 0.22 * t
        v.co.x += 0.014 * t * max(0.0, v.co.x - HEAD_C.x) / HEAD_R * 3


def cap_cut(bm):
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z < HEAD_C.z + 0.035], context="FACES")


def visor_cut(bm):
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().x < 0.085], context="FACES")


def hair_cut(bm):
    gone = [f for f in bm.faces if (lambda c: (c.x > 0.045 and c.z < 1.705) or c.z < 1.60 or (abs(c.y) > 0.09 and c.z < 1.64 and c.x > -0.03))(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=gone, context="FACES")


def head_parts(coll):
    hc, r = HEAD_C, HEAD_R
    obs = [part(coll, "H_head", "sphere", hc, (r, r * 0.9, r * 1.1), "Skin", u=24, v=18, cut=jaw),
           part(coll, "H_hair", "sphere", hc + Vector((-0.008, 0, 0.018)), (r * 1.07, r * 0.98, r * 1.1), "Hair", u=24, v=18, cut=hair_cut),
           part(coll, "H_nose", "sphere", (0.123, 0, 1.622), (0.017, 0.014, 0.026), "Skin", u=12, v=8)]
    for s in (1, -1):
        obs += [part(coll, "H_ear", "sphere", (0.0, 0.1 * s, 1.635), (0.018, 0.012, 0.03), "Skin", u=12, v=8),
                part(coll, "H_eyeW", "sphere", (0.104, 0.037 * s, 1.655), (0.017, 0.017, 0.015), "EyeW", u=12, v=8),
                part(coll, "H_eyeD", "sphere", (0.119, 0.037 * s, 1.654), (0.006, 0.009, 0.009), "EyeD", u=10, v=6),
                part(coll, "H_brow", "cube", (0.117, 0.038 * s, 1.684), (0.004, 0.017, 0.0035), "Hair")]
    obs.append(part(coll, "H_mouth", "cube", (0.13, 0, 1.584), (0.003, 0.017, 0.0028), "EyeD"))
    # casquette (matériau Cap) : masquée par le jeu sauf pour les skins qui la portent
    obs.append(part(coll, "H_cap", "sphere", hc + Vector((-0.004, 0, 0.03)), (r * 1.13, r * 1.05, r * 0.92), "Cap", u=24, v=16, cut=cap_cut))
    obs.append(part(coll, "H_visor", "sphere", (0.118, 0, 1.676), (0.062, 0.092, 0.009), "Cap", u=20, v=8, cut=visor_cut))
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


def gear_parts(coll):
    """Équipement du soldat (matériau Gear) : gilet, poches, bretelles, sac, genouillères, ceinturon."""
    obs = [part(coll, "G_vest_f", "cube", (0.112, 0, 1.25), (0.032, 0.15, 0.14), "Gear"),
           part(coll, "G_vest_b", "cube", (-0.108, 0, 1.26), (0.03, 0.15, 0.14), "Gear"),
           part(coll, "G_pack", "cube", (-0.165, 0, 1.24), (0.045, 0.12, 0.15), "Gear"),
           part(coll, "G_packtop", "sphere", (-0.165, 0, 1.39), (0.05, 0.12, 0.03), "Gear", u=16, v=8)]
    for y in (-0.075, 0, 0.075):
        obs.append(part(coll, "G_pouch", "cube", (0.152, y, 1.17), (0.016, 0.03, 0.04), "Gear"))
    for s in (1, -1):
        obs += [part(coll, "G_strap", "cube", (0.0, 0.1 * s, 1.425), (0.13, 0.03, 0.012), "Gear"),
                part(coll, "G_knee", "sphere", (0.055, 0.095 * s, 0.50), (0.022, 0.05, 0.055), "Gear", u=14, v=10),
                part(coll, "G_hip", "cube", (0.02, 0.15 * s, 0.97), (0.04, 0.025, 0.045), "Gear")]
    return obs


def build_human(soldier=False):
    BOOT[0] = 0.22 if soldier else 0.13
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
    parts = head_parts(coll) + (gear_parts(coll) if soldier else [])
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
    for v in me.vertices:
        for n, w in weights(v.co).items():
            if w > 1e-4:
                groups[n].add([v.index], w, "REPLACE")
    rig.location = (2600, 0, 0)
    return coll, {"verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons)}


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
