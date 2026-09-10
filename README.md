# Editable Visual Assets

A ChatGPT Skill for producing editable visual structure instead of flattened images.

It is designed for requests such as:

- "Make this scientific illustration editable in PowerPoint."
- "Generate an SVG where I can move each part separately."
- "Create PPT-ready artwork with separate objects, labels, and arrows."
- "Keep the text editable and export each icon as a separate SVG."

## Core idea

The skill plans a semantic `scene_manifest.json`, routes each object to the most editable representation, and produces a composed SVG plus independent object SVGs. Complex visual elements may remain separate transparent raster assets rather than forcing the whole composition into a flattened image.

## Structure

```text
editable-visual-assets/
  SKILL.md
  agents/openai.yaml
  scripts/
    validate_manifest.py
    build_svg_bundle.py
  references/
    scene-manifest.md
    svg-authoring.md
    ppt-handoff.md
    example-manifest.json
```

## Local test

```bash
python scripts/validate_manifest.py references/example-manifest.json
python scripts/build_svg_bundle.py references/example-manifest.json --out /tmp/editable-visual-demo
```

The intended installation artifact is the validated `skill.zip` produced by the official ChatGPT skill packaging utility.
