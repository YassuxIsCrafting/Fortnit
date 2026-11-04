"""Clips Mixamo retranscrits sur le squelette d'Île Éclair (celui de human.glb et hero-eclair.glb), exporte models/anims.glb.

blender -b --factory-startup -P tools/blender/build_anims.py

Entrées : tools/mixamo/anims/*.fbx (exports Mixamo de Y Bot, « sans peau »), tools/blender/build_human.py (squelette).
Les deux squelettes sont en T au repos. Pour chaque image, chacun de nos os prend la rotation (repère monde) de son os
Mixamo par rapport à la T : base = Repos⁻¹ · D_parent⁻¹ · D_os · Repos. Le bassin garde aussi son déplacement,
ramené à notre taille. Le jeu joue ces clips (emotes, planeur, chute) sur le même squelette que l'ancienne marche.
"""
import bpy, math, os, glob
from mathutils import Matrix, Vector

ROOT = r"C:/Repos/Fortnit/"
ANIMS = ROOT + "tools/mixamo/anims/"
P = "mixamorig:"
# notre os -> os Mixamo dont il suit la rotation (P = côté -Y = droite du perso, qui regarde +X)
MAP = {"Hips": "Hips", "Spine": "Spine2", "Head": "Head",
       "ArmP": "RightArm", "ForeP": "RightForeArm", "ArmN": "LeftArm", "ForeN": "LeftForeArm",
       "LegP": "RightUpLeg", "ShinP": "RightLeg", "LegN": "LeftUpLeg", "ShinN": "LeftLeg"}
STEP = 2  # 30 -> 15 images/s

bpy.ops.wm.read_factory_settings(use_empty=True)
ns = {"__name__": "human"}
exec(open(ROOT + "tools/blender/build_human.py", encoding="utf-8").read(), ns)
coll, _ = ns["build_human"]()
rig = next(o for o in coll.objects if o.type == "ARMATURE")
for o in [o for o in coll.objects if o.type != "ARMATURE"]:
    bpy.data.objects.remove(o)
rig.location = (0, 0, 0)
rig.name = "Rig"
bpy.context.view_layer.update()
REST = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
HIP_H = rig.data.bones["Hips"].head_local.z
report = {}

for f in sorted(glob.glob(ANIMS + "*.fbx")):
    key = os.path.basename(f)[:-4]
    if key == "tpose":
        continue
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=f)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    src = arm.animation_data.action
    # Mixamo regarde -Y : un quart de tour le tourne vers +X comme nos persos
    arm.rotation_euler = (arm.rotation_euler.x, arm.rotation_euler.y, arm.rotation_euler.z + math.pi / 2)
    bpy.context.view_layer.update()
    mw = arm.matrix_world
    mrest = {n: (mw @ arm.data.bones[P + m].matrix_local) for n, m in MAP.items()}
    rq = {n: M.to_3x3().normalized().to_quaternion() for n, M in mrest.items()}
    hip0 = mrest["Hips"].to_translation()
    k = HIP_H / max(hip0.z, 1e-6)
    act = bpy.data.actions.new(key)
    act.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act
    a, b = (int(round(x)) for x in src.frame_range)
    frames = list(range(a, b + 1, STEP))
    if frames[-1] != b:
        frames.append(b)
    for fr in frames:
        bpy.context.scene.frame_set(fr)
        D = {}
        for n, m in MAP.items():
            wm = mw @ arm.pose.bones[P + m].matrix
            D[n] = wm.to_3x3().normalized().to_quaternion() @ rq[n].inverted()
        for pb in rig.pose.bones:
            n = pb.name
            par = pb.parent.name if pb.parent else None
            d = D[n] if par is None else D[par].inverted() @ D[n]
            q = REST[n].inverted() @ d @ REST[n]
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=fr - a)
            if par is None:
                t = ((mw @ arm.pose.bones[P + "Hips"].matrix).to_translation() - hip0) * k
                pb.location = REST[n].inverted() @ t
                pb.keyframe_insert("location", frame=fr - a)
    rig.animation_data.action = None
    for o in new:
        bpy.data.objects.remove(o)
    report[key] = len(frames)

for pb in rig.pose.bones:
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.location = (0, 0, 0)
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
out = ROOT + "models/anims.glb"
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_apply=False, export_yup=True,
                          export_skins=True, export_animations=True, export_animation_mode="ACTIONS",
                          export_force_sampling=False, export_optimize_animation_size=True,
                          export_anim_single_armature=True, export_reset_pose_bones=True)
print("RESULT", len(report), "clips", os.path.getsize(out))
