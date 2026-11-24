#!/usr/bin/env python3
"""Style map for Career Reels (24 Nov 2026). One source of truth for Claude AND ChatGPT.

    python3 tools/style_map.py menu                 # line-to-style map (pick styles per line, Gate 1)
    python3 tools/style_map.py recent [N]           # Proven styles NOT used as extras in the last N reels (default 3)
    python3 tools/style_map.py check SPEC.json      # which codes the spec really contains vs its style_codes

Why: the reels kept reusing the same 4-6 extras (X2 B1 E2 R1 ...) out of 54 Proven styles. spec_lint now needs
>= 4 extra Proven styles per reel, >= 2 of them not in the last 3 reels, and every claimed code really in the spec.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ["H6", "C5", "L1", "P6", "B6", "B9", "B10", "B11", "E1", "M3", "S1", "S2", "G1", "A1"]   # Energy v3 preset

# Proven styles that do NOT go on Energy v3 (decided 24 Nov 2026). Listing them in style_codes fails spec_lint.
NOT_WITH_V3 = {
    "C1": "Pop captions replace the C5 minimal captions (Energy v3 caption).",
    "C2": "Keywords-only removes the C5 captions Energy v3 needs.",
    "X1": "Whip flash lives in the ads pipeline (reel-video-editor), not in the Career Reels engine.",
}
# Proven styles allowed on Energy v3 only within limits (decided 24 Nov 2026).
LIMITS = {
    "K": "clip-art stickers: max 2 per reel, shoulder height y 1000-1250, x <= 200 or >= 880, never over the face",
    "M1": "punch-ins: max 2 per reel, only on key lines (result / turn), never with a shake at the same moment",
    "SHOWPIECE": "one showpiece (X2/X3/X4) per reel",
}
SHOWPIECES = ("X2", "X3", "X4")
STICKER_KIND = {"chat": "K1", "question": "K2", "link": "K3", "doc": "K4", "check": "K5", "cross": "K6",
                "briefcase": "K7", "share": "K8"}

# Line-to-style map: what the LINE is -> which Proven styles fit it (first = most used in approved reels).
LINE_MAP = [
    ("Hook (first spoken line)", "H6 always + one of H1 question pill, H3 rising headline, H4 myth, H5 title behind you (needs headroom), B9 keyword"),
    ("Recruiter / HR asks something, a skit", "H2 skit labels, P6 typing box, K2 question mark"),
    ("Quoted message, DM, email, pitch line", "P6 typing box, P1 message card, K1 chat bubble"),
    ("Reply, invite or result arrives", "B7 phone alert, P1 message card, P5 stamp"),
    ("Myth / wrong belief", "H4 myth crossed out, K6 red cross"),
    ("Right way / do this", "K5 green tick, B5 tick list, B11 build card"),
    ("Wrong way / don't", "K6 red cross, H4 myth"),
    ("A list or checklist", "B5 tick list, B11 build card, B8 step tracker"),
    ("Numbered steps / method", "B10 section header, B8 step tracker, B1 chips"),
    ("Framework or comparison (problem->result, A vs B)", "B1 chips, B11 build card, L3 side column"),
    ("A number: salary, %, views, calls", "P3 number roll-up, X2 number slam (showpiece), P5 stamp"),
    ("Offer / win / cleared a round", "P5 stamp, B7 phone alert, K7 briefcase"),
    ("Jobs, roles, JDs", "B2 JD cards fan out, K7 briefcase"),
    ("Resume / CV", "K4 resume page, B3 one resume three versions, P2 before/after"),
    ("Tailor / cut / shorten", "B4 scissors tailor, B3 resume split"),
    ("Link / profile / URL", "K3 link, L2 screen top, P4 insights pointer"),
    ("Proof on a screen (LinkedIn, Naukri, dashboard)", "L2 screen top you below, P4 insights pointer, R3 screen recording, L4 floating proof card"),
    ("Showing a document / product", "L3 side column, L4 floating proof card"),
    ("The turn (lekin, iske badle, but)", "B6 big word behind you, X4 quick glitch (showpiece)"),
    ("Emotional big line", "X3 spotlight (showpiece)"),
    ("Office, commute, first-job story", "R2 office & commute B-roll, R1 stock B-roll"),
    ("Concept with no footage of your own", "R1 auto stock B-roll"),
    ("Key phrase of any line", "B9 keyword slam"),
    ("Share / send / forward", "K8 share icon, E1 save & share"),
    ("Ending: useful tip", "E1 save & share"),
    ("Ending: comment a keyword", "E2 comment keyword (+ E1)"),
    ("Ending: series", "E3 follow for part 2 (+ E1)"),
    ("Result line that needs a push", "M1 punch-in (max 2)"),
    ("Always (Energy v3 base)", "C5 L1 M3 S1 S2 G1 A1"),
]


def _els(spec, t):
    return [e for e in spec.get("elements", []) if e.get("type") == t]


def _fx(spec, t):
    return [e for e in spec.get("effects", []) if e.get("type") == t]


def detect(spec):
    """Codes whose element is really in the spec (what the viewer will see)."""
    found = set()
    E = lambda t: bool(_els(spec, t))
    pairs = {"H2": "skit_label", "H3": "rising_headline", "H4": "myth", "H6": "pop_bg", "L3": "side_column",
             "L4": "float_card", "P1": "message_card", "P2": "before_after", "P3": "number", "P4": "insights",
             "P5": "stamp", "P6": "typing_box", "B2": "jd_fan", "B3": "resume_split", "B4": "scissors",
             "B5": "tick_list", "B7": "phone_alert", "B8": "steps", "B9": "keyword", "B10": "header",
             "B11": "build_card", "X2": "number_slam", "E2": "comment_keyword", "E3": "part_two"}
    for code, t in pairs.items():
        if E(t): found.add(code)
    if spec.get("hook"): found.add("H1")
    if spec.get("behind_titles"): found.add("H5")
    if spec.get("bigwords"): found.add("B6")
    if spec.get("chips"): found.add("B1")
    cs = spec.get("caption_style", {}).get("style")
    if spec.get("captions"):
        found.add({"minimal": "C5", "pop": "C1", "karaoke": "C3", "accent": "C4"}.get(cs, "C1"))
    elif _els(spec, "keyword"):
        found.add("C2")
    if _fx(spec, "split"): found.add("L2")
    if _fx(spec, "spotlight"): found.add("X3")
    if _fx(spec, "glitch"): found.add("X4")
    for b in spec.get("broll", []) + _fx(spec, "split"):
        tag = str(b.get("style", "")).upper(); path = str(b.get("clip", ""))
        if tag in ("R2", "R3"): found.add(tag)
        elif "Screen Recordings" in path or "screen" in Path(path).stem.lower(): found.add("R3")
        elif b in spec.get("broll", []): found.add("R1")
    for st in spec.get("stickers", []):
        if st.get("kind") in STICKER_KIND: found.add(STICKER_KIND[st["kind"]])
    if spec.get("punches"): found.add("M1")
    if spec.get("save"): found.add("E1")
    if spec.get("zoom_levels") and not spec.get("pace"): found.add("M3")
    found |= {"L1", "S1", "S2", "G1", "A1"} if spec.get("segments") else set()
    if not spec.get("sfx"): found.discard("S1")
    if not spec.get("look"): found.discard("G1")
    return found


def log_rows(log=None):
    """[(reel, handle, codes)] from docs/Reels-Log.md, newest first, real reels only (handle starts with @)."""
    log = Path(log or ROOT / "docs" / "Reels-Log.md")
    rows = []
    if not log.exists(): return rows
    for line in log.read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 5 or not re.match(r"\d{4}-\d{2}-\d{2}", c[0]) or not c[2].startswith("@"): continue
        if c[5].lower().startswith("rejected"): continue
        rows.append((c[1], c[2], set(re.findall(r"\b[A-Z]\d{1,2}\b", c[3]))))
    return rows


def recent_extras(n=3, exclude=None):
    rows = [r for r in log_rows() if r[0] != exclude][:n]
    used = set().union(*[r[2] for r in rows]) if rows else set()
    return rows, used - set(BASE)


def proven():
    g = (ROOT / "docs" / "TRI-Reel-Style-Guide.md").read_text(encoding="utf-8")
    return {c: n.strip() for c, n, s in re.findall(r"\|\s*\*\*([A-Z]\d+)\*\*\s*\|\s*([^|]*)\|.*?\|\s*(Proven)[^|]*\|", g)}


def main():
    a = sys.argv[1:] or ["menu"]
    if a[0] == "menu":
        print("LINE -> PROVEN STYLES (pick per line; base Energy v3 always on)")
        for k, v in LINE_MAP: print(f"  {k:48s} {v}")
        print("\nNot with Energy v3:", "; ".join(f"{k} ({v})" for k, v in NOT_WITH_V3.items()))
        print("Allowed within limits:", "; ".join(f"{k}: {v}" for k, v in LIMITS.items()))
    elif a[0] == "recent":
        n = int(a[1]) if len(a) > 1 else 3
        rows, used = recent_extras(n)
        pv = proven(); fresh = [c for c in pv if c not in used and c not in BASE and c not in NOT_WITH_V3]
        print(f"Last {n} reels: " + " | ".join(f"{r[0]} ({' '.join(sorted(r[2] - set(BASE)))})" for r in rows))
        print("Styles not used recently: " + " ".join(fresh))
    elif a[0] == "check":
        spec = json.load(open(a[1])); have = detect(spec); claimed = set(spec.get("style_codes", []))
        print("in spec:      ", " ".join(sorted(have)))
        print("claimed only: ", " ".join(sorted(claimed - have - set(BASE))) or "-")
        print("not claimed:  ", " ".join(sorted(have - claimed)) or "-")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
