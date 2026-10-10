# -*- coding: utf-8 -*-
"""Body landmarks (Z-up, facing +Y) + low-poly body mesh builder."""
from .common import log, uv_sphere, tapered, box, join, smooth, tris, make_mat


class Landmarks:
    """Joint positions in meters. Z is up, character faces +Y."""

    def __init__(self, gender):
        if gender == "male":
            self.height = 1.72
            self.ankle_z = 0.085
            self.knee_z = 0.50
            self.hip_j_z = 0.92
            self.hip_j_x = 0.095
            self.pelvis_r = 0.16
            self.pelvis_scale = (1.0, 0.72, 0.58)
            self.waist_z = 1.04
            self.waist_r = 0.135
            self.chest_z = 1.24
            self.chest_r = 0.185
            self.shoulder_z = 1.40
            self.shoulder_j_x = 0.175
            self.shoulder_cap_x = 0.19
            self.neck_base_z = 1.42
            self.neck_top_z = 1.49
            self.neck_r = 0.052
            self.head_c = (0.0, 0.005, 1.585)
            self.head_r = 0.105
            self.head_scale = (0.92, 1.02, 1.08)
            self.elbow_x = 0.395
            self.wrist_x = 0.565
            self.hand_tip_x = 0.69
            self.arm_r1 = 0.055
            self.arm_r2 = 0.047
            self.thigh_r1 = 0.085
            self.thigh_r2 = 0.062
            self.calf_r = 0.058
            self.ankle_r = 0.042
            self.knee_x = 0.10
            self.foot_l = 0.17
            self.foot_w = 0.055
            self.breast = 0.0
        else:
            self.height = 1.64
            self.ankle_z = 0.08
            self.knee_z = 0.47
            self.hip_j_z = 0.86
            self.hip_j_x = 0.09
            self.pelvis_r = 0.15
            self.pelvis_scale = (1.12, 0.74, 0.60)
            self.waist_z = 0.99
            self.waist_r = 0.115
            self.chest_z = 1.18
            self.chest_r = 0.155
            self.shoulder_z = 1.32
            self.shoulder_j_x = 0.145
            self.shoulder_cap_x = 0.155
            self.neck_base_z = 1.34
            self.neck_top_z = 1.41
            self.neck_r = 0.045
            self.head_c = (0.0, 0.004, 1.50)
            self.head_r = 0.10
            self.head_scale = (0.90, 1.00, 1.07)
            self.elbow_x = 0.36
            self.wrist_x = 0.515
            self.hand_tip_x = 0.625
            self.arm_r1 = 0.047
            self.arm_r2 = 0.040
            self.thigh_r1 = 0.078
            self.thigh_r2 = 0.057
            self.calf_r = 0.050
            self.ankle_r = 0.038
            self.knee_x = 0.095
            self.foot_l = 0.155
            self.foot_w = 0.050
            self.breast = 0.028


def head_center(lm):
    return lm.head_c


