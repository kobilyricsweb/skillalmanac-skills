---
name: 3d-scene-scripting
description: Plans and scripts 3D scenes in Blender Python or three.js so they render correctly the first time, using a scene contract (units, up axis, scale, origin), naming rules, materials found by node type, camera and lighting presets, render settings by purpose, a render-thumbnail verification loop and a script that validates a scene description JSON. Use when the user asks to script, generate or fix a 3D scene, product shot, bpy script or three.js scene, or says the render is black, tiny, upside down, floating or cut off. Do not use for sculpting or character modelling by hand, game-engine editor workflows, CAD, or 3D printing slicing.
license: Apache-2.0
compatibility: The validator needs Python 3.9 or newer, standard library only, no network. Blender and three.js code is generated for the user's own install and is not run by this skill. Without Python, walk the checklist in step 3 by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# 3D scene scripting

Most failed first renders come from five causes: a missing light or camera, wrong units, a camera aimed at nothing, an object below or floating off the ground, and scale applied the wrong way. Fix those in a plain description before writing any tool-specific code.

## Workflow

```
- [ ] 1 Write the scene contract
- [ ] 2 Write the scene description JSON
- [ ] 3 Run scripts/scene_check.py until ok is true
- [ ] 4 Generate the tool script (Blender or three.js)
- [ ] 5 Render a thumbnail and run the thumbnail checks
- [ ] 6 Report
```

