#!/usr/bin/env python3
"""Preflight for ANY environment that renders Career Reels (ChatGPT sandbox, Claude cloud, laptop).

    python3 tools/preflight.py [--model PATH/u2net_human_seg.onnx]

Exit 0 = ready. Exit 1 = STOP: tell Prafulla what is missing. Never work around a FAIL
(no colour-key mattes, no DejaVu/default font, no home-made renderer, no "lightweight" substitute).
"""
import importlib, os, shutil, subprocess, sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
fails, notes = [], []


def need(ok, msg, fix):
    (notes if ok else fails).append(("OK  " if ok else "FAIL") + f" {msg}" + ("" if ok else f"\n       fix: {fix}"))


def main():
    a = sys.argv[1:]
    model = a[a.index("--model") + 1] if "--model" in a else None
    cands = [model] if model else [str(REPO / "models/u2net_human_seg.onnx"), str(REPO.parent / "models/u2net_human_seg.onnx"),
                                   str(Path.home() / "seg/human.onnx"), str(Path.home() / "seg/u2net_human_seg.onnx"),
                                   "/mnt/data/models/u2net_human_seg.onnx", "/mnt/data/u2net_human_seg.onnx"]
    model = next((c for c in cands if c and Path(c).exists()), None)

    need(sys.version_info >= (3, 9), f"python {sys.version.split()[0]}", "python 3.9+")
    need(bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe")), "ffmpeg + ffprobe on PATH", "install ffmpeg")
    for m in ("numpy", "PIL"):
        try:
            importlib.import_module(m); need(True, f"import {m}", "")
        except Exception:
            need(False, f"import {m}", f"pip install {'pillow' if m == 'PIL' else m}")
    try:
        import onnxruntime  # noqa
        need(True, f"onnxruntime {onnxruntime.__version__}", "")
    except Exception:
        need(False, "onnxruntime (person mattes)",
             "pip install --no-index --find-links <kit>/wheels --no-deps onnxruntime flatbuffers protobuf packaging")
    need(bool(model) and Path(model).stat().st_size > 150_000_000,
         f"u2net_human_seg.onnx model ({model or 'not found'})",
         "upload models/u2net_human_seg.onnx from the ChatGPT kit (176 MB) and pass --model")
    fonts = [TOOLS / "fonts" / f"Poppins-{w}.ttf" for w in ("ExtraBold", "Bold", "SemiBold")]
    need(all(f.exists() for f in fonts), "Poppins ExtraBold/Bold/SemiBold in tools/fonts/",
         "tools/fonts/ ships in the repo; re-clone or unzip the kit")
    for rel in ("tools/career_reel.py", "tools/career_styles2.py", "tools/templates/approved_energy_v3.json",
                "tools/templates/bgA.png", "docs/Daily-Reel-SOP.md", "docs/style-frames/_all-proven-styles.jpg",
                "tools/spec_lint.py"):
        need((REPO / rel).exists(), rel, "use the full repo / kit, not loose files")
    need(os.environ.get("CR_STRICT", "") not in ("", "0"), "CR_STRICT=1 set (engine stops instead of degrading)",
         "export CR_STRICT=1  (or os.environ['CR_STRICT']='1' before calling the engine)")
    # engine smoke test: fonts resolve to Poppins under strict mode
    try:
        env = dict(os.environ, CR_STRICT="1")
        r = subprocess.run([sys.executable, "-c", "import sys;sys.path.insert(0,'.');import career_reel as c;"
                            "f=c.font(52);print(f.path if hasattr(f,'path') else 'default')"],
                           cwd=TOOLS, env=env, capture_output=True, text=True, timeout=60)
        need(r.returncode == 0 and "Poppins" in r.stdout, f"engine font = {r.stdout.strip() or r.stderr.strip()[-120:]}",
             "engine must load Poppins; see tools/fonts/")
    except Exception as e:
        need(False, f"engine import ({e})", "check python deps")

    print("Career Reels preflight")
    for n in notes + fails:
        print(" ", n)
    if fails:
        print(f"RESULT: FAIL ({len(fails)}). STOP and tell Prafulla exactly what is missing. Do NOT improvise a substitute.")
        sys.exit(1)
    print(f"RESULT: READY. model={model}")


if __name__ == "__main__":
    main()
