#!/usr/bin/env python3
"""Career Reels editor engine (Python + ffmpeg, no Remotion/Chrome needed).

  python3 career_reel.py cut     SPEC.json WORK          # cut + clean voice -> WORK/cut.mp4, WORK/voice.wav
  python3 career_reel.py matte   SPEC.json WORK u2net_human_seg.onnx [--from A --to B]  # person mattes for behind-you text
  python3 career_reel.py stills  SPEC.json WORK t1,t2,..  # preview frames -> WORK/stills.png
  python3 career_reel.py render  SPEC.json WORK OUT.mp4 [--from A --to B]   # chunk = video only
  python3 career_reel.py join    SPEC.json WORK OUT.mp4 C1.mp4 C2.mp4 ...   # chunks + voice/sfx/music mix, loudnorm

All times in SPEC are OUTPUT times (after cutting), except "segments" (source times).
"""
import json, math, os, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
YELLOW = (255, 200, 61, 255)
INK = (17, 17, 17, 255)
WHITE = (255, 255, 255, 255)


# ---------------- fonts ----------------
def font(size, weight="bold"):
    cands = {
        "bold": ["Poppins-ExtraBold.ttf", "Poppins-Bold.ttf", "Montserrat-ExtraBold.ttf", "DejaVuSans-Bold.ttf"],
        "semi": ["Poppins-SemiBold.ttf", "Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"],
    }[weight]
    dirs = [os.environ.get("CR_FONTS", ""), str(Path(__file__).parent / "fonts"),
            "/usr/share/fonts/truetype/google-fonts", "/usr/share/fonts/truetype/dejavu",
            "C:/Windows/Fonts", "/Library/Fonts", "/System/Library/Fonts/Supplemental"]
    for n in cands:
        for d in dirs:
            p = Path(d) / n
            if d and p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size)


# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def back_out(t, s=1.7): t = clamp(t) - 1; return 1 + t * t * ((s + 1) * t + s)
def ease_io(t): t = clamp(t); return t * t * (3 - 2 * t)


# ---------------- drawing helpers ----------------
def rounded(size, radius, fill):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=fill)
    return im


def shadow(im, blur=18, alpha=110, off=(0, 8)):
    pad = blur * 3
    a = im.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk, (pad + off[0], pad + off[1]))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    sh.alpha_composite(im, (pad, pad))
    return sh, pad


