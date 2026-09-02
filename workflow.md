# Semi-automated workflows for managing this repo

Same shape as the earlier `Human` interface design for raw zarr snapshot management (`Edit`/`Decide` are
things a person does themselves, not permission gates a function asks through before proceeding
automatically) — but this repo's actual nouns are git commits/tags, CUE/JSON files, and GitHub Project
fields, not zarr snapshots, so the interface below is adapted to those, not a literal reuse.

Every workflow in this repo already follows the same rhythm: a scripted step produces a candidate change
or surfaces a problem, a person looks at it and decides, then a scripted step commits the outcome. The
scripted halves are `scripts/*.py`, already built and tested this session; the human halves were, until
now, only implicit in how we actually used them.

## The five real workflows this repo has

1. **Rebuild volumes from the filesystem** (`scripts/rebuild_volumes.py`) — mostly mechanical, but a
   person needs to eyeball the diff before it lands. Exercised for real this session: a rebuild surfaced
   421 new volumes at once (417 → 838) — legitimate, but the kind of jump that deserves a look before
   committing, not a blind `git commit -am`.
2. **Rebuild annotations from GitHub** (`scripts/rebuild_annotations.py`) — same shape, plus a wrinkle:
   `PENDING_UPSTREAM_FIXES` pins two fields locally because GitHub's own copy is still wrong. Nothing
   currently forces anyone to revisit that pin once GitHub is actually fixed (flagged as a real risk in
   `discussion.md`) — the workflow below gives that an explicit home instead of a comment in a dict.
3. **Triage a policy-check violation** (`scripts/check_integrity.py`/`check_complete.py`) — a script finds
   something wrong or incomplete; a person has to decide whether it's a real bug (like the FlyID49 #18/#19
   stale-path fix earlier this session), an expected gap (a new annotation with no volume yet, like
   NernLab), or a known, accepted exception.
4. **Evolve the schema** (`lmd_volumes.cue`/`lmd_annotations.cue`) — adding a field or enum value (like
   `#ROI` this session) is always a hand-edit, always followed by `cue vet`, and always followed by a
   human decision about whether existing data needs backfilling.
5. **Cut a release** (`scripts/check_semver.py`) — a person decides it's time to tag a version; the script
   gates whether the proposed bump is honest; a breaking change without a major bump sends the person back
   to workflow #3, not straight to a forced tag.

## `Human` interface

```go
// Human is the seam between automation and judgment in this repo. Every
// method is a point where a person acts with their own hands or makes a
// call only they can make -- none of them are "the system asks permission
// then proceeds automatically."
type Human interface {
	// ReviewDiff shows a person a candidate change (rebuild output vs. what's
	// committed) and returns whether it's approved as-is.
	ReviewDiff(diff Diff) bool

	// Investigate hands a person a single flagged item -- a check violation,
	// an unexpected diff entry -- to look into out-of-band: on the cluster,
	// in the GitHub Project UI, wherever the real answer lives. The person
	// returns their own classification, not something the function inferred.
	Investigate(item Violation) Resolution

	// Edit means a person hand-edits a file themselves. The function does
	// not receive new content back; it resumes only after the person is
	// done. Used for schema changes, one-off data fixes, and updating
	// hardcoded override tables (e.g. rebuild_volumes.py's IMAGE_KEY_OVERRIDES).
	Edit(path string)

	// EditUpstream means a person corrects a field in an external system of
	// record -- here, the GitHub Project -- directly. Never something
	// automation does on a person's behalf, even though gh has API access
	// for it (see discussion.md's addendum on why annotation authorship
	// stays in GitHub).
	EditUpstream(system, ref, field string)

	// Decide is a yes/no call only a person should make -- "is this version
	// bump intentional," "does this schema change need backfilling."
	Decide(prompt string) bool

	// Commit is a person authoring the commit message and creating the
	// commit -- the function stages files, the person writes why.
	Commit(files []string, message string) CommitID

	// Tag marks a specific commit as an official version, after CheckSemver
	// has passed or after Decide confirmed an intentional major bump.
	Tag(commit CommitID, version string)
}

type Diff struct {
	Path  string
	Added, Removed, Changed []string // entry names, e.g. volume/annotation names
}

type Violation struct {
	Source string // "check_integrity" or "check_complete"
	Detail string // the FAIL line itself
}

type Resolution int

const (
	FixLocalData Resolution = iota // edit lmd_volumes.json/lmd_annotations.json (or the .cue schema)
	FixUpstream                    // the GitHub Project field itself is wrong
	AcceptAsKnownGap               // e.g. a new annotation with no volume yet -- expected, not a bug
)

type CommitID string

// PendingFix tracks a local override that exists only because an upstream
// system hasn't been corrected yet -- gives PENDING_UPSTREAM_FIXES-style
// patches a queue instead of a comment nobody re-reads.
type PendingFix struct {
	Field       string // e.g. "annotations[18].source_paths"
	Reason      string
	OpenedAt    string
	System, Ref string // where the real fix belongs, e.g. "github", "issue #18"
}
```

