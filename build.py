#!/usr/bin/env python3
"""Build Hermes Agent profile files (SOUL.md + skills) from a SANA OS checkout.

The SANA OS repository is the source of truth. Everything under dist/ is a
derived projection and can be regenerated at any time:

    python3 build.py                                  # skills mode, from upstream/sana-os (submodule)
    python3 build.py --mode inline                    # GPTs-equivalent SOUL.md
    python3 build.py --sana-os ../sana-os             # build from another checkout
    python3 build.py --scan path/to/hermes-agent/tools/threat_patterns.py

The output is deterministic: the same SANA OS commit and the same sources give
byte-identical files, so dist/ can be committed and its diff shows exactly what
changes in the text the model receives.

Modes
  skills  SOUL.md = Core + persona + Hermes notes; frameworks become on-demand skills.
  inline  SOUL.md = Core + frameworks + persona (the GPTs / Project loading order);
          skills are still emitted. Use it to compare behaviour with the skills mode.

Checks performed on every build
  * the SANA OS checkout is a full git clone, so every recorded source commit is real
  * core/Core_Principle.md appears byte-for-byte unchanged in every SOUL.md
  * SOUL.md length against Hermes' context-file cap (20,000 chars when the
    model's context window is unknown; see README for context_file_max_chars)
  * skill names match Hermes' pattern; SKILL.md body length under the linter's ~24k advisory
  * optional: Hermes' own prompt-injection scanner (--scan)
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
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


def upstream_commit(src: Path) -> tuple[str, str]:
    """(commit hash, committer date) of the SANA OS checkout."""
    try:
        out = subprocess.run(["git", "-C", str(src), "log", "-1", "--format=%H %cI"], capture_output=True,
                             text=True, check=True).stdout.split()
        return out[0], out[1]
    except Exception:
        return "unknown", "unknown"


def file_commit(src: Path, rel: str) -> str:
    """Last commit that changed this file. Used instead of HEAD so a skill changes only when its source does."""
    try:
        return subprocess.run(["git", "-C", str(src), "log", "-1", "--format=%H", "--", rel], capture_output=True,
                              text=True, check=True).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def is_shallow(src: Path) -> bool:
    """In a shallow clone, `git log -- <file>` stops at the cut and names the wrong commit without failing."""
    try:
        return subprocess.run(["git", "-C", str(src), "rev-parse", "--is-shallow-repository"], capture_output=True,
                              text=True, check=True).stdout.strip() == "true"
    except Exception:
        return False


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


def build_skill(name: str, spec: dict, src: Path, category: str, source_commit: str) -> str:
    packaged = "overlay" in spec
    body = (HERE / spec["overlay"]).read_text(encoding="utf-8") if packaged else read(src, spec["source"])
    front = "\n".join([
        "---",
        f"name: {name}",
        f"description: {json.dumps(spec['description'], ensure_ascii=False)}",
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
        source = (f"`{spec['source']}` from https://github.com/sana-os/sana-os, as last changed in commit "
                  f"`{source_commit[:12]}`, "
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


def write(path: Path, text: str) -> None:
    """UTF-8, LF line endings on every platform. (Path.write_text(newline=...) needs Python 3.10.)"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def required_inputs(cfg: dict) -> tuple[list[str], list[Path]]:
    """Every file the build reads: (paths in the SANA OS checkout, paths in this repository)."""
    upstream = list(cfg["core_files"]) + ["core/Core_Principle.md"]
    local = [HERE / "overlays" / "hermes_runtime_notes.md"]
    for spec in cfg["skills"].values():
        if "overlay" in spec:
            local.append(HERE / spec["overlay"])
        else:
            upstream.append(spec["source"])
    for pcfg in cfg["profiles"].values():
        persona = pcfg["persona"]
        if "file" in persona:
            upstream.append(persona["file"])
        else:
            upstream.append(persona["template"])
            local.append(HERE / persona["custom_overlay"])
    return sorted(set(upstream)), sorted(set(local))


def check_output_dir(out: Path, src: Path) -> list[str]:
    """The output directory is deleted and replaced, so it must be a build output and nothing else."""
    problems = []
    def inside(a: Path, b: Path) -> bool:  # a == b or a is below b
        return a == b or b in a.parents
    if inside(HERE, out):
        problems.append(f"--out {out} contains this repository")
    elif inside(out, HERE) and not inside(out, HERE / "dist"):
        problems.append(f"--out {out} is inside this repository but not under dist/")
    if inside(out, src) or inside(src, out):
        problems.append(f"--out {out} overlaps the SANA OS checkout {src}")
    if out.exists():
        if not out.is_dir():
            problems.append(f"--out {out} is a file")
        elif any(out.iterdir()) and not (out / "MANIFEST.json").is_file():
            problems.append(f"--out {out} is not empty and has no MANIFEST.json, so it is not a previous build output")
    return problems


