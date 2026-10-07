"""Refresh lmd_annotations.json and lmd_pretraining.json from the GitHub Projects -- the rare step that spends the
account's GraphQL budget (about 2200 of its 5000 points/hour, shared by every gh call).

Run it locally when the projects have changed (needs `gh` authed with read:project; no /groups, no cluster):

    python3 scripts/sync_github.py

It runs rebuild_annotations.py and rebuild_pretraining.py, checks that the new data loads into the catalog
models, and only then replaces the two files and prints what changed. Nothing is committed or pushed: commit the
result (and set `main` on it) before running sync_release.py, which rebuilds volumes and does the release.
"""

import json
import os
import subprocess
import sys

try:
    from lmd_catalog import Catalog
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
    from lmd_catalog import Catalog

# Refuse to start with less than this left: two real runs used 2152 and 2253 points.
MIN_GRAPHQL_POINTS = 3000
# name -> (rebuild script, data file, key of the entry list in that file)
SOURCES = {
    "annotations": ("scripts/rebuild_annotations.py", "lmd_annotations.json", "annotations"),
    "pretraining": ("scripts/rebuild_pretraining.py", "lmd_pretraining.json", "pretraining"),
}


def graphql_budget() -> tuple:
    """(remaining, used, resetAt) of the shared GitHub GraphQL budget. This query itself costs 1 point."""
    query = "query { rateLimit { remaining used resetAt } }"
    result = subprocess.run(["gh", "api", "graphql", "-f", f"query={query}"], capture_output=True, text=True)
    assert result.returncode == 0, f"gh api graphql failed: {result.stderr}"
    r = json.loads(result.stdout)["data"]["rateLimit"]
    return r["remaining"], r["used"], r["resetAt"]


def rebuild(script: str) -> dict:
    print("$", script, flush=True)
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    assert result.returncode == 0, f"{script} failed:\n{result.stderr}"
    return json.loads(result.stdout)


def describe_changes(name: str, key: str, old: dict, new: dict) -> str:
    entry_key = lambda e: (e["issue"]["repository"], e["issue"]["number"])
    before, after = {entry_key(e): e for e in old[key]}, {entry_key(e): e for e in new[key]}
    added, removed = after.keys() - before.keys(), before.keys() - after.keys()
    changed = [k for k in after.keys() & before.keys() if after[k] != before[k]]
    return f"{name}: {len(before)} -> {len(after)} entries ({len(added)} added, {len(removed)} removed, {len(changed)} changed)"


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    remaining, used_before, resets = graphql_budget()
    assert remaining >= MIN_GRAPHQL_POINTS, f"GitHub GraphQL budget too low: {remaining} points left, resets {resets} (UTC). Wait and rerun; nothing was changed."

    new = {name: rebuild(script) for name, (script, _, _) in SOURCES.items()}  # fetch everything before writing anything
    Catalog(annotations_data=new["annotations"], pretraining_data=new["pretraining"])  # raises if the data no longer fits the models

    for name, (_, path, key) in SOURCES.items():
        old = json.load(open(path))
        print(describe_changes(name, key, old, new[name]))
        with open(path + ".tmp", "w") as f:
            f.write(json.dumps(new[name], indent=2) + "\n")
        os.replace(path + ".tmp", path)
    print(f"GitHub GraphQL points used: {graphql_budget()[1] - used_before} (shared budget resets {resets})")
    print("Not committed. Commit these files (jj commit; jj bookmark set main -r @-), then run scripts/sync_release.py.")


if __name__ == "__main__":
    main()
