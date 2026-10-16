#!/usr/bin/env python3
"""Build Hermes Agent profile files (SOUL.md + skills) from a SANA OS checkout.

The SANA OS repository is the source of truth. Everything under dist/ is a
derived projection and can be regenerated at any time:

    python3 build.py --sana-os ../sana-os                 # skills mode (default)
    python3 build.py --sana-os ../sana-os --mode inline   # GPTs-equivalent SOUL.md
    python3 build.py --sana-os ../sana-os --scan path/to/hermes-agent/tools/threat_patterns.py

Modes
  skills  SOUL.md = Core + persona + Hermes notes; frameworks become on-demand skills.
  inline  SOUL.md = Core + frameworks + persona (the GPTs / Project loading order);
          skills are still emitted. Use it to compare behaviour with the skills mode.

Checks performed on every build
  * core/Core_Principle.md appears byte-for-byte unchanged in every SOUL.md
  * SOUL.md length against Hermes' context-file cap (20,000 chars when the
    model's context window is unknown; see README for context_file_max_chars)
  * skill names match Hermes' pattern; SKILL.md body length under the linter's ~24k advisory
  * optional: Hermes' own prompt-injection scanner (--scan)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
SOUL_FLOOR_CAP = 20_000          # Hermes CONTEXT_FILE_MAX_CHARS (cap when context length is unknown)
SKILL_BODY_ADVISORY = 24_000     # Hermes skill linter "oversized-body" threshold
SEP = "\n\n---\n\n"


def sha256(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def read(src: Path, rel: str) -> str:
    # newline="" keeps the file's own line endings so the Core Principle stays byte-identical.
    with open(src / rel, encoding="utf-8", newline="") as fh:
        return fh.read()


def upstream_commit(src: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def provenance(rel: str) -> str:
    return f"<!-- SANA OS source: {rel} (included unchanged) -->\n\n"


def template_persona(src: Path, cfg: dict) -> str:
    """Persona_Template sections 0-1 verbatim + a package-written custom layer (sections 2-3)."""
    template = read(src, cfg["template"])
    cut = template.index("## 2. PERSONA CUSTOMIZATION")
    head = template[:cut]
    head = head[head.index("## 0. "):]  # drop template title and developer note (heading text varies by version)
    custom = (HERE / cfg["custom_overlay"]).read_text(encoding="utf-8")
    return ("<!-- SANA OS derivative: personas/Persona_Template.md sections 0-1 unchanged; "
            f"sections 2-3 written for this package -->\n\n"
            f"# System Prompt: {cfg['title']} (derived from Persona Template v1.0)\n\n"
            + head.rstrip() + "\n\n" + custom.strip() + "\n")


def runtime_notes(skills: list[str], specs: dict, mode: str) -> str:
    """Hermes shows only ~60 chars of each skill description in its prompt index, so the
    lens map below carries the selection cue in full."""
    text = (HERE / "overlays" / "hermes_runtime_notes.md").read_text(encoding="utf-8")
    lens_map = "\n".join(f"  * `{s}` — {specs[s]['short']}" for s in skills)
    if mode == "skills":
        sentence = ("The SANA OS framework files (and any procedures written for this profile) are installed "
                    "as skills in the `sana-os` category; Integrated Knowledge above is the compressed index of "
                    "the frameworks:\n" + lens_map)
    else:
        sentence = ("The framework files are loaded above in full; the same texts are also available as skills "
                    "for re-reading a specific section:\n" + lens_map)
    return text.replace("{{LENS_SENTENCE}}", sentence)


def build_skill(name: str, spec: dict, src: Path, commit: str, version: str, category: str) -> str:
    packaged = "overlay" in spec
    body = (HERE / spec["overlay"]).read_text(encoding="utf-8") if packaged else read(src, spec["source"])
    front = "\n".join([
        "---",
        f"name: {name}",
        f"description: {json.dumps(spec['description'], ensure_ascii=False)}",
        f"version: {json.dumps(version)}",
        "metadata:",
        "  hermes:",
        f"    category: {category}",
        f"    tags: [sana-os, {'review' if packaged else 'framework'}]",
        "---",
    ])
    if packaged:
        source = ("Written for this package (sana-hermes); not part of SANA OS. It applies the SANA OS "
                  "definitions as a review procedure and may be refined independently of them.\n")
    else:
        source = (f"`{spec['source']}` from https://github.com/sana-os/sana-os at commit `{commit[:12]}`, "
                  "included unchanged below. Powered by SANA OS — https://sana-os.org\n")
    header = (
        f"# SANA OS {'review skill' if packaged else 'lens'}: {name}\n\n"
        "## Viewpoint (invariant)\n\n"
        f"{spec['viewpoint']}\n\n"
        "This is what the lens looks at. The procedures and examples below may be refined over time; "
        "the viewpoint itself does not change. When refining, check that a change sharpens this viewpoint "
        "rather than shifting it.\n\n"
        "## Source\n\n" + source
    )
    return front + "\n\n" + header + SEP + body.rstrip() + "\n"


def join_parts(parts: list[str]) -> str:
    """Join with a horizontal rule, reusing one a source file already ends with."""
    out = parts[0]
    for part in parts[1:]:
        out += "\n\n" if out.rstrip().endswith("---") else SEP
        out += part
    return out + "\n"


def load_scanner(path: str | None):
    if not path:
        return None
    spec = importlib.util.spec_from_file_location("hermes_threat_patterns", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.scan_for_threats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sana-os", required=True, help="path to a sana-os/sana-os checkout")
    ap.add_argument("--mode", choices=["skills", "inline"], default="skills")
    ap.add_argument("--out", default=None, help="output dir (default: dist/mode-<mode>)")
    ap.add_argument("--scan", default=None, help="path to hermes-agent/tools/threat_patterns.py (optional)")
    args = ap.parse_args()

    src = Path(args.sana_os).resolve()
    cfg = json.loads((HERE / "sana-hermes.json").read_text(encoding="utf-8"))
    out = Path(args.out) if args.out else HERE / "dist" / f"mode-{args.mode}"
    if out.exists():
        shutil.rmtree(out)
    commit = upstream_commit(src)
    version = cfg["package_version"]
    category = cfg["skill_category"]
    scanner = load_scanner(args.scan)
    core_principle = read(src, "core/Core_Principle.md")
    problems: list[str] = []
    manifest: dict = {
        "package_version": version, "mode": args.mode, "built_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sana_os_commit": commit, "sources": {}, "profiles": {},
    }

    # Skills (shared definitions, copied into each profile that uses them)
    built_skills: dict[str, str] = {}
    for name, spec in cfg["skills"].items():
        if not NAME_RE.match(name):
            problems.append(f"skill name not accepted by Hermes: {name}")
        text = build_skill(name, spec, src, commit, version, category)
        if len(text) > SKILL_BODY_ADVISORY:
            problems.append(f"{name}: SKILL.md {len(text)} chars exceeds Hermes linter advisory {SKILL_BODY_ADVISORY}")
        built_skills[name] = text
        if "overlay" in spec:
            manifest["sources"][spec["overlay"]] = sha256((HERE / spec["overlay"]).read_text(encoding="utf-8"))
        else:
            manifest["sources"][spec["source"]] = sha256(read(src, spec["source"]))

    for rel in cfg["core_files"]:
        manifest["sources"][rel] = sha256(read(src, rel))

    print(f"SANA OS commit {commit[:12]}  mode={args.mode}  -> {out}")
    for pname, pcfg in cfg["profiles"].items():
        parts = [provenance(rel) + read(src, rel).strip("\n") for rel in cfg["core_files"]]
        if args.mode == "inline":
            for s in pcfg["skills"]:
                rel = cfg["skills"][s].get("source", "")
                if rel.startswith("frameworks/") and not rel.endswith("README.md"):
                    parts.append(provenance(rel) + read(src, rel).strip("\n"))
        persona = pcfg["persona"]
        if "file" in persona:
            parts.append(provenance(persona["file"]) + read(src, persona["file"]).strip("\n"))
            manifest["sources"][persona["file"]] = sha256(read(src, persona["file"]))
        else:
            parts.append(template_persona(src, persona).strip("\n"))
            manifest["sources"][persona["template"]] = sha256(read(src, persona["template"]))
        parts.append(runtime_notes(pcfg["skills"], cfg["skills"], args.mode).strip("\n"))
        soul = join_parts(parts)

        if core_principle.strip("\n") not in soul:
            problems.append(f"{pname}: Core_Principle.md is not byte-identical in SOUL.md")
        pdir = out / "profiles" / pname
        (pdir / "skills" / category).mkdir(parents=True, exist_ok=True)
        (pdir / "SOUL.md").write_text(soul, encoding="utf-8", newline="\n")
        for s in pcfg["skills"]:
            sd = pdir / "skills" / category / s
            sd.mkdir(parents=True, exist_ok=True)
            (sd / "SKILL.md").write_text(built_skills[s], encoding="utf-8", newline="\n")

        findings = scanner(soul, scope="context") if scanner else None
        n = len(soul)
        manifest["profiles"][pname] = {
            "soul_chars": n, "soul_sha256": sha256(soul), "skills": pcfg["skills"],
            "injection_scan": findings if scanner else "not run",
        }
        note = "OK" if n <= SOUL_FLOOR_CAP else f"over {SOUL_FLOOR_CAP:,} — pin context_file_max_chars"
        scan = "" if findings is None else f"  scan: {findings or 'clean'}"
        print(f"  {pname:<16} SOUL.md {n:>6,} chars ({note})  skills: {len(pcfg['skills'])}{scan}")

    (out / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if problems:
        print("\nProblems:")
        for p in problems:
            print("  -", p)
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
