# Requirements status

Against the wants list in `readme.md`. Given want 0 (no writer changes), this is read-side only —
not a menu of alternative data-versioning systems, just the one system (git-tagged CUE catalog,
name-keyed resolution) and how much of it exists.

| # | Want | Status |
|---|---|---|
| 0 | No change for zarr writers | Satisfied by construction — everything built so far is read-side only |
| 1 | Consumers don't have data move out from under them | Satisfied — `name` -> `path` stability + `examples/resolve_training_config.py` pattern |
| 2 | Compatible with Fileglancer / Neuroglancer | Partial. `fileglancer_path` already exists per-entry. No Neuroglancer equivalent field or generator yet — needs a known URL/scheme convention before it can be built |
| 3 | Add new zarrs/keys/metadata | Satisfied — append-only catalog, checked by `scripts/check_complete.py` |
| 4 | Specify subvolumes for train/test | Satisfied for the "which region is annotated" case — typed `#ROI` on `#AnnotationItem`, resolvable via `examples/resolve_roi.py` into a consumer's own axis order (verified against miao's ZYX `bounding_box`). No train/test *split* concept yet — today's real usage has a single annotated region used to restrict training only (test reuses the same volume unrestricted); add a `split` tag if/when a genuine held-out region shows up |
| 5 | Fix and update metadata | Satisfied — in-place edit + git/jj history is the versioning |
| 6 | Auto-verify no breakage except on major bumps | Satisfied for this repo's own tag history — `scripts/check_semver.py`, tested against a simulated rename (correctly failed a minor bump, allowed a major one). Deliberately scoped to *this repo's* history only: whether a specific consumer's pin-bump is safe for *them* is a separate question that belongs in the consumer, not here (see readme.md discussion) |
| 7 | Auto-verify paths valid/complete | Satisfied — `scripts/check_integrity.py` + `scripts/check_complete.py`, tested against the real `/groups` filesystem and caught a real stale-path bug (`FlyLICONN_FlyID49_40XW005/006`) |
