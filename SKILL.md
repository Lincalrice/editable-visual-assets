---
name: editable-visual-assets
description: Create or revise structured, editable visual assets for ChatGPT conversations, especially when the user asks for editable SVG, layered or separable image components, PowerPoint-ready graphics, Figma-ready artwork, scientific illustrations, diagrams, icons, flowcharts, or visuals whose parts must remain independently movable, recolorable, replaceable, or editable. Prefer native text, PowerPoint-native shapes, and semantic SVG over flattened raster images; isolate genuinely complex visual content as separate transparent raster objects.
---

# Editable Visual Assets

## Goal

Produce editable visual structure rather than a flattened picture. Preserve semantic objects, text, geometry, and reusable assets so PowerPoint, Figma, Inkscape, or Codex can modify individual parts.

## Core workflow

1. Plan `scene_manifest.json` with stable semantic object IDs before creating the final composition.
2. Route every object to the most editable representation that preserves the required appearance.
3. Author SVG fragments and native-object metadata; isolate only genuinely complex imagery as raster objects.
4. Validate the manifest with `scripts/validate_manifest.py`.
5. Build `scene.svg` plus tightly cropped `objects/<id>.svg` files with `scripts/build_svg_bundle.py`.
6. For PowerPoint work, dry-run and reconstruct with `scripts/powerpoint_reconstruct.py`.
7. Visually inspect and edit named objects rather than regenerating the whole scene.

Read `references/scene-manifest.md` for the object model. Read `references/svg-authoring.md` before writing SVG. Read `references/image-generation-layering.md` before using image generation. Read `references/subagent-image-delegation.md` when image generation occurs during a live PowerPoint/editable-slide workflow. Read `references/ppt-handoff.md` when PowerPoint is a target.

## Representation priority

Choose the first representation that is visually sufficient:

1. `native_text` for titles, labels, captions, equations, and other copy.
2. `ppt_shape` for rectangles, rounded rectangles, ellipses, lines, arrows, chevrons, and similar geometry when the destination is PowerPoint.
3. `svg` for icons, diagrams, apparatus, molecules, logos, technical schematics, and flat illustrations.
4. `transparent_raster` only for semantic objects whose appearance materially depends on texture, painterly detail, photorealism, or otherwise impractical vector geometry.
5. Flatten the full scene only when the user explicitly prefers a single final image over editability.

Never flatten the whole scene merely because one object requires raster rendering.

## Scene planning rules

Assign every editable object:

- stable lowercase `id` matching `^[a-z0-9][a-z0-9_-]*$`;
- human-readable `label`;
- semantic `type`;
- `editable_as`;
- `[x, y, width, height]` `bbox` in canvas coordinates;
- `z_index`;
- concise `description`.

Use `parent_id` when semantic grouping helps later reasoning. Keep backgrounds, main subjects, connectors, labels, and decorative elements separate whenever a user could reasonably want to move, recolor, replace, hide, or delete them later.

## SVG-native branch

Prefer SVG-native creation for scientific figures, diagrams, icon-like art, process schematics, infographics, and slide illustrations.

Author SVG-capable objects in full-canvas coordinates through `svg_fragment`. Keep native text and PowerPoint shapes authoritative in their structured metadata while optionally supplying `svg_fragment` for the composed preview.

Run:

```bash
python scripts/validate_manifest.py scene_manifest.json
python scripts/build_svg_bundle.py scene_manifest.json --out output
```

Do not hand-split a full-scene SVG when the builder can produce semantic object assets. Per-object SVGs must be tightly cropped to the object's `bbox`; a full-slide transparent selection box is a defect.

## Complex image-generation branch

Use image generation only for the smallest meaningful semantic object that actually needs raster detail.

Before invoking image generation:

1. Record the object in the manifest as `transparent_raster`.
2. Give it an `asset` path and `asset_prompt`.
3. Keep all ordinary text, arrows, labels, diagrams, charts, and simple geometry outside the raster object.
4. Request an isolated object with transparent background when supported.
5. Reuse one style signature across sibling raster objects.

