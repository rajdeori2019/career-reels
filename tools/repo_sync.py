#!/usr/bin/env python3
"""Copy everything that belongs in GitHub from the Career Reels folder into a clone of
rajdeori2019/career-reels, then print what changed. Claude commits and pushes after it.

  python3 repo_sync.py "<Career Reels folder or staged copy>" <repo clone> [--reel NAME --date YYYY-MM-DD
                       --handle @x --styles "..." --bg "Real room" --status Delivered]

Copies: tools/*.py engine files, tools/templates/*, tools/incoming/*_spec.json -> specs/,
the SOP and style guide docs. Never copies videos, broll.env or any *.env file.
With --reel it adds a row to the top of docs/Reels-Log.md (skips if that reel+date is already there).
"""
import shutil, subprocess, sys
from pathlib import Path

ENGINE = ["career_reel.py", "career_styles2.py", "broll.py", "hinglish_asr.py", "repo_sync.py"]
DOCS = {  # file in the Career Reels folder -> path in the repo
    "Career Reels - Daily Reel SOP.md": "docs/Daily-Reel-SOP.md",
    "Career Reels — Daily Reel SOP.md": "docs/Daily-Reel-SOP.md",   # laptop file uses an em dash
    "TRI Reel Style Guide.md": "docs/TRI-Reel-Style-Guide.md",
    "TRI Reel Style Guide.html": "docs/TRI-Reel-Style-Guide-interactive.html",
}


def arg(a, k, d=None):
    return a[a.index(k) + 1] if k in a else d


def copy(src, dst, changed):
    if not src.exists():
        return
    if src.suffix == ".env" or src.name.endswith(".env"):
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists() or dst.read_bytes() != src.read_bytes():
        if dst.exists() and dst.suffix in (".md", ".html") and src.stat().st_size < 0.5 * dst.stat().st_size:
            print(f"SKIP {dst.name}: source is under half the size of the repo copy (stub/export?). Fix the laptop copy.")
            return
        shutil.copyfile(src, dst)
        changed.append(str(dst))


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    src, repo = Path(a[0]), Path(a[1])
    changed = []
    for f in ENGINE:
        copy(src / "tools" / f, repo / "tools" / f, changed)
    for f in (src / "tools" / "templates").glob("*"):
        if f.is_file():
            copy(f, repo / "tools" / "templates" / f.name, changed)
    for f in (src / "tools" / "incoming").glob("*_spec.json"):
        copy(f, repo / "specs" / f.name, changed)
    for s, d in DOCS.items():
        copy(src / s, repo / d, changed)

    reel = arg(a, "--reel")
    if reel:
        log = repo / "docs" / "Reels-Log.md"
        date = arg(a, "--date", "")
        lines = log.read_text().splitlines()
        if not any(reel in ln and date in ln for ln in lines):
            spec = f"`specs/{reel}_spec.json`" if (repo / "specs" / f"{reel}_spec.json").exists() else "—"
            row = (f"| {date} | {reel} | {arg(a, '--handle', '')} | {arg(a, '--styles', 'Energy v3')} | "
                   f"{arg(a, '--bg', 'Real room')} | {arg(a, '--status', 'Delivered')} | {spec} |")
            i = next(k for k, ln in enumerate(lines) if ln.startswith("| ---")) + 1
            lines.insert(i, row)
            log.write_text("\n".join(lines) + "\n")
            changed.append(str(log))

    print("\n".join(changed) if changed else "Nothing changed.")
    subprocess.run(["git", "-C", str(repo), "status", "--short"])


if __name__ == "__main__":
    main()
