# Summary of this repo's work

## Starting point

`lmd-data-versioning` is a catalog (not a program) for the "lmd" microscopy/connectomics corpus at
`/groups/miaai/miaai/lmd-v0.0.1/data`. It started as two hand-authored CUE files mixing schema and literal
data: `lmd_volumes.cue` (every `.zarr` volume, discovered by walking the directory tree) and
`lmd_annotations.cue` (annotation-tracking metadata synced by hand from the `mia_annotation` GitHub
Project), joined by a live `tracked_by` comprehension.

## The motivating problem

Looked at `lsd_neuron_segmentation`'s jj history and found real, repeated churn: three separate commits
(`d55dd60639d3`, `948cdcbfe966`, `800b186d1851`) hand-repointed the same hardcoded paths/keys across
multiple YAML configs as the corpus reorganized, and one of those hand-edits caused a real Cortex/
Hippocampus data swap bug. This validated the premise: consumers need stable names to resolve through,
not paths to copy-paste and let drift.

## Policy checks (catch drift automatically)

- **`scripts/check_integrity.py`** — is everything the catalog claims *true*: no duplicate names/issue
  numbers, every `source_paths` entry resolves to a real volume, every volume's path/zarr-version-marker/
  `image_key` exists on disk, `roi` matches its source `bbox`/`bbox_size` text, and GT/proofread paths
  exist once status reaches a terminal state. **Caught a real bug on first run**: `FlyLICONN_FlyID49_
  40XW005/006` (issues #18/#19) still pointed at a pre-reorg `liconn_data/` path that no longer existed —
  fixed by repointing to the live reorganized volume.
- **`scripts/check_complete.py`** — the reverse direction: walks the filesystem for `.zarr` stores missing
  from the catalog, and diffs the live GitHub Project against `annotations` for un-synced items.
- **`scripts/check_semver.py`** — verifies a proposed version tag honors semver against this repo's own
  tag history: any existing volume's `path`/`image_key`/`zarr_version` must be unchanged (or removed)
  unless the major version bumped. Deliberately scoped to this repo's own history only — whether a
  specific consumer's pin-bump is safe belongs in that consumer, not here (see `readme.md`). Tested against
  simulated breaking changes in both `.cue`-only and post-split JSON-data refs.

## Typed ROI (`#ROI`)

Added a typed, axis-labeled, order-free region field (`{x,y,z}: [min,max]`) to `#AnnotationItem`,
normalizing two incompatible free-text `bbox`/`bbox_size` formats that had coexisted in the data
(range-labeled vs. bare offset+size triples). `check_integrity.py` now cross-checks `roi` against the
source text so the two can't silently drift.

## Example consumers (`examples/`)

Three, showing the name-keyed resolution pattern at increasing levels of generality:
- **`resolve_training_config.py`** — resolves a volume's `train_data_path`/`image_key`/`segmentation_key`
  by name, matching one consumer's (`lsd_neuron_segmentation`) YAML dialect. Verified against its real
  config.
- **`resolve_roi.py`** — resolves `roi` into a caller-specified spatial axis order.
- **`resolve_volume_config.py`** — resolves directly into `miao`'s real `VolumeConfig` pydantic field
  names (`label_key`, not `segmentation_key`; axis-order-parameterized `bounding_box`), built after
  exploring `miao` and `lsd_neuron_segmentation`'s `miao_pipeline.py` in depth. That exploration also
  surfaced two real, live bugs in `lsd_neuron_segmentation` (a silently-ignored `raw_min`/`raw_max`
  field-name mismatch, and GT-key drift across 4 duplicated config files) kept as motivating evidence only
  — no changes made to that repo. **Open thread, not resolved**: whether this resolver should live in the
  catalog at all, since "fully specify a miao config" arguably belongs entirely in a model-owning repo
  (`mia-muvit`/`mia-train`/`lsd_neuron_segmentation` each build their own miao configs already) — raised,
  not settled.

## Schema/data separation

Split `lmd_volumes.cue`/`lmd_annotations.cue` down to schema only, moved the literal data to sibling
`lmd_volumes.json`/`lmd_annotations.json`, and added two rebuild scripts so the data is never hand-typed:
- **`scripts/rebuild_volumes.py`** — walks `#DataRoot` for `.zarr` dirs, derives `name`, probes
  `.zgroup`/`zarr.json` for `zarr_version`, applies one hardcoded `image_key` override. Verified for real
  against the live filesystem: **the corpus had grown from 417 to 838 volumes (69 to 102 datasets)** since
  the last sync — purely additive (zero diffs among the original 417), new entries are public EM benchmark
  datasets (CellMap, CREMI, Lucchi, MitoEM, UroCell).
- **`scripts/rebuild_annotations.py`** — calls `gh project item-list`, maps fields into `#AnnotationItem`
  shape, computes `roi` via the shared **`scripts/roi_parse.py`**. Verified against the live GitHub
  Project: the initially-guessed field-name mapping was wrong (gh's real JSON keys follow a
  `data_Modality`/`wK_Ann_Link` casing pattern, not "Title Case"), fixed against a live response. Found 15
  legitimate upstream updates plus one new annotation item, and — importantly — found that issues #18/#19's
  GitHub fields *themselves* still had the stale path fixed locally earlier, which would have been
  silently reintroduced by a naive rebuild. Pinned the correct values locally
  (`PENDING_UPSTREAM_FIXES`) rather than editing the shared GitHub Project directly, per a human-in-the-loop
  principle (external systems of record get hand-corrected by a human, not by automation acting on their
  behalf) discussed and agreed on mid-session.
- Discovered along the way: CUE's package loader does not auto-include sibling `.json` files, and `@embed`
  requires a real CUE module this repo deliberately doesn't have (confirmed via
  `cannot embed files when not in a module`) — `export_catalog.sh`, `check_semver.py`, and `CLAUDE.md`'s
  documented commands were all updated to name all four catalog files explicitly.

