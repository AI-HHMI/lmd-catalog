"""Verify the catalog's own history honors semver: for every #Volume `name`
present both at --from (default: the parent of --to) and at --to (default:
HEAD), `path`/`image_key`/`zarr_version` must be identical, and no name may be
removed -- unless a proposed version is given whose major component is greater
than the latest tag's. Annotation fields are exempt: `gt_ingested_path` and
friends are meant to be mutated in place as labeling rounds land (see
CLAUDE.md), so their history is not a compatibility break.

No /groups mount needed:

    python3 scripts/check_semver.py                           # HEAD vs its parent commit
    python3 scripts/check_semver.py v1.0.0                    # same, but breaking changes OK if v1.0.0 bumps the latest tag's major
    python3 scripts/check_semver.py --from v0.1.0 --to HEAD  # compare against a tag instead
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

from data_root import DATA_ROOT

STABLE_FIELDS = ("path", "image_key", "zarr_version")
SEMVER_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, f"{' '.join(cmd)} failed: {result.stderr}"
    return result.stdout


def parse_semver(tag):
    m = SEMVER_RE.match(tag)
    assert m, f"not a vN.N.N tag: {tag}"
    return tuple(int(x) for x in m.groups())


def latest_tag(to_ref):
    tags = run(["git", "tag", "--merged", to_ref]).split()
    versions = sorted(parse_semver(t) for t in tags if SEMVER_RE.match(t))
    return None if not versions else "v" + ".".join(str(x) for x in versions[-1])


def volumes_at_ref(ref, tmp_root):
    # Try getting lmd_volumes.json directly via git show
    result = subprocess.run(["git", "show", f"{ref}:lmd_volumes.json"], capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        out = {}
        for v in data.get("volumes", []):
            name = v["name"]
            out[name] = {
                "name": name,
                "path": DATA_ROOT + "/" + name + ".zarr",
                "image_key": v.get("image_key", "raw"),
                "zarr_version": v.get("zarr_version", "zarr3"),
            }
        return out

    # Legacy fallback for historical commits before the schema/data split
    ref_dir = os.path.join(tmp_root, ref.replace("/", "_"))
    os.makedirs(ref_dir, exist_ok=True)
    fetched = []
    for fname in ("lmd_volumes.cue", "lmd_annotations.cue"):
        res = subprocess.run(["git", "show", f"{ref}:{fname}"], capture_output=True, text=True)
        if res.returncode == 0:
            with open(os.path.join(ref_dir, fname), "w") as f:
                f.write(res.stdout)
            fetched.append(fname)
    if fetched:
        volumes = json.loads(run(["cue", "export", *fetched, "-e", "volumes"], cwd=ref_dir))
        return {v["name"]: v for v in volumes}
    raise RuntimeError(f"Could not find volume data at git ref {ref}")



def breaking_changes(old, new):
    violations = []
    for name, old_v in old.items():
        new_v = new.get(name)
        if new_v is None:
            violations.append(f"{name}: removed (was present at the last tag)")
            continue
        for field in STABLE_FIELDS:
            if old_v[field] != new_v[field]:
                violations.append(f"{name}: {field} changed {old_v[field]!r} -> {new_v[field]!r}")
    return violations


def main():
    rest = sys.argv[1:]
    proposed = rest.pop(0) if rest and not rest[0].startswith("--") else None
    to_ref = "HEAD"
    from_ref = None
    while rest:
        flag, value, rest = rest[0], rest[1], rest[2:]
        if flag == "--to":
            to_ref = value
        elif flag == "--from":
            from_ref = value

    if from_ref is None:
        from_ref = f"{to_ref}~1"

    with tempfile.TemporaryDirectory() as tmp:
        old = volumes_at_ref(from_ref, tmp)
        new = volumes_at_ref(to_ref, tmp)

    violations = breaking_changes(old, new)
    last_tag = latest_tag(to_ref)
    is_major_bump = proposed is not None and (last_tag is None or parse_semver(proposed)[0] > parse_semver(last_tag)[0])

    for v in violations:
        print(f"{'ALLOWED (major bump)' if is_major_bump else 'FAIL'}: {v}")
    print(f"\n{len(violations)} breaking change(s) from {from_ref} -> {to_ref}" + (f", proposed tag {proposed}" if proposed else ""))
    sys.exit(0 if not violations or is_major_bump else 1)


if __name__ == "__main__":
    main()
