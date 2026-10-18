---
name: sana-review-design
description: "SANA Review — designs, handoff briefs, build results. Review the Hub's plans and briefs and executors' results: unstated premises, unverified environment claims, role separation, silent fallbacks, boundaries without reasons, irreversible steps, evidence of completion (設計レビュー, 構築物レビュー)."
metadata:
  hermes:
    category: sana-os
    tags: [sana-os, review]
---

# SANA OS review skill: sana-review-design

## Viewpoint (invariant)

Whether a design's premises are stated and footed, roles are separated, boundaries carry reasons, and results match the agreed brief. It does not substitute the reviewer's preferred design.

This is what the lens looks at. The procedures and examples below may be refined over time; the viewpoint itself does not change. When refining, check that a change sharpens this viewpoint rather than shifting it.

## Source

Written for this package (sana-hermes); not part of SANA OS. It applies the SANA OS definitions as a review procedure and may be refined independently of them.


---

# Review procedure: designs, handoff briefs and build results

Use for the Hub's design drafts and plans, briefs handed to task executors, and results built from a brief.

## Design drafts and plans

1. **Premises.** Write down, in your own words, what the design assumes: goals, constraints, environment, who does what. Then compare with what the user actually stated. Mark premises the user never stated.
2. **Unverified environment claims.** A claim about how a tool, service or model behaves that is not backed by an observation (a log, a test, documentation).
   *Example:* "the 500 error comes from Windows paths not being Base64-encoded" was proposed without any request capture. The real cause was a timeout followed by a fallback to a model without a vision projector. The proposed fix was concrete, which made the unverified premise harder to see.
3. **Role separation.** Does any role both align premises and execute? Does the reviewer role sit in a different place from the author? Is there a silent fallback that could make a component review its own work (for example, a commercial reviewer falling back to a local model)?
4. **Reasons attached to boundaries.** Every restriction should carry its reason. A restriction without one cannot be revisited when conditions change.
5. **Irreversible steps.** Deletions, publication to a public main branch, schema changes: is there a stop for the user's approval?
6. **Reversibility and records.** Are changes versioned, with the reason and the triggering observation recorded? Can the state be reproduced (commit, tag, snapshot, model file hash, runtime build)?
7. **Alternatives.** Were other options considered, and is it clear why this one was chosen as "better for now"? Do not demand a "correct" design; ask whether the choice and its reason are visible.

## Handoff briefs

- Goal, agreed premises, boundaries **with reasons**, and a return path ("when the brief does not cover a case, return to the Hub").
- Does the brief leave a gap the executor would have to fill with its own interpretation? Name it.
- If sana-alignment (Fact / View / Care) output is attached, check that `revision_required` or `needs_clarification` items were resolved, not overridden.

## Build results

- Compare against the **agreed brief**, not against your own preferred design. Separate two findings: "built differently from the brief" and "the brief itself has a problem". The second goes back to the Hub and the user, not to the executor.
- Check the evidence of completion (test output, logs, screenshots), not the executor's summary of it. HTTP 200 or "done" is not evidence.
- Note anything built that the brief did not ask for.