If the image tool does not expose layers, masks, or vector paths, treat the generated image as one raster object and do not claim otherwise. If image generation ends the response before bundling can continue, preserve the manifest first and continue from that asset in a later turn. Never compensate by flattening the whole composition.

### Sub-agent delegation during live slide editing

When PowerPoint or another live editable slide surface is the main task, preserve the parent agent as the slide orchestrator. For a complex `transparent_raster` object, prefer delegating only that bounded image-generation job **if and only if** the current host exposes sub-agents and the delegated worker can generate an image and return an asset accessible to the parent.

Do not assume delegation exists merely because this Skill requests it. If the capability is unavailable, use the object's `generation.fallback` policy. Never make sub-agent availability a hard dependency for the entire slide workflow.

Use `scripts/extract_image_jobs.py` to produce minimal object-scoped job packets before delegation. Follow `references/subagent-image-delegation.md` for capability checks, context isolation, style anchors, concurrency, return contracts, and reintegration. Default to at most two concurrent image jobs and generate a shared style anchor before dispatching anchor-dependent siblings.

## PowerPoint reconstruction

For a PowerPoint-ready result, run the SVG builder first, then:

```bash
python scripts/powerpoint_reconstruct.py output/scene_manifest.json --assets-dir output --dry-run
```

On Windows with Microsoft PowerPoint and `pywin32`, reconstruct into the visible active presentation:

```powershell
py scripts\powerpoint_reconstruct.py output\scene_manifest.json --assets-dir output --slide 1 --replace-existing
```

The reconstruction script maps:

- `native_text` -> native PowerPoint text box;
- `ppt_shape` -> native PowerPoint shape/line/arrow;
- `svg` -> independently selectable SVG object;
- `transparent_raster` -> independently selectable transparent raster object.

Every inserted PowerPoint shape is named with the manifest `id`. Prefer deterministic manifest updates plus `--replace-existing` for repeatable changes, and use Computer Use for subjective visual adjustments when the user wants to watch front-end editing.

## Editing existing structured visuals

When the user requests a change:

1. Reuse existing IDs.
2. Modify only affected objects unless reflow is necessary.
3. Preserve unrelated geometry and styling.
4. Rebuild affected assets and `scene.svg`.
5. Validate again.
6. In PowerPoint, replace only objects with matching IDs or manipulate the named objects directly.

Examples:

- "Move the GNN block to the center" -> update that object's `bbox` or native placement.
- "Make the CO2 arrow gray and dashed" -> update only its `shape` and preview fragment.
- "Remove the cloud" -> remove/hide only that semantic object.
- "Change the title" -> update `text`, not outlined vector glyphs.

## Output contract

A complete bundle should contain:

```text
output/
  scene_manifest.json
  scene.svg
  objects/
    <semantic-object>.svg
  raster/
    <raster-only-object>.png
```

Deliver `scene_manifest.json` as the source of truth. Identify any raster-only parts explicitly. Keep independent assets suitable for direct insertion into PowerPoint/Figma; do not embed a full-scene PNG inside SVG as a fake vector result.

## Quality rules

- Prefer semantic SVG primitives (`text`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`) over long paths when equivalent.
- Group related primitives under one stable `<g id="...">`.
- Keep SVG IDs unique and meaningful.
- Preserve text as text whenever editability matters.
- Avoid thousands of tiny tracing paths for flat artwork.
- Keep filters, masks, clip paths, gradients, and blend effects only when materially useful and compatible with the destination editor.
- Preserve deterministic z-order.
- Validate XML and manifest structure before delivery.
- When PowerPoint is the target, keep each semantic SVG's viewBox tight to its visible object.

## Verification

Run the bundled self-test after modifying scripts or the manifest schema:

```bash
python scripts/self_test.py
```

The self-test verifies manifest validation, SVG generation/XML parsing, tight per-object viewBoxes, asset resolution, image-job delegation metadata, negative schema cases, and a PowerPoint dry-run plan.

## Scope boundary

Do not promise perfect semantic vectorization of arbitrary photorealistic images. For high-detail imagery, preserve separate transparent raster layers plus editable vector/text overlays rather than misrepresenting auto-traced paths as meaningful editable structure.
