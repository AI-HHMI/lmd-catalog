# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This repository provides **`lmd-catalog` (`src/lmd_catalog`)**: an installable, SemVer-versioned Python package and client SDK (`import lmd_catalog as lmd`) for the "lmd" (Large Microscopy Dataset) corpus at `/groups/miaai/miaai/lmd-v0.0.1/data`.

The data and schema are structured as follows:
- **Canonical Schema**: Defined strictly in pure Pydantic v2 models ([`src/lmd_catalog/models.py`](file:///Users/broaddusc/proj/lmd-data-versioning/src/lmd_catalog/models.py)) with closed `Literal` enums (`AnnotationStatus`, `DataModality`, etc.) and `extra="forbid"`.
- **Reference Data**: Sibling JSON files (`lmd_volumes.json`, `lmd_annotations.json`), also bundled into package data (`src/lmd_catalog/data/`):
  - `lmd_volumes.json` — 838 volumes across 102 datasets, mechanically discovered by directory walk.
  - `lmd_annotations.json` — 27 annotation issues synced from GitHub Projects (`AI-HHMI/projects/1`).
- **Miao Integration**: Directly outputs typed `miao.config.VolumeConfig` instances via `.to_miao()` without eager PyTorch or CUDA imports.

`scripts/rebuild_volumes.py` and `scripts/rebuild_annotations.py` regenerate the data from ground truth; `tests/test_catalog.py` verifies all 838 volumes resolve to valid `miao.config.VolumeConfig` models. Never hand-edit the `.json` files directly.

## Commands

### Python Package & Test Suite

```sh
# Run fast test suite (<50ms, verifies all 838 volumes resolve to miao VolumeConfig)
pytest tests/ -v
```

```python
import lmd_catalog as lmd

# Fast lookup by name or path (<50ms import, zero torch/CUDA initialization)
vol = lmd.get("em-UNKNOWN-lucchi-hippocampus/crop-001_train")

# Resolve directly into a miao VolumeConfig (pure Pydantic)
cfg = vol.to_miao(spatial_axes="zyx")

# Query and filter
with_gt = lmd.find(has_ground_truth=True)
url = vol.fileglancer_url()
```

## Rebuilding the data

`scripts/rebuild_volumes.py` (needs `/groups` mounted, no `gh`) walks `#DataRoot` for `.zarr` directories,
derives each `name`, probes for `.zgroup`/`zarr.json` to set `zarr_version` (omitted when it's the default
`zarr3`), and applies one hardcoded `image_key` override (the one volume in the corpus with no `raw`
wrapper group) — this is fully mechanical, verified to reproduce the current data with zero diff. It also
lists a volume's own `labels/` subgroup (mechanical directory listing, omitted when empty) into
`label_keys` — this is what lets `#VolumeEntry.has_ground_truth` cover public benchmark datasets (CellMap,
CREMI, Lucchi, MitoEM, UroCell) that ship ingested ground truth directly in their own zarr store with no
tracking issue, not just volumes tracked by an annotation with a `gt_ingested_path`.

`scripts/rebuild_annotations.py` (needs `gh` authenticated with `read:project`, no `/groups`) calls
`gh project item-list 1 --owner AI-HHMI --format json --limit 200` and maps its fields into `#AnnotationItem`
shape, computing `roi` from `bbox`/`bbox_size` via `scripts/roi_parse.py` (shared with
`check_integrity.py`'s consistency check — import it, don't duplicate the parsing). `FIELD_MAP`'s keys are
gh's own JSON-ified project column names (verified against a live response — see the module docstring for
the exact naming rule gh applies). `PENDING_UPSTREAM_FIXES` pins the two annotation items whose GitHub
Project fields still have a stale path a human hasn't corrected upstream yet (see "Editing the data"
above); this is a human-in-the-loop seam, not something to silently override — remove an entry once
someone fixes it in the GitHub UI, don't fix it by editing the GH Project via `gh` from here.

```sh
# Both rebuild scripts read the existing JSON (volumes: hand-set normalize_min/
# normalize_max; annotations: hand-set shape/voxelsize/axes), so redirecting stdout
# straight onto it truncates the file before Python can read it back -- write to a
# temp file and move it into place instead.
python3 scripts/rebuild_volumes.py > /tmp/lmd_volumes.json.new && mv /tmp/lmd_volumes.json.new lmd_volumes.json
python3 scripts/rebuild_annotations.py > /tmp/lmd_annotations.json.new && mv /tmp/lmd_annotations.json.new lmd_annotations.json
```

Two fields exist only to date the data for the growth charts in `scripts/analysis/`:
`#Volume.added` is the store directory's mtime the *first* time `rebuild_volumes.py` sees the volume (the
filesystem exposes no birth time; once recorded it is carried over, so later writes to the store don't move
it, and a bulk re-write of the tree shows up as one big step), and `#AnnotationItem.created_at` is the
GitHub issue's creation date, fetched by `rebuild_annotations.py` with `gh issue list` (the project items
don't carry it). `python scripts/analysis/report.py` and `slides.py` write `report.html` / `slides.html`.