def place(canvas, im, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.002:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        a = im.split()[3].point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def text_block(lines, f, fill, pad=(44, 26), bg=None, radius=26, gap=10, stroke=0, stroke_fill=INK):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    boxes = [d.textbbox((0, 0), ln, font=f, stroke_width=stroke) for ln in lines]
    lw = [b[2] - b[0] for b in boxes]; lh = max(b[3] - b[1] for b in boxes)
    w = max(lw) + 2 * pad[0]; h = lh * len(lines) + gap * (len(lines) - 1) + 2 * pad[1]
    im = rounded((w, h), radius, bg) if bg else Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    y = pad[1]
    for ln, b, wdt in zip(lines, boxes, lw):
        dr.text(((w - wdt) / 2 - b[0], y - b[1]), ln, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        y += lh + gap
    return im


# ---------------- elements ----------------
class Hook:            # H1 Question Pill
    def __init__(self, spec):
        self.s = spec; self.cy = spec.get("y", 250)
        img = text_block(spec["text"].upper().split("\n"), font(spec.get("size", 66)), WHITE,
                         bg=(17, 17, 17, 235), pad=(48, 30), radius=30, gap=12)
        self.img, _ = shadow(img, 20, 120)
    def draw(self, c, t):
        a, b = self.s["from"], self.s["to"]
        if not (a <= t <= b + 0.25): return
        k_in = ease_out((t - a) / 0.25) if a > 0 else 1.0
        k_out = 1 - ease_io((t - b) / 0.25) if t > b else 1.0
        place(c, self.img, W / 2, self.cy, scale=0.94 + 0.06 * k_in, alpha=min(k_in if a > 0 else 1, k_out))


class Captions:        # C1 word-by-word, current word yellow
    def __init__(self, groups, y=1400, size=64, max_words=4, hide=()):
        self.y = y; self.f = font(size); self.pages = []; self.hide = hide
        for g in groups:
            words = g["text"].split()
            wt = g.get("words")              # optional explicit word start times
            if not wt:                        # spread by length across the group window
                lens = [len(w) + 2 for w in words]; tot = sum(lens); acc = 0; wt = []
                for L in lens:
                    wt.append(g["from"] + (g["to"] - g["from"]) * acc / tot); acc += L
            for i in range(0, len(words), max_words):
                ws = words[i:i + max_words]; ts = wt[i:i + max_words]
                end = wt[i + max_words] if i + max_words < len(words) else g["to"]
                self.pages.append((ws, ts, end))
    def _render(self, ws, ts, t):
        d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        sp = d.textlength(" ", font=self.f)
        widths = [d.textlength(w, font=self.f) for w in ws]
        lines, cur, cw = [], [], 0          # wrap to <= 860 px
        for i, wdt in enumerate(widths):
            if cur and cw + sp + wdt > 860:
                lines.append(cur); cur, cw = [], 0
            cur.append(i); cw += wdt + (sp if cw else 0)
        lines.append(cur)
        lh = self.f.size * 1.25
        im = Image.new("RGBA", (W, int(lh * len(lines) + 40)), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        active = max([i for i, s in enumerate(ts) if s <= t] or [-1])
        for li, line in enumerate(lines):
            lw = sum(widths[i] for i in line) + sp * (len(line) - 1)
            x = (W - lw) / 2; y = 20 + li * lh
            for i in line:
                if ts[i] <= t:
                    col = YELLOW if i == active else WHITE
                    dr.text((x, y), ws[i], font=self.f, fill=col, stroke_width=7, stroke_fill=(0, 0, 0, 235))
                x += widths[i] + sp
        return im
    def draw(self, c, t):
        if any(a <= t <= b for a, b in self.hide): return
        for ws, ts, end in self.pages:
            if ts[0] <= t < end + 0.05:
                im = self._render(ws, ts, t)
                c.alpha_composite(im, (0, int(self.y - im.height / 2)))
                return


class BigWord:         # B6 big turn word
    def __init__(self, spec, y=1430):
        self.s = spec; self.y = spec.get("y", y)
        img = text_block([spec["text"].upper()], font(spec.get("size", 150)), INK, bg=(255, 255, 255, 250),
                         pad=(56, 18), radius=24)
        self.img, _ = shadow(img, 22, 130)
    def draw(self, c, t):
        a = self.s["at"]; b = a + self.s.get("dur", 0.8)
        if not (a <= t <= b + 0.2): return
        k = back_out((t - a) / 0.3); out = 1 - ease_io((t - b) / 0.2) if t > b else 1
        place(c, self.img, W / 2, self.y, scale=1.35 - 0.35 * k, alpha=min(1, (t - a) / 0.08) * out)


class PopCaptions:     # C1 "pop" style: 2-3 big words per page, page pops in, active word on a yellow box
    def __init__(self, groups, y=1400, size=84, max_words=3, hide=(), emphasis=(), upper=False):
        self.y = y; self.size = size; self.f = font(size); self.hide = hide; self.upper = upper
        self.emph = {e.lower().strip(".,?!:\"'") for e in emphasis}; self.pages = []; self.cache = {}
        for g in groups:
            words = g["text"].split(); wt = g.get("words")
            if not wt:
                lens = [len(w) + 2 for w in words]; tot = sum(lens); acc = 0; wt = []
                for L in lens: wt.append(g["from"] + (g["to"] - g["from"]) * acc / tot); acc += L
            i = 0
            while i < len(words):                     # break pages at punctuation or max_words
                j = i + 1
                while j < len(words) and j - i < max_words and not words[j - 1][-1] in ",.?!:":
                    j += 1
                end = wt[j] if j < len(words) else g["to"]
                self.pages.append((words[i:j], wt[i:j], end)); i = j
    def _word(self, w, active, emph):
        key = (w, active, emph)
        if key not in self.cache:
            txt = w.upper() if self.upper else w
            f = font(int(self.size * (1.12 if emph else 1)))
            d = ImageDraw.Draw(Image.new("RGBA", (1, 1))); b = d.textbbox((0, 0), txt, font=f, stroke_width=8)
            pw, ph = b[2] - b[0] + 28, b[3] - b[1] + 24
            im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
            if active:
                dr.rounded_rectangle([0, 0, pw - 1, ph - 1], 18, fill=YELLOW)
                dr.text((14 - b[0], 12 - b[1]), txt, font=f, fill=INK)
            else:
                dr.text((14 - b[0], 12 - b[1]), txt, font=f, fill=YELLOW if emph else WHITE,
                        stroke_width=8, stroke_fill=(0, 0, 0, 240))
            sh, pad = shadow(im, 10, 150 if not active else 110, (0, 6))
            self.cache[key] = sh
        return self.cache[key]
    def draw(self, c, t):
        if any(a <= t <= b for a, b in self.hide): return
        for ws, ts, end in self.pages:
            if ts[0] <= t < end + 0.04:
                active = max(i for i, s in enumerate(ts) if s <= t)
                imgs = [self._word(w, i == active, w.lower().strip(".,?!:\"'") in self.emph) for i, w in enumerate(ws)]
                pad = 30; gap = 14 - 2 * pad              # images carry a 30 px shadow margin
                rows, row, rw = [], [], 0
                for im in imgs:
                    vis = im.width - 2 * pad
                    if row and rw + 14 + vis > 1000: rows.append(row); row, rw = [], 0
                    rw += vis + (14 if row else 0); row.append(im)
                rows.append(row)
                kp = back_out((t - ts[0]) / 0.18)              # page pop
                y = self.y - (len(rows) - 1) * self.size * 0.66
                for r in rows:
                    tw = sum(i.width for i in r) + gap * (len(r) - 1); x = (W - tw) / 2
                    for im in r:
                        is_act = im is imgs[active]
                        ka = back_out((t - ts[active]) / 0.14) if is_act else 1
                        sc = (0.82 + 0.18 * kp) * (1.18 - 0.18 * ka if is_act else 1)
                        place(c, im, x + im.width / 2, y, scale=sc, alpha=clamp((t - ts[0]) / 0.06))
                        x += im.width + gap
                    y += self.size * 1.32
                return


class BehindTitle:     # H5 title behind you (drawn under the person matte)
    behind = True
    def __init__(self, spec):
        self.s = spec; self.lines = []
        for ln in spec["lines"]:
            col = YELLOW if ln.get("color") == "yellow" else WHITE
            img = text_block([ln["text"]], font(ln.get("size", 180)), col, pad=(20, 10), stroke=0)
            self.lines.append(shadow(img, 26, 170, (0, 10))[0])
    def draw(self, c, t):
        a, b = self.s["from"], self.s["to"]
        if not (a <= t <= b + 0.3): return
        out = 1 - ease_io((t - b) / 0.3) if t > b else 1
        y = self.s.get("y", 420)
        for i, im in enumerate(self.lines):
            k = ease_out((t - a - 0.08 * i) / 0.35) if a > 0 or i else ease_out((t + 0.35 - 0.08 * i) / 0.35)
            place(c, im, W / 2, y + 90 * (1 - k), scale=(1 + 0.08 * (1 - out)), alpha=clamp(k * 1.4) * out)
            y += im.height * 0.62


class BehindWord(BigWord):  # B6 big turn word, behind you, with shake
    behind = True
    def __init__(self, spec, y=560):
        self.s = spec; self.y = spec.get("y", y)
        img = text_block([spec["text"].upper()], font(spec.get("size", 230)), YELLOW, pad=(20, 10))
        self.img, _ = shadow(img, 28, 190, (0, 12))


def _sticker_img(kind, size=230):
    S = size * 2                                   # draw 2x, downsample for smooth edges
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    BLUE, GREEN, RED, GREY = (47, 111, 237, 255), (34, 170, 90, 255), (226, 75, 59, 255), (120, 124, 132, 255)
    d.ellipse([10, 10, S - 10, S - 10], fill=WHITE)
    c = S / 2
    if kind == "chat":
        d.rounded_rectangle([S * .18, S * .22, S * .82, S * .66], 50, fill=BLUE)
        d.polygon([(S * .30, S * .62), (S * .26, S * .80), (S * .46, S * .64)], fill=BLUE)
        for k in (-1, 0, 1): d.ellipse([c + k * 70 - 20, S * .44 - 20, c + k * 70 + 20, S * .44 + 20], fill=WHITE)
    elif kind == "question":
        d.ellipse([S * .14, S * .14, S * .86, S * .86], fill=YELLOW)
        f = font(int(S * .55)); b = d.textbbox((0, 0), "?", font=f)
        d.text((c - (b[2] - b[0]) / 2 - b[0], c - (b[3] - b[1]) / 2 - b[1]), "?", font=f, fill=INK)
    elif kind == "link":
        for dx, dy in ((-52, 52), (52, -52)):
            box = Image.new("RGBA", (S, S), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
            bd.rounded_rectangle([c - 105, c - 52, c + 105, c + 52], 52, outline=BLUE, width=30)
            box = box.rotate(45, resample=Image.BICUBIC)
            im.alpha_composite(box, (dx, dy))
    elif kind == "doc":
        x0, y0, x1, y1 = S * .27, S * .16, S * .73, S * .84
        d.polygon([(x0, y0), (x1 - 70, y0), (x1, y0 + 70), (x1, y1), (x0, y1)], fill=(236, 240, 247, 255), outline=GREY)
        d.polygon([(x1 - 70, y0), (x1 - 70, y0 + 70), (x1, y0 + 70)], fill=(200, 206, 216, 255))
        for k in range(5):
            yy = y0 + 120 + k * 50; d.rounded_rectangle([x0 + 40, yy, x1 - 40 - (60 if k == 4 else 0), yy + 18], 9, fill=GREY)
        d.rounded_rectangle([x0 + 40, y0 + 40, x0 + 140, y0 + 80], 10, fill=BLUE)
        d.arc([x1 - 60, y0 - 50, x1 + 10, y0 + 110], 200, 520, fill=(90, 94, 102, 255), width=12)
    elif kind == "check":
        d.ellipse([S * .14, S * .14, S * .86, S * .86], fill=GREEN)
        d.line([(S * .33, S * .52), (S * .45, S * .64), (S * .69, S * .38)], fill=WHITE, width=44, joint="curve")
    elif kind == "cross":
        d.ellipse([S * .14, S * .14, S * .86, S * .86], fill=RED)
        d.line([(S * .36, S * .36), (S * .64, S * .64)], fill=WHITE, width=44)
        d.line([(S * .64, S * .36), (S * .36, S * .64)], fill=WHITE, width=44)
    elif kind == "briefcase":
        d.rounded_rectangle([S * .2, S * .34, S * .8, S * .76], 34, fill=(140, 90, 50, 255))
        d.rounded_rectangle([S * .38, S * .22, S * .62, S * .38], 20, outline=(140, 90, 50, 255), width=24)
        d.rectangle([S * .2, S * .5, S * .8, S * .54], fill=(110, 70, 40, 255))
    elif kind == "share":
        for px, py in ((.32, .5), (.66, .3), (.66, .7)):
            d.ellipse([S * px - 44, S * py - 44, S * px + 44, S * py + 44], fill=BLUE)
        d.line([(S * .32, S * .5), (S * .66, S * .3)], fill=BLUE, width=22)
        d.line([(S * .32, S * .5), (S * .66, S * .7)], fill=BLUE, width=22)
    im = im.resize((size, size), Image.LANCZOS)
    return shadow(im, 16, 140, (0, 8))[0]


class Sticker:         # relatable clip-art icon that pops in beside you
    def __init__(self, spec):
        self.s = spec; self.img = _sticker_img(spec["kind"], spec.get("size", 230))
    def draw(self, c, t):
        a, b = self.s["from"], self.s["to"]
        if not (a <= t <= b + 0.2): return
        k = back_out((t - a) / 0.35, 2.4); out = 1 - ease_io((t - b) / 0.2) if t > b else 1
        rot = -14 * (1 - ease_out((t - a) / 0.45)) + 3 * math.sin((t - a) * 3)
        im = self.img.rotate(rot, resample=Image.BICUBIC, expand=True)
        place(c, im, self.s.get("x", 170), self.s.get("y", 900) + 8 * math.sin((t - a) * 2.4),
              scale=max(0.01, k * out), alpha=clamp((t - a) / 0.08))


class SavePill:        # E1 Save this pill + bookmark
    def __init__(self, spec, y=1430):
        self.s = spec; self.y = spec.get("y", y)
        f = font(60); h = font(34, "semi")
        txt = spec.get("text", "Save this")
        d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        tw = d.textlength(txt, font=f)
        w, hh = int(tw + 170), 120
        pill = rounded((w, hh), hh // 2, YELLOW)
        dr = ImageDraw.Draw(pill)
        bx, by = 52, 30                               # bookmark icon
        dr.polygon([(bx, by), (bx + 40, by), (bx + 40, by + 60), (bx + 20, by + 44), (bx, by + 60)], fill=INK)
        tb = d.textbbox((0, 0), txt, font=f)
        dr.text((bx + 64 - tb[0], (hh - (tb[3] - tb[1])) / 2 - tb[1]), txt, font=f, fill=INK)
        if spec.get("share_icon"):                    # share icon after the text
            pill2 = rounded((w + 90, hh), hh // 2, YELLOW); pill2.alpha_composite(pill, (0, 0))
            dr2 = ImageDraw.Draw(pill2); sx = w + 10
            for px, py in ((sx, 60), (sx + 44, 34), (sx + 44, 86)):
                dr2.ellipse([px - 13, py - 13, px + 13, py + 13], fill=INK)
            dr2.line([(sx, 60), (sx + 44, 34)], fill=INK, width=7); dr2.line([(sx, 60), (sx + 44, 86)], fill=INK, width=7)
            pill = pill2; w = pill.width
        handle = spec.get("handle")
        if handle:
            hb = d.textbbox((0, 0), handle, font=h)
            full = Image.new("RGBA", (max(w, hb[2] + 10), hh + 70), (0, 0, 0, 0))
            full.alpha_composite(pill, ((full.width - w) // 2, 0))
            ImageDraw.Draw(full).text(((full.width - hb[2]) / 2, hh + 18), handle, font=h, fill=WHITE,
                                      stroke_width=4, stroke_fill=(0, 0, 0, 220))
            pill = full
        self.img, _ = shadow(pill, 20, 120)
    def draw(self, c, t):
        a = self.s["at"]
        if t < a: return
        k = back_out((t - a) / 0.35)
        place(c, self.img, W / 2, self.y + 60 * (1 - ease_out((t - a) / 0.35)), scale=0.8 + 0.2 * k,
              alpha=clamp((t - a) / 0.12))


class Chips:           # B1 framework chips
    def __init__(self, spec, y=200):
        self.s = spec; self.y = spec.get("y", y); f = font(spec.get("size", 46))
        self.imgs = [shadow(text_block([c["text"].upper()], f, INK, bg=YELLOW, pad=(30, 16), radius=16), 14, 110)[0]
                     for c in spec["chips"]]
        gap = spec.get("gap", 70); total = sum(i.width for i in self.imgs) - 2 * 42 * len(self.imgs) + gap * (len(self.imgs) - 1)
        x = (W - total) / 2; self.xs = []
        for im in self.imgs:
            vis = im.width - 84; self.xs.append(x + vis / 2); x += vis + gap
    def draw(self, c, t):
        chips = self.s["chips"]; end = self.s["to"]
        if t < chips[0]["at"] or t > end + 0.3: return
        out = 1 - ease_io((t - end) / 0.3) if t > end else 1
        d = ImageDraw.Draw(c)
        for i, (ch, im, x) in enumerate(zip(chips, self.imgs, self.xs)):
            if t < ch["at"]: break
            k = back_out((t - ch["at"]) / 0.3)
            later = [n for n in chips[i + 1:] if n["at"] <= t]
            dim = 0.55 if later else 1.0
            place(c, im, x, self.y, scale=0.6 + 0.4 * k, alpha=min(1, (t - ch["at"]) / 0.1) * dim * out)
            if i < len(chips) - 1 and chips[i + 1]["at"] <= t:   # arrow to next chip
                x2 = self.xs[i + 1]; ax0 = x + (im.width - 84) / 2 + 12; ax1 = x2 - (self.imgs[i + 1].width - 84) / 2 - 12
                d.line([(ax0, self.y), (ax1, self.y)], fill=(255, 255, 255, int(230 * out)), width=10)
                d.line([(ax0, self.y), (ax1, self.y)], fill=(17, 17, 17, int(255 * out)), width=5)
                d.polygon([(ax1, self.y), (ax1 - 16, self.y - 12), (ax1 - 16, self.y + 12)], fill=(17, 17, 17, int(255 * out)))


# ---------------- camera ----------------
def zoom_at(spec, t):
    """L1/M1: bottom-anchored push. spec["zoom"] = [[shot_start, s0, s1], ...] in output time."""
    shots = spec.get("zoom", [[0, 1.0, 1.0]])
    cur = shots[0]; nxt_t = None
    for i, s in enumerate(shots):
        if s[0] <= t: cur = s; nxt_t = shots[i + 1][0] if i + 1 < len(shots) else spec["_dur"]
    span = max(0.1, (nxt_t or spec["_dur"]) - cur[0])
    k = ease_io((t - cur[0]) / span)
    punch = 1 + 0.025 * max(0.0, 1 - (t - cur[0]) / 0.18) if cur[0] > 0 and not spec.get("_no_cut_punch") else 1
    amt = spec.get("energy", {}).get("punch", 0.06)
    extra = sum(amt * max(0.0, 1 - (t - p) / 0.3) for p in spec.get("punches", []) if p <= t)
    return (cur[1] + (cur[2] - cur[1]) * k) * punch * (1 + extra)


def shake_at(spec, t):
    dx = dy = 0.0
    for p in spec.get("shakes", []):
        if 0 <= t - p < 0.3:
            amp = 14 * (1 - (t - p) / 0.3)
            dx += amp * math.sin((t - p) * 90); dy += amp * math.cos((t - p) * 70)
    return dx, dy


def apply_zoom(frame, s, ox=0.5, oy=1.0):
    if s <= 1.001: return frame
    cw, ch = W / s, H / s
    x0 = (W - cw) * ox; y0 = (H - ch) * oy
    im = Image.fromarray(frame).crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)
    return np.asarray(im)


# ---------------- commands ----------------
def run(cmd): subprocess.run(cmd, check=True)


def cmd_cut(spec_f, work):
    spec = json.loads(Path(spec_f).read_text()); work = Path(work); work.mkdir(exist_ok=True)
    src = spec["source"]; segs = spec["segments"]; sp = float(spec.get("speed", 1.0))
    v, a = [], []
    for i, (s, e) in enumerate(segs):
        v.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}];")
        a.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={e - s - 0.012:.3f}:d=0.012[a{i}];")
    n = len(segs)
    fc = "".join(v) + "".join(a) + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0," + \
         f"setpts=PTS/{sp},fps={FPS},scale={W}:{H},setsar=1" + (("," + spec["grade"]) if spec.get("grade") else "") + "[vo];" + \
         "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,atempo={sp}[ao]"
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-filter_complex", fc, "-map", "[vo]", "-c:v", "libx264",
         "-preset", "ultrafast", "-crf", "12", "-pix_fmt", "yuv420p", str(work / "cut.mp4"),
         "-map", "[ao]", "-ar", "48000", "-ac", "1", str(work / "voice_raw.wav")])
    clean = spec.get("voice_filter", "highpass=f=80,afftdn=nr=8:nf=-40,equalizer=f=250:t=q:w=1:g=-1.5,"
                                     "equalizer=f=3200:t=q:w=1:g=1.5,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(work / "voice_raw.wav"), "-af", clean, str(work / "voice.wav")])
    dur = sum(e - s for s, e in segs) / sp
    print(f"cut {n} segments at {sp}x -> {dur:.2f}s  (out starts: " +
          ", ".join(f"{sum(e - s for s, e in segs[:i]) / sp:.2f}" for i in range(n)) + ")")


class Mattes:
    def __init__(self, work): self.d = Path(work) / "matte"
    def get(self, t):
        p = self.d / f"{int(round(t * FPS)):05d}.png"
        return Image.open(p).convert("L").resize((W, H), Image.BILINEAR) if p.exists() else None


def behind_windows(spec):
    win = []
    for b in spec.get("behind_titles", []): win.append((b["from"], b["to"] + 0.3))
    for b in spec.get("bigwords", []):
        if b.get("behind"): win.append((b["at"], b["at"] + b.get("dur", 0.8) + 0.2))
    for e in spec.get("elements", []):
        if e.get("type") in ("pop_bg", "serif_title"): win.append((e["from"], e["to"] + 0.3))
    return win


_S2 = None
def styles2():
    global _S2
    if _S2 is None:
        import importlib, sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent))
        _S2 = importlib.import_module("career_styles2")
        ns = dict(globals()); ns["H_"] = H; _S2.setup(ns)
    return _S2


_TIME_KEYS = {"from", "to", "at", "strike_at", "truth_at", "wipe_at", "split_at", "snap_at", "tap_at"}
def _map_times(obj, m):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _TIME_KEYS and isinstance(v, (int, float)): obj[k] = m(v)
            elif isinstance(v, (list, dict)): _map_times(v, m)
    elif isinstance(obj, list):
        for v in obj: _map_times(v, m)


def load_spec(spec_f, work=None):
    """Read SPEC. If "time_base" is "source", every time is given in SOURCE seconds and is mapped here
    to output seconds (after cuts and speed). "zoom": "auto" punches in on every cut."""
    spec = json.loads(Path(spec_f).read_text())
    segs = spec["segments"]; sp = float(spec.get("speed", 1.0))
    starts = [sum(e - s for s, e in segs[:i]) / sp for i in range(len(segs))]
    def m(t):
        for (s, e), o in zip(segs, starts):
            if t < s: return o
            if t <= e: return o + (t - s) / sp
        return starts[-1] + (segs[-1][1] - segs[-1][0]) / sp
    spec["_map"] = m
    if spec.get("time_base") == "source":
        for g in spec.get("captions", []):
            g["from"], g["to"] = m(g["from"]), m(g["to"])
            if g.get("words"): g["words"] = [m(x) for x in g["words"]]
        if spec.get("hook"): spec["hook"]["from"], spec["hook"]["to"] = m(spec["hook"]["from"]), m(spec["hook"]["to"])
        for b in spec.get("bigwords", []): b["at"] = m(b["at"]); b["dur"] = b.get("dur", 0.8)
        for b in spec.get("behind_titles", []): b["from"], b["to"] = m(b["from"]), m(b["to"])
        spec["punches"] = [m(x) for x in spec.get("punches", [])]
        spec["shakes"] = [m(x) for x in spec.get("shakes", [])]
        if spec.get("save"): spec["save"]["at"] = m(spec["save"]["at"])
        if spec.get("chips"):
            for c in spec["chips"]["chips"]: c["at"] = m(c["at"])
            spec["chips"]["to"] = m(spec["chips"]["to"])
        for r in spec.get("broll", []): r["start"], r["end"] = m(r["start"]), m(r["end"])
        for st in spec.get("stickers", []): st["from"], st["to"] = m(st["from"]), m(st["to"])
        spec["sfx"] = [[k, m(t)] for k, t in spec.get("sfx", [])]
        _map_times(spec.get("elements", []), m); _map_times(spec.get("effects", []), m)
        spec["time_base"] = "output"
    if spec.get("pace") == "calm":                       # M2 Calm & Warm
        spec.setdefault("zoom_levels", [[1.03, 1.05], [1.05, 1.06]]); spec["_no_cut_punch"] = True
    if spec.get("zoom", "auto") == "auto":
        z = spec.get("zoom_levels", [[1.10, 1.12], [1.15, 1.16]])
        spec["zoom"] = [[o, *z[i % len(z)]] for i, o in enumerate(starts)]
    spec["_cuts"] = starts[1:]
    en = spec.get("energy", {})
    if en.get("emphasis_punch"):
        emph = {e.lower().strip(".,?!:\"'") for e in spec.get("caption_style", {}).get("emphasis", [])}
        for g in spec.get("captions", []):
            words = g["text"].split(); lens = [len(w) + 2 for w in words]; tot = sum(lens); acc = 0
            for w, L in zip(words, lens):
                if w.lower().strip(".,?!:\"'") in emph:
                    spec.setdefault("punches", []).append(g["from"] + (g["to"] - g["from"]) * acc / tot)
                acc += L
    if en.get("cut_whoosh"):
        spec["sfx"] = spec.get("sfx", []) + [["swish", c] for c in starts[1:]]
    if work: spec["_dur"] = dur_of(work)
    return spec


class BRoll:           # full-frame cutaways (clips already 1080x1920, e.g. from broll.py fetch)
    def __init__(self, items):
        self.items = items; self.cache = {}
    def _load(self, i):
        if i not in self.cache:
            self.cache.clear()                     # keep only one clip in memory
            r = self.items[i]
            raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", r["clip"], "-vf", f"scale={W}:{H},fps={FPS}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            n = len(raw) // (W * H * 3)
            self.cache[i] = np.frombuffer(raw[:n * W * H * 3], np.uint8).reshape(n, H, W, 3)
        return self.cache[i]
    def frame(self, t, base):
        for i, r in enumerate(self.items):
            if r["start"] <= t < r["end"]:
                fr = self._load(i); k = min(len(fr) - 1, int((t - r["start"]) * FPS))
                img = fr[k]
                kb = 1.0 + 0.08 * (t - r["start"]) / max(0.1, r["end"] - r["start"])      # slow push-in
                img = apply_zoom(img, kb, 0.5, 0.5)
                a = min(1.0, (r["end"] - t) / 0.12)
                out = img if a >= 0.999 else (img * a + base * (1 - a)).astype(np.uint8)
                fl = max(0.0, 1 - (t - r["start"]) / 0.12)                                # white flash in
                if fl > 0: out = (out * (1 - 0.7 * fl) + 255 * 0.7 * fl).astype(np.uint8)
                return out
        return None


def build(spec):
    els = []
    if spec.get("hook"): els.append(Hook(spec["hook"]))
    if spec.get("chips"): els.append(Chips(spec["chips"]))
    hide = [(b["at"], b["at"] + b.get("dur", 0.8) + 0.1) for b in spec.get("bigwords", [])]
    if spec.get("save"): hide.append((spec["save"]["at"], 1e9))
    for b in spec.get("behind_titles", []): els.append(BehindTitle(b))
    for b in spec.get("bigwords", []): els.append(BehindWord(b) if b.get("behind") else BigWord(b))
    if spec.get("captions"):
        cs = spec.get("caption_style", {})
        hide2 = [h for h, b in zip(hide, spec.get("bigwords", []) + [None]) if not (b and b.get("behind"))] \
            if spec.get("bigwords") else hide
        for e in spec.get("elements", []):
            if e.get("type") == "keyword": hide2 = list(hide2) + [(e["at"], e["at"] + e.get("dur", 1.2) + 0.1)]
        if cs.get("style") == "minimal":
            els.append(styles2().MinimalCaptions(spec["captions"], y=cs.get("y", 1480), size=cs.get("size", 52),
                                                 max_words=cs.get("max_words", 5), hide=hide2))
        elif cs.get("style") == "karaoke":
            els.append(styles2().KaraokeCaptions(spec["captions"], y=cs.get("y", 1430), size=cs.get("size", 62),
                                                 max_words=cs.get("max_words", 5), hide=hide2))
        elif cs.get("style") == "accent":
            els.append(styles2().AccentCaptions(spec["captions"], y=cs.get("y", 1420), size=cs.get("size", 64),
                                                max_words=cs.get("max_words", 4), hide=hide2, accents=cs.get("accents", [])))
        elif cs.get("style") == "pop":
            els.append(PopCaptions(spec["captions"], y=cs.get("y", 1400), size=cs.get("size", 84),
                                   max_words=cs.get("max_words", 3), hide=hide2, emphasis=cs.get("emphasis", []),
                                   upper=cs.get("upper", False)))
        else:
            els.append(Captions(spec["captions"], y=cs.get("y", 1400), size=cs.get("size", 64),
                                max_words=cs.get("max_words", 4), hide=hide2))
    for st in spec.get("stickers", []): els.append(Sticker(st))
    for e in spec.get("elements", []): els.append(styles2().ELEMENTS[e["type"]](e))
    if spec.get("effects"): spec["_ctx"] = styles2().Ctx()
    if spec.get("save"): els.append(SavePill(spec["save"]))
    spec["_broll"] = BRoll(spec.get("broll", []))
    return els


def frames(work, t0, t1):
    p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", str(Path(work) / "cut.mp4"),
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    n = 0
    while True:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        yield t0 + n / FPS, np.frombuffer(buf, np.uint8).reshape(H, W, 3); n += 1
    p.stdout.close(); p.wait()


_LOOK = {}
def apply_look(frame, look):
    """Fast colour grade: brightness/contrast/gamma LUT, saturation, warmth, vignette."""
    if not look: return frame
    key = json.dumps(look, sort_keys=True)
    if key not in _LOOK:
        x = np.arange(256) / 255.0
        y = (x - 0.5) * look.get("contrast", 1.0) + 0.5 + look.get("brightness", 0.0)
        y = np.clip(y, 0, 1) ** (1 / look.get("gamma", 1.0))
        w = look.get("warm", 0.0)
        luts = [np.clip(y * (1 + w) * 255, 0, 255).astype(np.uint8), np.clip(y * 255, 0, 255).astype(np.uint8),
                np.clip(y * (1 - w) * 255, 0, 255).astype(np.uint8)]
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
        vig = (1 - look.get("vignette", 0.0) * np.clip((r - 0.45) / 0.55, 0, 1) ** 2).astype(np.float32)[..., None]
        _LOOK[key] = (luts, vig)
    luts, vig = _LOOK[key]
    out = np.stack([luts[c][frame[..., c]] for c in range(3)], -1).astype(np.float32)
    sat = look.get("saturation", 1.0); vib = look.get("vibrance", 0.0)
    if sat != 1.0 or vib:
        lum = out @ np.array([0.299, 0.587, 0.114], np.float32)
        chroma = out - lum[..., None]
        if vib:                                   # boost dull colours more than already-rich ones (skin stays natural)
            cs = np.abs(chroma).max(-1, keepdims=True) / 255.0
            sat = sat * (1 + vib * np.clip(1 - cs * 3, 0, 1))
        out = lum[..., None] + chroma * sat
    return np.clip(out * vig, 0, 255).astype(np.uint8)


def compose(spec, els, t, frame):
    frame = apply_look(frame, spec.get("look"))
    z = zoom_at(spec, t); ox, oy = spec.get("zoom_origin", [0.5, 1.0])
    zf = apply_zoom(frame, z, ox, oy)
    dx, dy = shake_at(spec, t)
    if dx or dy:
        zf = np.asarray(Image.fromarray(zf).transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), Image.BILINEAR))
    br = spec["_broll"].frame(t, zf) if spec.get("_broll") else None
    arr = br if br is not None else zf
    for fx in spec.get("effects", []):
        arr = styles2().EFFECTS[fx["type"]](arr, t, fx, spec["_ctx"])
    en = spec.get("energy", {})
    if en.get("cut_flash") and br is None:
        for st in spec.get("_cuts", []):
            if 0 <= t - st < 0.1:
                a = en["cut_flash"] * (1 - (t - st) / 0.1)
                arr = (arr * (1 - a) + 255 * a).astype(np.uint8); break
    base = Image.fromarray(arr).convert("RGBA")
    behind = [e for e in els if getattr(e, "behind", False)]
    front = [e for e in els if not getattr(e, "behind", False)]
    if behind and br is None:
        mt = spec["_mattes"].get(t) if spec.get("_mattes") else None
        if mt is not None:
            mt = Image.fromarray(apply_zoom(np.stack([np.asarray(mt)] * 3, -1), z, ox, oy)[..., 0])
            if dx or dy: mt = mt.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), Image.BILINEAR)
            person = base.copy()
            for e in behind: e.draw(base, t)
            base.paste(person, (0, 0), mt)
            for e in behind:
                if getattr(e, "outline", False): e.outline_draw(base, mt, t)
        else:
            front = behind + front                      # no matte yet: draw in front
    for e in front: e.draw(base, t)
    return base.convert("RGB")


