# -*- coding: utf-8 -*-
"""Mixamo-compatible T-pose armature + auto skin weights.

Bone names/hierarchy follow Mixamo so the exported FBX can be re-rigged or
re-used by any Mixamo pipeline. Character faces +Y, Z is up (Blender native);
the rig is built in world space so a T-pose mesh exported as-is matches.
"""
import bpy
import bmesh
import math

from .common import log, get_ob, tris
from .body import Landmarks

# ---------------------------------------------------------------------------
# Bone layout: (name, head (world xyz), parent, use_connect)
# Head/tail computed from Landmarks so every part is weighted correctly.
# ---------------------------------------------------------------------------

def _build_bone_map(lm):
    """Return an ordered list of (name, head, tail, parent, connect)."""
    S = lm.shoulder_z
    W = lm.waist_z
    H = lm.hip_j_z
    K = lm.knee_z
    A = lm.ankle_z
    nx = lm.knee_x

    hip_l = (-lm.hip_j_x, 0.0, H)
    hip_r = (lm.hip_j_x, 0.0, H)
    sp1 = (0.0, 0.0, W)
    sp2 = (0.0, 0.0, (W + S) * 0.5)
    neck_b = (0.0, 0.0, lm.neck_base_z)
    neck_t = (0.0, 0.0, lm.neck_top_z)
    head_c = lm.head_c
    head_t = (head_c[0], head_c[1] + lm.head_r * 0.9,
              head_c[2] + lm.head_r * 1.35)

    bones = []
    bones.append(("Hips", (0.0, 0.0, H), None, False))
    bones.append(("Spine", sp1, "Hips", False))
    bones.append(("Spine1", (0.0, 0.0, (W + S) * 0.35), "Spine", True))
    bones.append(("Spine2", sp2, "Spine1", True))
    bones.append(("Neck", neck_b, "Spine2", False))
    bones.append(("Head", neck_t, "Neck", True))

    # Torso -> shoulders -> arms (T-pose along +X / -X)
    for side, sx in (("Left", -1), ("Right", 1)):
        sh_head = (sx * 0.02, 0.0, S)
        sh_tail = (sx * lm.shoulder_j_x, 0.0, S)
        bones.append(("%sShoulder" % side, sh_head, "Spine2", False))
        arm_head = (sx * lm.shoulder_j_x, 0.0, S)
        arm_tail = (sx * lm.elbow_x, 0.0, S)
        bones.append(("%sArm" % side, arm_head, "%sShoulder" % side, True))
        fa_head = (sx * lm.elbow_x, 0.0, S)
        fa_tail = (sx * lm.wrist_x, 0.0, S)
        bones.append(("%sForeArm" % side, fa_head, "%sArm" % side, True))
        hand_head = (sx * lm.wrist_x, 0.0, S)
        hand_tail = (sx * (lm.wrist_x + 0.055), 0.0, S)
        bones.append(("%sHand" % side, hand_head, "%sForeArm" % side, True))
        # Fingers: short stubs past the hand for Mixamo name compatibility.
        hx = sx * (lm.wrist_x + 0.055)
        hx2 = sx * (lm.wrist_x + 0.10)
        bones.append(("%sHandThumb1" % side,
                      (hx, 0.02, S - 0.01), "%sHand" % side, False))
        for name, dy in (("Index", 0.028), ("Middle", 0.014),
                        ("Ring", 0.0), ("Pinky", -0.028)):
            bones.append(("%sHand%s1" % (side, name),
                          (hx, dy, S), "%sHand" % side, False))

    # Legs
    for side, sx in (("Left", -1), ("Right", 1)):
        up_head = (sx * lm.hip_j_x, 0.0, H)
        up_tail = (sx * nx, 0.015, K)
        bones.append(("%sUpLeg" % side, up_head, "Hips", False))
        bones.append(("%sLeg" % side, up_tail, "%sUpLeg" % side, True))
        foot_head = (sx * nx, 0.015, A)
        foot_tail = (sx * nx, 0.015 + 0.06, A)
        bones.append(("%sFoot" % side, foot_head, "%sLeg" % side, True))
        toe_head = (sx * nx, 0.015 + 0.06, A)
        toe_tail = (sx * nx, 0.015 + 0.06 + lm.foot_l * 0.7, A)
        bones.append(("%sToes" % side, toe_head, "%sFoot" % side, True))

    return bones


def _create_armature(name, lm):
    """Create the Mixamo armature in world space and return it."""
    bones = _build_bone_map(lm)
    bpy.ops.object.armature_add(location=(0.0, 0.0, 0.0))
    arm = bpy.context.active_object
    arm.name = name
    arm.data.name = name + "_Armature"
    bpy.ops.object.mode_set(mode="EDIT")
    ed = arm.data.edit_bones
    created = {}
    for (bn, head, parent, _conn) in bones:
        b = ed.new(bn)
        b.head = head
        # Set a reasonable tail from the next bone head when possible.
        b.tail = _default_tail(bn, head, bones, created)
        if parent is not None and parent in created:
            b.parent = created[parent]
            b.use_connect = _conn_of(bn, bones)
        created[bn] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.data.display_type = "WIRE"
    return arm, bones


def _default_tail(bn, head, bones, created):
    """Pick a tail for a bone: use child head if known else a small offset."""
    for (cn, chead, parent, _c) in bones:
        if parent == bn:
            return chead
    # No children: nudge tail forward along a sensible axis.
    if "Toes" in bn or "Foot" in bn:
        return (head[0], head[1] + 0.08, head[2])
    if "Hand" in bn and "Thumb" not in bn and "Index" not in bn \
            and "Middle" not in bn and "Ring" not in bn and "Pinky" not in bn:
        return (head[0] * 1.06, head[1], head[2])
    if "Head" == bn:
        return (head[0], head[1] + 0.1, head[2] + 0.15)
    return (head[0] * 1.05, head[1], head[2])


def _conn_of(bn, bones):
    for (cn, _h, parent, conn) in bones:
        if cn == bn:
            return conn
    return False


def _enforce_tpose(arm):
    """Explicitly set a canonical T-pose so the rig is flat/rotated=0."""
    # Bones are already placed in world space with no parent rotations, which
    # IS a T-pose. Reset any residual rotation to be safe.
    for b in arm.pose.bones:
        b.rotation_mode = "XYZ"
        b.rotation_euler = (0.0, 0.0, 0.0)
        b.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        b.location = (0.0, 0.0, 0.0)


def bind(name, lm, meshes):
    """Create armature for `lm`, parent `meshes` with auto weights.

    Returns the armature object. Each mesh is parented to the armature and
    weighted to the nearest bones via Blender's auto weights.
    """
    reset = bpy.data.objects.get(name + "_Armature")
    if reset is not None:
        bpy.data.objects.remove(reset, do_unlink=True)

    arm, _bones = _create_armature(name + "_Armature", lm)
    _enforce_tpose(arm)

    for ob in meshes:
        ob.select_set(False)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        try:
            bpy.ops.object.parent_set(
                type="ARMATURE_AUTO", keep_transform=True)
        except TypeError:
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    log("rig %s: %d bones bound to %d mesh(es)"
        % (name, len(arm.data.bones), len(meshes)))
    return arm