"""Example consumer: resolve a volume's annotated ROI by name, in a specific
consumer's expected axis order -- instead of parsing the free-text bbox
field. The catalog stores roi.{x,y,z} order-free (see #ROI in
lmd_annotations.cue); this is where a consumer's own order gets applied.

    scripts/export_catalog.sh
    python3 examples/resolve_roi.py "exm-drosophila-flyliconn-matt-260601-60X-B4-1-042/crop-001"
"""

from __future__ import annotations

import json
import sys


def load(path):
    with open(path) as f:
        return json.load(f)


def resolve_bounding_box_zyx(name, volumes, annotations):
    """miao's `bounding_box` config field: [[z_min,z_max],[y_min,y_max],[x_min,x_max]]."""
    matches = [v for v in volumes if v["name"] == name]
    assert matches, f"unknown volume name: {name}"
    volume = matches[0]

    tracked = [a for a in annotations if volume["path"] in a["source_paths"]]
    assert len(tracked) == 1, f"expected exactly one tracking annotation for {name}, got {len(tracked)}"
    annotation = tracked[0]

    roi = annotation.get("roi")
    assert roi is not None, f"{name} has a tracking annotation but no roi set"
    return [roi["z"], roi["y"], roi["x"]]


def main():
    name = sys.argv[1]
    volumes = load("volumes.json")
    annotations = load("annotations.json")
    print(json.dumps({"bounding_box": resolve_bounding_box_zyx(name, volumes, annotations)}))


if __name__ == "__main__":
    main()
