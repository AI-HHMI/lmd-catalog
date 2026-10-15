#!/usr/bin/env bash
# Daily dashboard snapshot, run by cron on submit.int.janelia.org (login nodes don't allow crontab).
#
# In a worktree of this clone (~/lmd-dashboard, made on the first run, used by nothing else) it rebuilds the catalog from
# today's disk and GitHub Projects, renders docs/, and pushes docs/ as the root of origin's `gh-pages` branch. It never
# commits to main, tags, or touches this clone's own working tree, so sync_release.py is unaffected. Releases stay manual.
#
#   crontab -e:  0 23 * * * $HOME/proj/lmd-catalog/scripts/daily_dashboard.sh >> $HOME/lmd-dashboard.log 2>&1
#
# GitHub Pages must serve the gh-pages branch (root); main's docs/ is then only the copy matching each release.
set -euo pipefail

export PATH="$HOME/.local/share/mise/shims:$PATH"  # cron's PATH has no uv or gh
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WT="$HOME/lmd-dashboard"

echo "== $(date '+%F %T %Z')"
[ -d "$WT" ] || git -C "$REPO" worktree add --detach "$WT" main
cd "$WT"
git checkout --quiet --detach --force main  # the clone's main (refs are shared); drops yesterday's rebuilt JSON
uv sync --quiet --extra dev --extra analysis  # uv.lock is gitignored, so this resolves (and locks) in the worktree
py="$WT/.venv/bin/python"

tmp=$(mktemp)
"$py" scripts/rebuild_volumes.py > "$tmp"
mv "$tmp" lmd_volumes.json
"$py" scripts/sync_github.py || echo "GitHub sync failed (above); using the committed annotations/pretraining"  # writes nothing unless it all succeeds
"$py" scripts/check_integrity.py || echo "integrity violations above; publishing the snapshot anyway"
"$py" scripts/analysis/report.py
"$py" scripts/analysis/slides.py

git fetch --quiet origin gh-pages || true  # absent before the first publish
git add --force docs
tree=$(git write-tree --prefix=docs/)
parent=$(git rev-parse --verify --quiet origin/gh-pages || true)
commit=$(git commit-tree "$tree" ${parent:+-p "$parent"} -m "dashboard snapshot $(date '+%F %H:%M %Z')")
git push --quiet origin "$commit:refs/heads/gh-pages"
git checkout --quiet --detach --force main
echo "published $commit"
