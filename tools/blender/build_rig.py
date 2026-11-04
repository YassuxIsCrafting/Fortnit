"""Rig des personnages d'Île Éclair sur le squelette Mixamo et paquet d'animations Mixamo.

blender -b --factory-startup -P tools/blender/build_rig.py

Entrées : tools/mixamo/anims/*.fbx (exports Mixamo de Y Bot, « sans peau » sauf tpose.fbx), models/hero-eclair.glb,
          tools/blender/build_human.py (corps réaliste + accessoires des skins).
Sorties : models/human_rig.glb (perso réaliste + accessoires), models/hero_rig.glb (Héros Éclair), models/anims.glb (clips).

Tous les personnages gardent l'orientation exacte des os de Mixamo : seule la position des articulations est
ajustée à chaque corps. Les rotations des clips s'appliquent donc telles quelles à tous ; le jeu recale seulement
la hauteur du bassin (piste de position des hanches) pour Héros Éclair, plus petit.
Poids : distance aux os (enveloppe), chaque côté du corps limité à ses os ; les mains moufles suivent l'os de la main.
"""
import bpy, bmesh, math, os, glob, re
from mathutils import Vector, Matrix

ROOT = r"C:/Repos/Fortnit/"
ANIMS = ROOT + "tools/mixamo/anims/"
P = "mixamorig:"
FACE = Matrix.Rotation(-math.pi / 2, 4, "Z")  # nos modèles regardent +X -> -Y (face des personnages Mixamo)
DROP = re.compile(r"(Thumb|Index|Middle|Ring|Pinky|_End)")


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def select(objs, active=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]


