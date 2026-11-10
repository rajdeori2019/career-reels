#!/usr/bin/env python3
"""Career Reels B-roll Autopilot.

Finds, downloads and places vertical b-roll for a talking-head reel.
Order of sources per shot: your own clips folder -> Pexels -> Pixabay -> (optional) Veo.

  python3 broll.py search  shots.json WORK [--own DIR]   # rank candidates per shot
  python3 broll.py fetch   WORK                          # download + crop/trim picks to 1080x1920
  python3 broll.py sheet   WORK                          # contact sheet of picks (picks.png)
  python3 broll.py veo     WORK SHOT_ID                  # generate one clip with Veo (paid)
  python3 broll.py place   BASE.mp4 WORK OUT.mp4 [--from A --to B]  # b-roll over the base (chunk = video only)
  python3 broll.py join    BASE.mp4 OUT.mp4 CHUNK1.mp4 CHUNK2.mp4 ... # join chunks + original audio
  python3 broll.py credits WORK                          # credits.txt for the caption / description

Keys: env PEXELS_API_KEY, PIXABAY_API_KEY, GEMINI_API_KEY, or a keys file (KEY=value lines)
given by env BROLL_KEYS (default ./broll.env).

shots.json: [{"id":1,"start":6.2,"end":8.0,"line":"I applied to 200 jobs",
              "query":"person applying jobs on laptop","alt":["typing laptop night"]}]
"""
import json, os, re, subprocess, sys, urllib.parse, urllib.request, time, shutil
from pathlib import Path

UA = "career-reels-broll/1.0"
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
STOP = set("a an the of to in on at for and or with my your our is are was i me you it this that".split())


def keys():
    k = {}
    f = Path(os.environ.get("BROLL_KEYS", "broll.env"))
    if f.exists():
        for ln in f.read_text().splitlines():
            if "=" in ln and not ln.strip().startswith("#"):
                a, b = ln.split("=", 1)
                k[a.strip()] = b.strip().strip('"').strip("'")
    for n in ("PEXELS_API_KEY", "PIXABAY_API_KEY", "GEMINI_API_KEY"):
        if os.environ.get(n):
            k[n] = os.environ[n]
    return k


def http_json(url, headers=None, data=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})},
                                 data=json.dumps(data).encode() if data is not None else None)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def download(url, dest, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def words(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 1}


def score(c, q, need):
    """0-100. Text match 45, orientation 20, resolution 15, duration 15, source bonus 5."""
    qw = words(q)
    tw = words(c.get("text", ""))
    match = len(qw & tw) / max(1, len(qw))
    if c["src"] == "own" and match == 0:
        return 0.0                                          # own clip must match by its file name
    w, h, d = c.get("w", 0), c.get("h", 0), c.get("dur", 0)
    orient = 20 if h > w else (8 if h == w else 0)          # landscape can still be centre-cropped
    short = min(w, h) if h > w else h                         # usable height after a 9:16 crop
    res = 15 if short >= 1080 else 10 if short >= 720 else 3
    dur = 15 if d >= need + 0.5 else 8 if d >= need else 0
    bonus = 5 if c["src"] == "own" else 0
    return round(45 * match + orient + res + dur + bonus, 1)


# ---------- sources ----------
def src_own(folder, q):
    out = []
    if not folder or not Path(folder).is_dir():
        return out
    for p in Path(folder).rglob("*"):
        if p.suffix.lower() in VIDEO_EXT:
            w, h, d = probe(p)
            out.append({"src": "own", "id": p.name, "text": p.stem.replace("-", " ").replace("_", " "),
                        "w": w, "h": h, "dur": d, "file": str(p), "credit": "own footage"})
    return out


def src_pexels(key, q):
    if not key:
        return []
    url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
        {"query": q, "orientation": "portrait", "per_page": 15})
    js = http_json(url, {"Authorization": key})
    out = []
    for v in js.get("videos", []):
        files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("link")]
        if not files:
            continue
        # smallest file whose SHORT side is >= 1080 (true 1080p or better), else the largest
        side = lambda f: min(f.get("width") or 0, f.get("height") or 0)
        hd = sorted([f for f in files if side(f) >= 1080], key=side)
        f = hd[0] if hd else max(files, key=side)
        slug = urllib.parse.urlparse(v.get("url", "")).path
        out.append({"src": "pexels", "id": str(v["id"]), "text": slug.replace("-", " ").replace("/", " "),
                    "w": f.get("width") or v.get("width", 0), "h": f.get("height") or v.get("height", 0),
                    "dur": v.get("duration", 0), "url": f["link"], "page": v.get("url", ""),
                    "credit": f"Video by {v.get('user', {}).get('name', 'unknown')} on Pexels"})
    return out


