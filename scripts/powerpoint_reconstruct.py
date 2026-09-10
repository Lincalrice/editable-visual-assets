#!/usr/bin/env python3
"""Reconstruct a scene manifest as independent objects in Microsoft PowerPoint.

The script is intentionally import-safe on non-Windows systems: use --dry-run to
validate placement and asset resolution without importing pywin32.
"""

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_SLIDE_WIDTH_IN = 13.333333
DEFAULT_SLIDE_HEIGHT_IN = 7.5

SHAPE_TYPES = {
    "rectangle": 1,
    "rounded_rectangle": 5,
    "ellipse": 9,
    "chevron": 52,
}
DASH_STYLES = {
    "solid": 1,
    "square_dot": 2,
    "round_dot": 3,
    "dash": 4,
    "dash_dot": 5,
    "dash_dot_dot": 6,
    "long_dash": 7,
    "long_dash_dot": 8,
}
ALIGNMENTS = {"left": 1, "center": 2, "right": 3, "justify": 4}
VERTICAL_ANCHOR = {"top": 1, "middle": 3, "bottom": 4}


def parse_color(value):
    if not value or value == "none":
        return None
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"invalid color: {value}")
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    # Office COM uses BGR integer packing through the RGB property.
    return r + (g << 8) + (b << 16)


def resolve_asset(manifest_path, assets_dir, obj):
    editable_as = obj.get("editable_as")
    asset = obj.get("asset")
    if asset:
        p = Path(asset)
        if not p.is_absolute():
            p = assets_dir / p
        return p.resolve()
    if editable_as == "svg" and obj.get("svg_fragment"):
        return (assets_dir / "objects" / f'{obj["id"]}.svg').resolve()
    return None


def target_size_points(data):
    target = data.get("target", {}) if isinstance(data.get("target"), dict) else {}
    ppt = target.get("powerpoint", {}) if isinstance(target.get("powerpoint"), dict) else {}
    width_in = float(ppt.get("slide_width_in", DEFAULT_SLIDE_WIDTH_IN))
    height_in = float(ppt.get("slide_height_in", DEFAULT_SLIDE_HEIGHT_IN))
    return width_in * 72.0, height_in * 72.0


def build_plan(data, manifest_path, assets_dir, slide_width_pt=None, slide_height_pt=None):
    canvas = data["canvas"]
    if slide_width_pt is None or slide_height_pt is None:
        slide_width_pt, slide_height_pt = target_size_points(data)
    sx = slide_width_pt / float(canvas["width"])
    sy = slide_height_pt / float(canvas["height"])

    plan = []
    for obj in sorted(data.get("objects", []), key=lambda o: (o.get("z_index", 0), o.get("id", ""))):
        x, y, w, h = obj["bbox"]
        entry = {
            "id": obj["id"],
            "editable_as": obj["editable_as"],
            "z_index": obj.get("z_index", 0),
            "left_pt": x * sx,
            "top_pt": y * sy,
            "width_pt": w * sx,
            "height_pt": h * sy,
            "rotation": float(obj.get("rotation", 0)),
        }
        asset = resolve_asset(manifest_path, assets_dir, obj)
        if asset is not None:
            entry["asset"] = str(asset)
            entry["asset_exists"] = asset.exists()
        plan.append(entry)
    return plan


def remove_existing_named_shape(slide, name):
    for i in range(slide.Shapes.Count, 0, -1):
        shape = slide.Shapes(i)
        if shape.Name == name:
            shape.Delete()


def tag_shape(shape, obj):
    shape.Name = obj["id"]
    try:
        shape.Tags.Add("scene_id", obj["id"])
        shape.Tags.Add("scene_type", str(obj.get("type", "")))
        shape.Tags.Add("editable_as", obj["editable_as"])
    except Exception:
        pass
    try:
        shape.AlternativeText = str(obj.get("description", ""))
    except Exception:
        pass