def base_rig():
    """Squelette de Y Bot (T-pose) sans doigts ni bouts d'os."""
    bpy.ops.import_scene.fbx(filepath=ANIMS + "tpose.fbx")
    rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        bpy.data.objects.remove(o)
    if rig.animation_data:
        rig.animation_data.action = None
    select([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    for b in list(rig.data.edit_bones):
        if DROP.search(b.name):
            rig.data.edit_bones.remove(b)
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.name = rig.data.name = "Rig"
    return rig


def fit(rig, targets):
    """Déplace les articulations (repère monde) sans changer l'orientation des os."""
    mw, inv = rig.matrix_world, rig.matrix_world.inverted()
    select([rig])
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    old = {b.name: (b.head.copy(), b.tail.copy()) for b in eb}
    for b in eb:
        b.use_connect = False
    for b in eb:
        n = b.name[len(P):]
        if n not in targets:
            continue
        h, t = old[b.name]
        wh = targets[n]
        k = targets.get("_k", {}).get(n, 1.0)
        b.head = inv @ Vector(wh)
        b.tail = b.head + (t - h) * k
    bpy.ops.object.mode_set(mode="OBJECT")


def segs(rig):
    mw = rig.matrix_world
    return [(b.name, mw @ b.head_local, mw @ b.tail_local) for b in rig.data.bones]


def dist_seg(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length


def skin(mesh, rig, pins=None):
    """Poids par enveloppe : 2 os les plus proches, côté gauche/droit séparés, épingles par matériau."""
    S = segs(rig)
    groups = {n: mesh.vertex_groups.new(name=n) for n, _, _ in S}
    pinned = {}
    if pins:
        mats = [m.name if m else "" for m in mesh.data.materials]
        for f in mesh.data.polygons:
            bone = pins(mats[f.material_index])
            if bone:
                for v in f.vertices:
                    pinned[v] = bone
    mw = mesh.matrix_world
    for v in mesh.data.vertices:
        if v.index in pinned:
            groups[P + pinned[v.index]].add([v.index], 1.0, "REPLACE")
            continue
        p = mw @ v.co
        cand = []
        for n, a, b in S:
            if p.x > 0.03 and "Right" in n or p.x < -0.03 and "Left" in n:
                continue
            cand.append((dist_seg(p, a, b), n))
        cand.sort()
        top = cand[:2]
        ws = [1.0 / (d * d + 1e-4) ** 2 for d, _ in top]
        s = sum(ws)
        for (d, n), w in zip(top, ws):
            if w / s > 0.02:
                groups[n].add([v.index], w / s, "REPLACE")
    md = mesh.modifiers.new("Armature", "ARMATURE")
    md.object = rig
    mesh.parent = rig
    mesh.matrix_parent_inverse = rig.matrix_world.inverted()


def export(path, objs, anims=False):
    select(objs)
    kw = dict(filepath=path, export_format="GLB", use_selection=True, export_apply=False, export_yup=True,
              export_normals=True, export_texcoords=True, export_skins=True, export_animations=anims)
    if anims:
        kw.update(export_animation_mode="ACTIONS", export_force_sampling=False, export_optimize_animation_size=True,
                  export_anim_single_armature=True, export_reset_pose_bones=True)
    bpy.ops.export_scene.gltf(**kw)
    return os.path.getsize(path)


report = {}

# --- perso réaliste + accessoires des skins ---
clear()
rig = base_rig()
ns = {"__name__": "human"}
exec(open(ROOT + "tools/blender/build_human.py", encoding="utf-8").read(), ns)
ns["build_human"]()
human = bpy.data.objects["Human"]
old = human.parent
human.parent = None
for m in list(human.modifiers):
    human.modifiers.remove(m)
human.vertex_groups.clear()
human.data.transform(FACE)
bpy.data.objects.remove(old)
PIN = {"Spine": "Spine2", "Hips": "Hips"}
skin(human, rig, lambda m: PIN.get(m.split("_")[-1]) if m.startswith("H_A_") else None)
report["human"] = export(ROOT + "models/human_rig.glb", [rig, human])

# --- Héros Éclair ---
clear()
rig = base_rig()
bpy.ops.import_scene.gltf(filepath=ROOT + "models/hero-eclair.glb")
dg = bpy.context.evaluated_depsgraph_get()
src = next(o for o in bpy.context.scene.objects if o.type == "MESH" and o.data.materials)
me = bpy.data.meshes.new_from_object(src.evaluated_get(dg), depsgraph=dg)
me.transform(src.matrix_world)
me.transform(FACE)
hero = bpy.data.objects.new("Hero", me)
bpy.context.scene.collection.objects.link(hero)
for o in list(bpy.context.scene.objects):
    if o not in (rig, hero):
        bpy.data.objects.remove(o)
# articulations de Héros Éclair (repère monde après rotation, d'après son ancien squelette)
T = {"Hips": (0, 0, 0.61), "Spine": (0, 0.01, 0.80), "Spine1": (0, 0.01, 0.98), "Spine2": (0, 0.02, 1.15),
     "Neck": (0, 0.02, 1.34), "Head": (0, 0, 1.43)}
for s, x in (("Left", 1), ("Right", -1)):
    T.update({s + "Shoulder": (0.10 * x, 0.02, 1.27), s + "Arm": (0.27 * x, 0.0, 1.265), s + "ForeArm": (0.562 * x, 0.0, 1.265),
              s + "Hand": (0.80 * x, 0.0, 1.265), s + "UpLeg": (0.177 * x, 0.0, 0.61), s + "Leg": (0.177 * x, 0.0, 0.317),
              s + "Foot": (0.177 * x, 0.02, 0.07), s + "ToeBase": (0.177 * x, -0.10, 0.02)})
T["_k"] = {"Hips": 0.65, "Spine": 0.8, "Spine1": 0.8, "Spine2": 0.8, "Neck": 0.6, "Head": 1.3}
fit(rig, T)
skin(hero, rig)
report["hero"] = export(ROOT + "models/hero_rig.glb", [rig, hero])

# --- clips d'animation (sur le squelette de Y Bot, sans doigts) ---
clear()
rig = base_rig()
keep = {b.name for b in rig.data.bones}
for f in sorted(glob.glob(ANIMS + "*.fbx")):
    key = os.path.basename(f)[:-4]
    if key == "tpose":
        continue
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=f)
    arm = next(o for o in bpy.data.objects if o not in before and o.type == "ARMATURE")
    act = arm.animation_data.action
    act.name = key
    act.use_fake_user = True
    fcs = getattr(act, "fcurves", None)  # Blender 5 : courbes rangées par slot (channelbag)
    if fcs is None:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        fcs = action_get_channelbag_for_slot(act, act.slots[0]).fcurves
    for fc in list(fcs):
        m = re.match(r'pose\.bones\["([^"]+)"\]\.(\w+)', fc.data_path)
        bone, prop = (m.group(1), m.group(2)) if m else (None, None)
        if bone not in keep or prop == "scale" or (prop == "location" and bone != P + "Hips"):
            fcs.remove(fc)
            continue
        kp = fc.keyframe_points  # 30 -> 15 images/s : on garde une clé sur deux (et la dernière)
        for i in range(len(kp) - 2, 0, -2):
            kp.remove(kp[i])
    for o in [o for o in bpy.data.objects if o not in before]:
        bpy.data.objects.remove(o)
rig.animation_data_create()
report["clips"] = len([a for a in bpy.data.actions if a.use_fake_user])
report["anims"] = export(ROOT + "models/anims.glb", [rig], anims=True)
print("RESULT", report)
