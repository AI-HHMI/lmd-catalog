"""Parse the free-text bbox/bbox_size annotation fields into #ROI's shape
({x: [min,max], y: [min,max], z: [min,max]}, max exclusive). Two formats show
up in practice: range-labeled ("X:908-1390, Y:910-1392, Z:218-412") or a bare
offset triple paired with a bbox_size triple ("13720, 16025, 3570" /
"482, 482, 194"). Shared by check_integrity.py (verifies roi matches this)
and rebuild_annotations.py (computes roi from this in the first place).
"""

import re

BBOX_RANGE_RE = re.compile(r"([XYZ]):(\d+)-(\d+)")
PLAIN_TRIPLE_RE = re.compile(r"^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")


def parse_roi(bbox, bbox_size):
    range_matches = BBOX_RANGE_RE.findall(bbox) if bbox else []
    if range_matches:
        return {axis.lower(): [int(lo), int(hi)] for axis, lo, hi in range_matches}

    offset_m = PLAIN_TRIPLE_RE.match(bbox or "")
    size_m = PLAIN_TRIPLE_RE.match(bbox_size or "")
    assert offset_m and size_m, f"bbox/bbox_size not in a recognized format: {bbox!r} {bbox_size!r}"
    ox, oy, oz = (int(x) for x in offset_m.groups())
    sx, sy, sz = (int(x) for x in size_m.groups())
    return {"x": [ox, ox + sx], "y": [oy, oy + sy], "z": [oz, oz + sz]}