def apply_line_style(shape, shape_spec, scale):
    stroke = parse_color(shape_spec.get("stroke", "#000000"))
    if stroke is None:
        shape.Line.Visible = 0
    else:
        shape.Line.Visible = -1
        shape.Line.ForeColor.RGB = stroke
        if "stroke_width" in shape_spec:
            shape.Line.Weight = max(0.25, float(shape_spec["stroke_width"]) * scale)
        dash = shape_spec.get("dash", "solid")
        if dash in DASH_STYLES:
            shape.Line.DashStyle = DASH_STYLES[dash]


def apply_fill_style(shape, shape_spec):
    fill = parse_color(shape_spec.get("fill", "none"))
    if fill is None:
        shape.Fill.Visible = 0
    else:
        shape.Fill.Visible = -1
        shape.Fill.ForeColor.RGB = fill


def add_native_text(slide, obj, box, scale):
    left, top, width, height = box
    shape = slide.Shapes.AddTextbox(1, left, top, width, height)
    tag_shape(shape, obj)
    shape.TextFrame.TextRange.Text = obj.get("text", "")
    style = obj.get("text_style", {}) or {}
    font = shape.TextFrame.TextRange.Font
    if style.get("font_family"):
        font.Name = style["font_family"]
    if style.get("font_size") is not None:
        font.Size = max(1, float(style["font_size"]) * scale)
    if style.get("font_weight", 400) >= 600:
        font.Bold = -1
    if style.get("italic"):
        font.Italic = -1
    color = parse_color(style.get("fill", "#000000"))
    if color is not None:
        font.Color.RGB = color
    paragraph = shape.TextFrame.TextRange.ParagraphFormat
    align = style.get("align", "left")
    if align in ALIGNMENTS:
        paragraph.Alignment = ALIGNMENTS[align]
    try:
        anchor = style.get("vertical_align", "top")
        if anchor in VERTICAL_ANCHOR:
            shape.TextFrame2.VerticalAnchor = VERTICAL_ANCHOR[anchor]
    except Exception:
        pass
    try:
        shape.TextFrame.WordWrap = -1
        shape.TextFrame.AutoSize = 0
        shape.TextFrame.MarginLeft = 0
        shape.TextFrame.MarginRight = 0
        shape.TextFrame.MarginTop = 0
        shape.TextFrame.MarginBottom = 0
    except Exception:
        pass
    return shape


def add_ppt_shape(slide, obj, box, sx, sy):
    left, top, width, height = box
    spec = obj.get("shape", {})
    kind = spec.get("kind")
    scale = (sx + sy) / 2.0
    if kind in {"line", "arrow"}:
        points = spec.get("points")
        if isinstance(points, list) and len(points) == 2:
            (x1, y1), (x2, y2) = points
            shape = slide.Shapes.AddLine(x1 * sx, y1 * sy, x2 * sx, y2 * sy)
        else:
            shape = slide.Shapes.AddLine(left, top + height / 2.0, left + width, top + height / 2.0)
        tag_shape(shape, obj)
        apply_line_style(shape, spec, scale)
        if kind == "arrow":
            shape.Line.EndArrowheadStyle = 3
        return shape

    auto_shape_type = SHAPE_TYPES.get(kind)
    if auto_shape_type is None:
        raise ValueError(f"unsupported PowerPoint shape kind: {kind}")
    shape = slide.Shapes.AddShape(auto_shape_type, left, top, width, height)
    tag_shape(shape, obj)
    apply_fill_style(shape, spec)
    apply_line_style(shape, spec, scale)
    return shape


def add_picture(slide, obj, box, asset):
    if asset is None:
        raise FileNotFoundError(f"no asset resolved for {obj['id']}")
    if not asset.exists():
        raise FileNotFoundError(f"asset not found for {obj['id']}: {asset}")
    left, top, width, height = box
    shape = slide.Shapes.AddPicture(str(asset), 0, -1, left, top, width, height)
    tag_shape(shape, obj)
    return shape


