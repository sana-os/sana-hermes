#!/usr/bin/env python3
"""Check that a version tag is about to point at the right commit, before pushing it.

    python check_release.py v0.5.2          # locally: before `git push origin v0.5.2`
    python check_release.py v0.5.2 --ci     # in CI, on a tag push (no fetch; HEAD is the tagged commit)

Why: v0.5.1 was first tagged on the commit before the licence pull request was merged,
because the local main had not been pulled. CI passed, since every commit builds
consistently on its own; nothing compared the tag with what the release claimed.

Checks (all against the committed HEAD, not the working tree):
  * the tag looks like v<major>.<minor>.<patch>
  * sana-hermes.json and both dist/*/MANIFEST.json carry that version
  * CHANGELOG.md has a section for it
  * LICENSE, LICENSING.md and LICENSES/SANA-OS-1.0.md are committed
  * locally: no uncommitted changes; HEAD is the merge commit at the tip of origin/main
    (after a fetch); an existing tag of that name points at HEAD
  * in CI: HEAD is a merge commit contained in origin/main
Exit code 0 when everything holds, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

LICENCE_FILES = ["LICENSE", "LICENSING.md", "LICENSES/SANA-OS-1.0.md"]
MANIFESTS = ["dist/mode-skills/MANIFEST.json", "dist/mode-inline/MANIFEST.json"]


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    # git prints file contents as UTF-8. Without an explicit encoding, Python decodes with the
    # locale's code page (cp932 on Japanese Windows), fails in a reader thread, and the file
    # then looks missing.
    return subprocess.run(["git", *args], capture_output=True, encoding="utf-8", errors="replace", check=check)


def show(path: str) -> str | None:
    r = git("show", f"HEAD:{path}", check=False)
    return r.stdout if r.returncode == 0 else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tag", help="the tag to check, e.g. v0.5.2")
    ap.add_argument("--ci", action="store_true", help="CI mode: no fetch; HEAD must be contained in origin/main")
    args = ap.parse_args()

    problems: list[str] = []
    m = re.fullmatch(r"v(\d+\.\d+\.\d+)", args.tag)
    if not m:
        print(f"{args.tag}: not of the form v<major>.<minor>.<patch>")
        return 1
    version = m.group(1)

    head = git("rev-parse", "HEAD").stdout.strip()
    subject = git("log", "-1", "--format=%s", "HEAD").stdout.strip()
    parents = git("log", "-1", "--format=%P", "HEAD").stdout.split()
    print(f"HEAD {head[:12]}  {subject}")

    cfg = show("sana-hermes.json")
    if cfg is None:
        problems.append("sana-hermes.json is not committed")
    elif json.loads(cfg).get("package_version") != version:
        problems.append(f"sana-hermes.json package_version is {json.loads(cfg).get('package_version')}, not {version}")
    for path in MANIFESTS:
        text = show(path)
        if text is None:
            problems.append(f"{path} is not committed")
        elif json.loads(text).get("package_version") != version:
            problems.append(f"{path} package_version is {json.loads(text).get('package_version')}, not {version} "
                            "(rebuild dist/ after changing sana-hermes.json)")
    changelog = show("CHANGELOG.md") or ""
    if not re.search(rf"^## {re.escape(version)}\b", changelog, flags=re.M):
        problems.append(f"CHANGELOG.md has no section '## {version}'")
    for path in LICENCE_FILES:
        if show(path) is None:
            problems.append(f"{path} is not committed")

    if len(parents) < 2:
        problems.append("HEAD is not a merge commit; tag the merge commit of the pull request")

    if args.ci:
        if git("merge-base", "--is-ancestor", "HEAD", "origin/main", check=False).returncode != 0:
            problems.append("HEAD is not contained in origin/main")
    else:
        if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
            problems.append("there are uncommitted changes")
        fetched = git("fetch", "--quiet", "origin", check=False)
        if fetched.returncode != 0:
            problems.append(f"git fetch origin failed: {fetched.stderr.strip()}")
        else:
            remote = git("rev-parse", "origin/main", check=False).stdout.strip()
            if remote != head:
                problems.append(f"HEAD is not origin/main ({remote[:12] or 'unknown'}). "
                                "Was the pull request merged on GitHub, and did you run `git pull` on main?")
        existing = git("rev-parse", "--verify", "--quiet", f"refs/tags/{args.tag}^{{commit}}", check=False)
        if existing.returncode == 0 and existing.stdout.strip() != head:
            problems.append(f"tag {args.tag} already exists and points at {existing.stdout.strip()[:12]}, not HEAD")

    if problems:
        print(f"\n{args.tag}: NOT ready to tag")
        for p in problems:
            print("  -", p)
        return 1
    print(f"\n{args.tag}: ready. HEAD is the merge commit on origin/main and carries version {version}.")
    return 0


if __name__ == "__main__":
    # Console or pipe in a legacy code page (cp932 on Japanese Windows): replace what it
    # cannot show (such as an em dash) instead of stopping with UnicodeEncodeError.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")
    sys.exit(main())
