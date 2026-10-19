# Licensing

This repository contains files under **different terms**. It is not "all MIT". Which terms apply depends on the path.

| Path | Terms | What it is |
|---|---|---|
| `build.py`, `install.ps1`, `.github/`, `.gitattributes`, `.gitignore` | [MIT License](LICENSE) | Tools that build and install the profiles |
| `README.md`, `CHANGELOG.md`, `LICENSING.md` | [MIT License](LICENSE), except passages quoted from SANA OS materials, which keep the SANA OS License | Documentation of the tools and of this package |
| `overlays/` (personas, procedures, runtime notes) and `sana-hermes.json` (profile and lens definitions) | [SANA OS License v1.0](LICENSES/SANA-OS-1.0.md) | Texts that define how SANA behaves, written for this package as an adaptation of SANA OS |
| `dist/` (`SOUL.md`, `SKILL.md`, `NOTICE.md`, `MANIFEST.json`; each profile also carries a copy of the licence) | [SANA OS License v1.0](LICENSES/SANA-OS-1.0.md) | Built from SANA OS materials and `overlays/`. Being generated does not make them MIT |
| `upstream/sana-os` | The license in that repository (`LICENSE.md` of the pinned commit) | A submodule: a pointer to `sana-os/sana-os`, not a copy |

`LICENSES/SANA-OS-1.0.md` is `LICENSE.md` from sana-os commit `95ee190`, the commit `upstream/sana-os` is pinned to, copied unchanged.

## Why two licenses

The tools should be easy to reuse. The texts that define SANA's behaviour carry the SANA OS conditions: Core Principle immutability, purpose preservation, attribution and adaptation marking. MIT grants broad reuse with no conditions on purpose, so it is used only where no such condition is needed.

Applying the SANA OS License to the texts written for this package (`overlays/`, `sana-hermes.json`) is a decision of this repository (2026-10-19). The SANA OS License does not by itself require new files to use it.

## What the MIT grant does not do

The MIT License in `LICENSE` does not relicense SANA OS materials, the texts under `overlays/`, or anything in `dist/`. Third-party material keeps its own terms.

## Attribution

Using or distributing the SANA OS parts requires the attribution in the SANA OS License:

- **"Powered by SANA OS"** and a link to **https://sana-os.org**
- For AI implementations, this must appear in the product description or documentation visible to end users. The attribution line inside `SOUL.md` is read by the model; it does not replace a notice that users can see.
- A distributed modification must say that it was changed and that it is a derivative work. `core/Core_Principle.md` may not be modified; `build.py` checks that it is included byte-for-byte.

## Distributing a profile on its own

Each profile folder in `dist/` carries `NOTICE.md` (attribution, derivative-work notice, source commit) and `LICENSES/SANA-OS-1.0.md`, so a folder passed on without this repository keeps its terms. Keep both with it, and give the attribution above where users can see it.

## Hermes Agent

This repository contains no Hermes Agent code. CI fetches `tools/threat_patterns.py` from NousResearch/hermes-agent (MIT License, Copyright (c) 2025 Nous Research) at the pinned commit to run it during the build; it is not committed or distributed here. If Hermes code is ever included, its copyright and license notice must be kept with it.

---

This file states how this repository applies the licenses. It is not legal advice.
