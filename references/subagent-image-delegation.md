# Sub-agent Image Delegation Protocol

Use this protocol when PowerPoint or another live editable slide surface is the primary task and one or more semantic objects genuinely require image generation.

## Core principle

Keep the parent agent as the slide orchestrator. Delegate only bounded raster-object generation jobs. The parent remains authoritative for:

- the current slide and user intent;
- `scene_manifest.json`;
- object IDs, layout, and z-order;
- style coordination;
- PowerPoint insertion/replacement;
- final visual QA and integration.

A delegated worker must never redesign the whole slide or flatten unrelated objects into its image.

## Capability gate

Do not assume every ChatGPT surface exposes sub-agents or that every sub-agent can use image generation.

Before delegating, confirm that the current host supports all of the following:

1. spawning/delegating a sub-agent or worker;
2. image generation in that delegated context;
3. returning an asset or file reference that the parent can access;
4. waiting for the delegated result before final integration.

If any requirement is unavailable, follow the fallback policy in the manifest. Never fail the whole slide merely because delegation is unavailable.

## When delegation is preferred

Prefer delegation when all of these are true:

- the destination is a live PowerPoint/editable-slide workflow;
- the object is `transparent_raster` rather than `native_text`, `ppt_shape`, or `svg`;
- the object is a standalone semantic unit;
- the generation task has enough visual complexity to justify a separate model/tool call;
- preserving the parent thread's slide-level context is valuable;
- the generated asset can be reinserted without redesigning the whole page.

Examples: detailed reactor rendering, laboratory apparatus cutaway, human/character illustration, photorealistic material sample, textured industrial scene fragment.

## When not to delegate

Do not delegate image generation merely because a visual is needed. Keep work in the parent thread when:

- native PowerPoint shapes or compact SVG are sufficient;
- the request is only moving, recoloring, resizing, or relabeling an object;
- the visual is a trivial icon or decoration;
- the child would need the entire conversation to understand its task;
- the object is tightly coupled to the full-page composition and cannot be generated independently.

Delegation adds model/tool work and can increase token use. Use it only when context isolation, parallelism, or specialization materially helps.

## Minimal delegation packet

Send the child only the context needed to generate one object:

```json
{
  "object_id": "hero_reactor",
  "label": "Detailed reactor",
  "description": "Cutaway reactor used as the right-side hero illustration",
  "bbox": [1030, 170, 420, 590],
  "asset_prompt": "isolated detailed reactor cutaway, transparent background, no text",
  "style_signature": "clean scientific editorial illustration; restrained blue-gray materials; soft isometric perspective",
  "anchor_ids": ["style_anchor_reactor"],
  "forbidden_content": ["text", "labels", "arrows", "full-slide background"],
  "target_asset_path": "raster/hero_reactor.png"
}
```

Do not forward the entire parent reasoning trace or irrelevant slide history. Summarize only the facts needed for the asset.

## Style continuity and anchor-first generation

Independent image workers can drift in style. Use this order:

1. Generate one representative raster object first when multiple raster objects must share a visual language.
2. Treat that object or its concise textual description as the style anchor.
3. Dispatch independent sibling objects only after the anchor exists.
4. Pass the same `style_signature` and accessible anchor reference to every worker.
5. If the worker cannot access anchor files, use a precise textual style signature instead of assuming file inheritance.

Avoid parallel generation of strongly interdependent visual objects before a style anchor exists.

## Concurrency

Default to at most two concurrent raster-generation jobs. Increase only when the host clearly supports it and the jobs are visually independent. Generate anchor-dependent objects in a later batch.

## Return contract

The child returns only:

- the generated asset or accessible file reference;
- the `object_id`;
- actual pixel dimensions when known;
- transparency status when known;
- a short note describing any deviation from the requested prompt.

The child must not modify unrelated manifest objects, slide geometry, or PowerPoint content.

## Parent reintegration

After a delegated asset returns, the parent must:

1. confirm the asset is accessible;
2. update the object's `generation.status` to `generated` only after the asset exists;
3. preserve the existing object ID and bbox unless a deliberate layout change is needed;
4. insert or replace only that object in PowerPoint;
5. visually verify scale, crop, alpha edges, style consistency, and z-order;
6. continue the main slide workflow only after required delegated assets are resolved.

Do not claim the slide is complete while required image jobs remain unresolved.

## Fallbacks

Use one of these manifest fallbacks:

- `parent`: generate the isolated raster object in the parent thread when possible.
- `preserve_placeholder`: keep the manifest/object placeholder and stop before claiming final completion; useful when invoking image generation would terminate the current response or the asset cannot yet be reintegrated.
- `manual`: leave a clearly identified asset job for a human/external tool.

Never fall back to flattening the whole slide.
