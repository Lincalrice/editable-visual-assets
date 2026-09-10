# PowerPoint Handoff

## Goal

Reconstruct the scene as independently selectable PowerPoint objects while keeping the PowerPoint window visible for Codex/Computer Use inspection and manual intervention.

## Object mapping

| Manifest representation | PowerPoint result |
| --- | --- |
| `native_text` | Native text box |
| `ppt_shape` | Native PowerPoint AutoShape or line/arrow |
| `svg` | Independent SVG picture object |
| `transparent_raster` | Independent transparent raster picture |

Semantic editability is the priority. An imported SVG is one selectable PowerPoint object by default; its internal SVG paths are still present in the SVG asset and can be converted/ungrouped in PowerPoint when needed. Keep commonly moved units as separate SVG files rather than one full-scene SVG.

## Build and validate

From the skill directory:

```bash
python scripts/validate_manifest.py scene_manifest.json
python scripts/build_svg_bundle.py scene_manifest.json --out output
python scripts/powerpoint_reconstruct.py output/scene_manifest.json --assets-dir output --dry-run
```

The builder creates tightly cropped SVG files under `output/objects/`, so PowerPoint selection boxes stay close to the visible artwork.

## Windows reconstruction

Install the Windows COM dependency once:

```powershell
py -m pip install pywin32
```

Open the desired presentation in Microsoft PowerPoint, leave it visible, then run:

```powershell
py scripts\powerpoint_reconstruct.py output\scene_manifest.json --assets-dir output --slide 3 --replace-existing
```

To open a presentation explicitly:

```powershell
py scripts\powerpoint_reconstruct.py output\scene_manifest.json --assets-dir output --ppt "C:\path\deck.pptx" --slide 3 --replace-existing --save
```

To append a blank slide:

```powershell
py scripts\powerpoint_reconstruct.py output\scene_manifest.json --assets-dir output --new-slide --save
```

The script keeps PowerPoint visible and names each inserted shape with its manifest `id`. Re-running with `--replace-existing` replaces only matching scene objects rather than rebuilding unrelated slide content.

## Codex / Computer Use workflow

Prefer this sequence when the user wants to watch edits happen:

1. Open PowerPoint and navigate to the target slide.
2. Build/validate the asset bundle in the project terminal.
3. Run `powerpoint_reconstruct.py` against the active presentation.
4. Keep PowerPoint in the foreground after insertion.
5. Use Computer Use for visual judgement: spacing, hierarchy, alignment, crop, and aesthetic adjustments.
6. For later deterministic changes, update the manifest and rerun with `--replace-existing`; for subjective tweaks, manipulate the named PowerPoint objects directly.

Do not silently regenerate the presentation with a separate PPTX library when the user explicitly asked to watch PowerPoint-front-end editing.

## Recommended bundle

```text
output/
  scene_manifest.json
  scene.svg
  objects/
    database.svg
    apparatus.svg
  raster/
    detailed_reactor.png
```

## Anti-patterns

Avoid full-slide PNGs, SVGs that only embed a full-slide PNG, outlined ordinary text, arrow labels baked into raster art, huge transparent SVG canvases around tiny objects, and automatic tracing that produces thousands of meaningless paths for simple flat geometry.
