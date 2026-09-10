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

    print("PASS: editable visual assets v2 pipeline self-test")


if __name__ == "__main__":
    main()