1. **Scene contract.** Decide and write down four things before any object exists: units (default meters), up axis (Blender Z, three.js and glTF Y), ground level (default 0 on the up axis) and origin rule (default: each object's origin at its center, except ground and walls, at their base). Never mix units inside one scene. If the user supplies assets in other units, convert at import, not by scaling in the scene.
2. **Scene description.** Build one JSON file (shape below). It is the single source for the tool script, so the two cannot disagree.
3. **Check.** Run `python scripts/scene_check.py scene.json`. Fix every `error`; read each `warning`. Run the script; do not edit it to make a check pass.
4. **Generate.** Write the tool script from the JSON. Use the rules in the sections below. Anything in [references/api_notes.md](references/api_notes.md) marked `verify (unconfirmed)` must be checked against the user's installed version before it is relied on: read the enum, print the attribute, or run a one-line probe.
5. **Render and look.** Follow the verification loop below. Maximum 3 render rounds; change one thing per round and say what.
6. **Report** in the fixed shape at the end.

## Scene description JSON

```json
{
  "units": "meters", "up_axis": "Z", "ground_level": 0.0,
  "objects": [{"name": "Mesh_Crate_01", "type": "mesh", "location": [0,0,0.5],
               "scale": [1,1,1], "dimensions": [1,1,1], "origin": "center",
               "rigid_body": true, "material": "Mat_Wood"}],
  "materials": [{"name": "Mat_Wood", "shader": "principled"}],
  "lights": [{"name": "Light_Key", "type": "area", "location": [3,-3,4], "energy": 200}],
  "camera": {"name": "Cam_Main", "location": [7,-7,5], "fov_deg": 40,
             "target": [0,0,0.5]}
}
```

All transforms are world space. `dimensions` is the final size along the world axes with scale included (the same meaning as Blender's `obj.dimensions`). The camera takes either `target`, or `rotation_euler_deg` with `euler_order` and `euler_convention` (`blender` or `three`). Omit `role` for normal objects; use `"ground"` for floors, which are exempt from the ground and aim checks.

## Validator output contract

`scripts/scene_check.py` prints one strict JSON object (no NaN, ASCII only):

```json
{"command": "validate", "ok": false, "errors": 2, "warnings": 1, "objects": 4,
 "findings": [{"severity": "error", "rule": "below-ground",
               "subject": "Crate_01", "message": "..."}]}
```

Exit 0: no errors (warnings allowed). Exit 1: at least one error. Exit 2: file missing, empty, not JSON, or not an object (plain message on stderr). Findings are sorted errors first, then by rule and subject.

| Rule | Severity | Meaning |
|---|---|---|
| `contract-units`, `contract-up-axis`, `contract-ground` | error | contract field missing or invalid |
| `camera-missing`, `light-missing` | error | nothing to render with |
| `camera-fov` | error | `fov_deg` outside 1 to 170 |
| `camera-aim`, `camera-degenerate` | error | no object inside the view cone, rotation fields unusable, or camera sits on its target |
| `below-ground` | error | lowest point lies under `ground_level` by more than 0.001 |
| `nonuniform-scale-rigid` | error | rigid body whose scale axes differ by more than 0.1 percent |
| `name-duplicate`, `name-missing` | error | name reused across objects, lights, camera (or materials), or absent |
| `material-undefined` | error | an object names a material that is not listed |
| `scale-zero` | error | a scale axis is 0 |
| `vector-shape` | error | a vector is not three finite numbers |
| `material-unreferenced`, `light-energy`, `scale-negative`, `name-case-collision` | warning | harmless alone, usually a leftover or a trap |

The aim check treats each object as a sphere of half its dimension diagonal and asks whether any of it enters a cone of half-angle `fov_deg / 2` around the camera forward axis. It does not test occlusion or aspect ratio.

## Naming

- Pattern `<Kind>_<Role>_<NN>`: `Mesh_Crate_01`, `Mat_Wood`, `Light_Key`, `Cam_Main`, `Empty_Rig`. Kinds: Mesh, Mat, Light, Cam, Empty, Col (collection).
- Names are unique across objects, lights and cameras together. Blender appends `.001` to a clash and returns the renamed object, so a script that looks the object up by its intended name later gets the wrong one. Keep the object reference in a variable; look up by name only once.
- ASCII, no spaces, no differences only in case (collisions on case-insensitive disks and in exports).
- Name length limits differ by tool and version: verify (unconfirmed) for the user's install; keep names under 40 characters to be safe.

## Materials

- Find shader nodes by `node.type`, never by node name or label, because names are localized and renamed: `next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")`. Types used here: `BSDF_PRINCIPLED`, `OUTPUT_MATERIAL`, `TEX_IMAGE`, `EMISSION`, `MIX_SHADER`, `TEX_ENVIRONMENT`, `BACKGROUND`.
- Put color on the shader's input sockets. `material.diffuse_color` only changes the viewport.
- Create the material, set `use_nodes = True` only if the version still needs it (verify (unconfirmed): newer versions create nodes by default and may deprecate the flag), then fetch the Principled node by type.
- Principled input names changed between 3.x and 4.x (emission, specular, subsurface, transmission sockets). Use `node.inputs.get("Name")` with a fallback list and skip with a printed warning if none exists, rather than raising.
- One material per surface kind, shared across objects. Do not make a new material per object unless the color differs.
- For portability keep to the PBR metallic-roughness set: base color, metallic, roughness, normal, emission. Anything else (clearcoat, sheen, subsurface) will not survive a glTF round trip to every viewer.

## Primitive sizes that surprise

| Call | Default size | Trap |
|---|---|---|
| Blender cube add | `size=2` (edge 2 m) | a "1 m crate" needs `size=1` or scale 0.5 applied |
| Blender plane add | `size=2` | same |
| Blender UV sphere add | `radius=1` (diameter 2 m) | |
| Blender cylinder add | `radius=1, depth=2` | |
| three.js `BoxGeometry(1,1,1)` | edge 1 | origin at center; base at y = height / 2 |
| three.js `PlaneGeometry` | faces +Z | rotate -90 degrees about X to lie flat on a Y-up ground |

To rest an object on the ground, compute its lowest world-space point from its bounding box corners and offset by the difference. Do not guess half-heights. After setting a non-uniform scale on anything that will be physics-simulated or parented under a rotated parent, apply the scale (`bpy.ops.object.transform_apply(scale=True)`) before adding the rigid body.

## Camera presets

Focal length to field of view: `fov = 2 * atan(sensor / (2 * focal))`, on a 36 mm sensor width. three.js takes the vertical angle; Blender's default sensor fit uses the larger image dimension.

| Look | Focal (36 mm) | Horizontal FOV | Vertical at 16:9 (three.js `fov`) | Use |
|---|---|---|---|---|
| Wide interior | 24 mm | 73.7 deg | 45.7 deg | rooms, environments |
| Natural | 35 mm | 54.4 deg | 32.3 deg | general scenes |
| Standard | 50 mm | 39.6 deg | 22.9 deg | default hero shot |
| Product | 85 mm | 23.9 deg | 13.6 deg | single objects, less distortion |
| Tight detail | 135 mm | 15.2 deg | 8.6 deg | small items |

Placement: azimuth 35 to 45 degrees off the object's front, elevation 20 to 30 degrees for a three-quarter hero view; elevation 0 for a front elevation; 90 for a plan view. Distance that frames a subject with a 15 percent margin: `d = 1.15 * R / sin(min(hfov, vfov) / 2)`, where `R` is half the subject's bounding-box diagonal and angles are for the actual output aspect. Set clip start to no more than d / 100 and clip end to at least 3 * d (Blender's default far clip may be smaller than a large scene: verify (unconfirmed)).

Aim with a look-at, not hand-typed Euler angles. In Blender add a Track To constraint on the camera (target the subject, track axis negative Z, up axis Y). In three.js call `camera.lookAt(target)`. If Euler angles are unavoidable, note that the same letters `XYZ` build different matrices in Blender (last letter leftmost) and three.js (first letter leftmost); the validator needs `euler_convention` for this reason.

## Lighting presets

These are starting ratios, not measured optima. Judge on the thumbnail.

| Preset | Setup | Starting values |
|---|---|---|
| Three-point | Key 45 deg to one side of the camera and 30 to 45 deg up; fill opposite side, low; rim behind and above the subject | fill at 25 to 50 percent of key; rim equal to key; key:fill ratio 2:1 to 4:1 |
| Soft product | One large area light above and in front, white or light-grey ground | area size about 1.5 times the subject width; sun-free |
| Outdoor | One sun light plus sky or environment lighting | sun elevation 35 to 55 deg; Blender sun strength starts near 3; three.js directional intensity starts near 2 (both verify (unconfirmed) for the installed version) |
| Flat check | Even environment light only | for debugging materials and layout |

Light units differ by tool: Blender sun in watts per square meter and others in watts; three.js point and spot lights in candela under its physical lighting rules (verify (unconfirmed) per release), with directional and ambient intensity on a scale of their own. Do not copy a number across tools; copy the ratio and re-judge exposure. Every scene needs at least one light and, when the background is not black, an environment or world color set explicitly.

## Render settings by purpose

Starting values; adjust after the first look.

| Purpose | Engine | Resolution | Samples and noise | Notes |
|---|---|---|---|---|
| Layout check | Workbench, or the real-time engine | about 480 x 270 | lowest | seconds; finds scale, aim and ground problems |
| Look check | Real-time engine (EEVEE in Blender) | 960 x 540 | 32 to 64 | judge materials and light ratios |
| Final still, glass, mirrors, accurate bounce light | Path tracer (Cycles) | 1920 x 1080 | 128 to 256 with denoising on | slower; write to a file, never rely on the viewport |
| CPU-only machine or time limit | Path tracer | 50 percent of final | 64 with denoising | raise samples only if noise is visible |
| Animation | Real-time engine | final size | 32 to 64 | render an image sequence, not a video file; set frame range explicitly |

Do not hard-code engine identifiers: read the allowed values from the installed version (they were renamed between releases) and assign inside a try/except that prints the valid list. Set color management explicitly (a filmic or AgX-style view transform in Blender; `SRGBColorSpace` output and a tone mapping in three.js) because defaults differ by version: verify (unconfirmed).

## Verification loop

1. Render a layout-size thumbnail to a named file (`render_check_01.png`).
2. Confirm the file exists and is not empty. In Blender a missing file usually means `write_still` was not set or the output path was relative to an unsaved file.
3. Look at the image and test each line:

| What you see | Probable cause |
|---|---|
| All black | no light, light energy 0, camera inside an object, or subject beyond clip end |
| All white or blown out | exposure too high; sun strength copied from another tool |
| Subject tiny or specks | unit error (centimeters read as meters), or distance too large |
| Subject cut off | distance below the framing formula, or FOV in the wrong axis |
| Subject missing, ground visible | aim error, or Euler convention mix-up |
| Subject floats, no contact shadow | origin at center but placed as if at base |
| Magenta or pink surfaces | missing image texture (renderer's placeholder color) |
| Upside down or sideways | up axis mismatch (Z-up data in a Y-up tool) |
| Flat grey, no shading | only ambient light, or a flat shading mode |
| Stripes or noise patterns | samples too low, or shadow-bias problem |

4. Put a 1 m reference cube or a 1.7 m figure in the scene while checking scale, and remove it after.
5. Fix one cause, re-render, repeat; after round 3 stop and report what is unresolved.

If no render can be run (no Blender, no GL context), say so, run the validator, and mark the thumbnail checks "not done" in the report. A live-Blender connector that returns a viewport image is acceptable for this step if the user has one.

## Portability

| Item | Blender | three.js | glTF 2.0 |
|---|---|---|---|
| Up axis | Z | Y | Y |
| Handedness | right | right | right |
| Unit | 1 = 1 m (scene setting) | 1 = whatever you choose, use 1 m | meters |
| Camera looks along | local -Z | local -Z | local -Z |
| Euler `XYZ` | Rz * Ry * Rx | Rx * Ry * Rz | quaternions only |
| FOV | by sensor fit | vertical, degrees | vertical, radians |
| Material model | node graph | `MeshStandardMaterial` or `MeshPhysicalMaterial` | metallic-roughness |

Moving a scene from Blender to three.js goes through glTF. Use the exporter's Y-up conversion (verify (unconfirmed): an option named `export_yup`), export materials as PBR only, and apply scale and modifiers first. After import, re-run the validator on a description of the imported scene with `up_axis` set to `Y`, then re-render a thumbnail: lights do not survive with the same brightness, so re-balance them.

## Report format

```
Contract: <units, up axis, ground, origin rule>
Validator: <ok true/false, errors, warnings, and what was fixed>
Script: <tool and version assumed; list of items marked verify (unconfirmed) and how each was checked>
Render: <rounds used, settings, final thumbnail path, which checks in the table were run>
Not checked: <e.g. final-quality render, other tools, animation, textures>
```

## Boundaries

This skill scripts scenes that the user owns or has rights to. It does not generate depictions of real people without consent or imitate someone else's protected assets; decline those requests.

## Limits

- The validator checks a description, not a live scene: it sees no parent hierarchy, no rotated bounding boxes, no occlusion and no real materials or textures.
- Ground checks use axis-aligned `dimensions`; a rotated object may dip below the ground without being flagged.
- The aim check is a cone test with bounding spheres, not a render; an object can pass it and still be hidden.
- The camera and lighting numbers are starting values, not measured optima.
- API names and defaults depend on the installed Blender or three.js version; items marked `verify (unconfirmed)` are not vouched for.
- Not covered: rigging, simulation tuning, shader authoring beyond PBR basics, game engines, CAD and slicing.
