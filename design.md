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

## Decision: don't absorb `normalize_windows.yaml` into `#Volume` yet

`lsd_neuron_segmentation`'s data configs carry per-volume `normalize_min`/`normalize_max` percentile
windows, sourced by hand from a separate cluster-side registry
(`/groups/miaai/miaai/lmd-v0.0.1/configs/source/normalize_windows.yaml`, described in that repo's own
README as "a property of a volume's stored intensity distribution... not a per-config artifact" — the same
category of fact this catalog already owns for `path`/`image_key`/`roi`). Considered absorbing it into
`#Volume` as part of the miao-integration work (see the `examples/resolve_volume_config.py` design), and
decided **not yet**:

- The precedent for absorbing an external per-volume registry already exists here (`lmd_annotations.cue`
  imports GitHub Project data, verified end-to-end by `check_complete.py`) — but that trustworthiness came
  from actually building the verification. Nobody has done the equivalent for `normalize_windows.yaml`;
  it isn't mounted/readable from this dev environment, so its coverage (all 417 volumes, or only the
  pretraining-config-curated subset?) and exact semantics are unverified.
- Concrete semantic risk visible in data already gathered: `mouse_liconn_deep.yaml` uses
  `image_key: "raw/s1"` (a downsampled scale) while `mouse_DG_anisotropic.yaml` uses `image_key: "raw"`
  (full res) for related data. If the normalize-window generator computed its percentile window against
  one specific scale's histogram, a `#Volume`-level (not scale-level) field would silently misattribute
  the wrong window to the wrong scale — exactly the kind of silent-drift bug this catalog exists to
  prevent, not introduce.
- Not absorbing it doesn't block consumers today: `VolumeConfig(**resolve_volume_config(name, ...),
  normalize_min=w.min, normalize_max=w.max)` already composes the catalog's resolver with a separate
  lookup into that registry, with zero coupling.
- **Trigger to revisit:** once someone has read `normalize_windows.yaml`'s generator/README and confirmed
  (a) it covers this catalog's full `name` space or a clearly-scoped subset, and (b) it's unambiguous
  about which `image_key`/scale each window applies to, adding `normalize_min?`/`normalize_max?` to
  `#Volume` (populated by a one-off/periodic import script parallel to `scripts/export_catalog.sh`) is a
  good, low-risk follow-up of the same shape as the existing policy-check scripts.
