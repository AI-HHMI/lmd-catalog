"""Verify a proposed version tag honors semver against the catalog's own
history: for every #Volume `name` present both at the last tagged version and
at --to, `path`/`image_key`/`zarr_version` must be identical, and no tracked
name may be removed -- unless the proposed version's major component is
greater than the last tag's. Annotation fields are exempt: `gt_ingested_path`
and friends are meant to be mutated in place as labeling rounds land (see
CLAUDE.md), so their history is not a compatibility break.

Run before creating a new tag, no /groups mount needed (diffs catalog
metadata only, via `git show` + `cue export` -- needs `cue` on PATH):

    python3 scripts/check_semver.py v0.2.0
    python3 scripts/check_semver.py v0.2.0 --from v0.1.0 --to HEAD
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

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
    ref_dir = os.path.join(tmp_root, ref.replace("/", "_"))
    os.makedirs(ref_dir)
    for fname in ("lmd_volumes.cue", "lmd_annotations.cue"):
        content = run(["git", "show", f"{ref}:{fname}"])
        with open(os.path.join(ref_dir, fname), "w") as f:
            f.write(content)
    volumes = json.loads(run(["cue", "export", ".", "-e", "volumes"], cwd=ref_dir))
    return {v["name"]: v for v in volumes}


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
    proposed = sys.argv[1]
    to_ref = "HEAD"
    from_ref = None
    rest = sys.argv[2:]
    while rest:
        flag, value, rest = rest[0], rest[1], rest[2:]
        if flag == "--to":
            to_ref = value
        elif flag == "--from":
            from_ref = value

    if from_ref is None:
        from_ref = latest_tag(to_ref)
        if from_ref is None:
            print(f"no prior vN.N.N tag reachable from {to_ref} -- {proposed} is a baseline, nothing to compare")
            sys.exit(0)

    with tempfile.TemporaryDirectory() as tmp:
        old = volumes_at_ref(from_ref, tmp)
        new = volumes_at_ref(to_ref, tmp)

    violations = breaking_changes(old, new)
    is_major_bump = parse_semver(proposed)[0] > parse_semver(from_ref)[0]

    for v in violations:
        print(f"{'ALLOWED (major bump)' if is_major_bump else 'FAIL'}: {v}")
    print(f"\n{len(violations)} breaking change(s) from {from_ref} -> {to_ref}, proposed tag {proposed}")
    sys.exit(0 if not violations or is_major_bump else 1)


if __name__ == "__main__":
    main()
