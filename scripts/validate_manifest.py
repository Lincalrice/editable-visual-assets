#!/usr/bin/env python3
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
EDITABLE_AS = {"native_text", "ppt_shape", "svg", "transparent_raster"}
REQUIRED_OBJECT_KEYS = {"id", "label", "type", "editable_as", "bbox", "z_index", "description"}
PPT_SHAPES = {"rectangle", "rounded_rectangle", "ellipse", "line", "arrow", "chevron"}
GEN_DISPATCH = {"delegate_preferred", "parent_only", "manual"}
GEN_FALLBACK = {"parent", "preserve_placeholder", "manual"}
GEN_STATUS = {"planned", "generated", "failed", "manual"}


def fail(messages):
    for message in messages:
        print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def valid_color(value):
    return isinstance(value, str) and (value == "none" or re.fullmatch(r"#[0-9A-Fa-f]{6}", value))


def validate_svg_fragment(fragment):
    if not isinstance(fragment, str) or "<svg" in fragment.lower():
        return False
    try:
        ET.fromstring(f'<g xmlns="http://www.w3.org/2000/svg">{fragment}</g>')
        return True
    except ET.ParseError:
        return False


def validate_manifest(data):
    errors = []
    if data.get("version") not in {1, 2}:
        errors.append("version must be 1 or 2")

    canvas = data.get("canvas")
    if not isinstance(canvas, dict):
        errors.append("canvas must be an object")
    else:
        for key in ("width", "height"):
            value = canvas.get(key)
            if not isinstance(value, (int, float)) or value <= 0:
                errors.append(f"canvas.{key} must be a positive number")
        if "unit" in canvas and canvas["unit"] not in {"px", "pt"}:
            errors.append("canvas.unit must be px or pt when provided")

    target = data.get("target")
    if target is not None and not isinstance(target, dict):
        errors.append("target must be an object when provided")

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
        elif bbox[2] <= 0 or bbox[3] <= 0:
            errors.append(f"{prefix}.bbox width and height must be positive")

        if not isinstance(obj.get("z_index"), (int, float)):
            errors.append(f"{prefix}.z_index must be numeric")

        if "rotation" in obj and not isinstance(obj["rotation"], (int, float)):
            errors.append(f"{prefix}.rotation must be numeric")
        if "opacity" in obj and (not isinstance(obj["opacity"], (int, float)) or not 0 <= obj["opacity"] <= 1):
            errors.append(f"{prefix}.opacity must be between 0 and 1")
        if "parent_id" in obj and obj["parent_id"] is not None and not isinstance(obj["parent_id"], str):
            errors.append(f"{prefix}.parent_id must be a string or null")

        if "svg_fragment" in obj and not validate_svg_fragment(obj.get("svg_fragment")):
            errors.append(f"{prefix}.svg_fragment must be well-formed SVG content without an outer <svg>")

        if editable_as == "native_text":
            if not isinstance(obj.get("text"), str):
                errors.append(f"{prefix}.text is required for native_text")
            style = obj.get("text_style", {})
            if style is not None and not isinstance(style, dict):
                errors.append(f"{prefix}.text_style must be an object")

        if editable_as == "ppt_shape":
            shape = obj.get("shape")
            if not isinstance(shape, dict):
                errors.append(f"{prefix}.shape is required for ppt_shape")
            else:
                if shape.get("kind") not in PPT_SHAPES:
                    errors.append(f"{prefix}.shape.kind must be one of {sorted(PPT_SHAPES)}")
                for key in ("fill", "stroke"):
                    if key in shape and not valid_color(shape[key]):
                        errors.append(f"{prefix}.shape.{key} must be #RRGGBB or none")

        if editable_as == "svg" and not isinstance(obj.get("svg_fragment"), str) and not isinstance(obj.get("asset"), str):
            errors.append(f"{prefix} svg objects need svg_fragment or asset")

        if editable_as == "transparent_raster":
            if not isinstance(obj.get("asset"), str):
                errors.append(f"{prefix}.asset is required for transparent_raster")
            if "asset_prompt" in obj and not isinstance(obj.get("asset_prompt"), str):
                errors.append(f"{prefix}.asset_prompt must be a string when provided")
            generation = obj.get("generation")
            if generation is not None:
                if not isinstance(generation, dict):
                    errors.append(f"{prefix}.generation must be an object")
                else:
                    dispatch = generation.get("dispatch", "delegate_preferred")
                    fallback = generation.get("fallback", "parent")
                    status = generation.get("status", "planned")
                    if dispatch not in GEN_DISPATCH:
                        errors.append(f"{prefix}.generation.dispatch must be one of {sorted(GEN_DISPATCH)}")
                    if fallback not in GEN_FALLBACK:
                        errors.append(f"{prefix}.generation.fallback must be one of {sorted(GEN_FALLBACK)}")
                    if status not in GEN_STATUS:
                        errors.append(f"{prefix}.generation.status must be one of {sorted(GEN_STATUS)}")
                    if "style_signature" in generation and not isinstance(generation.get("style_signature"), str):
                        errors.append(f"{prefix}.generation.style_signature must be a string")
                    anchors = generation.get("anchor_ids", [])
                    if not isinstance(anchors, list) or not all(isinstance(v, str) for v in anchors):
                        errors.append(f"{prefix}.generation.anchor_ids must be an array of strings")
                    forbidden = generation.get("forbidden_content", [])
                    if not isinstance(forbidden, list) or not all(isinstance(v, str) for v in forbidden):
                        errors.append(f"{prefix}.generation.forbidden_content must be an array of strings")

    for index, obj in enumerate(objects):
        if not isinstance(obj, dict):
            continue
        parent_id = obj.get("parent_id")
        if parent_id and parent_id not in seen:
            errors.append(f"objects[{index}].parent_id references unknown id: {parent_id}")
        generation = obj.get("generation") if isinstance(obj.get("generation"), dict) else None
        if generation:
            for anchor_id in generation.get("anchor_ids", []):
                if anchor_id not in seen:
                    errors.append(f"objects[{index}].generation.anchor_ids references unknown id: {anchor_id}")
                if anchor_id == obj.get("id"):
                    errors.append(f"objects[{index}].generation.anchor_ids must not reference itself")

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
