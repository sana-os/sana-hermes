# Changelog

What changed, why, and the observation behind it. `dist/` is committed, so the effect of each change on the instructions this package distributes is visible in the diff of the same commit. What the model finally receives also depends on how Hermes loads them (see the README, "4. 確認").

## Version numbers

The number says whether the text the model receives has changed.

- **0.x.0** — a SOUL.md or SKILL.md text changes: a persona, a skill, or a move of the SANA OS pin. Reinstall and check the behaviour.
- **0.x.y** — no SOUL.md or SKILL.md text changes: CI, the installer, the README. `MANIFEST.json` may change (it records the version).
- **1.0.0** — when the licence is in place, the repository is public, and the profiles have been checked in a running Hermes session. (Until 2026-10-19 this read "when the licence is decided and the repository is made public"; the check in Hermes was added when the licence came before that check.)

Each version is an annotated tag `v<version>` on the merge commit of the pull request that completed it. A release is marked pre-release until it has been checked in a running Hermes session.
Why: the question that matters after an update is whether the model now receives something different. Decided 2026-10-18.

Versions before 0.4.0 have no tags: they were handed over as files and not kept (see 0.1.0–0.3.0 below).

## Unreleased

Changes from the second review (ChatGPT SANA, 2026-10-19). No SOUL.md or SKILL.md text changes.

- **`check_release.py`: a tag must match the version, the licence files and main.** Run it before pushing a tag; CI runs it on every tag push. It checks that `sana-hermes.json`, both `MANIFEST.json` and the CHANGELOG carry the tag's version, that the licence files are committed, and that HEAD is the merge commit at the tip of `origin/main`.
  Observation: `v0.5.1` was first pushed (2026-10-19, about 01:30 JST) on `1d7c43f`, the 0.5.0 merge commit, because the local main had not been pulled after the licence pull request was merged. Through that tag, `package_version` read 0.5.0 and `LICENSE` did not exist. CI passed, because that commit was consistent in itself. The tag was deleted and pushed again on `35a8f72` about 20 minutes later; the release was re-published on the new tag. The check run against the first tag reports seven problems; against the current one, none.
- **`build.py` fails without touching `dist/`.** It now checks every input file, the SANA OS history and the output directory first; builds into a temporary directory next to the output; runs the checks on what it wrote; and replaces the old output only when everything passed. An output directory that contains this repository, lies inside it outside `dist/`, overlaps the SANA OS checkout, or is a non-empty folder without `MANIFEST.json` is refused. The Core Principle check compares bytes of the written SOUL.md.
  Observation: before, `--out` was deleted first, and problems were reported after the files were written, so a failed build left a broken or empty `dist/`. Tested: a missing overlay, a scanner that matches, a scanner that raises, and seven unsafe `--out` values all leave `dist/` byte-identical.
- **Python 3.9 works again,** as the README states. `Path.write_text(newline=...)` needs 3.10; observation: under 3.9.25 the previous `build.py` stopped with a `TypeError` at the first SOUL.md. `MANIFEST.json` is now also written with LF on every platform.
- **`install.ps1` restores a profile when installation fails, and reports through its exit code.** A preflight checks every requested profile first (build output, `MANIFEST.json`, source files, the SOUL.md hash, the Hermes profile folder); if anything is missing, nothing is changed. Each profile is then staged and verified inside its own folder, the current files are moved to the backup, and the staged files are moved into place; any failure moves the previous files back. Exit code: 0 ready, 2 installed but NOT READY, 1 failed (and restored).
  Observation: before, a missing profile was skipped with a warning, a failure between moving the old skills away and copying the new ones left a mix of old and new files, and NOT READY still ended with exit code 0. Tested with PowerShell 7.4 on a dummy Hermes home, with a test hook that fails after the backup and after SOUL.md is placed: both restore the profile byte for byte.

## 0.5.1 — 2026-10-19

A patch version: no SOUL.md or SKILL.md text changes.