def build_body(name, gender, skin_rgb):
    """Build a full low-poly body in T-pose. Returns the joined mesh object."""
    lm = Landmarks(gender)
    skin_mat = make_mat(name + "_skin", skin_rgb)
    parts = []

    # pelvis + torso
    parts.append(uv_sphere("%s_pelvis_%s" % (name, gender),
                           (0.0, 0.0, (lm.hip_j_z + lm.waist_z) * 0.5),
                           lm.pelvis_r, seg=14, ring=9, scale=lm.pelvis_scale))
    parts.append(tapered("%s_torso_%s" % (name, gender),
                         (0.0, 0.0, lm.waist_z),
                         (0.0, 0.0, lm.chest_z),
                         lm.waist_r, lm.chest_r, verts=14, zq=0.82))
    parts.append(uv_sphere("%s_chest_%s" % (name, gender),
                           (0.0, 0.0, lm.chest_z + 0.02),
                           lm.chest_r, seg=14, ring=9, scale=(1.0, 0.80, 0.92)))
    if lm.breast > 0.0:
        for sx in (-1, 1):
            parts.append(uv_sphere("%s_breast_%s_%d" % (name, gender, sx),
                                   (sx * 0.062, lm.chest_r * 0.55, lm.chest_z - 0.015),
                                   0.045, seg=10, ring=6))

    # neck + head
    parts.append(tapered("%s_neck_%s" % (name, gender),
                         (0.0, 0.0, lm.neck_base_z),
                         (0.0, 0.0, lm.neck_top_z),
                         lm.neck_r, lm.neck_r * 0.85, verts=10))
    parts.append(uv_sphere("%s_head_%s" % (name, gender),
                           lm.head_c, lm.head_r, seg=18, ring=12,
                           scale=lm.head_scale))

    # arms (T-pose: extended along +X/-X)
    for sx in (-1, 1):
        tag = "L" if sx < 0 else "R"
        sJ = (sx * lm.shoulder_j_x, 0.0, lm.shoulder_z)
        eJ = (sx * lm.elbow_x, 0.0, lm.shoulder_z)
        wJ = (sx * lm.wrist_x, 0.0, lm.shoulder_z)
        parts.append(uv_sphere("%s_shoulder_%s_%s" % (name, tag, gender),
                               (sx * lm.shoulder_cap_x, 0.0, lm.shoulder_z),
                               lm.arm_r1 * 1.25, seg=10, ring=6))
        parts.append(tapered("%s_uparm_%s_%s" % (name, tag, gender),
                             sJ, eJ, lm.arm_r1, lm.arm_r1 * 0.9, verts=10))
        parts.append(tapered("%s_forearm_%s_%s" % (name, tag, gender),
                             eJ, wJ, lm.arm_r2 * 0.95, lm.arm_r2, verts=10))
        parts.append(box("%s_hand_%s_%s" % (name, tag, gender),
                         (sx * (lm.wrist_x + 0.055), 0.0, lm.shoulder_z - 0.01),
                         (0.095, 0.115, 0.026)))
        parts.append(uv_sphere("%s_thumb_%s_%s" % (name, tag, gender),
                               (sx * (lm.wrist_x + 0.045), 0.05, lm.shoulder_z - 0.01),
                               0.016, seg=8, ring=5))

    # legs + feet
    for sx in (-1, 1):
        tag = "L" if sx < 0 else "R"
        hJ = (sx * lm.hip_j_x, 0.0, lm.hip_j_z)
        kJ = (sx * lm.knee_x, 0.015, lm.knee_z)
        aJ = (sx * lm.knee_x, 0.015, lm.ankle_z)
        parts.append(uv_sphere("%s_glute_%s_%s" % (name, tag, gender), hJ,
                               lm.thigh_r1 * 1.15, seg=10, ring=6))
        parts.append(tapered("%s_thigh_%s_%s" % (name, tag, gender),
                             hJ, kJ, lm.thigh_r1, lm.thigh_r2, verts=10))
        parts.append(tapered("%s_calf_%s_%s" % (name, tag, gender),
                             kJ, aJ, lm.calf_r, lm.ankle_r, verts=10))
        # foot: heel box + toe box (toes point +Y, facing forward)
        parts.append(box("%s_foot_%s_%s" % (name, tag, gender),
                         (sx * lm.knee_x, 0.02, 0.045),
                         (lm.foot_w * 2, 0.09, 0.105)))
        parts.append(box("%s_toe_%s_%s" % (name, tag, gender),
                         (sx * lm.knee_x, 0.055 + lm.foot_l * 0.55, 0.035),
                         (lm.foot_w * 1.9, 0.07, lm.foot_l * 0.45)))

    body = join(parts, name + "_body")
    body.data.materials.clear()
    body.data.materials.append(skin_mat)
    smooth(body)
    log("body %s: tris=%d" % (name, tris(body)))
    return body