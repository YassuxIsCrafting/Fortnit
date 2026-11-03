"""Prépare le coffre texturé (Sketchfab « Medieval Chest » par AIV, CC-BY-4.0) et exporte models/chest_hd.glb.

blender -b --factory-startup -P tools/blender/build_chest.py

Le jeu ouvre le coffre en tournant le couvercle autour de sa charnière (groupe « lid » de mkChest) :
- CH_base : caisse, posée au sol (y = 0), avant (cadenas) vers +Z du jeu ;
- CH_lid : couvercle, dans le repère de la charnière (bord arrière du haut de la caisse) ;
- CH_hinge : un repère vide placé sur la charnière, que le jeu lit pour positionner le couvercle.
Échelle uniforme (largeur 34 unités), texture de couleur seule en 512 px.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

SRC = r"C:/Repos/Fortnit/models/medieval_chest.glb"
OUT = r"C:/Repos/Fortnit/models/chest_hd.glb"
WIDTH, SEAM, TEX = 34, 0.66, 512  # SEAM : jointure du couvercle, en fraction de hauteur (relevée sur un rendu de face)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
dg = bpy.context.evaluated_depsgraph_get()
meshes = []
for o in list(bpy.context.scene.objects):
    if o.type == "MESH" and o.data.materials:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
        me.transform(o.matrix_world)
        meshes.append(me)
for o in list(bpy.context.scene.objects):
    bpy.data.objects.remove(o)

bm = bmesh.new()
for me in meshes:
    bm.from_mesh(me)
lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
s = WIDTH / (hi.x - lo.x)
# avant (cadenas, +Y Blender) vers +Z du jeu = -Y Blender : demi-tour autour de Z ; pied au sol
bmesh.ops.transform(bm, matrix=Matrix.Scale(s, 4) @ Matrix.Rotation(math.pi, 4, "Z") @
                    Matrix.Translation(Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))), verts=bm.verts)
H = (hi.z - lo.z) * s
seam = SEAM * H
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, seam), plane_no=(0, 0, 1))
back = max(v.co.y for v in bm.verts)  # arrière du coffre (+Y Blender = -Z du jeu)
lid_faces = [f for f in bm.faces if f.calc_center_median().z > seam]

lid_bm = bm.copy()
bmesh.ops.delete(lid_bm, geom=[f for f in lid_bm.faces if f.calc_center_median().z <= seam], context="FACES")
bmesh.ops.translate(lid_bm, vec=(0, -back, -seam), verts=lid_bm.verts)  # repère de la charnière
bmesh.ops.delete(bm, geom=lid_faces, context="FACES")

mat = meshes[0].materials[0]
for name, b in (("CH_base", bm), ("CH_lid", lid_bm)):
    me = bpy.data.meshes.new(name)
    b.to_mesh(me)
    b.free()
    me.materials.append(mat)
    bpy.context.scene.collection.objects.link(bpy.data.objects.new(name, me))
hinge = bpy.data.objects.new("CH_hinge", None)
hinge.location = (0, back, seam)
bpy.context.scene.collection.objects.link(hinge)

nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
for k in ("Normal", "Metallic", "Roughness", "Emission Color", "Alpha"):
    for l in list(bsdf.inputs[k].links):
        nt.links.remove(l)
for l in bsdf.inputs["Base Color"].links:
    img = getattr(l.from_node, "image", None)
    if img and max(img.size) > TEX:
        img.scale(TEX, TEX)

for o in bpy.context.scene.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True,
                          export_image_format="JPEG", export_jpeg_quality=85, export_animations=False)
print("RESULT", {"scale": round(s, 2), "height": round(H, 1), "seam": round(seam, 1), "back": round(back, 1),
                 "bytes": os.path.getsize(OUT)})