## Policy checks (scripts/)

The catalog promises consumers a stable set of names — once published, a `#Volume`'s `path`/`image_key`
never moves; only additions (new volumes/keys) or an explicit version bump are allowed. `scripts/`
enforces that promise is actually true, in both directions:

```sh
python3 scripts/check_integrity.py  # needs /groups mounted; verifies paths, bboxes, and GT exist
python3 scripts/check_complete.py   # needs /groups mounted + `gh auth refresh -s read:project`
```


- `check_integrity.py` — is everything the catalog claims *true*: no duplicate `name`s or tracked issue
  numbers, every `source_paths` entry under `#DataRoot` resolves to a real `#Volume.path`, every volume's
  path/zarr-version-marker/`image_key` exists on disk, every annotation's `source_paths` exists on disk
  (unconditionally — annotated source data must already exist), and `gt_ingested_path`/
  `proofread_ingested_path` exist once an item reaches `"GT_Ingested"`/`"Proofread_ingested"` status.
- `check_complete.py` — the reverse direction: is everything *real* reflected in the catalog. Walks
  `#DataRoot` for `.zarr` stores missing from `volumes` (or catalog entries no longer on disk), and diffs
  the live `mia_annotation` GitHub Project against `annotations` for un-synced or removed items.
- Both checkers are pure-stdlib Python (run on the cluster where external tools may not be installed).
- These are not wired into CI yet — run manually after rebuilding catalog data, and before cutting a
  new version tag.
- `check_semver.py` — verify the catalog honors semver against its own history: for every `#Volume`
  `name` present at both `HEAD`'s parent commit (the default; `--from` accepts any ref, e.g. a tag) and
  `HEAD`, `path`/`image_key`/`zarr_version` must be unchanged and the name must not be removed, unless a
  proposed version is given whose major component exceeds the latest `vN.N.N` tag's. It compares committed
  revisions, so commit a rebuild before running it. Needs only Python + git history (no `/groups` mount) —
  reads `lmd_volumes.json` across git revisions to compare volume definitions (with fallback to older
  formats if diffing against historical tags that predate the JSON catalog).
  Deliberately does not check
  `annotations` fields: `gt_ingested_path` and friends are meant to mutate in place as labeling rounds
  land (see "Editing the data" above), so that isn't a compatibility break. This check is scoped to this
  repo's own tag history; it does *not* verify that any specific consumer's usage stays safe when they
  bump their pin from one commit to another — that check belongs in the consumer, since only the consumer
  knows which `name`s/fields it actually depends on.

  ```sh
  python3 scripts/check_semver.py                           # compares HEAD against its parent commit
  python3 scripts/check_semver.py v1.0.0                    # same, but breaking changes are OK if v1.0.0 bumps the latest tag's major
  python3 scripts/check_semver.py --from v0.1.0 --to HEAD   # compare against a tag instead
  ```

## Release workflow (scripts/sync_release.py)

`python3 scripts/sync_release.py` automates the whole loop from the local jj repo: pushes `main` to the
`janelia` remote, then over ssh in the cluster clone rebuilds volumes + annotations, runs pytest /
`check_integrity.py` / `check_complete.py` (a failure reverts the rebuild), and commits the result. It then
fetches that commit back, fast-forwards local `main`, and picks the next version from the changes since the
latest tag (removed/changed volume: major, new volume: minor, other catalog/schema change: patch). It asks
before bumping the version files, tagging, and pushing `main` + the tag to `origin` and `janelia`.
Requires an empty working copy with `main` on its parent, a clean cluster working tree, `proj/lmd-catalog/.venv`
on the cluster (`uv sync --extra dev`), and `gh` authed with `read:project` there.

## Architecture: the volumes ↔ annotations join

- `#Volume.path` is derived (`#DataRoot + "/" + name + ".zarr"`), not stored — every volume in the corpus
  follows this convention, so no entry overrides it.
- `VolumeEntry.tracked_by` is an in-memory join back into `annotations`, computed automatically when
  `Catalog` loads volumes (`Catalog.__init__` indexes annotations by path). It is not persisted in
  `lmd_volumes.json` — do not add a manual `tracked_by` field to volume entries.
- The join is one-directional in the source text: `#AnnotationItem.source_paths` usually matches a
  `#Volume.path` 1:1, but not always — some annotation items track paths outside `#DataRoot` entirely
  (e.g. `/nrs` scratch space, or the legacy `liconn_data/` layout), and a few cover more than one crop
  (e.g. a paired `fullvol` + `sub` crop). These won't resolve to any `tracked_by` entry on the `volumes`
  side.
- Most volumes have no annotation-tracking issue yet (`tracked_by` is empty) — that's expected, not a
  data gap to fix.

## Editing the data

- Don't hand-edit `lmd_volumes.json`/`lmd_annotations.json` — regenerate with the matching `scripts/rebuild_*.py`
  (see "Rebuilding the data") instead. `lmd_volumes.json` is fully mechanical. The one field in
  `lmd_annotations.json` that isn't a straight GitHub Project sync is `roi`, which
  `rebuild_annotations.py` computes itself from `bbox`/`bbox_size`.