def main():
    parser = argparse.ArgumentParser(description="Reconstruct editable scene objects into Microsoft PowerPoint.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--assets-dir", type=Path, default=None, help="Bundle root containing objects/ and raster/.")
    parser.add_argument("--ppt", type=Path, default=None, help="Presentation to open; omit to use the active presentation.")
    parser.add_argument("--slide", type=int, default=1, help="1-based slide index.")
    parser.add_argument("--new-slide", action="store_true", help="Append a blank slide and ignore --slide.")
    parser.add_argument("--replace-existing", action="store_true", help="Delete shapes whose names match manifest IDs before insertion.")
    parser.add_argument("--save", action="store_true", help="Save the presentation after reconstruction.")
    parser.add_argument("--dry-run", action="store_true", help="Print placement/asset plan without requiring Windows or PowerPoint.")
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets_dir = (args.assets_dir or manifest_path.parent).resolve()

    if args.dry_run:
        plan = build_plan(data, manifest_path, assets_dir)
        print(json.dumps({"manifest": str(manifest_path), "objects": plan}, ensure_ascii=False, indent=2))
        missing = [p for p in plan if p.get("asset") and not p.get("asset_exists")]
        raise SystemExit(2 if missing else 0)

    if os.name != "nt":
        print("ERROR: PowerPoint reconstruction requires Windows. Use --dry-run elsewhere.", file=sys.stderr)
        raise SystemExit(3)

    try:
        import win32com.client  # type: ignore
    except ImportError:
        print("ERROR: pywin32 is required. Install with: pip install pywin32", file=sys.stderr)
        raise SystemExit(4)

    app = win32com.client.Dispatch("PowerPoint.Application")
    app.Visible = True

    if args.ppt:
        pres = app.Presentations.Open(str(args.ppt.resolve()), WithWindow=True)
    else:
        try:
            pres = app.ActivePresentation
        except Exception:
            pres = None
        if pres is None:
            raise RuntimeError("No active PowerPoint presentation. Pass --ppt or open a presentation first.")

    if args.new_slide:
        # ppLayoutBlank = 12
        slide = pres.Slides.Add(pres.Slides.Count + 1, 12)
    else:
        if args.slide < 1 or args.slide > pres.Slides.Count:
            raise IndexError(f"slide index {args.slide} is out of range 1..{pres.Slides.Count}")
        slide = pres.Slides(args.slide)

    slide_width_pt = float(pres.PageSetup.SlideWidth)
    slide_height_pt = float(pres.PageSetup.SlideHeight)
    canvas = data["canvas"]
    sx = slide_width_pt / float(canvas["width"])
    sy = slide_height_pt / float(canvas["height"])
    text_scale = (sx + sy) / 2.0

    for obj in sorted(data.get("objects", []), key=lambda o: (o.get("z_index", 0), o.get("id", ""))):
        if args.replace_existing:
            remove_existing_named_shape(slide, obj["id"])

        x, y, w, h = obj["bbox"]
        box = (x * sx, y * sy, w * sx, h * sy)
        editable_as = obj["editable_as"]

        if editable_as == "native_text":
            shape = add_native_text(slide, obj, box, text_scale)
        elif editable_as == "ppt_shape":
            shape = add_ppt_shape(slide, obj, box, sx, sy)
        elif editable_as in {"svg", "transparent_raster"}:
            asset = resolve_asset(manifest_path, assets_dir, obj)
            shape = add_picture(slide, obj, box, asset)
        else:
            raise ValueError(f"unsupported editable_as: {editable_as}")

        if obj.get("rotation"):
            shape.Rotation = float(obj["rotation"])

    if args.save:
        pres.Save()

    print(f"Inserted {len(data.get('objects', []))} objects into slide {slide.SlideIndex}. PowerPoint remains open.")


if __name__ == "__main__":
    main()