def replace_dir(new: Path, out: Path) -> None:
    """Put the finished build in place of the old one; restore the old one if that fails."""
    old = None
    if out.exists():
        old = Path(tempfile.mkdtemp(prefix=f".{out.name}.old-", dir=out.parent))
        old.rmdir()
        out.rename(old)
    try:
        new.rename(out)
    except Exception:
        if old is not None:
            old.rename(out)
        raise
    if old is not None:
        shutil.rmtree(old)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sana-os", default=str(HERE / "upstream" / "sana-os"),
                    help="path to a sana-os/sana-os checkout (default: the upstream/sana-os submodule)")
    ap.add_argument("--mode", choices=["skills", "inline"], default="skills")
    ap.add_argument("--out", default=None, help="output dir (default: dist/mode-<mode>)")
    ap.add_argument("--scan", default=None, help="path to hermes-agent/tools/threat_patterns.py (optional)")
    args = ap.parse_args()

    src = Path(args.sana_os).resolve()
    cfg = json.loads((HERE / "sana-hermes.json").read_text(encoding="utf-8"))
    out = (Path(args.out) if args.out else HERE / "dist" / f"mode-{args.mode}").resolve()

    # 1. Check everything that can be checked before anything is written.
    #    Why: a failed build must leave the previous dist/ as it was.
    problems: list[str] = []
    if not src.is_dir():
        problems.append(f"SANA OS checkout not found: {src} (run: git submodule update --init)")
    else:
        commit, commit_date = upstream_commit(src)
        # Provenance must be real: the Source line of each skill and MANIFEST.json name commits.
        if commit == "unknown":
            problems.append(f"{src} is not a git checkout; the source commits cannot be recorded "
                            "(clone sana-os, or run: git submodule update --init)")
        elif is_shallow(src):
            problems.append(f"{src} is a shallow clone; the Source line of each skill would name the wrong commit "
                            f"(run: git -C {src} fetch --unshallow)")
        upstream_files, local_files = required_inputs(cfg)
        problems += [f"missing in SANA OS: {rel}" for rel in upstream_files if not (src / rel).is_file()]
        problems += [f"missing in this repository: {p.relative_to(HERE)}" for p in local_files if not p.is_file()]
    problems += check_output_dir(out, src)
    if args.scan and not Path(args.scan).is_file():
        problems.append(f"scanner not found: {args.scan}")
    if problems:
        return report(problems, untouched=out)
    scanner = load_scanner(args.scan)

    # 2. Build into a temporary directory next to the output, check it, then swap.
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{out.name}.build-", dir=out.parent))
    try:
        problems = build(src, cfg, args.mode, tmp, scanner, commit, commit_date, out)
        if problems:
            return report(problems, untouched=out)
        replace_dir(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print("\nAll checks passed.")
    return 0


def report(problems: list[str], untouched: Path) -> int:
    print("\nProblems:")
    for p in problems:
        print("  -", p)
    print(f"\nNothing was written; {untouched} is unchanged.")
    return 1


def build(src: Path, cfg: dict, mode: str, out: Path, scanner, commit: str, commit_date: str,
          final: Path) -> list[str]:
    version = cfg["package_version"]
    category = cfg["skill_category"]
    core_bytes = (src / "core" / "Core_Principle.md").read_bytes().strip(b"\n")
    problems: list[str] = []
    manifest: dict = {
        "package_version": version, "mode": mode,
        "sana_os_commit": commit, "sana_os_commit_date": commit_date, "sources": {}, "profiles": {},
    }

    # Skills (shared definitions, copied into each profile that uses them)
    built_skills: dict[str, str] = {}
    for name, spec in cfg["skills"].items():
        if not NAME_RE.match(name):
            problems.append(f"skill name not accepted by Hermes: {name}")
        source_commit = "" if "overlay" in spec else file_commit(src, spec["source"])
        if source_commit == "unknown":
            problems.append(f"{name}: no commit found for {spec['source']}")
        text = build_skill(name, spec, src, category, source_commit)
        if len(text) > SKILL_BODY_ADVISORY:
            problems.append(f"{name}: SKILL.md {len(text)} chars exceeds Hermes linter advisory {SKILL_BODY_ADVISORY}")
        built_skills[name] = text
        if "overlay" in spec:
            manifest["sources"][spec["overlay"]] = sha256((HERE / spec["overlay"]).read_text(encoding="utf-8"))
        else:
            manifest["sources"][spec["source"]] = sha256(read(src, spec["source"]))

    for rel in cfg["core_files"]:
        manifest["sources"][rel] = sha256(read(src, rel))

    print(f"SANA OS commit {commit[:12]}  mode={mode}  -> {final}")
    for pname, pcfg in cfg["profiles"].items():
        parts = [provenance(rel) + read(src, rel).strip("\n") for rel in cfg["core_files"]]
        if mode == "inline":
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
        parts.append(runtime_notes(pcfg["skills"], cfg["skills"], mode).strip("\n"))
        soul = join_parts(parts)

        pdir = out / "profiles" / pname
        write(pdir / "SOUL.md", soul)
        for s in pcfg["skills"]:
            write(pdir / "skills" / category / s / "SKILL.md", built_skills[s])
        # Checked on the bytes written, not on the string in memory.
        if core_bytes not in (pdir / "SOUL.md").read_bytes():
            problems.append(f"{pname}: Core_Principle.md is not byte-identical in the written SOUL.md")

        findings = scanner(soul, scope="context") if scanner else None
        if findings:
            problems.append(f"{pname}: Hermes injection scan matched {findings}")
        n = len(soul)
        manifest["profiles"][pname] = {
            "soul_chars": n, "soul_sha256": sha256(soul), "skills": pcfg["skills"],
        }
        note = "OK" if n <= SOUL_FLOOR_CAP else f"over {SOUL_FLOOR_CAP:,} — pin context_file_max_chars"
        scan = "" if findings is None else f"  scan: {findings or 'clean'}"
        print(f"  {pname:<16} SOUL.md {n:>6,} chars ({note})  skills: {len(pcfg['skills'])}{scan}")

    write(out / "MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return problems


if __name__ == "__main__":
    sys.exit(main())