def dur_of(work):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(Path(work) / "cut.mp4")], capture_output=True, text=True).stdout
    return float(o.strip())


def cmd_stills(spec_f, work, times):
    spec = load_spec(spec_f, work); els = build(spec); spec["_mattes"] = Mattes(work)
    ims = []
    for t in [float(x) for x in times.split(",")]:
        fr = next(frames(work, t, t + 0.2))[1]
        im = compose(spec, els, t, fr).resize((360, 640))
        ImageDraw.Draw(im).text((10, 8), f"{t:.2f}s", fill=(255, 0, 0), font=font(26))
        ims.append(im)
    cols = min(4, len(ims)); rows = math.ceil(len(ims) / cols)
    sheet = Image.new("RGB", (cols * 364, rows * 644), "white")
    for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 364, (i // cols) * 644))
    sheet.save(Path(work) / "stills.png"); print(f"wrote {Path(work) / 'stills.png'}")


def cmd_render(spec_f, work, out, t0=None, t1=None):
    spec = load_spec(spec_f, work); els = build(spec); spec["_mattes"] = Mattes(work)
    t0 = float(t0 or 0); t1 = float(t1) if t1 is not None else spec["_dur"]
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", spec.get("preset", "veryfast"),
                            "-crf", "18", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    n = 0
    for t, fr in frames(work, t0, t1):
        enc.stdin.write(np.asarray(compose(spec, els, t, fr)).tobytes()); n += 1
    enc.stdin.close(); enc.wait()
    print(f"wrote {out} ({t0:.2f}-{t1:.2f}s, {n} frames)")


def cmd_matte(spec_f, work, model, t0=None, t1=None):
    """Person mattes (u2net_human_seg ONNX) for frames inside behind-you windows. Cached in WORK/matte."""
    import onnxruntime as ort
    spec = load_spec(spec_f, work); d = Path(work) / "matte"; d.mkdir(exist_ok=True)
    so = ort.SessionOptions(); so.intra_op_num_threads = os.cpu_count() or 2
    sess = ort.InferenceSession(model, so, providers=["CPUExecutionProvider"]); name = sess.get_inputs()[0].name
    t0 = float(t0 or 0); t1 = float(t1) if t1 is not None else spec["_dur"]; n = 0
    for a, b in behind_windows(spec):
        a, b = max(a, t0), min(b, t1)
        if a >= b: continue
        for t, fr in frames(work, a, b):
            p = d / f"{int(round(t * FPS)):05d}.png"
            if p.exists(): continue
            x = np.asarray(Image.fromarray(fr).resize((320, 320), Image.BILINEAR), np.float32) / 255.0
            x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
            o = sess.run(None, {name: x})[0][0, 0]; o = (o - o.min()) / (o.max() - o.min() + 1e-8)
            Image.fromarray((o * 255).astype(np.uint8)).resize((540, 960), Image.BILINEAR).save(p); n += 1
    print(f"mattes: {n} new frames in {d}")


# ---------------- audio ----------------
def synth(kind, sr=48000):
    rng = np.random.default_rng(7)
    if kind == "whoosh":
        n = int(0.45 * sr); x = rng.standard_normal(n)
        env = np.sin(np.linspace(0, np.pi, n)) ** 2
        f = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / sr)
        f *= np.exp(-((fr - 2500) / 1800) ** 2); x = np.fft.irfft(f, n) * env
    elif kind == "pop":
        t = np.arange(int(0.12 * sr)) / sr
        x = np.sin(2 * np.pi * (900 - 2500 * t) * t) * np.exp(-t * 40)
    elif kind == "chime":
        t = np.arange(int(0.9 * sr)) / sr
        x = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(1318.5, 1), (1975.5, .5), (2637, .25)]) * np.exp(-t * 5)
    elif kind == "swish":
        n = int(0.22 * sr); x = rng.standard_normal(n); env = np.sin(np.linspace(0, np.pi, n)) ** 3
        f = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / sr); f *= np.exp(-((fr - 4000) / 2500) ** 2)
        x = np.fft.irfft(f, n) * env * 0.5
    elif kind == "tick":
        t = np.arange(int(0.05 * sr)) / sr; x = np.sin(2 * np.pi * 2000 * t) * np.exp(-t * 90)
    else:
        raise ValueError(kind)
    return x / (np.abs(x).max() + 1e-9)


