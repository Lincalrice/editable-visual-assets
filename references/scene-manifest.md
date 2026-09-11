# Scene Manifest Specification

## Purpose

`scene_manifest.json` is the source of truth for editable visual composition. Version 2 adds explicit PowerPoint-native shape metadata, target slide hints, rotation/opacity, and parent relationships while remaining compatible with version 1 bundles.

## Top-level fields

```json
{
  "version": 2,
  "canvas": {"width": 1600, "height": 900, "unit": "px"},
  "target": {
    "powerpoint": {"slide_width_in": 13.333333, "slide_height_in": 7.5}
  },
  "objects": []
}
```

`canvas.width` and `canvas.height` must be positive. `canvas.unit` may be `px` or `pt`; geometry is always mapped proportionally to the destination slide. `target.powerpoint` is a dry-run/default hint only: when a real presentation is open, its actual slide dimensions are authoritative.

## Common object fields

Every object must contain:

```json
{
  "id": "absorption_tower",
  "label": "Absorption tower",
  "type": "equipment",
  "editable_as": "svg",
  "bbox": [160, 220, 260, 460],
  "z_index": 20,
  "description": "Primary absorption column"
}
```

Allowed `editable_as` values are `native_text`, `ppt_shape`, `svg`, and `transparent_raster`.

Optional common fields:

- `rotation`: degrees clockwise.
- `opacity`: 0 to 1. Preserve in the manifest even if the downstream editor cannot reproduce it exactly.
- `parent_id`: semantic parent/group ID. Use for reasoning and future regrouping; do not require PowerPoint grouping to succeed.

IDs must match `^[a-z0-9][a-z0-9_-]*$` and be unique.

## Native text

Keep authoritative text outside vector paths:

```json
{
  "id": "title",
  "label": "Title",
  "type": "text",
  "editable_as": "native_text",
  "bbox": [240, 50, 1120, 70],
  "z_index": 100,
  "description": "Slide title",
  "text": "Machine-learning-assisted solvent screening",
  "text_style": {
    "font_family": "Arial",
    "font_size": 42,
    "font_weight": 600,
    "italic": false,
    "fill": "#111827",
    "align": "center",
    "vertical_align": "middle"
  },
  "svg_fragment": "<text x=\"800\" y=\"96\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"42\" fill=\"#111827\">Machine-learning-assisted solvent screening</text>"
}
```

`text` is authoritative for PowerPoint reconstruction. `svg_fragment` is only the preview representation.

## Native PowerPoint shapes

Use `ppt_shape` when PowerPoint can represent the object directly. Supported v2 shape kinds are:

- `rectangle`
- `rounded_rectangle`
- `ellipse`
- `line`
- `arrow`
- `chevron`

Example:

```json
{
  "id": "flow_arrow",
  "label": "Flow arrow",
  "type": "connector",
  "editable_as": "ppt_shape",
  "bbox": [420, 330, 220, 60],
  "z_index": 30,
  "description": "Native PowerPoint connector",
  "shape": {
    "kind": "arrow",
    "points": [[430, 360], [610, 360]],
    "stroke": "#667085",
    "stroke_width": 8,
    "dash": "solid"
  },
  "svg_fragment": "<line x1=\"430\" y1=\"360\" x2=\"585\" y2=\"360\" stroke=\"#667085\" stroke-width=\"8\"/><polygon points=\"610,360 580,342 580,378\" fill=\"#667085\"/>"
}
```

For filled native shapes, use `fill` and `stroke` values in `#RRGGBB` format or `none`. `stroke_width` is expressed in canvas units. `dash` may use `solid`, `square_dot`, `round_dot`, `dash`, `dash_dot`, `dash_dot_dot`, `long_dash`, or `long_dash_dot`.

## SVG objects

SVG-capable objects may provide `svg_fragment` in full-canvas coordinates. Do not include an outer `<svg>` element.

The bundle builder wraps the fragment in a semantic group and writes two forms:

- full-canvas placement inside `scene.svg`;
- a tightly cropped `objects/<id>.svg` whose `viewBox` equals the object's `bbox`.

The tight per-object SVG is important for PowerPoint: the selection box should match the object rather than the entire slide.

An SVG object may instead provide `asset` when an externally authored SVG should be used as-is.

## Transparent raster objects

Use only for semantic objects that genuinely need texture, painterly detail, photorealism, or other non-vector appearance:

```json
{
  "id": "hero_reactor",
  "label": "Detailed reactor illustration",
  "type": "illustration",
  "editable_as": "transparent_raster",
  "bbox": [1030, 170, 420, 590],
  "z_index": 40,
  "description": "Detailed transparent reactor rendering",
  "asset": "raster/hero_reactor.png",
  "asset_prompt": "isolated detailed reactor, transparent background, no text"
}
```

Keep raster objects independent. Never embed the entire composition in one raster merely because one element needs raster rendering.

## Preview fragments

`svg_fragment` may be included for `native_text` and `ppt_shape` objects to make `scene.svg` a useful visual preview. The native metadata remains authoritative for reconstruction.

## Raster generation and delegation metadata

A `transparent_raster` object may include an optional `generation` object. This metadata expresses preference and state; it does not guarantee that the current ChatGPT/Codex surface exposes a compatible sub-agent.

```json
{
  "id": "hero_reactor",
  "label": "Detailed reactor illustration",
  "type": "illustration",
  "editable_as": "transparent_raster",
  "bbox": [1030, 170, 420, 590],
  "z_index": 40,
  "description": "Detailed transparent reactor rendering",
  "asset": "raster/hero_reactor.png",
  "asset_prompt": "isolated detailed reactor, transparent background, no text",
  "generation": {
    "dispatch": "delegate_preferred",
    "fallback": "parent",
    "status": "planned",
    "style_signature": "clean scientific editorial illustration; restrained blue-gray materials; soft isometric perspective",
    "anchor_ids": [],
    "forbidden_content": ["text", "labels", "arrows", "full-slide background"]
  }
}
```

Allowed `generation.dispatch` values:

- `delegate_preferred`: delegate only if the host and delegated worker expose the required image/file capabilities.
- `parent_only`: keep image generation in the parent thread.
- `manual`: do not invoke image generation automatically.

Allowed `generation.fallback` values:

- `parent`: parent agent generates the isolated object when delegation is unavailable.
- `preserve_placeholder`: preserve the unresolved manifest object and do not claim final completion.
- `manual`: leave the job explicitly unresolved for a human/external tool.

Allowed `generation.status` values:

- `planned`
- `generated`
- `failed`
- `manual`

`style_signature` is a concise reusable style description. `anchor_ids` is an array of object IDs that should visually anchor this generation job. `forbidden_content` is an array of strings describing content that must not be baked into the raster asset.

Do not set `status: generated` unless the referenced asset actually exists or an accessible returned asset reference has been received.