def src_pixabay(key, q):
    if not key:
        return []
    url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
        {"key": key, "q": q[:100], "per_page": 20, "safesearch": "true"})
    js = http_json(url)
    out = []
    for v in js.get("hits", []):
        vids = v.get("videos", {})
        f = next((vids[s] for s in ("large", "medium", "small") if vids.get(s, {}).get("url")), None)
        if not f:
            continue
        out.append({"src": "pixabay", "id": str(v["id"]), "text": v.get("tags", ""),
                    "w": f.get("width", 0), "h": f.get("height", 0), "dur": v.get("duration", 0),
                    "url": f["url"], "page": v.get("pageURL", ""),
                    "credit": f"Video by {v.get('user', 'unknown')} on Pixabay"})
    return out


def probe(p):
    try:
        o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height:format=duration", "-of", "json", str(p)],
                           capture_output=True, text=True, timeout=30).stdout
        j = json.loads(o)
        s = j["streams"][0]
        w, h = int(s["width"]), int(s["height"])
        return w, h, float(j["format"]["duration"])
    except Exception:
        return 0, 0, 0.0


# ---------- commands ----------
def cmd_search(shots_file, work, own=None):
    work = Path(work); work.mkdir(parents=True, exist_ok=True)
    k = keys()
    shots = json.loads(Path(shots_file).read_text())
    if not (k.get("PEXELS_API_KEY") or k.get("PIXABAY_API_KEY") or own):
        sys.exit("No PEXELS_API_KEY / PIXABAY_API_KEY found and no --own folder given.")
    own_pool = src_own(own, "")
    plan = []
    for s in shots:
        need = round(s["end"] - s["start"], 2)
        cands, errors = [], []
        for q in [s["query"]] + s.get("alt", []):
            for c in own_pool:
                cands.append(dict(c))
            for name, fn, key in (("pexels", src_pexels, k.get("PEXELS_API_KEY")),
                                  ("pixabay", src_pixabay, k.get("PIXABAY_API_KEY"))):
                try:
                    cands += fn(key, q)
                except Exception as e:
                    errors.append(f"{name}: {e}")
            seen, uniq = set(), []
            for c in cands:
                key2 = (c["src"], c["id"])
                if key2 not in seen:
                    seen.add(key2); c["score"] = score(c, q, need); uniq.append(c)
            cands = uniq
            if any(c["score"] >= 70 for c in cands):
                break                                   # good enough, skip the alt queries
        cands.sort(key=lambda c: c["score"], reverse=True)
        plan.append({**s, "need": need, "pick": 0 if cands else None, "candidates": cands[:8], "errors": errors})
        top = cands[0] if cands else None
        print(f"shot {s['id']} {s['start']:.2f}-{s['end']:.2f}s '{s['query']}': "
              + (f"{top['src']} #{top['id']} score {top['score']}" if top else "NO MATCH (try veo)")
              + (f"  [errors: {'; '.join(errors)}]" if errors else ""))
    (work / "plan.json").write_text(json.dumps(plan, indent=2))
    print(f"wrote {work/'plan.json'}")


