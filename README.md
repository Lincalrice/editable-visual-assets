# Editable Visual Assets

A ChatGPT Skill for generating **structured visual assets instead of flattened images**, with a practical handoff to Microsoft PowerPoint.

## What v2 does

```text
Chat request
   -> scene_manifest.json
   -> native text / native PPT shapes / semantic SVG / isolated raster objects
   -> validate_manifest.py
   -> build_svg_bundle.py
   -> scene.svg + tightly-cropped objects/*.svg
   -> powerpoint_reconstruct.py
   -> independently selectable objects in visible PowerPoint
```

Typical requests:

- "Make a scientific illustration I can edit in PowerPoint."
- "Generate an SVG where I can move each subsystem separately."
- "Keep the labels editable and export the apparatus as separate SVGs."
- "Use image generation only for the detailed reactor, not for the text and arrows."

## Repository structure

```text
editable-visual-assets/
  SKILL.md
  agents/openai.yaml
  scripts/
    validate_manifest.py
    build_svg_bundle.py
    powerpoint_reconstruct.py
    self_test.py
  references/
    scene-manifest.md
    svg-authoring.md
    image-generation-layering.md
    ppt-handoff.md
    example-manifest.json
```

## Test the portable pipeline

```bash
python scripts/self_test.py
```

## Build an asset bundle

```bash
python scripts/validate_manifest.py references/example-manifest.json
python scripts/build_svg_bundle.py references/example-manifest.json --out output
python scripts/powerpoint_reconstruct.py output/scene_manifest.json --assets-dir output --dry-run
```

## Reconstruct in PowerPoint on Windows

Install `pywin32`, open PowerPoint, then:

```powershell
py scripts\powerpoint_reconstruct.py output\scene_manifest.json --assets-dir output --slide 1 --replace-existing
```

PowerPoint remains visible. Inserted objects are named after their manifest IDs so Codex/Computer Use or a human can select and modify the intended element directly.
