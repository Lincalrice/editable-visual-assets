#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


def attrs_for(obj):
    return (
        f'id="{html.escape(obj["id"], quote=True)}" '
        f'data-label="{html.escape(str(obj.get("label", "")), quote=True)}" '
        f'data-type="{html.escape(str(obj.get("type", "")), quote=True)}" '
        f'data-editable-as="{html.escape(str(obj.get("editable_as", "")), quote=True)}"'
    )


def wrap_svg(width, height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n{body}\n</svg>\n'
    )


def main():
    parser = argparse.ArgumentParser(description="Build a composed SVG and per-object SVG files from a scene manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    width = data["canvas"]["width"]
    height = data["canvas"]["height"]
    objects = sorted(data.get("objects", []), key=lambda item: (item.get("z_index", 0), item.get("id", "")))

    args.out.mkdir(parents=True, exist_ok=True)
    object_dir = args.out / "objects"
    object_dir.mkdir(parents=True, exist_ok=True)

    groups = []
    written = 0
    for obj in objects:
        fragment = obj.get("svg_fragment")
        if not fragment:
            continue
        group = f'  <g {attrs_for(obj)}>\n    {fragment}\n  </g>'
        groups.append(group)
        object_svg = wrap_svg(width, height, group)
        (object_dir / f'{obj["id"]}.svg').write_text(object_svg, encoding="utf-8")
        written += 1

    scene_svg = wrap_svg(width, height, "\n".join(groups))
    (args.out / "scene.svg").write_text(scene_svg, encoding="utf-8")
    (args.out / "scene_manifest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {args.out / 'scene.svg'} and {written} object SVG files")


if __name__ == "__main__":
    main()
