# -*- coding: utf-8 -*-
"""6 outfits per gender (Nigerian + Western mix) + 4 shared shoe items.

Every part is built in world space (Z-up, facing +Y) so the result can be
joined and parented to the Mixamo armature with auto weights.
"""
import bpy
import bmesh

from .common import log, uv_sphere, tapered, box, join, smooth, tris, make_mat
from .body import Landmarks

FAB = {
    "ivory": (0.85, 0.82, 0.70),
    "rust": (0.72, 0.18, 0.12),
    "teal": (0.10, 0.40, 0.36),
    "denim": (0.16, 0.24, 0.42),
    "charcoal": (0.30, 0.30, 0.33),
    "grey": (0.78, 0.78, 0.76),
    "magenta": (0.55, 0.10, 0.28),
    "gold": (0.85, 0.55, 0.10),
    "indigo": (0.10, 0.12, 0.38),
    "coral": (0.85, 0.42, 0.20),
    "navy": (0.15, 0.20, 0.50),
    "white": (0.92, 0.92, 0.90),
    "olive": (0.35, 0.38, 0.20),
    "khaki": (0.62, 0.55, 0.38),
    "black": (0.08, 0.08, 0.09),
    "leather": (0.20, 0.10, 0.06),
    "sandal": (0.45, 0.30, 0.15),
}


def _m(name, key, rough=0.8):
    return make_mat(name + "_" + key, FAB[key], rough=rough)


def _torso(lm, r_off=0.015, z_off=0.0, zq=1.0):
    """Torso shell from waist to shoulders, offset outward by r_off."""
    return tapered("torso", (0.0, 0.0, lm.waist_z + z_off),
                   (0.0, 0.0, lm.shoulder_z + 0.02 + z_off),
                   lm.waist_r + r_off, lm.chest_r + r_off, verts=14, zq=zq)


def _sleeve(lm, sx, tag, elbow_frac, r_off=0.015):
    """Arm shell. elbow_frac=0.5 -> elbow (short), 1.0 -> wrist (full)."""
    tip_x = lm.shoulder_j_x + elbow_frac * (lm.wrist_x - lm.shoulder_j_x)
    start = (sx * (lm.shoulder_j_x - 0.02), 0.0, lm.shoulder_z)
    end = (sx * tip_x, 0.0, lm.shoulder_z)
    r1 = lm.arm_r1 + r_off
    r2 = lm.arm_r2 + r_off * (elbow_frac * 0.6 + 0.4)
    return tapered("sleeve_%s" % tag, start, end, r1, r2, verts=10)


def _pants(lm, sx, tag, bottom_z, r_off=0.02):
    parts = []
    hJ = (sx * lm.hip_j_x, 0.0, lm.hip_j_z)
    kJ = (sx * lm.knee_x, 0.015, lm.knee_z)
    if bottom_z > lm.knee_z:
        parts.append(tapered("thigh_%s" % tag, hJ, kJ,
                             lm.thigh_r1 + r_off, lm.thigh_r2 + r_off, verts=10))
        mid = (sj for sj in (0.015))
        bJ = (sx * lm.knee_x, 0.015, bottom_z)
        rmid = lm.thigh_r2 + r_off
        parts.append(tapered("shin_%s" % tag, kJ, bJ, rmid, rmid * 0.9, verts=8))
    else:
        bJ = (sx * lm.knee_x, 0.015, bottom_z)
        parts.append(tapered("leg_%s" % tag, hJ, bJ,
                             lm.thigh_r1 + r_off, lm.ankle_r + r_off, verts=12))
    return parts


def _skirt(lm, top_r, bottom_r, top_z, bottom_z, zq):
    return tapered("skirt", (0.0, 0.0, top_z), (0.0, 0.0, bottom_z),
                   top_r, bottom_r, verts=14, zq=zq)


def _collar(lm, key, name):
    return uv_sphere(name + "_collar", (0.0, 0.015, lm.shoulder_z + 0.015),
                     0.062, seg=10, ring=5, scale=(1.35, 0.9, 0.55))


# ---------------------------------------------------------------------------
# Shoes (both feet, world space)
# ---------------------------------------------------------------------------

SHOES = ["sneakers", "loafers", "heels", "sandals"]


def _foot_box(lm, sx, kind):
    fx = sx * lm.knee_x
    sole = box("sole_%d" % sx, (fx, 0.035, 0.028),
               (lm.foot_w * 2.35, 0.115, 0.055))
    return sole, fx


