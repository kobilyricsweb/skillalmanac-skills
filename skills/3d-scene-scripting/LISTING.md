# Listing page content: 3d-scene-scripting

**One line:** Helps an agent script Blender or three.js scenes that render right the first time, with a scene validator.

## What it does

The skill makes the agent write a scene contract (units, up axis, ground level, origin rule) and a scene description JSON before any Blender or three.js code. A standard-library script checks that description for missing camera or light, objects below the ground, non-uniform scale on rigid bodies, duplicate names, undefined or unreferenced materials, and a camera that sees no object (vector math, including the Blender and three.js Euler-order difference). The body adds naming rules, materials found by node type, a camera focal-length table, lighting ratios, render settings by purpose, a thumbnail verification loop with a symptom-to-cause table, and a portability table between Blender, three.js and glTF. Details it cannot vouch for are marked `verify (unconfirmed)`.

## Capabilities

- `scripts/scene_check.py`: strict JSON report of errors and warnings with rule names, exit 0 / 1 / 2
- Camera presets from 24 mm to 135 mm with horizontal and vertical field of view, and a framing-distance formula
- Render settings decision table (layout check, look check, final still, CPU-only, animation)
- Black / blown out / tiny / floating / pink-surface diagnosis table for the thumbnail step
- A fixed report: contract, validator result, script assumptions, render rounds, not checked

## When to use

You ask an agent to script, generate or repair a 3D scene (bpy script, three.js scene, product shot) or say the render is black, tiny, floating, cut off or the camera points the wrong way.

## When not to use

Hand modelling or sculpting, rigging and animation, game-engine editor work, CAD, or 3D print slicing. For images from text prompts see the image prompt skills; for 2D video from code see `programmatic-video`.

## Requirements

Python 3.9 or newer for the validator (standard library only, no network). Blender or a three.js runtime is needed by the user to render; the skill does not install or run either.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real fixture runs (`python scripts/scene_check.py evals/fixtures/<file>`):

1. `scene_good.json` (Z-up, Blender default-style camera): `ok: true`, 0 errors, 0 warnings, exit 0.
2. `scene_bad_many.json`: `ok: false`, 5 errors and 2 warnings, exit 1. Errors in order: `below-ground` (Crate_01, lowest point -0.3), `camera-aim` (camera uses the three.js Euler convention with Blender angles, so no object is in view), `material-undefined` (Mat_Metal), `name-duplicate` (Crate_01 used twice), `nonuniform-scale-rigid` (scale 1, 2, 1). Warnings: `light-energy` (energy 0) and `material-unreferenced` (Mat_Unused).

No with-skill agent run exists yet, so there is no saved end-to-end transcript.

## Limits

- The validator checks a description, not a live scene: no parent hierarchy, rotated bounds, occlusion or textures.
- The aim check is a bounding-sphere cone test.
- Camera and light numbers are starting values, not measured optima.
- API details vary by version; items marked `verify (unconfirmed)` are not vouched for.

## Evidence

See `VERIFICATION.md`. Passed: static lint, 7 script fixture cases. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool install, a real Blender or three.js render, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Prompt: "script a product shot of a bottle". The agent states the contract first.
2. It writes the scene JSON and runs `scene_check.py`; the output shows one error (object below ground).
3. It fixes the value, re-runs: `ok: true`, then generates the Blender script.
4. It renders a thumbnail, runs the symptom table, reports what was not checked.

## FAQ seeds

- Does it need network? No.
- Does it run Blender? No; it generates scripts and validates a description. Rendering happens on your install.
- Does it work with a live Blender connector? The viewport image can serve as the thumbnail, if you have one.
- How does it differ from `programmatic-video`? That skill is 2D, timeline and captions; this one is 3D scene setup and verification.
- Why `verify (unconfirmed)`? Blender and three.js names change between releases; the skill says so instead of guessing.
- What does the validator not catch? Occlusion, hierarchy, rotated bounds, texture problems.
- How do I uninstall? Delete the skill folder.

## Changelog

- 0.1.0, 2026-11-21: first draft. Static and fixture checks only.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
