#!/usr/bin/env python3
import argparse
import html
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


def attrs_for(obj):
    return (
        f'id="{html.escape(obj["id"], quote=True)}" '
        f'data-label="{html.escape(str(obj.get("label", "")), quote=True)}" '
        f'data-type="{html.escape(str(obj.get("type", "")), quote=True)}" '
        f'data-editable-as="{html.escape(str(obj.get("editable_as", "")), quote=True)}"'
    )


def wrap_svg(width, height, body, view_box=None):
    if view_box is None:
        view_box = f"0 0 {width} {height}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="{view_box}">\n{body}\n</svg>\n'
    )


def copy_asset(manifest_path, out_dir, asset_path):
    src = Path(asset_path)
    if not src.is_absolute():
        src = manifest_path.parent / src
    if not src.exists():
        return None
    rel = Path(asset_path)
    if rel.is_absolute():
        rel = Path("raster") / rel.name
    dst = out_dir / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return rel.as_posix()


def validate_xml(path):
    ET.parse(path)


def main():
    parser = argparse.ArgumentParser(description="Build composed and tightly-cropped per-object SVG assets from a scene manifest.")
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
    copied = 0
    for obj in objects:
        fragment = obj.get("svg_fragment")
        if fragment:
            group = f'  <g {attrs_for(obj)}>\n    {fragment}\n  </g>'
            groups.append(group)
            x, y, w, h = obj["bbox"]
            # Per-object SVGs are tightly cropped to the semantic bounding box. Keeping
            # the original canvas coordinates in the viewBox avoids rewriting paths.
            object_svg = wrap_svg(w, h, group, f"{x} {y} {w} {h}")
            object_path = object_dir / f'{obj["id"]}.svg'
            object_path.write_text(object_svg, encoding="utf-8")
            validate_xml(object_path)
            written += 1

        if obj.get("editable_as") == "transparent_raster" and obj.get("asset"):
            copied_path = copy_asset(args.manifest, args.out, obj["asset"])
            if copied_path:
                obj["asset"] = copied_path
                copied += 1

    scene_svg = wrap_svg(width, height, "\n".join(groups))
    scene_path = args.out / "scene.svg"
    scene_path.write_text(scene_svg, encoding="utf-8")
    validate_xml(scene_path)

    (args.out / "scene_manifest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {scene_path}, {written} object SVG files, copied {copied} raster assets")


if __name__ == "__main__":
    main()
