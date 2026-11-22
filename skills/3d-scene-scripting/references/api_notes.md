## Contents

- Where these notes come from
- Blender Python
- three.js
- glTF
- Items marked unconfirmed

# API notes for scene scripts

Short, original notes the main skill points to. Read the Blender section only for Blender work and the three.js section only for three.js work. Nothing here was fetched or run while writing it; every item marked `verify (unconfirmed)` must be probed on the user's install before use.

## Where these notes come from

Facts should be checked against the official references for the installed version:

- Blender Python API reference: https://docs.blender.org/api/current/
- three.js documentation: https://threejs.org/docs/
- glTF 2.0 specification: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html

## Blender Python

Skeleton in the order that avoids most failures (names are the usual `bpy` API; probe each on the installed version):

1. Start from an empty scene: remove default objects deliberately by name you collected, not by selecting all.
2. Set units: `scene.unit_settings.system = 'METRIC'` and `scene.unit_settings.scale_length = 1.0`.
3. Create materials, then objects, then assign materials by reference held in variables.
4. Rest objects on the ground by computing the lowest world-space bounding-box corner: transform each of `obj.bound_box` by `obj.matrix_world`, take the minimum on Z, then shift `obj.location.z` by the gap.
5. Create the camera data and object, link it to the scene collection, assign `scene.camera`. Add a Track To constraint: `con = cam.constraints.new('TRACK_TO')`, `con.target = subject`, `con.track_axis = 'TRACK_NEGATIVE_Z'`, `con.up_axis = 'UP_Y'`.
6. Create lights: `bpy.data.lights.new(name, type)` with types `'SUN'`, `'POINT'`, `'SPOT'`, `'AREA'`; set `.energy`.
7. Set render: engine (read the enum first), `scene.render.resolution_x`, `resolution_y`, `resolution_percentage`, `scene.render.filepath` as an absolute path, `scene.render.image_settings.file_format` (read the enum), then `bpy.ops.render.render(write_still=True)`.

Notes:

- Shader node lookup by type: `n.type == "BSDF_PRINCIPLED"`; output node type `"OUTPUT_MATERIAL"`; image texture `"TEX_IMAGE"`; world color node `"BACKGROUND"`.
- Principled input socket names changed in the 4.x series (emission color, specular level, subsurface and transmission weights): verify (unconfirmed) the exact names on the installed version by printing `[i.name for i in node.inputs]`.
- Render engine identifiers changed between releases (the real-time engine had different identifiers in different versions): verify (unconfirmed); read `bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items` and assign inside try/except.
- Path tracer settings live under `scene.cycles` (`samples`, `use_denoising`, `device`): verify (unconfirmed) for the installed version.
- `material.use_nodes`: verify (unconfirmed) whether needed in the installed version.
- Headless run: `blender --background --python script.py` is the usual form; confirm with `blender --help` on the install.
- Data-block name length limit: verify (unconfirmed).

## three.js

- Scene units are unitless; choose 1 = 1 m for portability.
- `PerspectiveCamera(fov, aspect, near, far)` takes a vertical fov in degrees. Call `camera.lookAt(x, y, z)` after setting position; update the projection matrix after changing `aspect` or `fov`.
- Color: set `renderer.outputColorSpace = THREE.SRGBColorSpace`; color textures need `texture.colorSpace = THREE.SRGBColorSpace`, data textures (roughness, normal) stay linear. Verify (unconfirmed) the property names for the installed release.
- Light intensities follow physical units in recent releases and differed in older ones: verify (unconfirmed); judge exposure on the thumbnail.
- Tone mapping: `renderer.toneMapping` with a constant such as `THREE.ACESFilmicToneMapping`; verify (unconfirmed) available names.
- Headless thumbnail: needs a browser with GL (a headless browser) or a headless GL binding. Render, then read the canvas in the same task; whether `preserveDrawingBuffer` is needed depends on the read method: verify (unconfirmed). Without a GL context, say so and fall back to the validator.
- `scene.getObjectByName(name)` returns the first match only, so duplicate names silently shadow each other.

## glTF

- Up axis Y, right-handed, meters. Cameras look down local -Z, and `yfov` is vertical in radians.
- Materials are metallic-roughness PBR; extra Blender shader features may be dropped or approximated.
- Blender's exporter has an option to convert Z-up to Y-up, on by default as far as is known: verify (unconfirmed) the option name `export_yup` on the installed version.

## Items marked unconfirmed

The main skill lists these inline. Collect them in the report under `Script:` with the probe used for each.
