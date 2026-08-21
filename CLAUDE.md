# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A CUE data catalog (not a program) for the "lmd" (Large Microscopy Dataset) corpus at
`/groups/miaai/miaai/lmd-v0.0.1/data`. Two files, both `package lmd`, no `cue.mod` (module-less —
`cue` commands work directly against the two files in this directory):

- `lmd_volumes.cue` — every `.zarr` volume actually present under `#DataRoot`, found by walking the
  directory tree directly. Defines `#Volume` and the `volumes: [...#Volume]` list (417 volumes across
  69 datasets as of the last regeneration — see the file's header comment for the current count).
- `lmd_annotations.cue` — annotation-tracking metadata synced by hand from the `mia_annotation` GitHub
  Project (`gh project item-list 1 --owner AI-HHMI --format json --limit 100`). Defines `#AnnotationItem`
  and the `annotations: [...#AnnotationItem]` list (26 annotation-tracking issues as of the last sync),
  covering the crop-proposal → annotation → ingestion → proofreading workflow for a subset of `volumes`.

There is no build, package manager, test suite, or application code — this is reference data plus CUE
schema constraints. Regeneration of either list from its source of truth (directory walk / GitHub
Project) is manual; there is no automation.

## Commands

```sh
cue vet ./...                                  # validate both files against their schemas
cue eval . -e 'len(volumes)'                   # quick queries against the data
cue export . -e 'volumes[0]'                   # export a value as JSON
cue export . -e 'volumes' > volumes.json        # dump full list as JSON
```

Use `cue export`/`cue eval` with a `-e <expr>` filter (CUE comprehensions, e.g.
`[for v in volumes if <cond> {v.name}]`) to answer questions about the catalog rather than grepping the
raw `.cue` source — the join logic (`tracked_by`) and defaults (`path`, `zarr_version`) only resolve
through CUE evaluation.

## Architecture: the volumes ↔ annotations join

- `#Volume.path` is derived (`#DataRoot + "/" + name + ".zarr"`), not stored — every volume in the corpus
  follows this convention, so no entry overrides it.
- `#Volume.tracked_by` is a **live** CUE comprehension that joins back into `annotations`:
  `[for a in annotations if list.Contains(a.source_paths, path) {a}]`. It is computed at evaluation time,
  not hand-maintained — do not add a manual `tracked_by` field to a volume entry.
- The join is one-directional in the source text: `#AnnotationItem.source_paths` usually matches a
  `#Volume.path` 1:1, but not always — some annotation items track paths outside `#DataRoot` entirely
  (e.g. `/nrs` scratch space, or the legacy `liconn_data/` layout), and a few cover more than one crop
  (e.g. a paired `fullvol` + `sub` crop). These won't resolve to any `tracked_by` entry on the `volumes`
  side.
- Most volumes have no annotation-tracking issue yet (`tracked_by` is empty) — that's expected, not a
  data gap to fix.

## Editing the data

- Preserve the per-dataset `// <dataset-name>` grouping comments in `volumes:` — volumes are grouped by
  dataset directory, alphabetically, with one comment line above the first crop of each dataset.
- When adding an annotation item, `source_paths` must be an absolute path list; match it against an
  existing `#Volume.path` when the data lives under `#DataRoot` so the `tracked_by` join resolves.
- Enum-like fields (`#AnnotationStatus`, `#AnnotationDataset`, `#AnnotationTool`, `#ModelOrganism`,
  `#DataModality`, `#AnnotationTask`, `#Structure`, `#Priority`) are closed disjunctions — adding a new
  value in an entry requires adding it to the corresponding `#Foo:` definition first, or `cue vet` fails.
- After editing either file, run `cue vet ./...` before considering the change done.
