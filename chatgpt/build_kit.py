#!/usr/bin/env python3
"""Build Career_Reels_ChatGPT_Kit.zip (upload it to the ChatGPT project) and the ChatGPT plugin zip.

    python3 chatgpt/build_kit.py OUT_DIR [--model u2net_human_seg.onnx] [--wheels DIR]

Kit layout (ChatGPT unzips to /mnt/data/kit):  repo/  (tools, docs, specs, skills, chatgpt)
                                              models/u2net_human_seg.onnx   wheels/*.whl   START_HERE.md
"""
import subprocess, sys, tempfile, zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "incoming"}


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    out = Path(a[0]); out.mkdir(parents=True, exist_ok=True)
    model = Path(a[a.index("--model") + 1]) if "--model" in a else None
    wheels = Path(a[a.index("--wheels") + 1]) if "--wheels" in a else None
    if wheels is None:
        wheels = Path(tempfile.mkdtemp())
        for v in ("3.11", "3.12"):
            subprocess.run([sys.executable, "-m", "pip", "download", "onnxruntime", "--no-deps", "--only-binary=:all:",
                            "--python-version", v, "--platform", "manylinux_2_28_x86_64", "-d", str(wheels), "-q"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "download", "flatbuffers", "protobuf", "packaging", "--no-deps",
                        "--only-binary=:all:", "--python-version", "3.11", "--platform", "manylinux2014_x86_64",
                        "-d", str(wheels), "-q"], check=True)
    kit = out / "Career_Reels_ChatGPT_Kit.zip"
    with zipfile.ZipFile(kit, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(REPO.rglob("*")):
            rel = p.relative_to(REPO)
            if p.is_dir() or SKIP_DIRS & set(rel.parts) or p.suffix in (".mp4", ".env") or p.name.endswith(".env"):
                continue
            z.write(p, f"repo/{rel.as_posix()}")
        for w in sorted(wheels.glob("*.whl")):
            if not w.name.startswith("numpy"):
                z.write(w, f"wheels/{w.name}")
        if model:
            z.write(model, "models/u2net_human_seg.onnx", compress_type=zipfile.ZIP_STORED)
        z.write(REPO / "chatgpt/PROJECT_INSTRUCTIONS.md", "START_HERE.md")
    plug = out / "career-reels-editor-chatgpt-v2.zip"
    with zipfile.ZipFile(plug, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(REPO / "chatgpt/skills/career-reels-editor/SKILL.md", "skills/career-reels-editor/SKILL.md")
    print(f"wrote {kit} ({kit.stat().st_size / 1e6:.0f} MB){'' if model else '  (NO MODEL: add --model)'}\nwrote {plug}")


if __name__ == "__main__":
    main()
