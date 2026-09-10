"""Example consumer: resolve a volume's annotated ROI by name, in a specific
consumer's expected axis order -- instead of parsing the free-text bbox
field.

    python3 examples/resolve_roi.py "exm-drosophila-flyliconn-matt-260601-60X-B4-1-042/crop-001"
"""

from __future__ import annotations

import json
import sys

import lmd_catalog as lmd


def resolve_bounding_box(name: str, axes: str = "zyx") -> list[list[int]]:
    vol = lmd.get(name)
    assert len(vol.tracked_by) == 1, (
        f"expected exactly one tracking annotation for {name}, got {len(vol.tracked_by)}"
    )
    annotation = vol.tracked_by[0]
    assert annotation.roi is not None, f"{name} has a tracking annotation but no roi set"
    return annotation.roi.to_order(axes)


def main():
    if len(sys.argv) < 2:
        print("Usage: resolve_roi.py <volume_name> [axes]")
        sys.exit(1)

    name = sys.argv[1]
    axes = sys.argv[2] if len(sys.argv) > 2 else "zyx"
    print(json.dumps({"bounding_box": resolve_bounding_box(name, axes)}))


if __name__ == "__main__":
    main()

