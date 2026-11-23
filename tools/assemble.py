#!/usr/bin/env python3
"""Join separately recorded parts (hook + MEAT + CTA) into ONE source video for career_reel.py.

    python3 tools/assemble.py OUT.mp4 HOOK.mp4 MEAT.mp4 [MEAT2.mp4 ...] CTA.mp4

Every part is normalised to 1080x1920, 30 fps, 48 kHz audio (high quality, so the engine's own cut/grade
still works on it), then concatenated. Prints where each part starts in the joined file: the hook part
must be covered by the first pop_bg and the CTA part by the last pop_bg (spec_lint checks this).
Batch folders: `Raw Videos/<week>/01 Hooks/Hxx.mp4`, `02 MEATs/Mx.mp4`, `03 CTAs/CTA_x.mp4`
(CTA_*_IG for Instagram, CTA_*_YT for YouTube).
"""
import json, subprocess, sys
from pathlib import Path


def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout.strip())


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        sys.exit(__doc__)
    out, parts = Path(a[0]), a[1:]
    tmp = out.parent / (out.stem + "_parts"); tmp.mkdir(parents=True, exist_ok=True)
    norm, t, marks = [], 0.0, []
    for i, p in enumerate(parts):
        n = tmp / f"p{i:02d}.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", p,
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p",
                        "-af", "aresample=48000", "-ac", "1", "-c:a", "aac", "-b:a", "192k", str(n)], check=True)
        d = dur(str(n)); marks.append({"part": Path(p).name, "start": round(t, 3), "end": round(t + d, 3)}); t += d
        norm.append(n)
    lst = tmp / "list.txt"; lst.write_text("".join(f"file '{n.resolve()}'\n" for n in norm))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)
    (out.with_suffix(".parts.json")).write_text(json.dumps(marks, indent=1))
    print(f"wrote {out} ({t:.2f}s)")
    for m in marks:
        print(f"  {m['part']:<20} {m['start']:>8.3f} - {m['end']:.3f}")
    print("Use OUT as spec 'source'. Hook part = first pop_bg, CTA part = last pop_bg.")


if __name__ == "__main__":
    main()
