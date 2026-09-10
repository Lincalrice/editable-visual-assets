# PowerPoint Handoff

## Contents

- Goal
- Object mapping
- Recommended bundle
- Editing behavior
- Anti-patterns

## Goal

Make the final visual convenient to manipulate in PowerPoint rather than merely importable.

## Object mapping

Map scene objects as follows:

| Manifest representation | PowerPoint target |
| --- | --- |
| `native_text` | Native text box |
| `ppt_shape` | Native PowerPoint shape or connector |
| `svg` | Independent SVG object |
| `transparent_raster` | Independent transparent PNG/WebP object |

Keep repeated or logically related SVG primitives grouped within one semantic SVG asset when the user normally wants to move them as a unit. Split them further only when internal manipulation is useful.

## Recommended bundle

```text
output/
  scene_manifest.json
  scene.svg
  objects/
    database.svg
    gnn_model.svg
    candidate_solvents.svg
    co2_arrow.svg
  raster/
    detailed_reactor.png
```

A downstream PowerPoint agent should reconstruct the slide from the manifest instead of inserting `scene.svg` as one immutable object when individual manipulation matters.

## Editing behavior

When the user asks to move or restyle one visual element, use its manifest ID and modify only that asset or its placement. Preserve unrelated objects.

For global style changes, update shared style attributes consistently, then rebuild the SVG bundle.

## Anti-patterns

Avoid:

- one full-slide PNG;
- one SVG containing an embedded full-slide raster image;
- outlined text when editable text is required;
- arrow labels baked into an illustration;
- decorative background and foreground merged into the same raster layer;
- automatic vector tracing that creates thousands of tiny paths for simple flat art.
