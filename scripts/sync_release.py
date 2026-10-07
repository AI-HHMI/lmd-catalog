"""Rebuild + check the catalog on the Janelia cluster, sync it back, and optionally cut a release.

Run from the local repo (jj, colocated with git) once your work is committed with the `main`
bookmark on it and an empty working copy:

    python3 scripts/sync_release.py

1. push local `main` to the `janelia` remote (its working tree must be clean: updateInstead)
2. over ssh in the cluster clone: rebuild volumes + annotations + pretraining, run pytest, check_integrity and
   check_complete, and commit the rebuild if anything changed (any failure reverts the rebuild)
3. fetch the cluster commit back and fast-forward local `main` to it
4. regenerate the GitHub Pages report + slides in docs/ and commit them if they changed
5. pick the next version from the changes since the latest tag (removed/changed volume: major,
   new volume: minor, any other catalog/schema change: patch), then ask before bumping + tagging
6. push `main` (and the tag, if any) to `origin` and `janelia`

Run it with the local env from `uv sync --extra analysis` (step 4 imports lmd_catalog + matplotlib).
Needs on the cluster: proj/lmd-catalog checked out on `main` (not a detached HEAD, or the push won't update its working tree),
clean, with .venv (`uv sync --extra dev`), and `gh` authed with read:project. The remote step verifies all of this.
"""

import os
import re
import subprocess
import sys
import tempfile

from check_semver import breaking_changes, latest_tag, parse_semver, volumes_at_ref

REMOTE_HOST = "login1.int.janelia.org"
REMOTES = ("origin", "janelia")
CATALOG_FILES = ("lmd_volumes.json", "lmd_annotations.json", "lmd_pretraining.json", "src/lmd_catalog/models.py")
VERSION_FILES = {"pyproject.toml": r'^(version = ")[^"]*(")', "src/lmd_catalog/__init__.py": r'^(__version__ = ")[^"]*(")'}

REMOTE_SCRIPT = """
set -euo pipefail
cd proj/lmd-catalog
branch=$(git symbolic-ref --short -q HEAD || true)
[ "$branch" = main ] || { echo "cluster clone is on '${branch:-a detached HEAD}', not main: run 'git checkout main' in proj/lmd-catalog" >&2; exit 1; }
[ "$(git rev-parse HEAD)" = "$1" ] || { echo "cluster HEAD is not the pushed commit $1 -- its working tree was not updated" >&2; exit 1; }
test -z "$(git status --porcelain)" || { echo "cluster working tree is dirty: 'git checkout -- .' there (or commit) and rerun" >&2; exit 1; }
test -x .venv/bin/python || { echo "no .venv on the cluster: run 'uv sync --extra dev' in proj/lmd-catalog" >&2; exit 1; }
trap 'git checkout -- .' ERR
# Separate statements, not `cmd > tmp && mv`: under set -e a failure on the left of && does not abort.
tmp=$(mktemp)
.venv/bin/python scripts/rebuild_volumes.py > $tmp
mv $tmp lmd_volumes.json
tmp=$(mktemp)
.venv/bin/python scripts/rebuild_annotations.py > $tmp
mv $tmp lmd_annotations.json
tmp=$(mktemp)
.venv/bin/python scripts/rebuild_pretraining.py > $tmp
mv $tmp lmd_pretraining.json
.venv/bin/python -m pytest tests -q
.venv/bin/python scripts/check_integrity.py
.venv/bin/python scripts/check_complete.py
git diff --quiet || git commit -qam "rebuild catalog"
"""


def run(*cmd, **kw) -> str:
    print("$", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, text=True, **kw).stdout


def out(*cmd) -> str:
    return subprocess.run(cmd, check=True, text=True, capture_output=True).stdout.strip()


def check_local_state():
    assert out("jj", "log", "-r", "@", "--no-graph", "-T", "empty") == "true", "working copy has changes: commit them (jj commit), set `main` on that commit, and rerun"
    assert out("jj", "log", "-r", "main & @-", "--no-graph", "-T", "commit_id"), "`main` is not the parent of the working copy: `jj bookmark set main -r @-` first"


def next_version(tag: str) -> str | None:
    """Version implied by the changes from `tag` to main, or None if the catalog is unchanged."""
    with tempfile.TemporaryDirectory() as tmp:
        old, new = volumes_at_ref(tag, tmp), volumes_at_ref("main", tmp)
    major, minor, patch = parse_semver(tag)
    if breaking_changes(old, new, tag):
        return f"v{major + 1}.0.0"
    if set(new) - set(old):
        return f"v{major}.{minor + 1}.0"
    if subprocess.run(["git", "diff", "--quiet", tag, "main", "--", *CATALOG_FILES]).returncode != 0:
        return f"v{major}.{minor}.{patch + 1}"
    return None


def set_version(version: str):
    for path, pattern in VERSION_FILES.items():
        text = open(path).read()
        new_text = re.sub(pattern, rf"\g<1>{version.lstrip('v')}\g<2>", text, count=1, flags=re.M)
        assert new_text != text or version.lstrip("v") in text, f"could not set the version in {path}"
        open(path, "w").write(new_text)


def refresh_docs():
    """Regenerate docs/ (GitHub Pages) from the synced catalog; commit it only if it changed."""
    for script in ("report.py", "slides.py"):
        run(sys.executable, f"scripts/analysis/{script}")
    if out("jj", "log", "-r", "@", "--no-graph", "-T", "empty") != "true":
        run("jj", "commit", "-m", "update report and slides")
        run("jj", "bookmark", "set", "main", "-r", "@-")


def push_main():
    for remote in REMOTES:
        run("jj", "git", "push", "--remote", remote, "--bookmark", "main")


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    check_local_state()
    run("jj", "git", "push", "--remote", "janelia", "--bookmark", "main")
    pushed = out("jj", "log", "-r", "main", "--no-graph", "-T", "commit_id")
    run("ssh", REMOTE_HOST, f"bash -s {pushed}", input=REMOTE_SCRIPT)
    run("jj", "git", "fetch", "--remote", "janelia")
    run("jj", "bookmark", "set", "main", "-r", "main@janelia")
    run("jj", "new", "main")
    refresh_docs()

    run("git", "fetch", "origin", "--tags", "--quiet")
    tag = latest_tag("main")
    version = next_version(tag) if tag else None
    if version is None:
        print(f"\nno catalog changes since {tag}: not tagging")
        push_main()
        return
    assert input(f"\nchanges since {tag} imply {version}. Bump, tag and push? [y/N] ").lower() == "y", "aborted before tagging (nothing pushed to origin)"
    set_version(version)
    run("jj", "commit", "-m", f"bump to {version}")
    run("jj", "bookmark", "set", "main", "-r", "@-")
    push_main()
    run("git", "tag", version, "main")
    for remote in REMOTES:
        run("git", "push", remote, version)


if __name__ == "__main__":
    sys.exit(main())
