"""Prépare les armes texturées (Sketchfab, CC-BY-4.0) pour le jeu et exporte models/weapons_hd.glb.

blender -b --factory-startup -P tools/blender/build_weapons_hd.py

Pour chaque arme : rig appliqué, pièces fusionnées, canon tourné vers +X, taille alignée sur les armes du jeu,
origine sur la poignée (là où la main tient l'arme, comme dans mkWeapon), texture de couleur seule en 512 px.
Les fractions de poignée ont été relevées sur des rendus de profil de chaque modèle.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

ROOT = r"C:/Repos/Fortnit/models/"
OUT = ROOT + "weapons_hd.glb"
TEX = 512
# fichier, nom dans le jeu, sens du canon (+1 = +Y Blender), longueur cible (unités du jeu),
# poignée : fraction de longueur depuis l'arrière, fraction de hauteur depuis le bas
WEAPONS = [("t77_handgun.glb", "W0", -1, 24, 0.18, 0.55),
           ("sg553_assault_rifle.glb", "W1", 1, 60, 0.35, 0.56),
           ("shotgun.glb", "W2", -1, 54, 0.08, 0.52)]


def bounds(obs):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in obs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            for i in range(3):
                lo[i] = min(lo[i], w[i]); hi[i] = max(hi[i], w[i])
    return lo, hi


def bake(name):
    """Remplace chaque maillage par sa version évaluée (rig appliqué) et supprime le reste."""
    dg = bpy.context.evaluated_depsgraph_get()
    keep = []
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and o.data.materials:
            e = o.evaluated_get(dg)
            me = bpy.data.meshes.new_from_object(e, depsgraph=dg)
            me.transform(e.matrix_world)
            n = bpy.data.objects.new(name, me)
            bpy.context.scene.collection.objects.link(n)
            keep.append(n)
    for o in list(bpy.context.scene.objects):
        if o not in keep:
            bpy.data.objects.remove(o)
    for o in keep:
        o.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    if len(keep) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def drop_extras(ob):
    """T77 : chargeurs et balles posés sous le canon, à l'avant et en bas -> supprimés."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for v in bm.verts:
        for i in range(3):
            lo[i] = min(lo[i], v.co[i]); hi[i] = max(hi[i], v.co[i])
    seen, gone = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        part, stack = [], [v]
        seen.add(v)
        while stack:
            a = stack.pop()
            part.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b not in seen:
                    seen.add(b)
                    stack.append(b)
        c = sum((p.co for p in part), Vector()) / len(part)
        top = max(p.co.z for p in part)
        front_low = c.y < (lo.y + hi.y) / 2 + 0.02 * (hi.y - lo.y) and top < lo.z + 0.62 * (hi.z - lo.z)
        loose_bullet = len(part) < 0.03 * len(bm.verts) and top < lo.z + 0.35 * (hi.z - lo.z)
        if front_low or loose_bullet:
            gone += part
    bmesh.ops.delete(bm, geom=gone, context="VERTS")
    bm.to_mesh(ob.data)
    bm.free()
    return len(gone)


def shrink_textures(ob):
    """Garde la texture de couleur de base (le jeu éclaire en Lambert), réduite à TEX px."""
    for m in ob.data.materials:
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        for k in ("Normal", "Metallic", "Roughness", "Emission Color", "Alpha"):
            for l in list(bsdf.inputs[k].links):
                nt.links.remove(l)
        bsdf.inputs["Metallic"].default_value = 0
        bsdf.inputs["Roughness"].default_value = 0.6
        for n in list(nt.nodes):
            if n.type == "NORMAL_MAP":
                nt.nodes.remove(n)
        for l in bsdf.inputs["Base Color"].links:
            img = getattr(l.from_node, "image", None)
            if img and max(img.size) > TEX:
                img.scale(TEX, TEX)


def prepare(f, name, sign, length, gx, gy):
    bpy.ops.import_scene.gltf(filepath=ROOT + f)
    ob = bake(name)
    removed = drop_extras(ob) if name == "W0" else 0
    ob.data.transform(Matrix.Rotation(-sign * math.pi / 2, 4, "Z"))  # canon vers +X
    lo, hi = bounds([ob])
    s = length / (hi.x - lo.x)
    grip = Vector((lo.x + gx * (hi.x - lo.x), (lo.y + hi.y) / 2, lo.z + gy * (hi.z - lo.z)))
    ob.data.transform(Matrix.Scale(s, 4) @ Matrix.Translation(-grip))
    shrink_textures(ob)
    lo, hi = bounds([ob])
    return ob, {"removed_verts": removed, "lo": [round(v, 1) for v in lo], "hi": [round(v, 1) for v in hi],
                "tris": sum(len(p.vertices) - 2 for p in ob.data.polygons)}


bpy.ops.wm.read_factory_settings(use_empty=True)
report, done = {}, []
for f, name, sign, length, gx, gy in WEAPONS:
    before = set(bpy.data.objects)
    hold = [o for o in bpy.context.scene.objects]
    for o in hold:  # met de côté les armes déjà prêtes pendant l'import suivant
        bpy.context.scene.collection.objects.unlink(o)
    ob, info = prepare(f, name, sign, length, gx, gy)
    for o in hold:
        bpy.context.scene.collection.objects.link(o)
    done.append(ob)
    report[name] = info
for o in bpy.context.view_layer.objects:
    o.select_set(o in done)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                          export_image_format="JPEG", export_jpeg_quality=85, export_animations=False, export_skins=False)
report["bytes"] = os.path.getsize(OUT)
print("RESULT", report)
