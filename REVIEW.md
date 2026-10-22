# Review guide

Every PR is reviewed before it is merged (rule in `agent.md`): by PR-Agent
(owner, 22.10.2026); a new Claude agent checks the **Wichtig** of earlier
rounds, and reviews when PR-Agent fails. The
reviewer knows nothing of the session that wrote the change: it gets the
PR's intent, its diff and the repository, and this file. The owner does not read code; this review is the second reader.

## What failure looks like here

Kader crops camera scans of film negatives: the detection proposes a crop
per image, the local web UI (companion) lets the user check and correct
it, and a target writes the result (copies, crop list, sidecars for
darktable, RawTherapee or Lightroom, the darktable Lua plugin). A bug that
matters is one that gives wrong crops or touches the user's files:

- **Crops wrong:** a change that fits single images but shifts the bias
  across a roll; code that handles only one polarity (image lighter or
  darker than the film border); changed detection results without a run
  against the corrected set (ΔHeight < 100 px, ΔWidth < 50 px = OK).
- **Rates wrong:** a doubtful crop not marked for review, or a good one
  sorted as uncertain.
- **Harms user files:** originals or editor sidecars changed, overwritten
  or lost; a target that writes something other than the plan (`plan.json`) says.
- **Breaks a target or converter:** darktable, RawTherapee, Lightroom or
  the RAW converters fed paths or values they do not take.
- **Ships the demo:** demo code or rolls in a release package.
- **Lies:** README, `scan-howto.md`, `CHANGELOG.md` or comments the code
  contradicts.

## What to check in particular

- Detection changes: both polarities; results on the corrected set and
  the demo rolls (`demo/`) named in the PR; the demo rolls updated when
  results change.
- Repeated code patterns (`agent.md`, "Gelernte Bugs"): a change that hit
  the wrong one of two similar blocks.
- GUI rule: Kante as it is (`agent.md`), no raw colours or sizes.
- Bug fixes: a test that failed before the fix, and the cause removed,
  not one case hidden.

## Skip

- `companion/static/vendor/` (`tools/sync-kante.sh`) and
  `companion/kante_tokens.py` (`tools/gen_kante_tokens.py`); check only
  that they match Kante.
- `review_data/`, test images and other images; style and formatting.

## How to report

- Every finding names file and line and the concrete input or state that
  goes wrong. No guess without evidence; if unsure, say so.
- Each finding gets one label: **Wichtig** (a bug from the list above,
  must be fixed or answered before the merge), **Kleinigkeit** (optional,
  at most five) or **Bestand** (the bug was there before this PR; not
  blocking).
- The report starts with the count, e.g. "2 Wichtig, 1 Kleinigkeit" (the
  session puts the heading above it). The count of **Wichtig** holds every
  one still open, also from an earlier round, e.g. "1 Wichtig (offen aus
  Runde 1)". Only when none is open it says plainly: "Nichts zu beheben."
- In a later round: say for each open **Wichtig** of the last round whether
  it is fixed, or whether its answer is accepted, with the reason. PR-Agent
  sees no earlier round: it reports only its own findings with their labels,
  and a new Claude agent closes the open ones (`agent.md`).
- Findings in German, code names as they are.