## Flow 1: rebuild volumes

```go
func RebuildVolumes(human Human) error {
	// scripted: walk #DataRoot, derive name/zarr_version/image_key overrides
	candidate, err := runRebuildVolumes() // scripts/rebuild_volumes.py, subprocess or reimplemented
	if err != nil {
		return err
	}

	diff := diffAgainstCommitted("lmd_volumes.json", candidate)
	if diff.Empty() {
		return nil // nothing changed, nothing to review
	}

	if !human.ReviewDiff(diff) {
		return fmt.Errorf("rebuild not approved: %d added, %d removed", len(diff.Added), len(diff.Removed))
	}

	writeFile("lmd_volumes.json", candidate)
	if err := runCueVet(); err != nil {
		return err // schema violation -- something about the walk is wrong, not a human call
	}
	human.Commit([]string{"lmd_volumes.json"}, describeRebuild(diff))
	return nil
}
```

## Flow 2: rebuild annotations, with outstanding pins tracked explicitly

```go
func RebuildAnnotations(human Human, pending []PendingFix) error {
	candidate, err := runRebuildAnnotations() // scripts/rebuild_annotations.py
	if err != nil {
		return err
	}

	// Check each outstanding pin against the fresh pull -- has a human fixed
	// it upstream since we last checked? If so, this ISN'T a silent-forever
	// override; it surfaces for a real decision.
	var stillOpen []PendingFix
	for _, p := range pending {
		if upstreamStillStale(candidate, p) {
			applyPin(candidate, p)
			stillOpen = append(stillOpen, p)
		} else if !human.Decide(fmt.Sprintf("%s looks fixed upstream now (opened %s) -- drop the pin?", p.Field, p.OpenedAt)) {
			stillOpen = append(stillOpen, p) // human isn't ready to trust it yet, keep pinned
		}
		// else: dropped, the fresh GitHub value is used as-is
	}

	diff := diffAgainstCommitted("lmd_annotations.json", candidate)
	if !diff.Empty() && !human.ReviewDiff(diff) {
		return fmt.Errorf("annotation rebuild not approved")
	}

	writeFile("lmd_annotations.json", candidate)
	writePendingFixes(stillOpen) // never silent -- always re-checked next rebuild
	if err := runCueVet(); err != nil {
		return err
	}
	human.Commit([]string{"lmd_annotations.json", "pending_fixes.json"}, describeRebuild(diff))
	return nil
}
```

## Flow 3: triage a policy-check violation

```go
func TriageViolation(v Violation, human Human) error {
	resolution := human.Investigate(v)

	switch resolution {
	case FixLocalData:
		human.Edit(likelyDataFile(v)) // e.g. lmd_annotations.cue, for the FlyID49 #18/#19 case
		if err := runCueVet(); err != nil {
			return err
		}
		if !human.Decide("re-run check_integrity.py -- confirm this specific violation is gone?") {
			return fmt.Errorf("fix not confirmed")
		}
		human.Commit(changedFiles(), "fix: "+v.Detail)

	case FixUpstream:
		human.EditUpstream("github", extractIssueRef(v), extractFieldName(v))
		// don't touch local data yet -- the next RebuildAnnotations run will
		// pick it up and TriageViolation's own PendingFix check confirms it

	case AcceptAsKnownGap:
		// e.g. NernLab (issue #29): a new annotation with no volume yet --
		// resolved itself once RebuildVolumes ran, no fix needed at all
	}
	return nil
}
```

## Flow 4: evolve the schema

```go
func EvolveSchema(human Human) error {
	human.Edit(schemaPath()) // e.g. adding #ROI to lmd_annotations.cue

	if err := runCueVet(); err != nil {
		return err // schema doesn't even validate against itself yet
	}

	if human.Decide("does existing data need backfilling for this new field?") {
		human.Edit(dataPath()) // hand-populate the field for existing entries (#ROI: 11 entries, by hand)
		if err := runCueVet(); err != nil {
			return err
		}
	}

	human.Commit([]string{schemaPath(), dataPath()}, describeSchemaChange())
	return nil
}
```

## Flow 5: cut a release

```go
func CutRelease(proposedVersion string, human Human) error {
	result := runCheckSemver(proposedVersion) // scripts/check_semver.py

	if result.HasBreakingChanges && !result.IsMajorBump {
		if !human.Decide(fmt.Sprintf("%s breaks %d existing names without a major bump -- was this intentional?", proposedVersion, len(result.Violations))) {
			for _, v := range result.Violations {
				if err := TriageViolation(Violation{Source: "check_semver", Detail: v}, human); err != nil {
					return err
				}
			}
			return fmt.Errorf("release aborted, sent to triage instead")
		}
		// human confirmed it's intentional -- but check_semver.py itself still
		// requires the major component to actually be bumped; re-propose or stop
		return fmt.Errorf("bump the major version component and re-run")
	}

	head := currentCommit()
	human.Tag(head, proposedVersion)
	return nil
}
```
