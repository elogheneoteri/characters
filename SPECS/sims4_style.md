# Sims 4 Style — Headless Simulation Spec

No build artifacts will be created; this is a headless Sims 4 style spec.

This document defines a data-driven life simulation in the spirit of The Sims 4,
implemented headlessly (no renderer, no 3D pipeline). The prior box-primitive
Blender characters are intentionally deprecated as a game layer: they were a
modeling exercise, not a simulation. This spec defines the *behaviour* system
that would drive characters (Sims) on a lot, tick by tick, with a JSON
persistence format.

Design goals:

- Pure data + rules. Every state change is a transition in `tick()`.
- Deterministic given a seed and an input stream (replayable, testable).
- No 3D assets required to run; any future renderer consumes this state.

---

## Lot

A **Lot** is a self-contained playable area.

```json
{
  "id": "lot-001",
  "name": "Ogba Residence",
  "plot": { "width_m": 20, "depth_m": 20, "grid": 1.0 },
  "zones": [
    { "id": "kitchen", "type": "kitchen", "area": [2, 2, 6, 5] },
    { "id": "living",  "type": "living",  "area": [7, 2, 15, 10] },
    { "id": "bed1",    "type": "bedroom", "area": [11, 11, 18, 18] }
  ],
  "objects": [
    { "id": "obj-refrigerator", "type": "refrigerator", "zone": "kitchen",
      "pos": [3.5, 3.5, 0], "state": { "food_units": 8 } },
    { "id": "obj-bed-master",   "type": "bed",          "zone": "bed1",
      "pos": [14.5, 14.5, 0], "state": { "occupied_by": null } },
    { "id": "obj-sofa",         "type": "sofa",         "zone": "living",
      "pos": [11.0, 6.0, 0] }
  ],
  "clima": { "temperature_c": 28, "humidity": 70, "light": "day" },
  "sims_here": ["sim-ade", "sim-amara"]
}
```

Rules:

- Every `Sim` must be `on` a lot; a lot must be `exists` before Sims can act.
- Object types carry **affordances** (verb list), e.g. `refrigerator: [open, take_food,
  put_food, clean]`, `bed: [sleep, wake, make_bed]`, `toilet: [use, clean]`.
- Zones restrict which affordances are contextually valid (eating is valid in
  kitchen/dining, sleeping in bedroom).
- The lot owns the object *state* (food levels, mess, comfort) — Sims only
  read/write through affordances, never directly.

## Sim

A **Sim** is a persistent agent with a mood-driven brain.

```json
{
  "id": "sim-ade",
  "name": "Ade Okonkwo",
  "age": "young_adult",
  "traits": ["outgoing", "loves_food", "night_owl"],
  "skills": { "cooking": 3, "cleaning": 1, "fitness": 2, "charisma": 4 },
  "appearance": { "gender": "male", "height_cm": 178, "build": "athletic",
                  "hair": "coily_short", "skin_tone": "shade_6",
                  "outfit": "casual_sunday" },
  "moodlets": [
    { "id": "ml-01", "type": "full",        "intensity": 62, "until_tick": null },
    { "id": "ml-02", "type": "tired",       "intensity": 30, "until_tick": null },
    { "id": "ml-03", "type": "embarrassed", "intensity": 18, "until_tick": 4820 }
  ],
  "inventory": [ { "type": "food_item", "kind": "jollof", "freshness": 90 } ],
  "plumb": "PM 6:40",
  "on_lot": "lot-001",
  "current_task": { "verb": "sleep", "object_id": "obj-bed-master",
                    "started_tick": 4800, "steps": ["walk_to", "lie_down", "rest"] }
}
```

Rules:

- `traits` are fixed multipliers that bias need decay and moodlet gains (e.g.
  `loves_food` ×1.5 need-hunger gain, ×2.0 happiness from eating).
- `skills` grow only when the matching activity is completed; skill level is
  a 0–10 integer, each level adds +5% efficiency to that activity.
- One `current_task` at a time; tasks are sequences of steps with explicit
  fail/abort conditions. No parallel actions.
- `appearance` is *metadata only* — it renders nothing here, but is the exact
  contract a future Sims-4-style character system would consume (procedural
  rig + swappable outfit/hair slots, not hand-modeled meshes).
- Death/aging: at `age_threshold` ticks the Sim ages up; traits may be
  re-rolled per the aging table.

## Needs

Eight core needs, each 0–100, decay at per-tick rates modified by traits,
age, and lot climate.

| Need      | Base decay / 100s-ticks | Restored by            | Crisis at ≤ |
|-----------|------------------------|------------------------|-------------|
| Hunger    | 3.2                    | eat (obj: food source) | 15          |
| Energy    | 2.4                    | sleep (obj: bed)       | 10          |
| Social    | 1.8                    | interact (obj: Sim)    | 20          |
| Hygiene   | 2.1                    | shower/bath (obj)      | 15          |
| Bladder   | 2.9                    | use (obj: toilet)      | 10          |
| Fun       | 2.0                    | play/entertain (obj)   | 20          |
| Comfort   | 1.5                    | sit/lie (obj: sofa/bed)| 20          |
| Blameless | 0.8 (only if messy)    | clean (obj: anything)  | 10          |

Rules:

- Decay is a fixed-tick arithmetic op: `need -= base * trait_mult * climate_mult`.
  Climate: heat +10% hygiene decay; cold +10% comfort decay.
- When a need crosses its crisis threshold, a negative moodlet is added
  (`type = need_crisis_<name>`, `intensity = 25`, decays 5/tick).
- Moodlet → mood: overall mood = clamp(50 + Σ moodlet_intensity, 0, 100).
  Mood gates behaviour: `mood < 20` biases the task chooser toward
  self-care verbs (sleep, eat, clean) over social verbs.
- Needs are **derived state**: the only stored values are the eight floats;
  everything else (mood, task bias) is computed at each tick.

## Relationships

Directed, per-pair edges between Sims, stored on the Sim (owner → target).

```json
{
  "relationships": {
    "sim-amara": {
      "affinity": 74, "category": "close_friend",
      "history": [
        { "tick": 4120, "event": "positive_interact", "delta": +6 },
        { "tick": 4550, "event": "hug",               "delta": +10 }
      ],
      "conflict": null
    },
    "sim-chidi": {
      "affinity": -12, "category": "dislike",
      "conflict": { "id": "cf-01", "type": "stolen_food", "until_tick": 5200 }
    }
  }
}
```

Rules:

- `affinity` ∈ [-100, 100]; **category** is derived: `≥70 close_friend`,
  `≥30 friend`, `>0 acquaintance`, `≤-30 dislike`, `≤-70 rival`.
- Interaction deltas: hug +10, positive_interact +6, argument −15,
  steal −20 (and spawns a `conflict`), gift +8 (scales with gift value).
- Arguments only happen when `mood < 30` or a shared conflict is active.
- Conflicts expire by tick; while active, related Sims avoid the same zone
  (task chooser excludes the other's zone as a candidate).
- History is capped at the last 20 events per pair (ring buffer) to bound
  save size.
- Marriages: `affinity ≥ 90` unlocks `propose` verb; acceptance is a 2-tick
  resolving interaction with trait-based accept probability.

## Tick

The simulation advances in fixed **ticks**; 1 tick = 1 in-game minute.

```
tick(N):
  for each lot:
    clima = advance_clima(lot, N)          # day/night, temperature drift
    for each sim on lot:
      decay_needs(sim, clima)
      expire_moodlets(sim, N)
      recompute_mood(sim)
      resolve_current_task(sim, N)         # progress/complete/fail one step
      if no current_task:
        current_task = choose_task(sim, lot, N)
      age_up(sim, N) if threshold crossed
  for each lot:
    pair_pass(lot)                          # Social need + relationship deltas
    expire_conflicts(N)
  if N % 60 == 0:
    autosave(N)                             # see Save JSON
```

Rules:

- `choose_task` scores every valid affordance: `score = need_weight * mood_gate
  * trait_mult * randomness(seed, N, sim.id)`; highest score wins. Randomness
  is drawn from a PRNG seeded at lot creation — full determinism.
- `pair_pass` runs once per lot: each adjacent pair of Sims (same zone) has a
  social-interaction probability based on their `Social` need and traits
  (`outgoing` ×2). Interactions apply relationship deltas and Social recovery.
- Task steps advance at most one step per tick; total task time is the sum of
  per-verb durations (e.g. `sleep` = 300 ticks to full Energy).
- No tick may mutate state without also appending to the tick log
  (`tick_log.jsonl`: `{tick, sim_id, event, before, after}`) for replay/debug.
- Determinism contract: same seed + same input stream → byte-identical
  save at every autosave.

## Save JSON

Single-file save, versioned, atomic write (write temp + rename).

```json
{
  "save_version": "1.0",
  "format": "sims4_style_headless",
  "seed": 987654321,
  "current_tick": 4800,
  "plumb_time": "PM 6:40",
  "lots": [ /* full Lot objects as defined above */ ],
  "sims": [ /* full Sim objects as defined above */ ],
  "global": {
    "active_lot": "lot-001",
    "settings": { "tick_rate": 1, "pause_at_crisis": false }
  },
  "checksum": "sha256:<hex of everything above>"
}
```

Rules:

- **One source of truth**: the save is the entire world; the tick loop is a
  pure function `state(N) -> state(N+1)`.
- `checksum` is computed over the canonicalized JSON (sorted keys, no
  whitespace) of every field except `checksum` itself. Load validates it;
  mismatch = corrupted save, abort load with a clear error (never silently
  "recover").
- Versioning: loader is strict on `save_version` major; minor bumps must be
  backwards-compatible. Migration table lives next to the loader, not in
  the save.
- Autosave every 60 ticks (1 in-game hour); manual save on explicit command;
  save on graceful shutdown.
- Save size budget: ≤ 512 KB for 8 Sims / 3 lots. History ring buffers
  (relationships), capped tick-log retention (last 1000 lines kept
  in `tick_log.jsonl`, rotated), and object-state whitelisting keep it under.

---

## What this is *not*

- Not a renderer. No meshes, no Blender output, no FBX/OBJ.
- Not a character model spec. `Sim.appearance` is deliberately a flat
  metadata block so a future procedural-rig system can consume it without
  this spec ever touching geometry.
- Not a networked sim. Single process, single save file.