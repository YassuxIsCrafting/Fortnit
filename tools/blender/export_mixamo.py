"""Exporte les personnages d'Île Éclair en FBX pour l'auto-rig de Mixamo.

blender -b --factory-startup -P tools/blender/export_mixamo.py -- <dossier de sortie>

- ile_eclair_base.fbx : corps réaliste de base (sans accessoires de skins), maillage seul, sans squelette ;
- heros_eclair.fbx : Héros Éclair (hero-eclair.glb) en pose de repos, sans squelette, texture intégrée.
Face avant tournée vers -Y Blender (convention attendue par Mixamo avec l'export FBX par défaut), pieds au sol.
"""
import bpy, math, os, sys
from mathutils import Matrix

OUT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else r"C:/Repos/Fortnit/tools/mixamo"
os.makedirs(OUT, exist_ok=True)
FACE = Matrix.Rotation(-math.pi / 2, 4, "Z")  # avant +X -> -Y


def export(path, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_ALL",  # sinon Mixamo affiche le perso à la mauvaise taille
                             bake_anim=False, add_leaf_bones=False, path_mode="COPY", embed_textures=True)
    return os.path.getsize(path)


def static_meshes():
    """Remplace chaque maillage par sa version évaluée (pose de repos), sans modificateur ni parent."""
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(o.matrix_world)
        me.transform(FACE)
        n = bpy.data.objects.new(o.name + "_static", me)
        bpy.context.scene.collection.objects.link(n)
        out.append(n)
    for o in list(bpy.context.scene.objects):
        if o not in out:
            bpy.data.objects.remove(o)
    return out


res = {}
# corps réaliste sans accessoires
bpy.ops.wm.read_factory_settings(use_empty=True)
ns = {"__name__": "human"}
exec(open(r"C:/Repos/Fortnit/tools/blender/build_human.py", encoding="utf-8").read(), ns)
ns["ACC"].clear()
ns["build_human"]()
for o in bpy.context.scene.objects:  # repos : pas de pose, l'armature est neutre
    if o.type == "MESH":
        for m in list(o.modifiers):
            o.modifiers.remove(m)
res["ile_eclair_base"] = export(os.path.join(OUT, "ile_eclair_base.fbx"), static_meshes())

# Héros Éclair
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"C:/Repos/Fortnit/models/hero-eclair.glb")
for o in list(bpy.context.scene.objects):
    if o.type == "MESH" and not o.data.materials:
        bpy.data.objects.remove(o)  # sphère parasite du fichier
res["heros_eclair"] = export(os.path.join(OUT, "heros_eclair.fbx"), static_meshes())
print("RESULT", res)