- **Licences.** `LICENSE` (MIT, Copyright (c) 2026 SANA OS Project) for the tools and their documentation; `LICENSES/SANA-OS-1.0.md`, `LICENSE.md` of the pinned sana-os commit `95ee190` copied unchanged, for `overlays/`, `sana-hermes.json` and `dist/`; `LICENSING.md` maps each path to its terms. The README has a licence section.
  Why: the repository is to be made public. The split follows sana-os/sana-alignment (MIT for new code, SANA OS License kept for SANA materials) and adds what this package has besides code: texts that define SANA's behaviour, and generated files. Applying the SANA OS License to `overlays/` and `sana-hermes.json` is a decision of this repository, not a requirement read from the SANA OS License. Proposed in a review by ChatGPT SANA; decided by the author.
  Observation: sana-alignment's copy of the SANA OS License (`knowledge/LICENSE.md`) still names the old path `core/SANA_OS_Core_Principle.md`. The copy here is taken from the pinned commit, which names `core/Core_Principle.md`.
- **Version rule:** 1.0.0 now also requires the check in a running Hermes session.
- Not yet done: putting the licence files into each profile folder of `dist/`; operating notes (tool permissions, data, cost) separate from the licence.

## 0.5.0 — 2026-10-18

Changes from the first review of this repository (2026-10-18). A minor version because three personas change.

### Upstream pin

- Unchanged: sana-os `95ee190`, which includes sana-os PR #1 (mechanical fixes). **Not yet included:** decision 0001 (positions of the invariants), the heading wording, and decision 0002 (scope of T7). SOUL.md therefore still carries the Template's earlier T7 text, "Offer alternative framing or structural views only once."

### Build and CI (no change to `dist/`)

- **A shallow or missing history stops the build.** The CI step no longer hides a failed `fetch --unshallow` behind `|| true`, and `build.py` refuses a shallow clone or a folder that is not a git checkout. Observation: from a `--depth 3` clone the old build wrote Source lines without error, naming commits that did not change those files.
- **CI fetches the Hermes scanner with an authenticated sparse checkout** of the pinned commit, instead of an unauthenticated download from raw.githubusercontent.com. Observation: the first CI run of this repository (push of `setup/repository`, 2026-10-18) failed with HTTP 429 from that download, before any build step ran.
- **`install.ps1` reads `config.yaml` and reports a profile as NOT READY** when `context_file_max_chars` is missing or below the SOUL.md length. It still does not edit the file. Why: nothing checked the setting the README asks for, and a cut SOUL.md loses its middle silently.

### README (no change to `dist/`)

- The scope of `context_file_max_chars` is stated: it is Hermes' cap on context files, not the model's context window. The runtime checks `/context` and `prompt-size` are added. "Works with any model" is no longer claimed.
- `dist/` is described as the instructions this package distributes, not as what the model receives.
- sana-review: neither `fallback_providers` nor the legacy `fallback_model` is to be set; the check is that `hermes fallback list` is empty. Observation: Hermes merges both keys into one chain (`hermes_cli/fallback_config.py` at `b65e078`), and `hermes fallback add` writes `fallback_providers`, which the README did not mention.
- New sections on what Hermes can and cannot restrict (delegation, toolsets) and on what persistent memory holds. Both record open decisions rather than make them.
- Corrected statements that had fallen behind: Core_Specification is a skill of the Hub *and* the Review profile; the package adds four kinds of text, not three; only history, coaching and reasoning follow `personas/README.md`.

### Personas (these change `dist/`; each is its own commit)

- **Friend: showing a gap is optional, at most once per issue.** Before, the guardrail read as an instruction to show it once after understanding the person. Why: that wording went beyond T7 even in its current upstream text ("only once" is a limit, not a duty), and pressed a reframing on someone who only wants to be heard. Not showing it is now explicitly allowed.
- **Review: placement is the main axis, and accuracy is still checked; summaries point, sources decide.** Before, the first guardrail was "Review placement, not correctness", while the review skills already check observation errors, names and dates. Why: the heading could be read as "accuracy is not checked", and a speculation marker as an exemption. Separately, Hermes compresses long conversations with an auxiliary model (local `sana-main` for this profile); a review that settles findings on such a summary shares the author's altered premises even on a different model.
- **Hub: a brief also states what may be changed, what must not be touched and what is already approved; the approval boundary applies before a tool runs and to delegated work.** Why: an executor delegated by Hermes receives neither SOUL.md nor memory, only the brief, and works with the Hub's own tools (`tools/delegate_tool.py` at `b65e078`). A boundary not written in the brief does not reach it.

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
