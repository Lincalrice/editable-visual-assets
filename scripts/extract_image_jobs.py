#!/usr/bin/env python3
"""Extract minimal raster-generation job packets from a scene manifest.

This script does not spawn sub-agents. It creates a deterministic handoff file that
an agent runtime can dispatch when sub-agent + image-generation capabilities exist.
"""

import argparse
import json
from pathlib import Path


DEFAULT_FORBIDDEN = ["text", "labels", "arrows", "full-slide background", "watermark"]


def make_job(obj):
    gen = obj.get("generation") if isinstance(obj.get("generation"), dict) else {}
    forbidden = gen.get("forbidden_content")
    if not isinstance(forbidden, list):
        forbidden = DEFAULT_FORBIDDEN
    return {
        "object_id": obj["id"],
        "label": obj.get("label", ""),
        "description": obj.get("description", ""),
        "bbox": obj.get("bbox"),
        "asset_prompt": obj.get("asset_prompt", ""),
        "style_signature": gen.get("style_signature", ""),
        "anchor_ids": gen.get("anchor_ids", []),
        "forbidden_content": forbidden,
        "target_asset_path": obj.get("asset"),
        "dispatch": gen.get("dispatch", "delegate_preferred"),
        "fallback": gen.get("fallback", "parent"),
        "status": gen.get("status", "planned"),
        "return_contract": {
            "required": ["object_id", "asset_reference"],
            "optional": ["pixel_width", "pixel_height", "has_transparency", "deviation_note"],
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Extract object-scoped image generation jobs from a scene manifest.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, default=None, help="Optional output JSON path; stdout when omitted.")
    parser.add_argument("--include-resolved", action="store_true", help="Include jobs already marked generated.")
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    jobs = []
    for obj in sorted(data.get("objects", []), key=lambda o: (o.get("z_index", 0), o.get("id", ""))):
        if obj.get("editable_as") != "transparent_raster":
            continue
        gen = obj.get("generation") if isinstance(obj.get("generation"), dict) else {}
        status = gen.get("status", "planned")
        if status == "generated" and not args.include_resolved:
            continue
        jobs.append(make_job(obj))

    payload = {
        "version": 1,
        "source_manifest": str(args.manifest),
        "dispatch_note": "Capability-gate delegation: spawn a sub-agent only if it can generate an image and return an asset accessible to the parent.",
        "jobs": jobs,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"Wrote {len(jobs)} image job(s) to {args.out}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
