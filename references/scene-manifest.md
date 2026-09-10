# Scene Manifest Specification

## Contents

- Purpose
- Required fields
- Object fields
- SVG object fields
- Raster object fields
- Example

## Purpose

`scene_manifest.json` is the source of truth for editable visual composition. It describes layout, semantics, editability, z-order, and the relationship between reusable assets.

## Required fields

```json
{
  "version": 1,
  "canvas": {
    "width": 1600,
    "height": 900
  },
  "objects": []
}
```

Canvas width and height must be positive numbers.

## Object fields

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

Allowed `editable_as` values:

- `native_text`
- `ppt_shape`
- `svg`
- `transparent_raster`

IDs must match `^[a-z0-9][a-z0-9_-]*$` and be unique.

## SVG object fields

SVG-capable objects should provide `svg_fragment` in canvas coordinates. The fragment may contain one element or a group of elements. Do not include an outer `<svg>` element.

```json
{
  "id": "co2_arrow",
  "label": "CO2 flow",
  "type": "connector",
  "editable_as": "svg",
  "bbox": [420, 330, 220, 60],
  "z_index": 30,
  "description": "Flow arrow between process blocks",
  "svg_fragment": "<line x1=\"430\" y1=\"360\" x2=\"610\" y2=\"360\" stroke=\"#667085\" stroke-width=\"8\"/><polygon points=\"610,360 585,344 585,376\" fill=\"#667085\"/>"
}
```

The builder wraps this fragment in `<g id="co2_arrow">`.

## Native text fields

Keep editable text in the manifest even if an SVG preview also includes it.

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
    "fill": "#111827"
  },
  "svg_fragment": "<text x=\"240\" y=\"96\" font-family=\"Arial\" font-size=\"42\" font-weight=\"600\" fill=\"#111827\">Machine-learning-assisted solvent screening</text>"
}
```

The text field remains authoritative for downstream slide reconstruction.

## Raster object fields

Raster objects must remain separate assets.

```json
{
  "id": "hero_reactor",
  "label": "Detailed reactor illustration",
  "type": "illustration",
  "editable_as": "transparent_raster",
  "bbox": [1030, 170, 420, 590],
  "z_index": 40,
  "description": "Detailed transparent reactor rendering",
  "asset": "raster/hero_reactor.png"
}
```

Do not embed the entire scene as one raster asset.

## Example

```json
{
  "version": 1,
  "canvas": {"width": 1600, "height": 900},
  "objects": [
    {
      "id": "database",
      "label": "Database",
      "type": "icon",
      "editable_as": "svg",
      "bbox": [100, 280, 180, 180],
      "z_index": 10,
      "description": "Source data icon",
      "svg_fragment": "<ellipse cx=\"190\" cy=\"315\" rx=\"70\" ry=\"22\" fill=\"#D9EAF7\" stroke=\"#3B82B6\" stroke-width=\"4\"/><rect x=\"120\" y=\"315\" width=\"140\" height=\"90\" fill=\"#EAF4FB\" stroke=\"#3B82B6\" stroke-width=\"4\"/><ellipse cx=\"190\" cy=\"405\" rx=\"70\" ry=\"22\" fill=\"#D9EAF7\" stroke=\"#3B82B6\" stroke-width=\"4\"/>"
    }
  ]
}
```
