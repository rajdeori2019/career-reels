#!/usr/bin/env python3
"""Final-render QA (SOP step 11). Run on every finished reel before delivering it.

    python3 tools/qa_check.py FINAL.mp4 [SHEET.jpg]

Checks 1080x1920, 30 fps, H.264 + AAC, loudness -14 LUFS (+-1), true peak <= -1.0 dBTP,
and writes a 12-frame contact sheet. Look at the sheet next to docs/style-frames/_all-proven-styles.jpg
before you deliver: no halo around the head, no blurred face, Poppins captions with a yellow underline,
nothing on the face, navy hook/CTA = ink pattern, ends on "Save & Share" + the right handle.
"""
import json, re, subprocess, sys

fails = []


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    f = sys.argv[1]
    sheet = sys.argv[2] if len(sys.argv) > 2 else f.rsplit(".", 1)[0] + "_qa_sheet.jpg"
    p = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", f],
                                  capture_output=True, text=True).stdout)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    au = [s for s in p["streams"] if s["codec_type"] == "audio"]
    dur = float(p["format"]["duration"])
    fps = eval(v["r_frame_rate"])
    if (v["width"], v["height"]) != (1080, 1920): fails.append(f"size {v['width']}x{v['height']} (need 1080x1920)")
    if abs(fps - 30) > 0.01: fails.append(f"fps {fps:.2f} (need 30)")
    if v["codec_name"] != "h264": fails.append(f"video codec {v['codec_name']} (need h264)")
    if not au or au[0]["codec_name"] != "aac": fails.append("audio must be AAC")
    e = subprocess.run(["ffmpeg", "-nostats", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]); tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    if not -15.0 <= I <= -13.0: fails.append(f"loudness {I} LUFS (need -14 +-1)")
    if tp > -1.0: fails.append(f"true peak {tp} dBTP (need <= -1.0)")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", f"fps=12/{dur},scale=270:480,tile=6x2",
                    "-frames:v", "1", sheet])
    print(f"QA {f}: {dur:.2f}s {v['width']}x{v['height']} {fps:.0f}fps, {I} LUFS, TP {tp}")
    print(f"contact sheet: {sheet}  <- LOOK at it vs docs/style-frames before delivering")
    for x in fails:
        print("  FAIL", x)
    print("RESULT:", "FAIL" if fails else "PASS (technical). Visual check still required.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