## Design records

- **`readme.md`** — the original design-problem framing and requirements ("wants") list.
- **`design.md`** — requirements-status table against those wants, plus two recorded decisions: not
  absorbing the separate `normalize_windows.yaml` registry into `#Volume` yet (with a concrete trigger to
  revisit), and the schema/data split rationale.
- **`schema.md`** — CUE vs. Python vs. JSON Schema for this catalog's specific needs. First draft
  overstated CUE's case; revised after testing claims empirically rather than arguing them:
  - `cue vet` genuinely reports all independent violations in one pass (tested with 3 simultaneous
    violations) — but so does pydantic's `ValidationError`, with cleaner output. Not CUE-exclusive.
  - `cue trim` (strips fields matching their schema default) works exactly as advertised on literal `.cue`
    data, but tested directly against JSON and it left the file completely untouched — it doesn't operate
    on JSON at all. The schema/data split traded this convenience away; `rebuild_volumes.py`'s manual
    "omit if default" logic does by hand what `cue trim` would've automated had data stayed as CUE
    literals.
  - Clarified what metadata belongs where: voxel size/axes/shape live in the zarr's own OME-NGFF metadata
    and are never duplicated; `name`/`tracked_by`/`roi` have no zarr-side representation at all;
    `zarr_version`/`image_key` are the interesting overlap, technically inspectable from the store but
    duplicated in the catalog because `miao.config.VolumeConfig` requires them explicitly (its own
    `detect_zarr_version` helper exists but is never called).
  - Net conclusion narrowed to two genuine CUE-specific advantages (the cross-file join is automatic by
    package scope; the unification-based type system is more principled than Python's split
    static-hints/runtime-library story) rather than the broader "avoids imperative glue" claim, which
    doesn't hold — `check_integrity.py`/`check_complete.py`/both rebuild scripts are unavoidably
    imperative Python regardless of schema language, since none of CUE/pydantic/JSON Schema can see a live
    filesystem or call `gh`.
- **`discussion.md`** — git-versioned snapshots vs. an append-only event log (no git) for this catalog.
  Core argument: event sourcing earns its keep least when the ground truth is already external and
  re-derivable, which is exactly this catalog's situation (a directory walk, the GitHub Project). Surfaced
  two concrete follow-ups: GitHub already retains full per-field history for annotations that
  `rebuild_annotations.py` discards by only pulling the latest snapshot; and `rebuild_volumes.py` discards
  real filesystem `ctime`/`mtime` per volume, relying only on "whenever the rebuild happened to run" as a
  time signal (the NernLab volume/annotation sat unnoticed for 2+ days as a direct example). Addendum:
  checked whether anything in `#AnnotationItem` is actually derived (only `roi` is) and concluded the
  reason annotation authorship stays in GitHub isn't derivation, it's that annotators are a different,
  non-technical audience than this repo's consumers, and GitHub Projects already solves concurrent
  multi-user editing and per-field audit trail for free — the same repo/consumer boundary argument as the
  `resolve_volume_config.py` open thread, mirrored to the other end of the pipeline.
- **`workflow.md`** — the five real semi-automated workflows this repo has (rebuild volumes, rebuild
  annotations, triage a policy-check violation, evolve the schema, cut a release), each grounded in
  something actually exercised this session, plus a `Human` interface (Go) adapted from the earlier
  zarr-snapshot design — same philosophy (`Edit`/`Decide` are things a person does themselves, not
  permission gates) but with this repo's actual nouns (git commits/tags, CUE/JSON files, GitHub Project
  fields). Gives `PENDING_UPSTREAM_FIXES` a real fix: a `PendingFix` queue that gets re-tested against each
  fresh GitHub pull instead of silently pinning forever. Verified the Go actually compiles (`gofmt`/
  `go vet`/`go build` clean against all five flows plus stubs for the undefined helpers).

## Current state

Everything above is committed (`jj`/`git`, colocated). No version tag has been cut yet.

**Open items:**
- `resolve_volume_config.py`'s fate (keep as a catalog-shipped miao-schema resolver, or retire it in favor
  of consumers owning their own translation entirely) — raised, not decided.
- Neuroglancer compatibility (`design.md` want #2) — still partial; `fileglancer_path` exists, no
  Neuroglancer equivalent yet.
- `normalize_windows.yaml` absorption — deliberately deferred, trigger condition documented in `design.md`.
- No real version tag cut yet, so `check_semver.py` has only been exercised against simulated history.

**Follow-ups suggested but not implemented** (from `discussion.md`/`workflow.md`):
- Record real filesystem `ctime` per volume in `rebuild_volumes.py`'s output instead of relying solely on
  rebuild-run timing as the only time signal.
- If point-in-time annotation history is ever needed, query GitHub's own item timeline rather than build a
  parallel log.
- `workflow.md`'s `Human` interface and `PendingFix` queue are a design, not yet wired into the actual
  Python scripts (`rebuild_annotations.py` still uses the plain `PENDING_UPSTREAM_FIXES` dict).
