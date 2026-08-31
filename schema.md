# Schema language: CUE vs. Python vs. JSON Schema

Prompted by the question in `readme.md`: "why .cue? why not specify schema in .py and verify with .py?"
First pass at this document overstated CUE's case in a few places; this revision corrects those against
things actually tested, not just argued.

This catalog's schema does three genuinely different jobs:

1. **Closed-enum validation** — `#AnnotationStatus`, `#AnnotationDataset`, etc. reject typos and
   unapproved new values until someone deliberately extends the definition.
2. **Derived defaults** — `#Volume.path` is computed from `name`; `zarr_version`/`image_key` fall back to
   `"zarr3"`/`"raw"` unless overridden. No entry stores `path` itself.
3. **A live cross-file join** — `#Volume.tracked_by` is computed at evaluation time by scanning
   `annotations` for any `source_paths` match.

## What needs imperative Python regardless of which schema language wins

None of CUE, pydantic, or JSON Schema can see a live filesystem or call `gh`. `check_integrity.py` (path
existence, zarr-version-marker matching against the store's own `.zgroup`/`zarr.json`, `image_key` group
existence, `roi`-vs-`bbox` text consistency), `check_complete.py` (diffing the catalog against a directory
walk and the live GitHub Project), and both `rebuild_*.py` scripts are unavoidably imperative Python no
matter what — this was true before the schema/data split and stays true after it. So the honest framing
isn't "CUE avoids imperative glue" (it doesn't, and can't) — it's "CUE covers three specific jobs
declaratively that are internal to the two data files; everything that reaches outside those two files
was always going to be a Python script."

## What metadata lives in the zarr store vs. in this catalog

Worth being explicit about the boundary, since it's not a clean split:

- **Zarr-intrinsic, never duplicated here**: array shape, chunk shape, on-disk dtype, and — via OME-NGFF
  `multiscales`/`coordinateTransformations` — physical voxel size and axis order. Confirmed this session
  reading `miao`'s `dataset.py`: these are read straight from the store's own metadata; there is no
  config field for any of them, and no reason for this catalog to carry a copy.
- **Catalog-only, no zarr-side representation**: `name` (an organizational convention imposed on top of
  the store, not derivable from it), `tracked_by`/annotation workflow status (a GitHub Project fact,
  unrelated to pixel data), `roi` (an annotated-region pointer that predates/parallels the zarr write, not
  encoded in it), GT/proofread path pointers.
- **The overlap that actually explains two of `#Volume`'s fields**: `zarr_version` and `image_key` are
  both, in principle, inspectable directly from the store — `check_integrity.py` does exactly that,
  reading `.zgroup`/`zarr.json` to verify the catalog's claim. But they're duplicated in the catalog
  anyway, for a concrete, non-obvious reason: `miao.config.VolumeConfig` requires both explicitly. Its own
  `detect_zarr_version` helper exists in the codebase but is never actually called in the construction
  path — confirmed reading `dataset.py` — so a consumer must supply the value rather than rely on
  auto-detection, and `image_key` has no discovery mechanism in miao at all (the top-level group name is
  never guessed). So these two fields exist not because CUE "needs" them structurally, but because a real
  downstream consumer's API contract forces an explicit value despite the fact being independently
  verifiable. `check_integrity.py` is the actual arbiter of truth for these two fields, not the schema —
  the schema just declares the shape/default of a value Python then checks against the store.

## CUE's type system, on its own merits

Set aside job-coverage for a moment: CUE's model — types are sets of values, `&` narrows by intersection,
`|` unions, a default (`*"raw"`) is part of the same expression as the type, not a separate keyword — is a
more principled fit for *describing data* than Python's. Python's typing story is two disconnected layers:
static type hints (`str | None`) that tooling checks but the runtime never enforces, plus a separate
runtime-validation library (pydantic) that re-implements the enforcement pydantic's way. CUE doesn't have
that split — the same expression is simultaneously the type, the default, and (via unification with
concrete data) the validator. That's a genuine, structural advantage, independent of anything below.

## Can Python just be "type definitions + a validate() function"?

Yes, more cleanly than the first draft of this document gave it credit for. A pydantic module reads
almost as declaratively as a `.cue` file for jobs #1 and #2:

```python
class AnnotationStatus(str, Enum):
    CROP_PENDING_APPROVAL = "Crop Pending Approval"
    ...

class Volume(BaseModel):
    name: str
    image_key: str = "raw"
    zarr_version: Literal["zarr2", "zarr3"] = "zarr3"
```

