# Changelog

What changed, why, and the observation behind it. `dist/` is committed, so the effect of each change on what the model receives is visible in the diff of the same commit.

## 0.4.0 — 2026-10-18

### Repository

- **This repository** (`sana-os/sana-hermes`). Before, the package was handed over as zip files in conversation. Why now: improved skills and personas will keep being added, and each change should leave a diff.
- **`upstream/sana-os` submodule**, pinned to sana-os `95ee190` (main after sana-os PR #1). Moving the pin is a commit of its own, together with the rebuilt `dist/`.
- **Deterministic build; `dist/` committed.** `MANIFEST.json` no longer records the build time or the scan result. Observation: two builds from the same sources differed only in those fields, which would make every rebuild look like a change.
- **SKILL.md Source line** names the last commit that changed that framework file, not SANA OS HEAD; the package version is no longer written into each skill. Observation: otherwise every pin move or version bump rewrites every skill, hiding the real changes.
- **A scan match is a build error.** Before, it was only printed.
- **CI** (`.github/workflows/build.yml`): rebuilds both modes with the pinned Hermes scanner and fails if the committed `dist/` differs.

### Effect of sana-os PR #1 on the prompts

- Hub, Review, Friend: the Template's sections 0–1 now carry the restored characters (`victory/defeat`, `$\rightarrow$`, labels and list markers).
- Every profile: `Communication_Layer.md` is no longer wrapped in a code block; its metadata is front matter.
- Skills: CPM and Legitimacy Layer unwrapped; Value Formation without citation markers.

## 0.3.0 — 2026-10-17

- **`sana-friend`** and the skill **`sana-friend-story`**. Built from `Persona_Template.md`. The character is only tone and first person; no instruction to act as a human. Rules (each with its reason): align rather than agree; offer inferences about the person as questions; give absent people the same baseline; save only what the person said; keep their world wide; safety before structure.
  Why: friend was not in SANA OS on GitHub; the author decided to implement it as a light SANA that aligns premises in conversation.

## 0.2.0 — 2026-10-17

- **`sana-review`** and three review skills (`sana-review-design`, `sana-review-history`, `sana-review-framework-change`). SANA's invariants are shared as the way of reviewing; SANA's definitions are the specification being reviewed. Reviews placement, not correctness; does not punish speculation; does not rewrite.
  Why: the Hub's designs and History SANA's reasoning are to be reviewed by a different model family (Claude), as a separate role.

## 0.1.0 — 2026-10-16

- **`sana-hub`, `sana-history`, `sana-coaching`, `sana-reasoning`.** SOUL.md = the three Core files + persona + Hermes runtime notes; frameworks as on-demand skills; an inline mode equivalent to the GPTs loading order, for comparison. The Hub persona was written from `Persona_Template.md`.
- Observations from reading the Hermes source (`b65e078`) that shaped the build:
  - SOUL.md is cut to 20,000 characters when the model's context length is unknown, keeping the head and tail. That would remove `Communication_Layer.md` entirely, so the README asks for `context_file_max_chars`.
  - The skill index shows only the first 60 characters of a description, so each description starts with the lens name and viewpoint, and SOUL.md lists the lenses.
  - A SOUL.md installed by a shared profile is blocked if it matches the injection scanner, so every build runs it.

Versions 0.1.0–0.3.0 were not kept as separate files; they are described here and in the first commit rather than reconstructed.
