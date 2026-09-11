# PowerPoint Handoff

## Purpose

Use this guidance when editable visual assets must be reconstructed in Microsoft PowerPoint while preserving independently selectable objects.

## Preferred object mapping

Map manifest objects to PowerPoint using this priority:

- `native_text` -> native PowerPoint text box.
- `ppt_shape` -> native PowerPoint shape, line, or arrow.
- `svg` -> independently inserted SVG object.
- `transparent_raster` -> independently inserted transparent raster object.

Do not flatten a full slide merely because one object is raster-only.

## Naming and identity

Use the manifest `id` as the PowerPoint Shape name whenever possible. Stable names allow deterministic replacement and make Computer Use/Codex instructions more reliable.

Examples:

- `title`
- `co2_arrow`
- `absorption_tower`
- `hero_reactor`

When replacing an object, target the existing PowerPoint Shape with the same name instead of rebuilding unrelated slide content.

## Reconstruction workflow

1. Validate `scene_manifest.json`.
2. Build `scene.svg` and independent SVG assets.
3. Ensure all required raster assets exist.
4. Run a PowerPoint dry-run:

```bash
python scripts/powerpoint_reconstruct.py output/scene_manifest.json --assets-dir output --dry-run
```

5. On Windows with PowerPoint open, reconstruct into the visible presentation:

```powershell
py scripts\powerpoint_reconstruct.py output\scene_manifest.json --assets-dir output --slide 1 --replace-existing
```

6. Keep PowerPoint visible for visual inspection and manual/Computer Use refinement.
7. Save only after the user or workflow requests it.

## SVG behavior in PowerPoint

Treat each semantic SVG file as one independently selectable object at insertion time. If the user needs to edit internal SVG paths as Office shapes, use PowerPoint's SVG-to-shape conversion workflow when available. Do not assume every SVG primitive automatically becomes a separate Office Shape on insertion.

For this reason, split semantically independent elements into separate SVG files before insertion rather than relying on later ungrouping.

## Raster behavior

A raster asset should correspond to exactly one semantic visual object. Keep its background transparent where supported. Do not bake editable labels, arrows, captions, or page background into the raster object.

## Positioning

Manifest geometry is specified in canvas coordinates and is mapped proportionally to the destination slide. When an actual presentation is open, its real page size is authoritative over any manifest slide-size hint.

## Visual QA

After reconstruction, inspect:

- whether object bounds match visible content;
- whether SVG selection boxes are tight;
- whether transparent PNG edges are clean;
- whether text remains native and editable;
- whether z-order is correct;
- whether arrows/connectors align with the intended semantic targets;
- whether any object was accidentally duplicated during replacement;
- whether raster elements visually match the slide's style anchor.

## Image generation while the slide is live

Keep the parent agent responsible for the live slide and `scene_manifest.json`. If a complex isolated raster object is needed, follow `subagent-image-delegation.md`: capability-check the host, extract a minimal image job, delegate only that object when supported, wait for the returned asset, then replace/insert the named PowerPoint object. Do not let a delegated worker redesign the whole slide.

Use at most two concurrent raster jobs by default. Establish a style anchor before parallel sibling generation when visual consistency matters. If delegation or delegated image generation is unavailable, apply the object's manifest fallback without flattening the slide.
