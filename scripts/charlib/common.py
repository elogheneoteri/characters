# -*- coding: utf-8 -*-
"""Shared helpers: scene reset, materials, primitives, join/evaluate.

Coordinate convention (Blender native): Z-up, character faces +Y.
"""
import mathutils
import bpy

# ---------------------------------------------------------------------------
# Scene / logging
# ---------------------------------------------------------------------------


def log(msg):
    print("[make_assets] " + msg)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def get_ob(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        raise KeyError("object %r not found" % name)
    return ob


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------


def make_mat(name, rgb, rough=0.75, metallic=0.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf is not None:
            bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Metallic"].default_value = metallic
    return m


# ---------------------------------------------------------------------------
# Primitives (single objects; joined + rigged later)
# ---------------------------------------------------------------------------


def uv_sphere(name, center, radius, seg=16, ring=10, scale=(1.0, 1.0, 1.0)):
    bpy.ops.mesh.primitive_uv_sphere_add(
        location=tuple(center), radius=radius, segments=seg, ring_count=ring
    )
    ob = bpy.context.active_object
    ob.name = name
    if tuple(scale) != (1.0, 1.0, 1.0):
        ob.scale = tuple(scale)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


def tapered(name, p1, p2, r1, r2, verts=12, cap=True, zq=None):
    """Cone from p1 (radius r1) to p2 (radius r2), axis along p1->p2.

    Blender's primitive cone has its axis on local Z, so track Z onto the
    direction vector.
    """
    p1 = mathutils.Vector(p1)
    p2 = mathutils.Vector(p2)
    d = p2 - p1
    mid = (p1 + p2) / 2.0
    bpy.ops.mesh.primitive_cone_add(
        location=tuple(mid),
        radius1=r1,
        radius2=r2,
        depth=1.0,
        end_fill_type="NGON" if cap else "NOTHING",
        vertices=verts,
    )
    ob = bpy.context.active_object
    ob.name = name
    if d.length > 0:
        quat = d.to_track_quat("Z", "Y")
        ob.rotation_euler = quat.to_euler()
        ob.scale = (1.0, 1.0, d.length)
        if zq is not None:
            ob.scale = (ob.scale[0] * zq, ob.scale[1] * zq, ob.scale[2])
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return ob


def box(name, center, size, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(location=tuple(center), size=1.0)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = tuple(size)
    if tuple(rot) != (0.0, 0.0, 0.0):
        ob.rotation_euler = tuple(rot)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.select_all(action="DESELECT")
    return ob


def smooth(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.shade_smooth()


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)