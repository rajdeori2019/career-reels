#!/usr/bin/env python3
"""Energy v3 spec checker. Run before the storyboard AND before render, by any AI (Claude, ChatGPT, ...).

    python3 tools/spec_lint.py SPEC.json [--work WORK] [--render]

Exit 0 = PASS. Exit 1 = FAIL (fix the spec, never render a FAIL).
Every value here comes from tools/templates/approved_energy_v3.json and the Daily Reel SOP.
A rule may only be broken when Prafulla asked for it: list it in the spec as
    "approved_overrides": {"<rule id>": "<his words / date>"}
Rule ids are printed in [brackets].
"""
import json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from pathlib import Path

LOOK = {"brightness": 0.045, "contrast": 1.12, "saturation": 1.15, "vibrance": 0.2,
        "gamma": 1.05, "warm": 0.03, "vignette": 0.2}
ZOOMS_OK = ([[1.08, 1.10], [1.10, 1.12]], [[1.0, 1.02], [1.02, 1.04]])   # 2nd = face-safe (SOP 16 Nov)
HANDLES = ("@iamprafz", "@i.am.a.recruiter")
FORBIDDEN_CAPTION_STYLES = ("pop", "karaoke", "accent")                  # replace v3 parts; only on request
GRAPHIC_TYPES = {"keyword", "header", "typing_box", "build_card", "pop_bg", "myth", "message_card",
                 "before_after", "number", "number_slam", "insights", "stamp", "tick_list", "steps",
                 "side_column", "float_card", "jd_fan", "resume_split", "scissors", "phone_alert",
                 "skit_label", "rising_headline", "comment_keyword", "part_two"}

errors, warns = [], []


