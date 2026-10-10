# -*- coding: utf-8 -*-
"""Six unique faces. Each face is a set of small low-poly parts placed on the
head using Landmarks, so it follows the head automatically."""
from .common import log, uv_sphere, box, join, tris


# Per-face parameter table.
# nose: (length, width, height), brow: (width, thickness, height),
# mouth: (width, thickness), lips: fullness scale, jaw: chin width scale,
# ear: ear size scale
FACE_PARAMS = [
    {  # 0 — round, soft
        "nose": (0.020, 0.014, 0.016), "brow": (0.030, 0.005, 0.004),
        "mouth": (0.034, 0.006), "lips": 1.0, "jaw": 1.0, "ear": 1.0,
        "eye_y": 0.85, "eye_z": 0.020,
    },
    {  # 1 — strong jaw, short nose, wide mouth
        "nose": (0.016, 0.018, 0.014), "brow": (0.034, 0.007, 0.005),
        "mouth": (0.042, 0.007), "lips": 1.25, "jaw": 1.22, "ear": 1.05,
        "eye_y": 0.83, "eye_z": 0.018,
    },
    {  # 2 — long nose, narrow mouth
        "nose": (0.028, 0.011, 0.013), "brow": (0.030, 0.005, 0.004),
        "mouth": (0.026, 0.005), "lips": 0.85, "jaw": 0.95, "ear": 0.9,
        "eye_y": 0.86, "eye_z": 0.022,
    },
    {  # 3 — full lips, wide brows, softer jaw
        "nose": (0.018, 0.015, 0.015), "brow": (0.032, 0.006, 0.005),
        "mouth": (0.038, 0.008), "lips": 1.45, "jaw": 0.98, "ear": 1.0,
        "eye_y": 0.84, "eye_z": 0.020,
    },
    {  # 4 — angular: thin mouth, heavy brows
        "nose": (0.022, 0.012, 0.015), "brow": (0.036, 0.008, 0.006),
        "mouth": (0.030, 0.005), "lips": 0.80, "jaw": 1.15, "ear": 0.85,
        "eye_y": 0.85, "eye_z": 0.019,
    },
    {  # 5 — balanced: medium nose, medium mouth
        "nose": (0.022, 0.014, 0.014), "brow": (0.031, 0.006, 0.004),
        "mouth": (0.035, 0.006), "lips": 1.1, "jaw": 1.05, "ear": 1.0,
        "eye_y": 0.85, "eye_z": 0.020,
    },
]

EYE_WHITE = (0.90, 0.90, 0.88)
EYE_PUPIL = (0.10, 0.06, 0.04)
LIP = (0.35, 0.16, 0.12)
BROW = (0.12, 0.07, 0.04)
SKIN_FALLBACK = (0.42, 0.25, 0.14)


def build_face(name, head_c, head_r, idx, mat_fn, skin=None):
    """Build face parts for head centred at head_c with radius head_r.

    mat_fn(color) -> material. `skin` colors the nose/jaw/ears so they match
    the head (falls back to a neutral brown). Returns a single joined object
    (or None if parts end up empty)."""
    p = FACE_PARAMS[idx]
    hz = head_c[2]
    hy = head_c[1]
    ry = head_r * p["eye_y"]      # forward offset factor for eye line
    ey = hy + ry                  # eye front position (y)
    parts = []

    # Eyes: white sphere + pupil (slightly forward)
    for sx in (-1, 1):
        tag = "L" if sx < 0 else "R"
        ex = sx * head_r * 0.38
        parts.append(uv_sphere("%s_eye_white_%s" % (name, tag),
                               (ex, ey - 0.004, hz + head_r * p["eye_z"]),
                               head_r * 0.10, seg=8, ring=5))
        parts.append(uv_sphere("%s_eye_pupil_%s" % (name, tag),
                               (ex, ey + 0.004, hz + head_r * p["eye_z"]),
                               head_r * 0.045, seg=8, ring=5))

    # Brows
    for sx in (-1, 1):
        tag = "L" if sx < 0 else "R"
        parts.append(box("%s_brow_%s" % (name, tag),
                         (sx * head_r * 0.36, ey + 0.002,
                          hz + head_r * (p["eye_z"] + 0.14)),
                         (p["brow"][0], p["brow"][1], p["brow"][2])))

    # Nose: small tapered cone pointing +Y (forward)
    nz = hz - head_r * 0.02
    parts.append(uv_sphere("%s_nose" % name,
                           (0.0, hy + head_r * 0.92, nz),
                           p["nose"][0], seg=8, ring=5,
                           scale=(p["nose"][1] / p["nose"][0],
                                  1.0, p["nose"][2] / p["nose"][0])))

    # Mouth / lips: thin box
    parts.append(box("%s_mouth" % name,
                     (0.0, hy + head_r * 0.86, hz - head_r * 0.42),
                     (p["mouth"][0], p["mouth"][1] * p["lips"],
                      p["mouth"][1] * 1.6 * p["lips"])))

    # Chin: widens/narrows the lower face
    jaw_w = head_r * 0.55 * p["jaw"]
    parts.append(uv_sphere("%s_jaw" % name,
                           (0.0, hy + head_r * 0.28, hz - head_r * 0.62),
                           jaw_w, seg=10, ring=6,
                           scale=(1.0, 0.85, 0.6)))

    # Ears
    for sx in (-1, 1):
        tag = "L" if sx < 0 else "R"
        parts.append(uv_sphere("%s_ear_%s" % (name, tag),
                               (sx * head_r * 0.95, hy - head_r * 0.02,
                                hz - head_r * 0.02),
                               head_r * 0.14 * p["ear"], seg=8, ring=5,
                               scale=(0.45, 0.85, 1.0)))

    skin = skin or SKIN_FALLBACK
    m_skin = mat_fn(skin)
    m_lip = mat_fn(LIP)
    m_brow = mat_fn(BROW)
    m_white = mat_fn(EYE_WHITE)
    m_pupil = mat_fn(EYE_PUPIL)
    for ob in parts:
        if "eye_pupil" in ob.name:
            m = m_pupil
        elif "eye_white" in ob.name:
            m = m_white
        elif "brow" in ob.name:
            m = m_brow
        elif "mouth" in ob.name:
            m = m_lip
        else:  # nose, jaw, ears
            m = m_skin
        ob.data.materials.clear()
        ob.data.materials.append(m)

    face = join(parts, name + "_face")
    log("face %s (variant %d): tris=%d" % (name, idx, tris(face)))
    return face