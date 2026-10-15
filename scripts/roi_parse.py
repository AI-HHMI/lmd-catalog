"""Parse the free-text bbox/bbox_size annotation fields into #ROI's shape
({x: [min,max], y: [min,max], z: [min,max]}, max exclusive). Two formats show
up in practice: range-labeled ("X:908-1390, Y:910-1392, Z:218-412") or an
offset triple -- bare ("13720, 16025, 3570") or labeled ("X=1013, Y=1013, Z=580,")
-- paired with an XYZ bbox_size, either a triple ("482, 482, 194" or "482×482×194 vox") or labeled
("sizeX=482, sizeY=482, sizeZ=194 vox"). A labeled offset may carry the size pasted after it
("X=680, Y=1300, Z=480, 482×482×194 vox"); that copy must agree with bbox_size. Shared by check_integrity.py
(verifies roi matches this) and rebuild_annotations.py (computes roi from this in the first place).
"""

import re

BBOX_RANGE_RE = re.compile(r"([XYZ]):\s*(\d+)\s*-\s*(\d+)")
LABELED_OFFSET_RE = re.compile(r"([XYZ])\s*=\s*(\d+)")
LABELED_SIZE_RE = re.compile(r"size([XYZ])\s*=\s*(\d+)")
PLAIN_TRIPLE_RE = re.compile(r"^\s*(\d+)\s*[,×x]\s*(\d+)\s*[,×x]\s*(\d+)")
TIMES_TRIPLE_RE = re.compile(r"(\d+)\s*×\s*(\d+)\s*×\s*(\d+)")


def parse_roi(bbox, bbox_size):
    range_matches = BBOX_RANGE_RE.findall(bbox) if bbox else []
    if range_matches:
        return {axis.lower(): [int(lo), int(hi)] for axis, lo, hi in range_matches}

    labeled = dict(LABELED_OFFSET_RE.findall(bbox or ""))
    offset_m = PLAIN_TRIPLE_RE.match(bbox or "")
    labeled_size = dict(LABELED_SIZE_RE.findall(bbox_size or ""))
    size_m = PLAIN_TRIPLE_RE.match(bbox_size or "")
    b1 = set(labeled) == set("XYZ") or offset_m
    b2 = set(labeled_size) == set("XYZ") or size_m
    assert b1 and b2, f"bbox/bbox_size not in a recognized format: {bbox!r} {bbox_size!r}"
    ox, oy, oz = (int(labeled[a]) for a in "XYZ") if labeled else (int(x) for x in offset_m.groups())
    size = [int(labeled_size[a]) for a in "XYZ"] if labeled_size else [int(x) for x in size_m.groups()]
    pasted = TIMES_TRIPLE_RE.search(bbox) if labeled else None
    assert not pasted or [int(x) for x in pasted.groups()] == size, f"size in bbox disagrees with bbox_size: {bbox!r} {bbox_size!r}"
    sx, sy, sz = size
    return {"x": [ox, ox + sx], "y": [oy, oy + sy], "z": [oz, oz + sz]}
