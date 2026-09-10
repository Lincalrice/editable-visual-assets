---
name: editable-visual-assets
description: Create or revise structured, editable visual assets for ChatGPT conversations, especially when the user asks for editable SVG, layered/separable image components, PowerPoint-ready graphics, Figma-ready artwork, diagrams, scientific illustrations, icons, flowcharts, or visuals whose parts must remain independently movable, recolorable, replaceable, or editable. Prefer native SVG primitives and semantic groups over flattened raster images; use transparent raster assets only for elements that are genuinely unsuitable for vector representation.
---

# Editable Visual Assets

## Goal

Produce visuals as editable structure, not merely as a flattened picture. Preserve semantic objects, text, geometry, and reusable components so downstream tools such as PowerPoint, Figma, Inkscape, or a coding agent can modify individual parts.

## Workflow

1. Classify the request before creating visual output.
2. Plan a scene manifest with semantic objects and stable IDs.
3. Route each object to the most editable representation that can preserve the requested appearance.
4. Create the vector scene and per-object assets.
5. Validate the manifest and SVG bundle.
6. Hand off structured assets plus a preview or raster-only components when needed.

Read `references/scene-manifest.md` for the required object model. Read `references/svg-authoring.md` before authoring SVG. Read `references/ppt-handoff.md` when the target is PowerPoint or another slide editor.

## Representation decision tree

Use the following priority order for every object:

1. **Native text**: Keep labels, titles, captions, equations, and editable copy as text metadata. Do not convert text to paths unless the user explicitly requests outlined lettering.
2. **Native geometry / PPT shape**: Use semantic rectangles, rounded rectangles, circles, ellipses, lines, connectors, arrows, polygons, and other simple primitives when they express the object accurately.
3. **Semantic SVG**: Use grouped SVG primitives and compact paths for icons, diagrams, scientific apparatus, logos, molecules, stylized objects, and flat illustrations.
4. **Transparent raster object**: Use an independently generated transparent raster asset only for objects whose required appearance depends on texture, painterly detail, photorealism, or geometry that would be impractical to represent as editable SVG.
5. **Flattened raster scene**: Use only when the user explicitly prioritizes a single final image over editability.

Never flatten the whole scene merely because one object requires raster rendering. Keep vector and raster representations mixed in the same manifest.

## Scene planning

Before authoring files, define a logical canvas and object tree. Assign every editable item:

- a stable lowercase `id` using letters, digits, hyphens, or underscores;
- a short human-readable `label`;
- a semantic `type`;
- `editable_as`: `native_text`, `ppt_shape`, `svg`, or `transparent_raster`;
- a bounding box `[x, y, width, height]` in canvas coordinates;
- a `z_index`;
- a concise description of its visual role.

Keep backgrounds, main subjects, connectors/arrows, labels, and decorative elements separate whenever the user could reasonably want to move, recolor, replace, hide, or delete them later.

## SVG-native creation

For diagrammatic, scientific, icon-like, infographic, and slide-illustration requests, prefer SVG-native creation instead of image generation.

Create:

- `scene_manifest.json`
- `scene.svg`
- `objects/<id>.svg` for each SVG-capable object

Author `svg_fragment` for SVG-capable objects in canvas coordinates. Then run:

```bash
python scripts/validate_manifest.py scene_manifest.json
python scripts/build_svg_bundle.py scene_manifest.json --out output
```

Use `scripts/build_svg_bundle.py` rather than hand-splitting the final scene when possible. The script preserves semantic IDs and writes both the composed SVG and independent object SVG files.

## Complex illustration branch

If an object genuinely requires image generation, keep that object isolated from the rest of the scene.

- Generate the smallest meaningful semantic object, not the entire scene.
- Prefer transparent background for isolated assets.
- Keep text, arrows, labels, charts, diagrams, and simple geometry outside the raster object.
- Record the asset as `transparent_raster` in the scene manifest.
- Preserve its intended bounding box and z-order so it can be placed later by PowerPoint/Figma/Codex.
- If the environment cannot both generate the raster asset and finish the structured bundle in one turn, preserve the manifest first and continue the raster-object generation in a subsequent turn rather than flattening the scene.

Do not claim that an image-generation model exposes internal layers or paths unless the tool actually provides them.

## Editing existing structured visuals

When the user asks to modify an existing scene:

1. Reuse existing object IDs.
2. Change only the affected objects unless the requested change requires reflow.
3. Preserve unrelated geometry and styling.
4. Regenerate `scene.svg` and affected `objects/*.svg` from the updated manifest.
5. Validate again.

Examples:

- "Move the GNN block to the center" -> change the object's geometry/transform, not the whole image.
- "Make the CO2 arrow gray and dashed" -> edit the arrow object only.
- "Remove the cloud" -> remove or hide that semantic object.
- "Change the title" -> modify native text metadata, not vector outlines.

## Output contract

For a complete editable visual bundle, provide:

- `scene_manifest.json` as the source of truth;
- `scene.svg` as the composed vector representation when vector content exists;
- `objects/` containing independent reusable SVG objects;
- any raster-only objects as separate transparent files rather than embedded into one flattened image;
- a short note identifying which parts remain fully editable and which parts are raster-only.

For PowerPoint-oriented work, follow `references/ppt-handoff.md`.

## Quality rules

- Prefer semantic SVG elements (`text`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`) over long paths when equivalent.
- Group related primitives under one stable `<g id="...">`.
- Keep SVG IDs unique and meaningful.
- Avoid embedding a full-scene PNG inside SVG as a fake vector result.
- Avoid converting ordinary text into paths.
- Avoid thousands of tiny tracing paths for flat artwork when a compact semantic approximation is possible.
- Keep gradients, filters, masks, and clip paths only when materially useful and compatible with the target editor.
- Preserve a sensible `viewBox`.
- Keep object ordering deterministic by `z_index`.
- Validate before delivery.

## Scope boundaries

This skill defines editable visual structure and asset generation. It does not itself promise perfect conversion of arbitrary photorealistic images into semantic vector art. For highly detailed raster imagery, favor separate transparent raster layers plus editable vector overlays.
