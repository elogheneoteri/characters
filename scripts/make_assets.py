# -*- coding: utf-8 -*-
"""Generate the six male character assets for the character pack.

Each character is a full T-pose body + one of the six face variants +
hairstyle + outfit + shoes, all rigged to a Mixamo-style armature and
exported as .fbx and .obj into ../malecharacters/.

Run headless inside Blender:

    blender --background --python scripts/make_assets.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

from charlib.body import Landmarks, build_body  # noqa: E402
from charlib.common import log, reset_scene, tris  # noqa: E402
from charlib.faces import build_face  # noqa: E402
from charlib.hair import build_hair  # noqa: E402
from charlib.outfits import (_build, _collar, _pants, _sleeve, _torso,  # noqa: E402
                             build_shoes)
from charlib.rig import bind  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "malecharacters")

# (name, skin, hair_style, hair_color, face_idx, sleeve_frac,
#  (torso_key, pants_key, collar_key or None), shoe_kind)
CHARACTERS = [
    ("Ade",      (0.45, 0.27, 0.16), "crop",     "black", 0, 1.0,
     ("ivory", "indigo", "gold"),  "loafers"),
    ("Chidi",    (0.35, 0.20, 0.11), "cornrows", "black", 1, 0.5,
     ("teal", "khaki", None),      "sneakers"),
    ("Emeka",    (0.50, 0.31, 0.18), "afro",     "dark",  2, 1.0,
     ("white", "denim", None),     "loafers"),
    ("Femi",     (0.38, 0.22, 0.12), "crop",     "black", 3, 1.0,
     ("grey", "charcoal", None),   "sneakers"),
    ("Ibrahim",  (0.46, 0.28, 0.16), "cornrows", "brown", 4, 1.0,
     ("magenta", "black", "gold"), "loafers"),
    ("Tunde",    (0.52, 0.34, 0.20), "afro",     "black", 5, 0.5,
     ("coral", "denim", None),     "sandals"),
]


def _outfit_spec(name, sleeve_frac, fabrics):
    torso_key, pants_key, collar_key = fabrics
    spec = [
        (lambda lm: _torso(lm), torso_key),
        (lambda lm, f=sleeve_frac: _sleeve(lm, -1, "L", f), torso_key),
        (lambda lm, f=sleeve_frac: _sleeve(lm, 1, "R", f), torso_key),
    ]
    if collar_key is not None:
        spec.append((lambda lm: _collar(lm, collar_key, name), collar_key))
    spec.append((lambda lm: _pants(lm, -1, "L", lm.ankle_z - 0.01), pants_key))
    spec.append((lambda lm: _pants(lm, 1, "R", lm.ankle_z - 0.01), pants_key))
    return spec


def _export(name, objs):
    os.makedirs(OUT, exist_ok=True)
    for ob in bpy.data.objects:
        ob.select_set(False)
    for ob in objs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]

    fbx = os.path.join(OUT, name + ".fbx")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True,
                             path_mode="COPY", embed_textures=False)
    obj = os.path.join(OUT, name + ".obj")
    bpy.ops.wm.obj_export(filepath=obj, export_selected_objects=True,
                           export_materials=True)
    log("exported %s: fbx=%s obj=%s" % (name, fbx, obj))


def make_character(i, spec):
    (cname, skin, hair_style, hair_color, face_idx, sleeve_frac,
     fabrics, shoe_kind) = spec

    reset_scene()
    lm = Landmarks("male")

    body = build_body(cname, "male", skin)

    _n = [0]

    def face_mat(color):
        _n[0] += 1
        from charlib.common import make_mat
        return make_mat("%s_face%d" % (cname, _n[0]), color)

    face = build_face(cname, lm.head_c, lm.head_r, face_idx, face_mat,
                      skin=skin)
    hair = build_hair(cname, hair_style, lm, color=hair_color)
    outfit = _build(cname, "male", _outfit_spec(cname, sleeve_frac, fabrics))
    shoes = build_shoes(cname, shoe_kind, lm)

    meshes = [body, face, hair, outfit, shoes]
    bind(cname, lm, meshes)

    total = sum(tris(ob) for ob in meshes)
    log("%s: total tris=%d" % (cname, total))

    _export(cname, [bpy.data.objects.get(cname + "_Armature")] + meshes)
    return total


def main():
    reset_scene()
    grand = 0
    for i, spec in enumerate(CHARACTERS):
        grand += make_character(i, spec)
    log("done: %d characters, total tris=%d, out=%s"
        % (len(CHARACTERS), grand, OUT))


if __name__ == "__main__":
    main()