- JSON has no comment syntax, so the old per-dataset `// <dataset-name>` grouping comments are gone —
  `rebuild_volumes.py` sorts by `name` instead, which reproduces the same grouped/alphabetical order
  since `name` is `<dataset>/<crop>`.
- When adding an annotation item, `source_paths` must be an absolute path list; match it against an
  existing `#Volume.path` when the data lives under `#DataRoot` so the `tracked_by` join resolves.
- Enum-like fields (`AnnotationStatus`, `AnnotationDataset`, `AnnotationTool`, `ModelOrganism`,
  `DataModality`, `AnnotationTask`, `StructureOfInterest`, `Priority`) are closed `Literal` types in
  `src/lmd_catalog/models.py` — adding a new value in an entry requires extending the definition there first,
  or Pydantic validation / pytest will fail.
- After editing any file or schema, run `pytest tests/ -v` before considering the change done.
- `#AnnotationItem.roi` is a parsed, axis-labeled, order-free version of the free-text `bbox`/
  `bbox_size` fields (`{x: [min,max], y: [min,max], z: [min,max]}`, max exclusive, level-0 voxel units).
  When adding/editing `bbox`/`bbox_size`, add/update `roi` to match — `check_integrity.py`'s
  `check_roi_matches_bbox_text` will fail otherwise. `bbox`/`bbox_size` show up in three different formats
  in practice (`"X:908-1390, ..."` range-labeled, a bare `"13720, 16025, 3570"` offset triple, or a labeled
  `"X=1013, Y=1013, Z=580,"` offset, the last two paired with an XYZ `bbox_size` triple such as `"482×482×194 vox"`) — the check handles both, but don't invent a third without updating it.

## Example consumers (examples/)

`examples/resolve_training_config.py` shows the intended integration pattern: a consumer resolves a
volume's `train_data_path`/`image_key`/`segmentation_key` by its stable `name`, instead of hardcoding
them. This is the fix for the churn seen in `lsd_neuron_segmentation`'s history — three separate commits
(`d55dd60639d3`, `948cdcbfe966`, `800b186d1851`) hand-repointed the same hardcoded paths/keys across
multiple YAML configs as this corpus reorganized, and one of those hand-edits caused a real Cortex/
Hippocampus data swap bug. A `name`-keyed lookup can't reproduce that swap, since there's no copy-pasted
path to mix up.

`examples/resolve_roi.py` shows the same pattern for subvolumes: resolves `#AnnotationItem.roi` into a
specific consumer's expected axis order (e.g. miao's ZYX `bounding_box: [[z_min,z_max],[y_min,y_max],
[x_min,x_max]]`) instead of parsing the free-text `bbox` field. `roi` only covers "which region is
annotated" today — there's no train/test split concept yet, since no consumer currently needs one (see
archive/design.md #4).

```sh
python3 examples/resolve_training_config.py "exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001"
```

Verified to reproduce the exact `train_data_path`/`image_key`/`segmentation_key` currently hand-written in
`lsd_neuron_segmentation/cfg/LICONN_AI_training/mouse_DG_anisotropic.yaml`.

`examples/resolve_volume_config.py` is the recommended pattern for a *new* consumer: it resolves a `name`
directly into miao's real `VolumeConfig` field names (`miao.config.VolumeConfig`, miao>=0.4) —
`label_key` not `segmentation_key`, `bounding_box` in the caller's own `output_axes` spatial order (a
`spatial_axes` parameter, not a hardcoded ZYX) — rather than a bespoke per-consumer dialect. `VolumeConfig`/
`MiaoConfig` are plain pydantic models constructible directly in Python, so a consumer can do
`VolumeConfig(**resolve_volume_config(name, volumes, annotations))` with no YAML involved. Two contracts
worth knowing: it never emits `exp_factor` (every volume in this catalog already bakes any expansion
correction into its own OME multiscale transform; miao applies that automatically, and setting
`exp_factor` on top double-applies it), and it raises rather than guessing when a `name` is tracked by more
than one annotation item (e.g. the `lm-zebrafish-Betzig-mosaic` corpus, annotated per-timepoint — pick one
by issue number yourself in that case). Verified against real drift: it resolves
`labels/manual_gt-cell-final` for the mouse DG crop, matching `mouse_DG_anisotropic.yaml`/
`mouse_DG_smoke.yaml` but *not* matching `cfg/data/mouse_liconn_deep.yaml` or its `benchmark_models_data/`
copy, which have hand-copied two different, older GT-key snapshots (`manual_gt-cell-snap_04142026/s0`,
`manual_gt-cell-snap_07072026/s0`) — exactly the kind of drift a name-keyed resolver surfaces instead of
letting three answers coexist silently.

```sh
python3 examples/resolve_volume_config.py "exm-mouse-liconn-DG-20250809_ExPID19-02_2ndGel_C5_Atto488_40XW_002/crop-001"
```