That's not meaningfully less clean than the CUE equivalent, and `extra="forbid"` (seen firsthand in
`miao.config.VolumeConfig`) gives the same "reject unknown/typo'd keys" property CUE's closedness gives.
The place this genuinely stops being "just types" is job #3: the cross-file join needs both files loaded
into memory and an explicit function call over both (`compute_tracked_by(volumes, annotations)`) — there's
no per-record `validate()` that can see a sibling file. That's a real, narrower difference than "Python
schema collapses into a script" — it's specifically "CUE's package scope makes cross-referencing implicit
and automatic (write `annotations` inside `#Volume` and it resolves), Python's doesn't (you pass both
explicitly)." Everything else translates to a clean Python module just fine.

## Does CUE actually find all errors at once? Tested this, and pydantic too

Ran the same 3-independent-violation case (two enum typos, one out-of-range int) through both:

- `cue vet`: reports all three, unprompted — confirmed by direct test. Verbose, though: each enum typo
  produces "N errors in empty disjunction" plus one "conflicting values" line per disjunction branch (3
  branches → 3 sub-errors for one typo).
- pydantic (`ValidationError.errors()`): also reports all three in one exception, one line each, no
  disjunction-branch noise.

So this is **not** a CUE-exclusive property — pydantic does it natively too, and with cleaner output.
Where it *does* matter: this repo's own `check_integrity.py` is hand-rolled Python (no pydantic), and
"accumulate every violation into a list, don't raise on the first" was a deliberate design choice we made
— not something plain Python gives you automatically. It's also in tension with this project's own default
Python convention (`~/.claude/CLAUDE.md`: "use assertions with a good error string" — which is
raise-on-first behavior). CUE and pydantic both give you "all errors at once" for free; hand-rolled
assertion-based Python has to deliberately opt out of its own fail-fast default to get the same property,
which is exactly what `check_integrity.py` does.

## Will letting CUE auto-minimize the JSON help? Tested this: no, not as things stand

`cue trim` exists and does precisely what this question describes — strips fields from concrete data when
they're already implied by the schema's default. Tested it directly: given
`{name: "a", image_key: "raw", zarr_version: "zarr3"}` (both fields redundant with their defaults) written
as **literal CUE syntax**, `cue trim` correctly deletes both, keeping only `{name: "a"}`, while correctly
preserving a real override (`zarr_version: "zarr2"`) on a sibling entry. It works exactly as advertised.

Tested the same case with the data in `lmd_volumes.json`'s actual format — a **JSON file** — and `cue trim`
left it completely untouched. It only rewrites literal `.cue` source text in place; it has no defined
behavior for editing a `.json` file's content. So the schema/data split (data in JSON, not CUE literals)
trades this away: `rebuild_volumes.py`'s manual `if version != "zarr3": volume["zarr_version"] = version`
omission logic is doing by hand exactly what `cue trim` would have automated for free, had the data stayed
as CUE literals instead of moving to JSON. Not a reason to reverse the split (mechanical Python
regeneration from ground truth was the actual point, not minimality), but a real, specific thing given up,
worth naming rather than leaving implicit.

## Where this leaves it

The balance is narrower than the first draft claimed. What survives scrutiny as a genuine CUE-specific
advantage:
- The cross-file join is automatic by package scope; Python always needs an explicit function call over
  both loaded structures.
- The type system itself (unification, defaults-as-part-of-type, closedness in one coherent model) is a
  more principled fit for pure data description than Python's split static-hints/runtime-library story.

What does *not* survive scrutiny as CUE-exclusive:
- "Avoids imperative glue" — false in general; only true for the two-file-internal parts (enums, defaults,
  the join). Everything touching the live filesystem or GitHub was always going to be Python.
- "Finds all errors at once" — pydantic does this equally well, with cleaner output; even hand-rolled
  Python can, if it deliberately chooses to accumulate rather than assert-and-stop.
- "Auto-minimizes data" — `cue trim` is real but doesn't apply to JSON at all, only to literal `.cue`
  syntax, which this repo deliberately moved away from.

Recommendation: keep CUE for schema, Python for rebuild scripts and policy checks — the split this repo
already settled on, but for narrower reasons than originally stated. Revisit if either becomes true: (a) a
non-Python, non-CUE consumer needs to validate against this schema directly, which would argue for JSON
Schema as a generated *artifact* (`cue def openapi: lmd_volumes.cue` / `-o jsonschema:...` both work,
though `cue help` flags JSON Schema output as still experimental); or (b) the team decides the join's
implicit-by-scope convenience isn't worth CUE's onboarding/tooling cost, in which case collapsing
everything into pydantic (schema-as-models, join-as-function) is a coherent, simpler alternative that
loses less than this document first suggested.