def rule(rid, ok, msg, spec, warn=False):
    if ok or rid in spec.get("approved_overrides", {}):
        return
    (warns if warn else errors).append(f"[{rid}] {msg}")


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    spec = json.load(open(a[0]))
    work = Path(a[a.index("--work") + 1]) if "--work" in a else None
    els = spec.get("elements", [])
    caps = spec.get("captions", [])
    cs = spec.get("caption_style", {})

    # --- base look ---
    rule("speed", abs(spec.get("speed", 0) - 1.2) < 1e-6, f"speed must be 1.2 (got {spec.get('speed')})", spec)
    rule("time_base", spec.get("time_base") == "source", "time_base must be \"source\" (all times in source seconds)", spec)
    lk = spec.get("look", {})
    rule("look", all(abs(lk.get(k, -9) - v) < 1e-6 for k, v in LOOK.items()),
         f"look must be the Energy v3 grade exactly: {LOOK}", spec)
    rule("zoom", spec.get("zoom_levels") in [list(map(list, z)) for z in ZOOMS_OK],
         f"zoom_levels must be {ZOOMS_OK[0]} (or face-safe {ZOOMS_OK[1]}); got {spec.get('zoom_levels')}", spec)
    # M1 punch-ins and K clip-art: allowed on Energy v3 only within limits (decided 24 Nov 2026)
    pun = spec.get("punches", [])
    rule("punch_limit", len(pun) <= 2, f"M1 punch-ins: max 2 per reel on key lines (got {len(pun)})", spec)
    rule("punch_code", not pun or "M1" in spec.get("style_codes", []), "punches used: add M1 to style_codes", spec)
    stk = spec.get("stickers", [])
    rule("sticker_limit", len(stk) <= 2, f"K clip-art: max 2 per reel (got {len(stk)})", spec)
    for st in stk:
        y, x = st.get("y", 900), st.get("x", 170)
        rule("sticker_place", 1000 <= y <= 1250 and (x <= 200 or x >= 880),
             f"sticker {st.get('kind')} at x {x}, y {y}: shoulder height only (y 1000-1250, x <= 200 or >= 880)", spec)
    rule("shakes", len(spec.get("shakes", [])) <= 1, "max ONE shake hit per reel", spec)
    rule("lufs", spec.get("lufs") == -14, "lufs must be -14", spec)
    rule("sfx_db", spec.get("sfx_db", -22) == -22, "sfx_db must be -22", spec)

    # --- captions (C5 minimal) ---
    rule("caption_style", cs.get("style") == "minimal",
         f"caption_style.style must be \"minimal\" (C5: white text, yellow underline on active word). "
         f"Got \"{cs.get('style')}\". pop/karaoke/accent boxes are NOT Energy v3", spec)
    rule("caption_size", cs.get("size") in (48, 52), f"caption size 52 (48 only if a line overflows); got {cs.get('size')}", spec)
    rule("caption_y", cs.get("y") == 1480 or bool([e for e in spec.get("effects", []) if e.get("type") == "split"]),
         f"caption y must be 1480; got {cs.get('y')}", spec)
    rule("caption_words", 3 <= cs.get("max_words", 0) <= 5, f"max_words 4-5; got {cs.get('max_words')}", spec)
    rule("captions", len(caps) >= 3, "captions missing", spec)

    # --- cuts: pauses and false starts must be removed ---
    segs = spec.get("segments", [])
    rule("segments", bool(segs), "segments missing", spec)
    for s0, s1 in segs:
        inside = sorted([c for c in caps if c["from"] >= s0 - 0.05 and c["to"] <= s1 + 0.05], key=lambda c: c["from"])
        for c1, c2 in zip(inside, inside[1:]):
            gap = c2["from"] - c1["to"]
            rule("pause_cut", gap <= 0.6,
                 f"pause of {gap:.2f}s kept inside segment [{s0},{s1}] between \"{c1['text'][:30]}\" and "
                 f"\"{c2['text'][:30]}\". Split the segment (cut pauses > ~0.35 s)", spec, warn=gap <= 0.9)
    rule("one_segment", not (len(segs) == 1 and segs[0][1] - segs[0][0] > 25),
         "one single segment over 25 s = no cuts were made. Cut false starts, repeats and pauses", spec)

    # --- Energy v3 graphics ---
    pops = sorted([e for e in els if e.get("type") == "pop_bg"], key=lambda e: e["from"])
    first_cap = min((c["from"] for c in caps), default=0)
    last_cap = max((c["to"] for c in caps), default=0)
    rule("hook_pop", bool(pops) and pops[0]["from"] <= first_cap + 1.0,
         "H6: pop_bg must cover the hook (first spoken line)", spec)
    rule("cta_pop", len(pops) >= 2 and pops[-1]["to"] >= last_cap - 1.5,
         "H6: pop_bg must cover the CTA (last spoken line)", spec)
    if spec.get("bg_replace"):
        rule("navy_ink", all(p.get("pattern") == "ink" for p in pops),
             "navy studio (bg_replace) => every pop_bg pattern must be \"ink\" (stripes/paper/brand are for real room)", spec)
        img = str(spec["bg_replace"].get("image", ""))
        rule("navy_img", img.endswith("templates/bgA.png"), "bg_replace image must be tools/templates/bgA.png", spec)
        rule("navy_cfg", spec["bg_replace"].get("clip") == [0.4, 0.85] and spec["bg_replace"].get("band") == 71,
             "bg_replace must be the approved config {clip:[0.4,0.85], feather:2, band:71, spill_ratio:1.5}", spec)
    kws = [e for e in els if e.get("type") == "keyword"]
    rule("keywords", len(kws) >= max(3, len(caps) // 3),
         f"B9: a keyword slam on the key phrase of most lines (have {len(kws)} for {len(caps)} lines)", spec)
    splits = [(e["from"], e["to"]) for e in spec.get("effects", []) if e.get("type") == "split"] \
        + [(b["start"], b["end"]) for b in spec.get("broll", [])]       # face not on screen there
    in_split = lambda t: any(a - 0.3 <= t <= b + 0.3 for a, b in splits)
    for k in kws:
        y, t = k.get("y", 1330), k.get("at", k.get("from", 0))
        if in_split(t):
            continue                                   # split screen / B-roll: no face under it (TMAY 16 Nov, approved)
        rule("keyword_face", not (380 <= y <= 1250),
             f"keyword \"{k.get('big')}\" at y {y} lands on the FACE (face box ~y 450-1250). Use y 1330", spec)
        rule("keyword_y", abs(y - 1330) <= 40, f"keyword y should be 1330 (got {y} for {k.get('big')})", spec, warn=True)
    for e in els:
        if e.get("type") == "typing_box":
            rule("typing_key", "type" not in {k for k in e if k != "type"} and "type_dur" in e,
                 "typing_box needs type_dur (never a second 'type' key)", spec, warn=True)
        if e.get("type") == "header":
            rule("header_y", 110 <= e.get("y", 150) <= 250, "header must sit at y 110-250", spec)

    # graphic every 1.5-3 s (allow 4.5 s)
    times = [e.get("from", e.get("at", 0)) for e in els if e.get("type") in GRAPHIC_TYPES]
    for e in els:
        times += [i.get("from", i.get("at")) for i in e.get("items", []) + e.get("chips", []) + e.get("steps", [])
                  if isinstance(i, dict) and i.get("from", i.get("at")) is not None]
    times += [b.get("start", 0) for b in spec.get("broll", [])] + [e.get("from", 0) for e in spec.get("effects", [])]
    times += [b.get("from", b.get("at", 0)) for b in spec.get("bigwords", [])]
    times = sorted(times)
    if times and caps:
        pts = [first_cap] + times + [last_cap]
        big = [(round(x, 1), round(y, 1)) for x, y in zip(pts, pts[1:]) if y - x > 4.5]
        rule("graphic_gap", not big, f"no graphic for > 4.5 s at source {big[:4]} (Energy v3 = new graphic every 1.5-3 s)",
             spec, warn=True)

    # B-roll: never in the first 2 s or over the CTA
    for b in spec.get("broll", []):
        t0 = b.get("start", 0)
        rule("broll_clip", bool(b.get("clip")), "B-roll entry needs a clip path", spec)
        rule("broll_hook", t0 >= first_cap + 2.0, f"B-roll at {t0} covers the hook (first 2 s)", spec)
        rule("broll_cta", t0 <= last_cap - 3.0, f"B-roll at {t0} covers the CTA", spec)

    # style codes vs TRI Reel Style Guide (Proven only; Energy v3 base always included)
    guide = Path(__file__).resolve().parent.parent / "docs" / "TRI-Reel-Style-Guide.md"
    status = {}
    if guide.exists():
        import re
        for code, st in re.findall(r"\|\s*\*\*([A-Z]\d+)\*\*\s*\|.*?\|\s*(Proven|Ready)[^|]*\|", guide.read_text()):
            status[code] = st
    codes = spec.get("style_codes", [])
    rule("style_codes", bool(codes), "spec needs \"style_codes\": [...] (every code named in Gate 1, from the TRI Reel Style Guide)", spec)
    base = ["H6", "C5", "L1", "P6", "B6", "B9", "B10", "B11", "E1", "M3", "S1", "S2", "G1", "A1"]
    if codes:
        missing = [c for c in base if c not in codes]
        rule("energy_v3_base", not missing, f"Energy v3 base codes missing from style_codes: {missing}", spec)
        for c in codes:
            rule(f"style_{c}", status.get(c) == "Proven",
                 f"{c} is {status.get(c, 'not in the TRI Reel Style Guide')}: use Proven styles only (Ready only if he asked)", spec)
            fr = guide.parent / "style-frames" / f"{c}.jpg"
            rule(f"frame_{c}", c in base or fr.exists() or status.get(c) != "Proven",
                 f"no reference frame docs/style-frames/{c}.jpg: check the style guide HTML before using {c}", spec, warn=True)
        for bad, code in (("karaoke", "C3"), ("accent", "C4")):
            if cs.get("style") == bad and code not in codes:
                errors.append(f"[caption_code] caption style {bad} = {code}, not in style_codes")

    # --- style variety (24 Nov 2026): Claude and ChatGPT kept reusing the same 4-6 extras out of 54 Proven ---
    if codes:
        import style_map as sm
        have = sm.detect(spec)
        extras = [c for c in codes if c not in sm.BASE]
        for c in codes:
            if c in sm.NOT_WITH_V3:
                errors.append(f"[not_with_v3] {c}: {sm.NOT_WITH_V3[c]} Remove it (see style_map.py menu)")
        fake = [c for c in extras if c not in have]
        rule("code_vs_reel", not fake, f"style_codes claims {fake} but the spec has no element for them. "
             "Add the element or drop the code (python3 tools/style_map.py check SPEC)", spec)
        unclaimed = sorted(c for c in have - set(codes) if c not in sm.BASE)
        rule("codes_unclaimed", not unclaimed, f"spec uses {unclaimed} but style_codes doesn't list them", spec, warn=True)
        rule("variety_count", len(extras) >= 4,
             f"only {len(extras)} extra styles on top of Energy v3 ({extras}); need >= 4 picked from the line-to-style map "
             "(python3 tools/style_map.py menu)", spec)
        rows, used = sm.recent_extras(3, exclude=spec.get("reel"))
        fresh = [c for c in extras if c not in used]
        rule("variety_fresh", len(fresh) >= 2,
             f"only {len(fresh)} extra style(s) not used in the last 3 reels ({fresh}); need >= 2. Recent extras: "
             f"{' '.join(sorted(used))}. Fresh options: python3 tools/style_map.py recent", spec)
        shows = [c for c in sm.SHOWPIECES if c in have]
        rule("one_showpiece", len(shows) <= 1, f"one showpiece per reel, got {shows}", spec)
    rule("reel_name", bool(spec.get("reel")), "spec needs \"reel\": \"<Name>\" (same name as the Reels-Log row)", spec, warn=True)

    # SOP gates: his own words, pasted into the spec (gate2 required for --render)
    ap = spec.get("approvals", {})
    rule("gate1", bool(str(ap.get("gate1", "")).strip()),
         "approvals.gate1 empty: send the Gate 1 reply and paste his OK (date + words) before building the storyboard", spec)
    if "--render" in a:
        rule("gate2", bool(str(ap.get("gate2", "")).strip()),
             "approvals.gate2 empty: no render without his OK on the FULL storyboard", spec)

    # ending
    sv = spec.get("save", {})
    rule("save_text", sv.get("text") == "Save & Share", "E1: ending pill must say \"Save & Share\"", spec)
    rule("save_icon", sv.get("share_icon") is True, "E1: share_icon must be true", spec)
    rule("handle", sv.get("handle") in HANDLES, f"handle must be one of {HANDLES}", spec)

    # work dir checks (after cut + matte)
    if work:
        rule("cut_done", (work / "base.mp4").exists() or any(work.glob("*.mp4")), f"no cut output in {work}; run cut first", spec)
        if spec.get("bg_replace") or pops:
            n = len(list((work / "matte").glob("*.png"))) if (work / "matte").exists() else 0
            rule("mattes", n > 0, "no person mattes found; run `matte` with u2net_human_seg.onnx before storyboard/render", spec)

    print(f"spec_lint {a[0]}")
    for w in warns:
        print("  WARN ", w)
    for e in errors:
        print("  FAIL ", e)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} errors, {len(warns)} warnings). Fix the spec. Do NOT storyboard or render.")
        sys.exit(1)
    print(f"RESULT: PASS ({len(warns)} warnings)")


if __name__ == "__main__":
    main()
