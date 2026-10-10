# -*- coding: utf-8 -*-
"""6 unique hairstyles (3 male, 3 female), Z-up, fitted to the head."""
import bpy
import bmesh

from .common import log, uv_sphere, tapered, join, smooth, tris, make_mat
from .body import Landmarks

HAIR_COLORS = {
    "black": (0.03, 0.02, 0.02),
    "dark": (0.08, 0.05, 0.04),
    "brown": (0.16, 0.09, 0.05),
}

STYLES = ["crop", "cornrows", "afro", "long", "buns", "headtie"]


def _trim_local(ob, z_cut):
    """Drop vertices whose local z is below z_cut (object is centred on head)."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    geom = [v for v in bm.verts if v.co.z < z_cut]
    if geom:
        bmesh.ops.delete(bm, geom=geom, context="VERTS")
    bm.to_mesh(me)
    bm.free()


def _cap(name, lm, r_mult, z_mult, trim, y_off, z_off, mat):
    hc, hr = lm.head_c, lm.head_r
    ob = uv_sphere(
        name + "_cap",
        (hc[0], hc[1] + y_off, hc[2] + z_off),
        hr,
        seg=16, ring=10,
        scale=(lm.head_scale[0] * r_mult, lm.head_scale[1] * r_mult,
               lm.head_scale[2] * z_mult),
    )
    _trim_local(ob, hr * trim)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def build_hair(name, style, lm, color="black"):
    """Return a single joined hair mesh for `style` on this head."""
    if style not in STYLES:
        raise ValueError("unknown style %r" % style)
    mat = make_mat(name + "_hairmat", HAIR_COLORS[color])
    parts = []

    if style == "crop":
        parts.append(_cap(name, lm, 1.06, 1.04, -0.28, 0.0, 0.005, mat))

    elif style == "cornrows":
        parts.append(_cap(name, lm, 1.08, 0.82, -0.32, -0.005, 0.01, mat))

    elif style == "afro":
        hc, hr = lm.head_c, lm.head_r
        parts.append(uv_sphere(name + "_afro",
                               (hc[0], hc[1] - 0.02, hc[2] + 0.02),
                               hr * 1.45, seg=16, ring=10,
                               scale=(lm.head_scale[0] * 1.45,
                                      lm.head_scale[1] * 1.5,
                                      lm.head_scale[2] * 1.4)))
        _trim_local(parts[0], -0.55 * hr)
        parts[0].data.materials.clear()
        parts[0].data.materials.append(mat)

    elif style == "long":
        parts.append(_cap(name, lm, 1.08, 1.02, -0.30, 0.0, 0.005, mat))
        hc, hr = lm.head_c, lm.head_r
        for sx in (-1, 1):
            tag = "L" if sx < 0 else "R"
            parts.append(tapered(
                "%s_lock_%s" % (name, tag),
                (sx * hr * 0.75, hc[1] - hr * 0.45, hc[2] - hr * 0.5),
                (sx * hr * 0.55, hc[1] - hr * 0.75, lm.shoulder_z - 0.03),
                hr * 0.34, hr * 0.16, verts=8))
        parts.append(tapered(
            name + "_back",
            (0.0, hc[1] - hr * 0.55, hc[2] - hr * 0.2),
            (0.0, hc[1] - hr * 0.9, lm.shoulder_z - 0.02),
            hr * 0.55, hr * 0.3, verts=10))
        for p in parts:
            p.data.materials.clear()
            p.data.materials.append(mat)

    elif style == "buns":
        parts.append(_cap(name, lm, 1.06, 1.02, -0.30, 0.0, 0.005, mat))
        hc, hr = lm.head_c, lm.head_r
        for sx in (-1, 1):
            tag = "L" if sx < 0 else "R"
            parts.append(uv_sphere("%s_bun_%s" % (name, tag),
                                   (sx * hr * 0.85, hc[1] - hr * 0.15,
                                    hc[2] + hr * 0.85),
                                   hr * 0.42, seg=12, ring=8))
        for p in parts:
            p.data.materials.clear()
            p.data.materials.append(mat)

    elif style == "headtie":
        parts.append(_cap(name, lm, 1.05, 1.0, -0.30, 0.0, 0.005, mat))
        hc, hr = lm.head_c, lm.head_r
        ob = uv_sphere(name + "_tie",
                       (hc[0], hc[1] + 0.01, hc[2] + hr * 0.85),
                       hr * 0.75, seg=14, ring=9,
                       scale=(1.25, 1.35, 0.95))
        _trim_local(ob, -0.35 * hr)
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        parts.append(ob)

    hair = join(parts, name + "_hair")
    hair.data.materials.clear()
    hair.data.materials.append(mat)
    smooth(hair)
    log("hair %s (style %s): tris=%d" % (name, style, tris(hair)))
    return hair