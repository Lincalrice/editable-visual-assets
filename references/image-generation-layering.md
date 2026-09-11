# Layered Image Generation Protocol

Use this branch only when a semantic object cannot be represented well enough with native shapes or compact SVG.

## Before image generation

Create or update `scene_manifest.json` first. For every raster-bound object record:

- stable object `id`;
- target `bbox` and `z_index`;
- `editable_as: transparent_raster`;
- a deterministic `asset` path such as `raster/reactor.png`;
- an `asset_prompt` describing only that object.

Keep text, connectors, arrows, labels, charts, icons, and simple geometry out of the raster prompt whenever they can remain editable separately.

## Raster prompt pattern

Prompt for one semantic object at a time. Include:

- isolated subject;
- transparent background when supported;
- no text, labels, arrows, frames, or watermark;
- complete object with comfortable transparent padding;
- consistent perspective, rendering style, stroke treatment, and lighting shared with sibling raster objects;
- aspect ratio compatible with the object's manifest `bbox`.

Do not generate the entire slide merely to obtain one complex element.

## Chat image-tool constraint

If the image-generation environment returns a rendered image without exposing internal layers, masks, or vector paths, treat the image as one raster semantic object. Do not claim that hidden layers or SVG paths exist.

If invoking image generation ends the current response or prevents immediate post-processing, make the manifest and `asset_prompt` authoritative before the tool call. Continue bundling from the generated asset on a later turn when the file is available. Never solve this limitation by flattening the full composition.

## Style continuity

Maintain a short reusable style signature for sibling raster objects, for example:

`clean scientific editorial illustration; soft isometric perspective; restrained materials; no text; transparent background`

Repeat the same signature for every separately generated object. Vary only the semantic subject and necessary local details.

## Fallback vectorization

Vectorize a raster object only when the artwork is already flat, low-color, and shape-like. If tracing creates excessive micro-paths or loses semantics, keep the raster object separate instead of pretending it is meaningfully editable SVG.

## Delegation during live PowerPoint editing

When the parent agent is actively maintaining a PowerPoint slide, use `references/subagent-image-delegation.md` for complex raster-only objects. Delegation is preferred only when the host supports sub-agents **and** the delegated worker can use image generation and return an accessible asset. Otherwise use the manifest fallback.

Treat delegation as a context-preservation and parallelism optimization, not as a requirement for every image. Native text, PowerPoint shapes, SVG, trivial icons, and simple visual edits should stay in the parent workflow.