def music_bed(dur, sr=48000, bpm=96):
    """Soft synth pad + light pulse. Quiet under the voice."""
    t = np.arange(int(dur * sr)) / sr
    chords = [(220.0, 277.18, 329.63), (174.61, 220.0, 261.63), (130.81, 164.81, 196.0), (196.0, 246.94, 293.66)]
    bar = 4 * 60 / bpm; x = np.zeros_like(t)
    for i, ch in enumerate(chords * int(dur / bar / 4 + 2)):
        s, e = i * bar, (i + 1) * bar
        m = (t >= s) & (t < e)
        if not m.any(): break
        tt = t[m] - s; env = np.minimum(1, tt / 0.4) * np.minimum(1, (bar - tt) / 0.4)
        x[m] += sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) for f in ch) * env / 6
    beat = 60 / bpm; ph = (t % beat) / beat
    x += 0.15 * np.sin(2 * np.pi * 55 * t) * np.exp(-ph * 12)
    return x / (np.abs(x).max() + 1e-9)


def mix_audio(spec, work):
    import wave
    with wave.open(str(Path(work) / "voice.wav")) as w:
        sr = w.getframerate(); v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    out = v.copy()
    for kind, at in spec.get("sfx", []):
        s = synth(kind, sr) * 10 ** ((spec.get("sfx_db", -24) - (7 if kind == "swish" else 0)) / 20)
        i = int(at * sr); j = min(len(out), i + len(s)); out[i:j] += s[:j - i]
    if spec.get("music", True):
        bed = music_bed(len(out) / sr, sr, spec.get("music_bpm", 96))[:len(out)]
        env = np.abs(v); k = int(0.25 * sr)
        env = np.convolve(env, np.ones(k) / k, mode="same")
        duck = np.where(env > 0.01, spec.get("music_under", 0.05), spec.get("music_gap", 0.10))
        duck = np.convolve(duck, np.ones(k) / k, mode="same")
        out += bed * duck
    path = Path(work) / "mix_pre.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    return path


