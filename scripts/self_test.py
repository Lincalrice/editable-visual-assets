#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "references" / "example-manifest.json"
VALIDATOR = ROOT / "scripts" / "validate_manifest.py"
BUILDER = ROOT / "scripts" / "build_svg_bundle.py"
PPT = ROOT / "scripts" / "powerpoint_reconstruct.py"
JOBS = ROOT / "scripts" / "extract_image_jobs.py"


def run(*args):
    result = subprocess.run([sys.executable, *map(str, args)], text=True, capture_output=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout


def main():
    run(VALIDATOR, EXAMPLE)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "bundle"
        run(BUILDER, EXAMPLE, "--out", out)

        scene = out / "scene.svg"
        database = out / "objects" / "database.svg"
        if not scene.exists() or not database.exists():
            raise SystemExit("missing expected SVG output")
        ET.parse(scene)
        root = ET.parse(database).getroot()
        if root.attrib.get("viewBox") != "100 280 180 180":
            raise SystemExit(f"unexpected cropped viewBox: {root.attrib.get('viewBox')}")
        if root.attrib.get("width") != "180" or root.attrib.get("height") != "180":
            raise SystemExit("per-object SVG dimensions are not tight to bbox")

        dry = run(PPT, out / "scene_manifest.json", "--assets-dir", out, "--dry-run")
        plan = json.loads(dry)
        ids = [item["id"] for item in plan["objects"]]
        if ids != ["database", "ml_model", "co2_arrow", "title"]:
            raise SystemExit(f"unexpected reconstruction order: {ids}")
        database_plan = plan["objects"][0]
        if not database_plan.get("asset_exists"):
            raise SystemExit("PowerPoint dry-run could not resolve database.svg")

        delegated_manifest = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        delegated_manifest["objects"].append({
            "id": "hero_reactor",
            "label": "Detailed reactor",
            "type": "illustration",
            "editable_as": "transparent_raster",
            "bbox": [1100, 180, 320, 480],
            "z_index": 40,
            "description": "Complex raster-only reactor",
            "asset": "raster/hero_reactor.png",
            "asset_prompt": "isolated reactor, transparent background, no text",
            "generation": {
                "dispatch": "delegate_preferred",
                "fallback": "parent",
                "status": "planned",
                "style_signature": "clean scientific editorial illustration",
                "anchor_ids": ["database"],
                "forbidden_content": ["text", "labels", "arrows"]
            }
        })
        delegated_path = Path(tmp) / "delegated.json"
        delegated_path.write_text(json.dumps(delegated_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        run(VALIDATOR, delegated_path)
        jobs_path = Path(tmp) / "image_jobs.json"
        run(JOBS, delegated_path, "--out", jobs_path)
        jobs = json.loads(jobs_path.read_text(encoding="utf-8"))["jobs"]
        if len(jobs) != 1 or jobs[0]["object_id"] != "hero_reactor":
            raise SystemExit(f"unexpected image job extraction: {jobs}")
        if jobs[0]["dispatch"] != "delegate_preferred" or jobs[0]["fallback"] != "parent":
            raise SystemExit("image delegation metadata was not preserved")
        if "database" not in jobs[0]["anchor_ids"]:
            raise SystemExit("style anchor was not preserved in job packet")

        invalid = json.loads(delegated_path.read_text(encoding="utf-8"))
        invalid["objects"][-1]["generation"]["dispatch"] = "always_spawn"
        invalid_path = Path(tmp) / "invalid_generation.json"
        invalid_path.write_text(json.dumps(invalid, ensure_ascii=False, indent=2), encoding="utf-8")
        bad = subprocess.run([sys.executable, str(VALIDATOR), str(invalid_path)], text=True, capture_output=True)
        if bad.returncode == 0 or "generation.dispatch" not in bad.stderr:
            raise SystemExit("validator did not reject invalid generation.dispatch")

        invalid_anchor = json.loads(delegated_path.read_text(encoding="utf-8"))
        invalid_anchor["objects"][-1]["generation"]["anchor_ids"] = ["missing_anchor"]
        invalid_anchor_path = Path(tmp) / "invalid_anchor.json"
        invalid_anchor_path.write_text(json.dumps(invalid_anchor, ensure_ascii=False, indent=2), encoding="utf-8")
        bad_anchor = subprocess.run([sys.executable, str(VALIDATOR), str(invalid_anchor_path)], text=True, capture_output=True)
        if bad_anchor.returncode == 0 or "anchor_ids references unknown id" not in bad_anchor.stderr:
            raise SystemExit("validator did not reject unknown generation anchor")

    print("PASS: editable visual assets v2.1 pipeline self-test")


if __name__ == "__main__":
    main()
