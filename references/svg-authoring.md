# SVG Authoring Guide

## Contents

- Semantic-first authoring
- Coordinate discipline
- Grouping and IDs
- Text
- Compatibility
- Complexity budget

## Semantic-first authoring

Prefer the simplest primitive that preserves meaning:

- boxes -> `rect`
- circles/bubbles -> `circle`
- ellipses -> `ellipse`
- connectors -> `line` or `polyline`
- simple arrows -> line/polyline plus polygon head
- simple icons -> grouped primitives
- irregular silhouettes -> compact `path`

Do not trace flat geometric artwork into hundreds of paths when several primitives can express it.

## Coordinate discipline

Use one canvas coordinate system. Keep all `svg_fragment` coordinates in scene coordinates so fragments can be composed without transform ambiguity.

Each standalone object SVG should use the full scene `viewBox` by default. This keeps its geometry identical to the composed scene and makes reinsertion deterministic. Cropped object variants can be added later if a downstream workflow needs them.

## Grouping and IDs

The scene builder wraps each fragment in:

```xml
<g id="object-id" data-label="Human label" data-type="semantic type">
  ...
</g>
```

Do not add a competing outer ID inside `svg_fragment` unless needed for subparts. Subpart IDs should be namespaced with the parent ID when practical.

## Text

Keep user-editable copy in text form. Use an SVG `text` element for preview only when helpful, while preserving the original string and styling in the manifest.

Do not outline normal labels. Avoid relying on unusual fonts unless the user supplies them or the environment can guarantee availability.

## Compatibility

For PowerPoint-oriented SVG:

- favor basic fills and strokes;
- minimize filters and blend modes;
- avoid JavaScript, animation, foreignObject, and external references;
- avoid CSS dependencies outside the SVG;
- use explicit presentation attributes when practical;
- keep gradients simple;
- keep masks and clipping minimal.

## Complexity budget

Prefer compact SVG that remains understandable to a human or coding agent. If a vector object becomes path-heavy because of realistic texture, reclassify that object as `transparent_raster` instead of degrading editability for the entire scene.