def build_shoes(name, kind, lm):
    """Two-foot shoe item, joined. kind is in SHOES."""
    parts = []
    for sx in (-1, 1):
        tag = "L" if sx < 0 else "R"
        fx = sx * lm.knee_x
        heel_z = 0.02
        if kind == "sneakers":
            parts.append(box("%s_sole_%s" % (name, tag),
                             (fx, 0.035, 0.025), (lm.foot_w * 2.4, 0.125, 0.05)))
            parts.append(box("%s_upper_%s" % (name, tag),
                             (fx, 0.028, 0.085), (lm.foot_w * 2.1, 0.10, 0.07)))
            parts.append(box("%s_toe_%s" % (name, tag),
                             (fx, 0.06 + lm.foot_l * 0.5, 0.06),
                             (lm.foot_w * 2.0, 0.085, 0.05)))
            sole_key, up_key = "black", "white"
        elif kind == "loafers":
            parts.append(box("%s_sole_%s" % (name, tag),
                             (fx, 0.035, 0.018), (lm.foot_w * 2.3, 0.115, 0.036)))
            parts.append(box("%s_body_%s" % (name, tag),
                             (fx, 0.03, 0.065), (lm.foot_w * 2.05, 0.10, 0.055)))
            parts.append(box("%s_toe_%s" % (name, tag),
                             (fx, 0.055 + lm.foot_l * 0.5, 0.045),
                             (lm.foot_w * 1.9, 0.075, 0.045)))
            sole_key, up_key = "black", "leather"
        elif kind == "heels":
            parts.append(box("%s_sole_%s" % (name, tag),
                             (fx, 0.02, 0.035), (lm.foot_w * 2.2, 0.09, 0.07)))
            parts.append(tapered("%s_body_%s" % (name, tag),
                                 (fx, 0.02, 0.07), (fx, 0.02, 0.16),
                                 lm.foot_w * 0.75, lm.foot_w * 0.95, verts=8))
            parts.append(box("%s_toe_%s" % (name, tag),
                             (fx, 0.055 + lm.foot_l * 0.45, 0.05),
                             (lm.foot_w * 1.8, 0.07, 0.04)))
            sole_key, up_key = "black", "leather"
        else:  # sandals
            parts.append(box("%s_sole_%s" % (name, tag),
                             (fx, 0.035, 0.012), (lm.foot_w * 2.3, 0.115, 0.024)))
            parts.append(box("%s_strap_%s" % (name, tag),
                             (fx, 0.03, 0.06), (lm.foot_w * 2.1, 0.015, 0.04)))
            parts.append(box("%s_ank_%s" % (name, tag),
                             (fx, 0.02, 0.09), (lm.foot_w * 2.0, 0.012, 0.05)))
            sole_key, up_key = "sandal", "sandal"
        # assign materials per part
    mats = [_m(name + "_sole", sole_key), _m(name + "_up", up_key)]
    for p in parts:
        p.data.materials.clear()
        p.data.materials.append(mats[0] if p.name.startswith("%s_sole" % name)
                                else mats[1])
    shoes = join(parts, name + "_shoes")
    shoes.data.materials.clear()
    shoes.data.materials.append(mats[0])
    shoes.data.materials.append(mats[1])
    log("shoes %s (%s): tris=%d" % (name, kind, tris(shoes)))
    return shoes


# ---------------------------------------------------------------------------
# Outfits
# ---------------------------------------------------------------------------

def _assembled(name, parts, spec, lm):
    """parts: list of objects; spec: list of (obj, fabric_key) pairs already applied."""
    joined = join(parts, name)
    joined.data.materials.clear()
    seen = []
    for key in spec:
        m = _m(name, key)
        if m.name not in [s.name for s in seen]:
            joined.data.materials.append(m)
            seen.append(m)
    # re-tag: reassign slots by walking original part names is lost after join,
    # so callers should apply materials BEFORE join instead (see _tagged).
    return joined


def _tagged(parts):
    """Join after per-part materials were set; keep slot order."""
    out = None
    return out


def _build(name, gender, spec):
    """spec: list of (builder_fn, fabric_key). Returns joined outfit mesh."""
    lm = Landmarks(gender)
    parts = []
    for fn, key in spec:
        built = fn(lm)
        for ob in (built if isinstance(built, list) else [built]):
            ob.data.materials.clear()
            ob.data.materials.append(_m(name, key))
            parts.append(ob)
    joined = join(parts, name)
    keys = []
    for _, k in spec:
        if k not in keys:
            keys.append(k)
    joined.data.materials.clear()
    for k in keys:
        joined.data.materials.append(_m(name, k))
    # join keeps each face's original slot index only if slots were unique
    # objects; since we re-added fresh materials, fix slot indices below.
    smooth(joined)
    log("outfit %s (%s): tris=%d" % (name, gender, tris(joined)))
    return joined