def conform(src, dest, need, start=None):
    """Centre-crop to 9:16, scale to 1080x1920, trim to `need` seconds, 30 fps, no audio."""
    w, h, d = probe(src)
    if start is None:
        start = max(0.0, min(0.5, d - need - 0.05)) if d > need else 0.0
    vf = ("crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1080:1920:flags=lanczos,setsar=1,fps=30,"
          "eq=saturation=0.95")
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.2f}", "-i", str(src), "-t", f"{need:.3f}",
           "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(dest)]
    if d and d < need:   # too short: freeze the last frame to fill
        cmd[cmd.index("-vf") + 1] = vf + f",tpad=stop_mode=clone:stop_duration={need - d + 0.1:.2f}"
    subprocess.run(cmd, check=True)


def cmd_fetch(work):
    work = Path(work); plan = json.loads((work / "plan.json").read_text())
    raw = work / "raw"; out = work / "clips"; raw.mkdir(exist_ok=True); out.mkdir(exist_ok=True)
    for s in plan:
        if s.get("pick") is None:
            print(f"shot {s['id']}: no pick, skipped"); continue
        c = s["candidates"][s["pick"]]
        if c["src"] == "own" or c["src"] == "veo":
            src = Path(c["file"])
        else:
            src = raw / f"{c['src']}_{c['id']}.mp4"
            if not src.exists():
                download(c["url"], src)
        dest = out / f"shot{s['id']:02d}.mp4"
        conform(src, dest, s["need"], c.get("in"))
        s["clip"] = str(dest)
        print(f"shot {s['id']}: {c['src']} #{c['id']} -> {dest.name}")
    (work / "plan.json").write_text(json.dumps(plan, indent=2))


def cmd_sheet(work):
    work = Path(work); plan = json.loads((work / "plan.json").read_text())
    clips = [s["clip"] for s in plan if s.get("clip")]
    if not clips:
        sys.exit("No clips yet. Run fetch first.")
    tmp = work / "thumbs"; tmp.mkdir(exist_ok=True)
    for i, c in enumerate(clips):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.4", "-i", c, "-frames:v", "1",
                        "-vf", "scale=270:480", str(tmp / f"{i:02d}.png")], check=True)
    cols = min(4, len(clips)); rows = (len(clips) + cols - 1) // cols
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp / "%02d.png"), "-vf",
                    f"tile={cols}x{rows}:padding=6:color=white", "-frames:v", "1", str(work / "picks.png")], check=True)
    print(f"wrote {work/'picks.png'}")


def cmd_veo(work, shot_id, model=None):
    k = keys(); key = k.get("GEMINI_API_KEY")
    if not key:
        sys.exit("No GEMINI_API_KEY. Veo is optional and paid.")
    model = model or os.environ.get("VEO_MODEL", "veo-3.1-fast-generate-preview")
    work = Path(work); plan = json.loads((work / "plan.json").read_text())
    s = next(x for x in plan if str(x["id"]) == str(shot_id))
    dur = 4 if s["need"] <= 4 else 6 if s["need"] <= 6 else 8
    prompt = (f"Vertical 9:16 realistic b-roll, {s['query']}. Natural light, Indian office or home setting, "
              "handheld but steady. No on-screen text, no captions, no logos, no watermarks.")
    base = "https://generativelanguage.googleapis.com/v1beta"
    op = http_json(f"{base}/models/{model}:predictLongRunning", {"x-goog-api-key": key},
                   {"instances": [{"prompt": prompt}],
                    "parameters": {"aspectRatio": "9:16", "durationSeconds": dur}})
    name = op["name"]
    for _ in range(60):
        time.sleep(10)
        op = http_json(f"{base}/{name}", {"x-goog-api-key": key})
        if op.get("done"):
            break
    if not op.get("done") or "error" in op:
        sys.exit(f"Veo failed: {op.get('error', 'timed out')}")
    uri = op["response"]["generateVideoResponse"]["generatedSamples"][0]["video"]["uri"]
    dest = work / "raw" / f"veo_shot{s['id']:02d}.mp4"; dest.parent.mkdir(exist_ok=True)
    download(uri, dest, {"x-goog-api-key": key})
    w, h, d = probe(dest)
    s["candidates"].insert(0, {"src": "veo", "id": dest.stem, "file": str(dest), "w": w, "h": h, "dur": d,
                               "text": s["query"], "score": 100, "credit": "AI-generated (Veo)"})
    s["pick"] = 0
    (work / "plan.json").write_text(json.dumps(plan, indent=2))
    print(f"shot {s['id']}: veo clip {dest.name} ({d:.1f}s) set as pick")


