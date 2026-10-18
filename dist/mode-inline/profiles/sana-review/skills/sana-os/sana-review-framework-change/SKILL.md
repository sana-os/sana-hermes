---
name: sana-review-framework-change
description: "SANA Review — framework change: sharpened or shifted. Review revisions of SANA skills and personas against their invariant viewpoint and the Core invariants (フレームワーク改訂, 研ぎ澄ましかズレか)."
metadata:
  hermes:
    category: sana-os
    tags: [sana-os, review]
---

# SANA OS review skill: sana-review-framework-change

## Viewpoint (invariant)

Whether a change to a SANA skill sharpens its fixed viewpoint, extends it, or shifts it to look at something else.

This is what the lens looks at. The procedures and examples below may be refined over time; the viewpoint itself does not change. When refining, check that a change sharpens this viewpoint rather than shifting it.

## Source

Written for this package (sana-hermes); not part of SANA OS. It applies the SANA OS definitions as a review procedure and may be refined independently of them.


---

# Review procedure: changes to framework skills

Use when a SANA skill (a framework lens, a review procedure, a persona) is revised. A framework's viewpoint is fixed; its procedures, examples and wording are sharpened over time. The review asks one thing: **was it sharpened, or did it shift?**

## Steps

1. Read the **Viewpoint (invariant)** section of the skill and the original SANA OS source it quotes. If the change touches the source text itself, flag it first: SANA OS files are included unchanged in this package, and `core/Core_Principle.md` may never be modified.
2. Read the change (diff, or old and new versions side by side).
3. For each changed passage, classify it:
   - **Sharpening** — clearer procedure, better example, a pitfall named, tighter wording; the same thing is looked at.
   - **Extension** — the lens now also covers a new kind of case. Check that the new case is still what the viewpoint looks at.
   - **Shift** — the lens now looks at something else, judges where it used to observe, or assigns blame or correctness where it used to locate structure.
4. Check the invariants a change can quietly erode: non-hostile baseline (`born_loved = true`), observation before logic, structural translation, autonomy preservation. A change that adds a verdict, a ranking of people, or a forced decision is a shift even if the wording is small.
5. Check the record of the change: what triggered it (an observation, a failed case), what it is expected to improve, and how that will be checked. A change without its trigger is a reason that has already evaporated.

## Output

Per passage: sharpening / extension / shift — with your confidence and the sentence that shows it. A shift is not forbidden; it may be a deliberate redesign. Ask whether it was intended, and if so, whether it should be a new lens rather than a silent change to an existing one.
