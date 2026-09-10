#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
EDITABLE_AS = {"native_text", "ppt_shape", "svg", "transparent_raster"}
REQUIRED_OBJECT_KEYS = {"id", "label", "type", "editable_as", "bbox", "z_index", "description"}


def fail(messages):
    for message in messages:
        print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_manifest(data):
    errors = []
    if data.get("version") != 1:
        errors.append("version must be 1")

    canvas = data.get("canvas")
    if not isinstance(canvas, dict):
        errors.append("canvas must be an object")
    else:
        for key in ("width", "height"):
            value = canvas.get(key)
            if not isinstance(value, (int, float)) or value <= 0:
                errors.append(f"canvas.{key} must be a positive number")

    objects = data.get("objects")
    if not isinstance(objects, list):
        errors.append("objects must be an array")
        return errors

    seen = set()
    for index, obj in enumerate(objects):
        prefix = f"objects[{index}]"
        if not isinstance(obj, dict):
            errors.append(f"{prefix} must be an object")
            continue

        missing = REQUIRED_OBJECT_KEYS - set(obj)
        if missing:
            errors.append(f"{prefix} missing keys: {', '.join(sorted(missing))}")

        obj_id = obj.get("id")
        if not isinstance(obj_id, str) or not ID_RE.fullmatch(obj_id):
            errors.append(f"{prefix}.id must match {ID_RE.pattern}")
        elif obj_id in seen:
            errors.append(f"duplicate object id: {obj_id}")
        else:
            seen.add(obj_id)

        editable_as = obj.get("editable_as")
        if editable_as not in EDITABLE_AS:
            errors.append(f"{prefix}.editable_as must be one of {sorted(EDITABLE_AS)}")

        bbox = obj.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(v, (int, float)) for v in bbox):
            errors.append(f"{prefix}.bbox must be [x, y, width, height] with numeric values")
        elif bbox[2] < 0 or bbox[3] < 0:
            errors.append(f"{prefix}.bbox width and height must be non-negative")

        if not isinstance(obj.get("z_index"), (int, float)):
            errors.append(f"{prefix}.z_index must be numeric")

        if editable_as in {"svg", "ppt_shape", "native_text"} and "svg_fragment" in obj:
            fragment = obj.get("svg_fragment")
            if not isinstance(fragment, str) or "<svg" in fragment.lower():
                errors.append(f"{prefix}.svg_fragment must be an SVG fragment without an outer <svg>")

        if editable_as == "native_text" and not isinstance(obj.get("text"), str):
            errors.append(f"{prefix}.text is required for native_text")

        if editable_as == "transparent_raster" and not isinstance(obj.get("asset"), str):
            errors.append(f"{prefix}.asset is required for transparent_raster")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate an editable visual scene manifest.")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        fail([f"could not read JSON: {exc}"])

    errors = validate_manifest(data)
    if errors:
        fail(errors)

    print(f"OK: {args.manifest} is valid ({len(data['objects'])} objects)")


if __name__ == "__main__":
    main()