def cmd_place(base, work, out, t0=None, t1=None):
    """Overlay b-roll on the base video. With t0/t1 renders a VIDEO-ONLY chunk of that range
    (for machines with short command time limits); join the chunks with `join`."""
    work = Path(work); plan = [s for s in json.loads((work / "plan.json").read_text()) if s.get("clip")]
    w, h, d = probe(base)
    chunk = t0 is not None
    t0 = float(t0 or 0); t1 = float(t1) if t1 is not None else d
    shots = [s for s in plan if s["end"] > t0 and s["start"] < t1]
    inputs = ["-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", str(base)]
    chain = f"[0:v]scale={w}:{h},setsar=1,fps=30[v0];"
    last = "v0"
    for i, s in enumerate(shots, 1):
        st, en = s["start"] - t0, s["end"] - t0          # times inside this chunk
        fade = 0.12
        if st < 0:                                        # shot began in the previous chunk
            inputs += ["-ss", f"{-st:.3f}", "-i", s["clip"]]; st = 0.0; fin = ""
        else:
            inputs += ["-itsoffset", f"{st:.3f}", "-i", s["clip"]]
            fin = f"fade=t=in:st={st:.3f}:d={fade}:alpha=1,"
        chain += (f"[{i}:v]scale={w}:{h},setsar=1,fps=30,format=yuva420p,{fin}"
                  f"fade=t=out:st={en - fade:.3f}:d={fade}:alpha=1[b{i}];"
                  f"[{last}][b{i}]overlay=enable='between(t,{st:.3f},{en:.3f})':eof_action=pass[v{i}];")
        last = f"v{i}"
    amap = [] if chunk else ["-map", "0:a?", "-c:a", "aac", "-b:a", "192k"]
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", chain.rstrip(";"),
           "-map", f"[{last}]", *amap, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print(f"wrote {out} ({t0:.1f}-{t1:.1f}s) with {len(shots)} b-roll shots")


def cmd_join(base, out, chunks):
    """Concatenate video-only chunks and add the base video's original audio."""
    import tempfile; lst = Path(tempfile.mkstemp(suffix=".txt")[1])
    lst.write_text("".join(f"file '{Path(c).resolve()}'\n" for c in chunks))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(base),
                    "-map", "0:v", "-map", "1:a?", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", str(out)], check=True)
    lst.unlink()
    print(f"wrote {out} from {len(chunks)} chunks")


def cmd_credits(work):
    work = Path(work); plan = json.loads((work / "plan.json").read_text())
    lines = sorted({s["candidates"][s["pick"]]["credit"] for s in plan
                    if s.get("pick") is not None and s["candidates"][s["pick"]]["src"] in ("pexels", "pixabay")})
    (work / "credits.txt").write_text("\n".join(lines) + ("\n" if lines else ""))
    print("\n".join(lines) or "No stock clips used.")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    c = a[0]
    if c == "search":
        own = a[a.index("--own") + 1] if "--own" in a else None
        cmd_search(a[1], a[2], own)
    elif c == "fetch": cmd_fetch(a[1])
    elif c == "sheet": cmd_sheet(a[1])
    elif c == "veo": cmd_veo(a[1], a[2])
    elif c == "place":
        t0 = a[a.index("--from") + 1] if "--from" in a else None
        t1 = a[a.index("--to") + 1] if "--to" in a else None
        cmd_place(a[1], a[2], a[3], t0, t1)
    elif c == "join": cmd_join(a[1], a[2], a[3:])
    elif c == "credits": cmd_credits(a[1])
    else: sys.exit(__doc__)