def cmd_join(spec_f, work, out, chunks):
    spec = load_spec(spec_f)
    pre = mix_audio(spec, work)
    lst = Path(tempfile.mkstemp(suffix=".txt")[1])
    lst.write_text("".join(f"file '{Path(c).resolve()}'\n" for c in chunks))
    lufs = spec.get("lufs", -14)
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af",
                           f"loudnorm=I={lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])      # two-pass loudnorm hits the target
    ln = (f"loudnorm=I={lufs}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(pre),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", ln,
         "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)])
    lst.unlink()
    print(f"wrote {out}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    c = a[0]
    if c == "cut": cmd_cut(a[1], a[2])
    elif c == "stills": cmd_stills(a[1], a[2], a[3])
    elif c == "render":
        t0 = a[a.index("--from") + 1] if "--from" in a else None
        t1 = a[a.index("--to") + 1] if "--to" in a else None
        cmd_render(a[1], a[2], a[3], t0, t1)
    elif c == "join": cmd_join(a[1], a[2], a[3], a[4:])
    elif c == "matte":
        t0 = a[a.index("--from") + 1] if "--from" in a else None
        t1 = a[a.index("--to") + 1] if "--to" in a else None
        cmd_matte(a[1], a[2], a[3], t0, t1)
    else: sys.exit(__doc__)
