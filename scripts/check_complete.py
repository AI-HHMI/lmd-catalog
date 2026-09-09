"""Check the catalog against its two sources of truth, in the direction
check_integrity.py doesn't cover: not "is everything the catalog claims
real", but "is everything real reflected in the catalog".

    python3 scripts/check_complete.py
    # or with exported JSON:
    python3 scripts/check_complete.py volumes.json annotations.json

Run on a machine with /groups mounted and `gh` authenticated with the
`read:project` scope (`gh auth refresh -s read:project`).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

DATA_ROOT = "/groups/miaai/miaai/lmd-v0.0.1/data"
PROJECT_OWNER = "AI-HHMI"
PROJECT_NUMBER = "1"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def find_zarr_dirs(root):
    """Every .zarr directory under root, without descending into one once found
    -- their chunk trees are enormous and irrelevant here."""
    found = []
    for dirpath, dirnames, _filenames in os.walk(root):
        keep = []
        for d in dirnames:
            if d.endswith(".zarr"):
                found.append(os.path.join(dirpath, d))
            else:
                keep.append(d)
        dirnames[:] = keep
    return found


def check_volumes_complete(volumes):
    on_disk = set(find_zarr_dirs(DATA_ROOT))
    in_catalog = {v["path"] for v in volumes}

    new_on_disk = sorted(on_disk - in_catalog)
    stale_in_catalog = sorted(in_catalog - on_disk)

    violations = [f"new volume on disk, not in catalog: {p}" for p in new_on_disk]
    violations += [f"catalog volume no longer on disk: {p}" for p in stale_in_catalog]
    return violations


def fetch_project_issues():
    result = subprocess.run(
        ["gh", "project", "item-list", PROJECT_NUMBER, "--owner", PROJECT_OWNER,
         "--format", "json", "--limit", "200"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"gh project item-list failed: {result.stderr}"
    items = json.loads(result.stdout)["items"]
    issues = set()
    for item in items:
        content = item.get("content", {})
        if content.get("type") == "Issue":
            issues.add((content["repository"], content["number"]))
    return issues


def check_annotations_complete(annotations):
    in_project = fetch_project_issues()
    in_catalog = {(a["issue"]["repository"], a["issue"]["number"]) for a in annotations}

    new_in_project = sorted(in_project - in_catalog)
    stale_in_catalog = sorted(in_catalog - in_project)

    violations = [f"project item not synced to annotations.cue: {repo}#{num}" for repo, num in new_in_project]
    violations += [f"annotation tracks an issue no longer in the project: {repo}#{num}" for repo, num in stale_in_catalog]
    return violations


def main():
    if len(sys.argv) >= 3:
        volumes = load_json(sys.argv[1])
        annotations = load_json(sys.argv[2])
    else:
        try:
            import lmd_catalog as lmd
        except ImportError:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
            import lmd_catalog as lmd
        volumes = [v.model_dump() for v in lmd.all()]
        annotations = [a.model_dump() for a in lmd.annotations()]


    violations = [
        *check_volumes_complete(volumes),
        *check_annotations_complete(annotations),
    ]

    for v in violations:
        print(f"FAIL: {v}")
    print(f"\n{len(violations)} completeness gap(s)")
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
