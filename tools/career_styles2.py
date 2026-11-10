"""Career Reels round-2 styles (overlay elements + frame effects).

Loaded by career_reel.py. Spec keys:
  "elements": [{"type": "<name>", ...times in from/to/at...}, ...]   -> overlay elements
  "effects":  [{"type": "split"|"spotlight"|"glitch"|"grid", ...}]   -> frame effects (under overlays)
  "pace": "calm"                                                     -> M2 Calm & Warm
"""
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

H = {}            # helpers injected by career_reel.setup_styles2()


def setup(ns):
    H.update(ns)
    globals().update({k: ns[k] for k in ("font", "place", "shadow", "text_block", "rounded", "clamp", "ease_out",
                                          "back_out", "ease_io", "W", "H_", "FPS", "YELLOW", "INK", "WHITE")})


BLUE, GREEN, RED, GREY = (47, 111, 237, 255), (34, 170, 90, 255), (226, 75, 59, 255), (120, 124, 132, 255)
CARD = (255, 255, 255, 250)


def serif(size):
    for d in ["/usr/share/fonts/truetype/google-fonts", "/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts"]:
        for n in ["Lora-Italic-Variable.ttf", "DejaVuSerif-Italic.ttf", "georgiai.ttf"]:
            p = Path(d) / n
            if p.exists():
                f = ImageFont.truetype(str(p), size)
                try: f.set_variation_by_axes([700])
                except Exception: pass
                return f
    return font(size)


def card(w, h, r=28, fill=CARD):
    return rounded((int(w), int(h)), r, fill)


def fit(im, max_w=1000):
    """Scale an overlay down so it never runs off the 1080 px frame."""
    if im.width <= max_w: return im
    r = max_w / im.width
    return im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)


def window(s, t, pad_out=0.25):
    return s["from"] <= t <= s["to"] + pad_out


def fade_out(s, t, d=0.25):
    return 1 - ease_io((t - s["to"]) / d) if t > s["to"] else 1.0


def load_image(path, w, h, mode="cover"):
    im = Image.open(path).convert("RGBA")
    r = max(w / im.width, h / im.height) if mode == "cover" else min(w / im.width, h / im.height)
    im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    if mode == "cover":
        x = (im.width - w) // 2; y = (im.height - h) // 2
        im = im.crop((x, y, x + w, y + h))
    return im


def rmask(size, r):
    m = Image.new("L", size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    return m


# ======================= HOOKS =======================
class SkitLabel:          # H2 role labels during a skit opening
    def __init__(self, s):
        self.s = s
        self.img = shadow(text_block([s["text"].upper()], font(38), INK, bg=YELLOW, pad=(26, 12), radius=14), 12, 110)[0]
    def draw(self, c, t):
        s = self.s
        if not window(s, t, 0.2): return
        k = back_out((t - s["from"]) / 0.3)
        place(c, self.img, s.get("x", 60) + self.img.width / 2 - 30, s.get("y", 1200), scale=0.7 + 0.3 * k,
              alpha=clamp((t - s["from"]) / 0.1) * fade_out(s, t, 0.2))


class RisingHeadline:     # H3 letters rise from a mask + underline sweep under the key word
    def __init__(self, s):
        self.s = s; self.f = font(s.get("size", 92)); self.lines = s["text"].upper().split("\n")
    def draw(self, c, t):
        s = self.s
        if not window(s, t, 0.3): return
        out = fade_out(s, t, 0.3); a = s["from"]
        d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        lh = self.f.size * 1.12; y0 = s.get("y", 230) - lh * len(self.lines) / 2
        layer = Image.new("RGBA", (W, int(lh * len(self.lines) + 60)), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        n = 0; key = s.get("key", "").upper(); kbox = None
        for li, line in enumerate(self.lines):
            lw = d.textlength(line, font=self.f); x = (W - lw) / 2; y = 20 + li * lh
            for ch in line:
                k = ease_out((t - a - 0.025 * n) / 0.35) if a > 0.01 else 1.0
                cw = d.textlength(ch, font=self.f)
                if k > 0:
                    glyph = Image.new("RGBA", (int(cw + 12), int(lh + 20)), (0, 0, 0, 0))
                    ImageDraw.Draw(glyph).text((4, 4 + (1 - k) * lh), ch, font=self.f, fill=WHITE,
                                               stroke_width=6, stroke_fill=(0, 0, 0, 230))
                    layer.alpha_composite(glyph, (int(x - 4), int(y - 4)))
                x += cw; n += 1
            if key and key in line:
                kx = (W - lw) / 2 + d.textlength(line[:line.index(key)], font=self.f)
                kbox = (kx, y + lh * 0.98, d.textlength(key, font=self.f))
        if kbox:
            ku = ease_out((t - a - 0.025 * n - 0.1) / 0.35) if a > 0.01 else 1.0
            ld.rounded_rectangle([kbox[0], kbox[1], kbox[0] + kbox[2] * ku, kbox[1] + 12], 6, fill=YELLOW)
        if out < 1:
            layer.putalpha(layer.split()[3].point(lambda v: int(v * out)))
        c.alpha_composite(layer, (0, int(y0 - 20)))


class MythCrossed:        # H4 wrong belief -> red strike -> truth
    def __init__(self, s):
        self.s = s
        self.myth = fit(shadow(text_block(s["myth"].upper().split("\n"), font(s.get("size", 64)), (90, 90, 90, 255),
                                          bg=CARD, pad=(34, 20), radius=22), 14, 110)[0])
        self.truth = fit(shadow(text_block(s["truth"].upper().split("\n"), font(s.get("size", 64)), INK,
                                           bg=YELLOW, pad=(34, 20), radius=22), 14, 120)[0])
    def draw(self, c, t):
        s = self.s
        if not window(s, t, 0.25): return
        a = s["from"]; strike = s.get("strike_at", a + 0.8); swap = s.get("truth_at", strike + 0.5)
        y = s.get("y", 260); out = fade_out(s, t)
        if t < swap + 0.15:
            k = back_out((t - a) / 0.3) if a > 0.01 else 1
            fade = 1 - clamp((t - swap) / 0.15)
            place(c, self.myth, W / 2, y, scale=0.8 + 0.2 * k, alpha=clamp((t - a) / 0.08 + (a <= 0.01)) * fade)
            if t >= strike:
                ks = ease_out((t - strike) / 0.25); w = (self.myth.width - 120) * ks
                d = ImageDraw.Draw(c); x0 = W / 2 - (self.myth.width - 120) / 2
                d.line([(x0, y + 6), (x0 + w, y - 6)], fill=RED[:3] + (int(255 * fade),), width=12)
        if t >= swap:
            k = back_out((t - swap) / 0.3)
            place(c, self.truth, W / 2, y, scale=0.6 + 0.4 * k, alpha=clamp((t - swap) / 0.08) * out)


# ======================= CAPTIONS =======================
class KaraokeCaptions:    # C3 frosted pill, upcoming words faded, current word gold
    def __init__(self, groups, y=1430, size=62, max_words=5, hide=()):
        self.y = y; self.f = font(size); self.hide = hide; self.pages = H["Captions"](groups, y, size, max_words).pages
    def draw(self, c, t):
        if any(a <= t <= b for a, b in self.hide): return
        for ws, ts, end in self.pages:
            if ts[0] <= t < end + 0.04:
                d = ImageDraw.Draw(Image.new("RGBA", (1, 1))); sp = d.textlength(" ", font=self.f)
                widths = [d.textlength(w, font=self.f) for w in ws]; tw = sum(widths) + sp * (len(ws) - 1)
                pw, ph = int(min(1000, tw + 70)), int(self.f.size * 1.6)
                x0, y0 = int((W - pw) / 2), int(self.y - ph / 2)
                region = c.crop((x0, y0, x0 + pw, y0 + ph)).filter(ImageFilter.GaussianBlur(18))
                dark = Image.new("RGBA", region.size, (10, 10, 12, 140)); region.alpha_composite(dark)
                c.paste(region, (x0, y0), rmask(region.size, ph // 2))
                dr = ImageDraw.Draw(c); x = (W - tw) / 2
                active = max([i for i, s in enumerate(ts) if s <= t] or [-1])
                for i, w in enumerate(ws):
                    col = (232, 199, 126, 255) if i == active else (WHITE if ts[i] <= t else (255, 255, 255, 107))
                    dr.text((x, self.y - self.f.size * 0.62), w, font=self.f, fill=col)
                    x += widths[i] + sp
                return


class AccentCaptions:     # C4 sans words + serif italic accent phrase + underline sweep
    def __init__(self, groups, y=1420, size=64, max_words=4, hide=(), accents=()):
        self.y = y; self.f = font(size, "semi"); self.sf = serif(int(size * 1.15)); self.hide = hide
        self.acc = {a.lower().strip(".,?!") for a in accents}
        self.pages = H["Captions"](groups, y, size, max_words).pages
    def draw(self, c, t):
        if any(a <= t <= b for a, b in self.hide): return
        for ws, ts, end in self.pages:
            if ts[0] <= t < end + 0.04:
                d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
                fonts = [self.sf if w.lower().strip(".,?!") in self.acc else self.f for w in ws]
                widths = [d.textlength(w + " ", font=f) for w, f in zip(ws, fonts)]
                x = (W - sum(widths)) / 2; dr = ImageDraw.Draw(c)
                for i, (w, f) in enumerate(zip(ws, fonts)):
                    if ts[i] <= t:
                        acc = f is self.sf
                        if acc:
                            dr.text((x + 3, self.y - f.size * 0.7 + 4), w, font=f, fill=(0, 0, 0, 170))
                            dr.text((x, self.y - f.size * 0.7), w, font=f, fill=YELLOW)
                        else:
                            dr.text((x, self.y - f.size * 0.7), w, font=f, fill=WHITE, stroke_width=5, stroke_fill=(0, 0, 0, 220))
                        if acc:
                            u = ease_out((t - ts[i]) / 0.35); lw = d.textlength(w, font=f)
                            dr.rounded_rectangle([x, self.y + f.size * 0.42, x + lw * u, self.y + f.size * 0.42 + 6], 3, fill=YELLOW)
                    x += widths[i]
                return


# ======================= LAYOUT =======================
def fx_split(arr, t, s, ctx):
    """L2 screen recording on top (0-46%), speaker below."""
    if not (s["from"] <= t <= s["to"]): return arr
    top_h = int(H_ * s.get("top", 0.46))
    clip = ctx.clip_frame(s["clip"], t - s["from"] + s.get("clip_start", 0), W, top_h)
    person = Image.fromarray(arr)
    fy = s.get("face_y", 0.42)                     # where the face sits in the full frame (fraction)
    ph = H_ - top_h; y0 = int(max(0, min(H_ - ph, fy * H_ - ph * 0.35)))
    bottom = person.crop((0, y0, W, y0 + ph))
    out = Image.new("RGB", (W, H_)); out.paste(clip, (0, 0)); out.paste(bottom, (0, top_h))
    d = ImageDraw.Draw(out); d.rectangle([0, top_h - 4, W, top_h + 4], fill=YELLOW[:3])
    k = clamp((t - s["from"]) / 0.15)
    return (np.asarray(out) * k + arr * (1 - k)).astype(np.uint8) if k < 1 else np.asarray(out)


class SideColumn:         # L3 product/document on one side, text in the other column
    def __init__(self, s):
        self.s = s; self.img = None
        if s.get("image"):
            im = load_image(s["image"], s.get("w", 280), s.get("h", 380), "fit")
            fr = card(im.width + 24, im.height + 24, 22); fr.alpha_composite(im, (12, 12))
            self.img = shadow(fr, 20, 140)[0]
        self.txt = [shadow(text_block([ln.upper()], font(46), INK, bg=YELLOW if i == 0 else CARD, pad=(26, 14), radius=16), 12, 110)[0]
                    for i, ln in enumerate(s.get("text", []))]
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        left = s.get("side", "left") == "left"; k = ease_out((t - s["from"]) / 0.4); out = fade_out(s, t)
        if self.img:
            x = (200 if left else W - 200) + (-1 if left else 1) * 300 * (1 - k)
            place(c, self.img, x, s.get("y", 1120), alpha=out)
        for i, im in enumerate(self.txt):
            ki = back_out((t - s["from"] - 0.25 - 0.15 * i) / 0.3)
            place(c, im, (W - 230) if left else 230, s.get("y", 1120) - 60 + i * 100, scale=max(0.01, ki), alpha=out)


class FloatCard:          # L4 small proof card floating above your head
    def __init__(self, s):
        self.s = s
        if s.get("image"):
            im = load_image(s["image"], s.get("w", 520), s.get("h", 300), "fit")
            fr = card(im.width + 20, im.height + 20, 20); fr.alpha_composite(im, (10, 10)); self.img = shadow(fr, 18, 130)[0]
        else:
            self.img = shadow(text_block(s["text"].split("\n"), font(50), INK, bg=CARD, pad=(34, 22), radius=22), 18, 130)[0]
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        k = back_out((t - s["from"]) / 0.4)
        place(c, self.img, W / 2, s.get("y", 250) + 10 * math.sin((t - s["from"]) * 2), scale=0.7 + 0.3 * k,
              alpha=clamp((t - s["from"]) / 0.1) * fade_out(s, t))


# ======================= PROOF =======================
class MessageCard:        # P1 recruiter message / interview invite with blurred name and a highlighted line
    def __init__(self, s):
        self.s = s; f = font(38, "semi"); fb = font(34)
        lines = s["lines"]; w = 880; h = 150 + 54 * len(lines)
        im = card(w, h, 30); d = ImageDraw.Draw(im)
        d.ellipse([36, 32, 112, 108], fill=(200, 205, 215, 255))
        d.rounded_rectangle([132, 44, 132 + 260, 72], 12, fill=(205, 210, 220, 255))       # blurred name
        d.rounded_rectangle([132, 82, 132 + 170, 100], 9, fill=(225, 228, 235, 255))
        hl = s.get("highlight", 0)
        for i, ln in enumerate(lines):
            y = 130 + i * 54
            if i == hl: d.rounded_rectangle([28, y - 6, w - 28, y + 46], 10, fill=(255, 226, 140, 255))
            d.text((44, y), ln, font=f if i == hl else fb, fill=INK)
        self.img = shadow(im, 22, 140)[0]
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        k = ease_out((t - s["from"]) / 0.45)
        place(c, self.img, W / 2, s.get("y", 330) - 260 * (1 - k), alpha=clamp((t - s["from"]) / 0.12) * fade_out(s, t))


class BeforeAfter:        # P2 wipe from the old image to the new one
    def __init__(self, s):
        self.s = s; self.w, self.h = s.get("w", 860), s.get("h", 1000)
        self.a = load_image(s["before"], self.w, self.h); self.b = load_image(s["after"], self.w, self.h)
        self.lab = [shadow(text_block([x], font(40), INK if x == "AFTER" else WHITE, bg=YELLOW if x == "AFTER" else (17, 17, 17, 230),
                                      pad=(22, 10), radius=12), 10, 100)[0] for x in ("BEFORE", "AFTER")]
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        wipe = s.get("wipe_at", s["from"] + 1.2); k = ease_io((t - wipe) / 0.7)
        comp = self.a.copy(); cut = int(self.w * k)
        if cut > 0: comp.paste(self.b.crop((0, 0, cut, self.h)), (0, 0))
        d = ImageDraw.Draw(comp)
        if 0 < k < 1: d.rectangle([cut - 4, 0, cut + 4, self.h], fill=WHITE)
        fr = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0)); fr.paste(comp, (0, 0), rmask(comp.size, 26))
        fr = shadow(fr, 24, 150)[0]
        a = clamp((t - s["from"]) / 0.2) * fade_out(s, t)
        place(c, fr, W / 2, s.get("y", 820), scale=0.92 + 0.08 * ease_out((t - s["from"]) / 0.3), alpha=a)
        lab = self.lab[1] if k > 0.5 else self.lab[0]
        place(c, lab, W / 2, s.get("y", 820) - self.h / 2 - 10, alpha=a)


class NumberRoll:         # P3 number roll-up (X2 adds slam rays + ring, shake via spec "shakes")
    def __init__(self, s, slam=False):
        self.s = s; self.slam = slam; self.f = font(s.get("size", 170))
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        dur = s.get("roll", 1.0); k = ease_out((t - s["from"]) / dur)
        v = s.get("start", 0) + (s["value"] - s.get("start", 0)) * k
        txt = f"{s.get('prefix', '')}{v:,.{s.get('decimals', 0)}f}{s.get('suffix', '')}"
        im = shadow(text_block([txt], self.f, INK, bg=YELLOW, pad=(40, 16), radius=28), 22, 150)[0]
        y = s.get("y", 300); out = fade_out(s, t)
        if self.slam and t >= s["from"] + dur:
            r = ease_out((t - s["from"] - dur) / 0.5); d = ImageDraw.Draw(c)
            for i in range(14):
                ang = i * math.pi / 7; r0, r1 = 160 + 120 * r, 220 + 220 * r
                d.line([(W / 2 + r0 * math.cos(ang), y + r0 * math.sin(ang)), (W / 2 + r1 * math.cos(ang), y + r1 * math.sin(ang))],
                       fill=(255, 200, 61, int(220 * (1 - r) * out)), width=10)
            d.ellipse([W / 2 - 200 - 250 * r, y - 200 - 250 * r, W / 2 + 200 + 250 * r, y + 200 + 250 * r],
                      outline=(255, 255, 255, int(200 * (1 - r) * out)), width=8)
        sc = (1 + 0.25 * (1 - back_out((t - s["from"] - dur) / 0.3))) if self.slam and t >= s["from"] + dur else 1
        place(c, im, W / 2, y, scale=sc, alpha=clamp((t - s["from"]) / 0.1) * out)


class InsightsPointer:    # P4 screenshot zooms to the number + self-drawing arrow
    def __init__(self, s):
        self.s = s; self.src = Image.open(s["image"]).convert("RGBA")
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        w, h = s.get("w", 900), s.get("h", 1100); k = ease_io((t - s["from"]) / s.get("zoom_dur", 1.2))
        px, py = s.get("point", [0.5, 0.5]); z = 1 + (s.get("zoom", 2.0) - 1) * k
        base = load_image(s["image"], w, h, "cover"); cw, ch = w / z, h / z
        x0 = min(max(0, px * w - cw / 2), w - cw); y0 = min(max(0, py * h - ch / 2), h - ch)
        view = base.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.BILINEAR)
        tx, ty = (px * w - x0) * z, (py * h - y0) * z
        d = ImageDraw.Draw(view); ka = ease_out((t - s["from"] - s.get("zoom_dur", 1.2)) / 0.4)
        if ka > 0:
            sx, sy = tx - 260, ty + 260; ex, ey = sx + (tx - 30 - sx) * ka, sy + (ty + 30 - sy) * ka
            d.line([(sx, sy), (ex, ey)], fill=RED, width=14)
            if ka > 0.95: d.polygon([(tx - 18, ty + 18), (tx - 70, ty + 34), (tx - 34, ty + 70)], fill=RED)
            d.ellipse([tx - 90, ty - 60, tx + 90, ty + 60], outline=(255, 200, 61, int(255 * ka)), width=10)
        fr = Image.new("RGBA", (w, h), (0, 0, 0, 0)); fr.paste(view, (0, 0), rmask((w, h), 26))
        place(c, shadow(fr, 24, 150)[0], W / 2, s.get("y", 760), alpha=clamp((t - s["from"]) / 0.2) * fade_out(s, t))


class OfferStamp:         # P5 stamp lands with a ring
    def __init__(self, s):
        self.s = s; f = font(s.get("size", 96))
        im = text_block([s.get("text", "OFFER").upper()], f, RED, pad=(40, 18), radius=20)
        fr = Image.new("RGBA", (im.width + 24, im.height + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
        d.rounded_rectangle([4, 4, fr.width - 5, fr.height - 5], 24, outline=RED, width=10); fr.alpha_composite(im, (12, 12))
        self.img = fr.rotate(-8, expand=True, resample=Image.BICUBIC)
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        k = clamp((t - s["from"]) / 0.22); sc = 2.4 - 1.4 * (k ** 3)
        y = s.get("y", 330)
        if k >= 1:
            r = ease_out((t - s["from"] - 0.22) / 0.5); d = ImageDraw.Draw(c)
            d.ellipse([W / 2 - 220 - 260 * r, y - 140 - 200 * r, W / 2 + 220 + 260 * r, y + 140 + 200 * r],
                      outline=(226, 75, 59, int(200 * (1 - r))), width=8)
        place(c, self.img, W / 2, y, scale=sc, alpha=min(1, k * 2) * fade_out(s, t))


# ======================= TEACHING BEATS =======================
def jd_card(title, lines=3, w=280, h=360, accent=BLUE):
    im = card(w, h, 22); d = ImageDraw.Draw(im)
    d.rounded_rectangle([22, 24, 22 + 70, 24 + 70], 14, fill=accent)
    d.text((22, 112), title, font=font(32), fill=INK)
    for i in range(lines):
        d.rounded_rectangle([22, 168 + i * 40, w - 22 - (50 if i == lines - 1 else 0), 186 + i * 40], 9, fill=(214, 218, 226, 255))
    return shadow(im, 16, 130)[0]


class JDFan:              # B2 JD cards fan out
    def __init__(self, s):
        self.s = s; titles = s.get("titles", ["JD 1", "JD 2", "JD 3"])
        self.cards = [jd_card(x, accent=a) for x, a in zip(titles, [BLUE, YELLOW, GREEN])]
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        k = back_out((t - s["from"]) / 0.5); out = fade_out(s, t); y = s.get("y", 300)
        for i, (cd, ang, dx) in enumerate(zip(self.cards, (14, 0, -14), (-280, 0, 280))):
            im = cd.rotate(ang * k, expand=True, resample=Image.BICUBIC)
            place(c, im, W / 2 + dx * k, y + abs(dx) * 0.12 * k, scale=0.85, alpha=clamp((t - s["from"]) / 0.12) * out)


class ResumeSplit:        # B3 one resume card splits into three coloured versions with ticks
    def __init__(self, s):
        self.s = s; labels = s.get("labels", ["Version A", "Version B", "Version C"])
        self.one = jd_card(s.get("title", "Resume"), 4, 300, 400, GREY)
        self.three = [jd_card(l, 4, 280, 380, a) for l, a in zip(labels, [BLUE, YELLOW, GREEN])]
        tick = Image.new("RGBA", (84, 84), (0, 0, 0, 0)); d = ImageDraw.Draw(tick)
        d.ellipse([0, 0, 83, 83], fill=GREEN); d.line([(22, 44), (37, 58), (62, 28)], fill=WHITE, width=10)
        self.tick = tick
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        split = s.get("split_at", s["from"] + 0.8); out = fade_out(s, t); y = s.get("y", 330)
        if t < split:
            place(c, self.one, W / 2, y, scale=0.8 + 0.2 * back_out((t - s["from"]) / 0.3), alpha=out)
            return
        k = back_out((t - split) / 0.45)
        for i, (im, dx) in enumerate(zip(self.three, (-310, 0, 310))):
            place(c, im, W / 2 + dx * k, y, scale=0.82, alpha=out)
            kt = back_out((t - split - 0.35 - 0.15 * i) / 0.25)
            if kt > 0: place(c, self.tick, W / 2 + dx * k + 100, y - 140, scale=max(0.01, kt), alpha=out)


class ScissorsTailor:     # B4 scissors cut along a dashed line and reveal the words
    def __init__(self, s):
        self.s = s; self.txt = shadow(text_block([s["text"].upper()], font(s.get("size", 90)), INK, bg=YELLOW,
                                                 pad=(34, 16), radius=20), 18, 140)[0]
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        k = ease_io((t - s["from"]) / s.get("cut", 0.9)); y = s.get("y", 300); out = fade_out(s, t)
        d = ImageDraw.Draw(c); x0, x1 = 90, W - 90
        for x in range(x0, x1, 40):
            if x > x0 + (x1 - x0) * k: d.line([(x, y + 70), (x + 22, y + 70)], fill=(255, 255, 255, int(230 * out)), width=6)
        reveal = self.txt.crop((0, 0, max(1, int(self.txt.width * k)), self.txt.height))
        if out < 1: reveal.putalpha(reveal.split()[3].point(lambda v: int(v * out)))
        c.alpha_composite(reveal, (int(W / 2 - self.txt.width / 2), int(y - self.txt.height / 2)))
        sx = x0 + (x1 - x0) * k; open_ = abs(math.sin((t - s["from"]) * 18)) * 18
        for sgn in (1, -1):
            d.line([(sx - 60, y + 70 + sgn * (10 + open_)), (sx + 10, y + 70)], fill=(210, 214, 222, int(255 * out)), width=12)
            d.ellipse([sx - 92, y + 70 + sgn * (10 + open_) - 18, sx - 56, y + 70 + sgn * (10 + open_) + 18],
                      outline=(226, 75, 59, int(255 * out)), width=8)


class TickList:           # B5 card beside you, items tick off at their times
    def __init__(self, s):
        self.s = s; self.f = font(40, "semi")
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        items = s["items"]; w, row = s.get("w", 380), 66; h = 40 + row * len(items)
        im = card(w, h, 24, (255, 255, 255, 240)); d = ImageDraw.Draw(im)
        for i, it in enumerate(items):
            y = 22 + i * row; done = t >= it["at"]
            d.rounded_rectangle([20, y + 8, 64, y + 52], 10, fill=GREEN if done else (230, 232, 238, 255))
            if done:
                kk = ease_out((t - it["at"]) / 0.2)
                d.line([(30, y + 30), (40, y + 40), (40 + 16 * kk, y + 40 - 22 * kk)], fill=WHITE, width=7)
            d.text((80, y + 10), it["text"], font=self.f, fill=INK if done else (130, 134, 142, 255))
        k = ease_out((t - s["from"]) / 0.35); left = s.get("side", "left") == "left"
        x = (w / 2 + 40) if left else (W - w / 2 - 40)
        place(c, shadow(im, 18, 130)[0], x + (-1 if left else 1) * 300 * (1 - k), s.get("y", 1150), alpha=fade_out(s, t))


class PhoneAlert:         # B7 notification slides down
    def __init__(self, s):
        self.s = s; w, h = 960, 190; im = card(w, h, 36, (250, 250, 252, 245)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([28, 34, 128, 134], 24, fill=s.get("color", GREEN))
        d.rounded_rectangle([52, 62, 104, 106], 8, outline=WHITE, width=6); d.line([(52, 64), (78, 88), (104, 64)], fill=WHITE, width=6)
        d.text((152, 36), s.get("app", "Mail").upper() + "  ·  now", font=font(28, "semi"), fill=GREY)
        d.text((152, 76), s["title"], font=font(40), fill=INK)
        d.text((152, 128), s.get("body", ""), font=font(32, "semi"), fill=(90, 94, 102, 255))
        self.img = shadow(im, 22, 150)[0]
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        k = back_out((t - s["from"]) / 0.45, 1.2)
        place(c, self.img, W / 2, s.get("y", 200) - 320 * (1 - k), alpha=fade_out(s, t))


class StepTracker:        # B8 steps row lights up
    def __init__(self, s):
        self.s = s
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        steps = s["steps"]; n = len(steps); y = s.get("y", 200); out = fade_out(s, t)
        gap = (W - 160) / max(1, n - 1); d = ImageDraw.Draw(c); f = font(30, "semi"); fn = font(40)
        active = max([i for i, st in enumerate(steps) if st["at"] <= t] or [-1])
        d.line([(80, y), (W - 80, y)], fill=(255, 255, 255, int(120 * out)), width=8)
        if active >= 0: d.line([(80, y), (80 + gap * active, y)], fill=YELLOW[:3] + (int(255 * out),), width=8)
        for i, st in enumerate(steps):
            x = 80 + gap * i; on = i <= active
            k = back_out((t - st["at"]) / 0.3) if on else 1
            r = 34 * (1.25 - 0.25 * k) if i == active else 30
            d.ellipse([x - r, y - r, x + r, y + r], fill=(YELLOW[:3] if on else (60, 62, 70)) + (int(255 * out),),
                      outline=(255, 255, 255, int(255 * out)), width=4)
            num = str(i + 1); b = d.textbbox((0, 0), num, font=fn)
            d.text((x - (b[2] - b[0]) / 2 - b[0], y - (b[3] - b[1]) / 2 - b[1]), num, font=fn, fill=INK if on else WHITE)
            lab = st["text"].upper(); lb = d.textbbox((0, 0), lab, font=f)
            d.text((x - (lb[2] - lb[0]) / 2, y + 48), lab, font=f, fill=(255, 255, 255, int((255 if on else 150) * out)),
                   stroke_width=4, stroke_fill=(0, 0, 0, int(200 * out)))


# ======================= SHOWPIECE EFFECTS (frame level) =======================
def fx_spotlight(arr, t, s, ctx):
    """X3 room goes dark, soft light on the speaker."""
    if not (s["from"] <= t <= s["to"] + 0.4): return arr
    k = min(ease_out((t - s["from"]) / 0.5), 1 - ease_io((t - s["to"]) / 0.4) if t > s["to"] else 1)
    key = ("spot", s.get("x", 0.5), s.get("y", 0.4))
    if key not in ctx.cache:
        yy, xx = np.mgrid[0:H_, 0:W]
        r = np.sqrt(((xx - W * s.get("x", 0.5)) / (W * 0.42)) ** 2 + ((yy - H_ * s.get("y", 0.4)) / (H_ * 0.32)) ** 2)
        ctx.cache[key] = np.clip((r - 0.7) / 0.6, 0, 1).astype(np.float32)[..., None]
    m = ctx.cache[key]
    return (arr * (1 - 0.78 * k * m)).astype(np.uint8)


def fx_glitch(arr, t, s, ctx):
    """X4 one short glitch burst."""
    if not (s["at"] <= t <= s["at"] + s.get("dur", 0.4)): return arr
    rng = np.random.default_rng(int(t * 1000)); out = arr.copy()
    sh = int(rng.integers(12, 30))
    out[..., 0] = np.roll(arr[..., 0], sh, axis=1); out[..., 2] = np.roll(arr[..., 2], -sh, axis=1)
    for _ in range(6):
        y0 = int(rng.integers(0, H_ - 80)); hh = int(rng.integers(20, 90)); dx = int(rng.integers(-80, 80))
        out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], dx, axis=1)
    return out


def fx_grid(arr, t, s, ctx):
    """X5 2x2 grid of clips snaps into one full frame (the last clip, or the speaker if 'speaker_last')."""
    if not (s["from"] <= t <= s["to"]): return arr
    clips = s["clips"][:4]; k = ease_io((t - s.get("snap_at", s["from"] + 0.8)) / 0.45)
    tiles = [ctx.clip_frame(c, t - s["from"], W // 2, H_ // 2) for c in clips]
    if s.get("speaker_last"): tiles[-1] = Image.fromarray(arr).resize((W // 2, H_ // 2))
    out = Image.new("RGB", (W, H_), (10, 10, 12))
    for i, tl in enumerate(tiles):
        x, y = (i % 2) * W // 2, (i // 2) * H_ // 2
        if i == 3 and k > 0:
            z = 1 + k; big = (Image.fromarray(arr) if s.get("speaker_last") else ctx.clip_frame(clips[3], t - s["from"], W, H_))
            bw, bh = int(W / 2 * z), int(H_ / 2 * z)
            out.paste(big.resize((bw, bh)), (int(x - (x) * k), int(y - (y) * k)))
        else:
            out.paste(tl.resize((W // 2 - 8, H_ // 2 - 8)), (x + 4, y + 4))
    return np.asarray(out)


# ======================= ENDINGS =======================
class CommentKeyword:     # E2 comment KEYWORD card types in and holds to the end
    def __init__(self, s):
        self.s = s
    def draw(self, c, t):
        s = self.s
        if t < s["from"]: return
        kw = s["keyword"].upper(); n = int(clamp((t - s["from"] - 0.3) / 0.6) * len(kw))
        f1, f2 = font(44, "semi"), font(96)
        d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1))); w = int(max(d0.textlength("COMMENT", font=f1), d0.textlength(kw, font=f2)) + 120)
        im = card(w, 230, 30); d = ImageDraw.Draw(im)
        d.text((60, 26), "COMMENT", font=f1, fill=GREY)
        d.rounded_rectangle([40, 92, w - 40, 206], 18, outline=(232, 72, 155, 255), width=6)
        d.text((60, 98), kw[:n] + ("|" if int(t * 3) % 2 and n < len(kw) else ""), font=f2, fill=INK)
        k = back_out((t - s["from"]) / 0.35)
        place(c, shadow(im, 20, 140)[0], W / 2, s.get("y", 1430), scale=0.8 + 0.2 * k, alpha=clamp((t - s["from"]) / 0.1))


class PartTwo:            # E3 "Part 2 tomorrow" card
    def __init__(self, s):
        self.s = s
        im = text_block([s.get("text", "PART 2 TOMORROW")], font(78), WHITE, bg=(17, 17, 17, 240), pad=(46, 26), radius=26)
        h = font(36, "semi"); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        full = Image.new("RGBA", (im.width, im.height + 70), (0, 0, 0, 0)); full.alpha_composite(im, (0, 0))
        ImageDraw.Draw(full).text(((im.width - d0.textlength(s.get("handle", ""), font=h)) / 2, im.height + 16), s.get("handle", ""),
                                  font=h, fill=YELLOW, stroke_width=4, stroke_fill=(0, 0, 0, 220))
        self.img = shadow(full, 20, 140)[0]
    def draw(self, c, t):
        s = self.s
        if t < s["from"]: return
        k = ease_out((t - s["from"]) / 0.4)
        place(c, self.img, W / 2, s.get("y", 1430) + 120 * (1 - k), alpha=k)


class ShopButton:         # E4 button springs in, cursor taps, ripple, shine, pulse
    def __init__(self, s):
        self.s = s; f = font(64); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        txt = s.get("text", "Shop Now"); tw = d0.textlength(txt, font=f); self.w, self.h = int(tw + 140), 140
        self.btn = rounded((self.w, self.h), 70, s.get("color", BLUE)); d = ImageDraw.Draw(self.btn)
        b = d.textbbox((0, 0), txt, font=f); d.text(((self.w - (b[2] - b[0])) / 2 - b[0], (self.h - (b[3] - b[1])) / 2 - b[1]), txt, font=f, fill=WHITE)
    def draw(self, c, t):
        s = self.s
        if t < s["from"]: return
        a = s["from"]; tap = s.get("tap_at", a + 0.9); y = s.get("y", 1420); k = back_out((t - a) / 0.4)
        press = 0.92 if tap <= t < tap + 0.12 else 1.0
        btn = self.btn.copy()
        sh = ((t - tap - 0.2) % 1.6) / 0.5                          # shine sweep
        if 0 <= sh <= 1 and t > tap:
            g = Image.new("RGBA", btn.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g); x = -80 + (self.w + 160) * sh
            gd.polygon([(x, 0), (x + 50, 0), (x - 30, self.h), (x - 80, self.h)], fill=(255, 255, 255, 110))
            btn.alpha_composite(Image.composite(g, Image.new("RGBA", btn.size, (0, 0, 0, 0)), rmask(btn.size, 70)))
        d = ImageDraw.Draw(c)
        if t >= tap:
            r = ease_out((t - tap) / 0.6)
            d.ellipse([W / 2 - 80 - 260 * r, y - 50 - 120 * r, W / 2 + 80 + 260 * r, y + 50 + 120 * r],
                      outline=(255, 255, 255, int(200 * (1 - r))), width=8)
        place(c, shadow(btn, 20, 140)[0], W / 2, y, scale=max(0.01, k * press), alpha=clamp((t - a) / 0.1))
        cx = W / 2 + 120 + 260 * (1 - ease_out((t - a - 0.3) / 0.6)); cy = y + 40 + 260 * (1 - ease_out((t - a - 0.3) / 0.6))
        if t > a + 0.3:
            pts = [(0, 0), (0, 64), (16, 50), (28, 78), (40, 72), (28, 46), (50, 46)]
            d.polygon([(cx + x, cy + yy) for x, yy in pts], fill=WHITE, outline=INK, width=4)


# ======================= registry =======================
ELEMENTS = {
    "skit_label": SkitLabel, "rising_headline": RisingHeadline, "myth": MythCrossed,
    "side_column": SideColumn, "float_card": FloatCard,
    "message_card": MessageCard, "before_after": BeforeAfter, "number": NumberRoll,
    "number_slam": lambda s: NumberRoll(s, slam=True), "insights": InsightsPointer, "stamp": OfferStamp,
    "jd_fan": JDFan, "resume_split": ResumeSplit, "scissors": ScissorsTailor, "tick_list": TickList,
    "phone_alert": PhoneAlert, "steps": StepTracker,
    "comment_keyword": CommentKeyword, "part_two": PartTwo, "shop_button": ShopButton,
}
EFFECTS = {"split": fx_split, "spotlight": fx_spotlight, "glitch": fx_glitch, "grid": fx_grid}


class Ctx:                # caches clip frames for split/grid effects
    def __init__(self):
        self.cache = {}; self.clips = {}
    def clip_frame(self, path, t, w, h):
        if path not in self.clips:
            import subprocess
            raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-vf", f"fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
                                  "-frames:v", "450", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            n = len(raw) // (w * h * 3)
            if n == 0:   # a still image
                self.clips[path] = [load_image(path, w, h).convert("RGB")]
            else:
                arr = np.frombuffer(raw[:n * w * h * 3], np.uint8).reshape(n, h, w, 3)
                self.clips[path] = [Image.fromarray(a) for a in arr]
        fr = self.clips[path]; im = fr[min(len(fr) - 1, max(0, int(t * FPS)))]
        return im if im.size == (w, h) else im.resize((w, h))


# ======================= ENERGY v3 (from reference analysis, 10 Nov 2026) =======================
class SectionHeader:      # numbered section header at the top that swaps per point ("#1 Verify")
    def __init__(self, s):
        self.s = s; self.f = font(s.get("size", 62))
    def _img(self, it):
        d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        num, txt = it.get("num", ""), it["text"]
        nw = d0.textlength(num + " ", font=self.f) if num else 0; tw = d0.textlength(txt, font=self.f)
        im = Image.new("RGBA", (int(nw + tw + 40), int(self.f.size * 1.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        if num: d.text((20, 6), num, font=self.f, fill=self.s.get("accent", (255, 92, 70, 255)), stroke_width=3, stroke_fill=(0, 0, 0, 120))
        d.text((20 + nw, 6), txt, font=self.f, fill=WHITE, stroke_width=4, stroke_fill=(0, 0, 0, 150))
        return fit(shadow(im, 12, 140)[0])
    def draw(self, c, t):
        for it in self.s["items"]:
            if it["from"] <= t <= it["to"] + 0.2:
                k = ease_out((t - it["from"]) / 0.3); out = 1 - ease_io((t - it["to"]) / 0.2) if t > it["to"] else 1
                place(c, self._img(it), W / 2, self.s.get("y", 150) - 40 * (1 - k), alpha=k * out)
                return


class BuildCard:          # card that builds while you talk: title/icon, then badge, then chips one by one
    def __init__(self, s):
        self.s = s
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        w = s.get("w", 760); chips = [x for x in s.get("chips", []) if x["at"] <= t]
        h = 170 + (64 if chips else 0) * ((len(chips) + 1) // 2)
        im = card(w, h, 26); d = ImageDraw.Draw(im)
        d.rounded_rectangle([26, 26, 106, 106], 20, fill=s.get("color", RED))
        d.text((44, 38), s.get("icon", s["title"][:1]).upper(), font=font(52), fill=WHITE)
        d.text((128, 30), s["title"], font=font(44), fill=INK)
        if s.get("subtitle"): d.text((128, 84), s["subtitle"], font=font(30, "semi"), fill=GREY)
        if s.get("badge") and t >= s["badge"]["at"]:
            kb = back_out((t - s["badge"]["at"]) / 0.3); bw = 150
            bd = rounded((bw, 54), 27, GREEN); ImageDraw.Draw(bd).text((24, 6), s["badge"]["text"], font=font(34), fill=WHITE)
            bd = bd.resize((max(1, int(bw * kb)), max(1, int(54 * kb))))
            im.alpha_composite(bd, (w - 30 - bd.width, 30))
        for i, ch in enumerate(chips):
            x = 26 + (i % 2) * (w // 2 - 13); y = 150 + (i // 2) * 64
            kc = clamp((t - ch["at"]) / 0.18)
            d.rounded_rectangle([x, y, x + w // 2 - 39, y + 50], 25, fill=(236, 240, 247, int(255 * kc)), outline=(210, 214, 222, int(255 * kc)))
            d.text((x + 22, y + 8), "+ " + ch["text"], font=font(30, "semi"), fill=(40, 44, 52, int(255 * kc)))
        k = back_out((t - s["from"]) / 0.35)
        place(c, shadow(im, 22, 140)[0], W / 2, s.get("y", 360) + h / 2 - 100, scale=0.85 + 0.15 * k,
              alpha=clamp((t - s["from"]) / 0.12) * fade_out(s, t))


class KeywordSlam:        # big two-tone keyword in the middle (small lead-in line + big word)
    def __init__(self, s):
        self.s = s
        small = s.get("small", ""); big = s["big"]
        fb = font(s.get("size", 140)); fs = font(44, "semi")
        d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bw = d0.textlength(big, font=fb); sw = d0.textlength(small, font=fs) if small else 0
        w = int(max(bw, sw) + 60); h = int(fb.size * 1.25 + (60 if small else 0))
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        if small: d.text(((w - sw) / 2, 0), small, font=fs, fill=WHITE, stroke_width=4, stroke_fill=(0, 0, 0, 180))
        col = YELLOW if s.get("color", "yellow") == "yellow" else WHITE
        d.text(((w - bw) / 2, 50 if small else 0), big, font=fb, fill=col, stroke_width=8, stroke_fill=(0, 0, 0, 200))
        self.img = fit(shadow(im, 16, 170)[0], 1040)
    def draw(self, c, t):
        s = self.s; a = s["at"]; b = a + s.get("dur", 1.2)
        if not (a <= t <= b + 0.15): return
        k = back_out((t - a) / 0.25, 2.2); out = 1 - ease_io((t - b) / 0.15) if t > b else 1
        place(c, self.img, W / 2, s.get("y", 1330), scale=0.6 + 0.4 * k, alpha=clamp((t - a) / 0.06) * out)


class TypingBox:          # chat / prompt box that types a line, then the send button lights
    def __init__(self, s):
        self.s = s; self.f = font(s.get("size", 44), "semi")
    def draw(self, c, t):
        s = self.s
        if not window(s, t): return
        txt = s["text"]; n = int(clamp((t - s["from"] - 0.25) / s.get("type_dur", 1.4)) * len(txt))
        w = s.get("w", 900); im = card(w, 110, 55, (250, 250, 252, 245)); d = ImageDraw.Draw(im)
        shown = txt[:n] + ("|" if n < len(txt) and int(t * 3) % 2 else "")
        while d.textlength(shown, font=self.f) > w - 170: shown = "…" + shown[2:]
        d.text((40, 28), shown, font=self.f, fill=INK if n else GREY)
        sent = n >= len(txt)
        d.ellipse([w - 96, 19, w - 24, 91], fill=(GREEN if sent else (200, 204, 212, 255)))
        d.polygon([(w - 70, 40), (w - 70, 70), (w - 44, 55)], fill=WHITE)
        out = shadow(im, 18, 130)[0]
        if s.get("label"):
            lab = text_block([s["label"]], font(30, "semi"), WHITE, bg=(17, 17, 17, 220), pad=(18, 8), radius=12)
            full = Image.new("RGBA", (out.width, out.height + lab.height + 6), (0, 0, 0, 0))
            full.alpha_composite(lab, (60, 0)); full.alpha_composite(out, (0, lab.height + 6)); out = full
        k = ease_out((t - s["from"]) / 0.3)
        place(c, out, W / 2, s.get("y", 280) - 60 * (1 - k), alpha=k * fade_out(s, t))


PATTERNS = {}
def _pattern(kind):
    if kind in PATTERNS: return PATTERNS[kind]
    im = Image.new("RGBA", (W, H_), (245, 239, 226, 255)); d = ImageDraw.Draw(im)
    if kind == "stripes":
        for x in range(0, W, 120): d.rectangle([x, 0, x + 60, H_], fill=(214, 64, 52, 255))
    elif kind == "paper":
        rng = np.random.default_rng(3)
        for _ in range(26):
            x, y = rng.integers(-100, W), rng.integers(-100, H_); cw, ch = rng.integers(220, 520), rng.integers(140, 360)
            col = [(232, 220, 196), (210, 196, 170), (243, 233, 214), (226, 206, 180)][rng.integers(0, 4)]
            d.polygon([(x, y), (x + cw, y + rng.integers(-30, 30)), (x + cw + rng.integers(-30, 30), y + ch), (x, y + ch)], fill=col + (255,))
    elif kind == "brand":
        for i in range(H_):
            k = i / H_; d.line([(0, i), (W, i)], fill=(int(255 * (1 - k) + 255 * k), int(200 * (1 - k) + 140 * k), int(61 * (1 - k) + 40 * k), 255))
        for x in range(-H_, W, 90): d.line([(x, 0), (x + H_, H_)], fill=(255, 255, 255, 40), width=26)
    elif kind == "ink":
        im = Image.new("RGBA", (W, H_), (22, 54, 44, 255))
    PATTERNS[kind] = im
    return im


class PopBackground:      # background swap behind you (needs mattes) + white outline + doodles
    behind = True; outline = True
    def __init__(self, s):
        self.s = s
    def active(self, t):
        return self.s["from"] <= t <= self.s["to"]
    def draw(self, c, t):
        if not self.active(t): return
        k = clamp((t - self.s["from"]) / 0.12)
        bg = _pattern(self.s.get("pattern", "stripes"))
        if k < 1:
            bg = bg.copy(); bg.putalpha(int(255 * k))
        c.alpha_composite(bg)
    def outline_draw(self, c, mt, t):
        if not self.active(t) or not self.s.get("outline", True): return
        big = mt.filter(ImageFilter.MaxFilter(17)); ring = Image.fromarray(np.clip(np.asarray(big, np.int16) - np.asarray(mt, np.int16), 0, 255).astype(np.uint8))
        white = Image.new("RGBA", (W, H_), (255, 255, 255, 255)); c.paste(white, (0, 0), ring)
        if self.s.get("doodles", True):
            d = ImageDraw.Draw(c); ph = (t - self.s["from"]) * 4
            for (x, y, r) in ((180, 380, 40), (900, 330, 34), (860, 900, 28)):
                rr = r * (1 + 0.1 * math.sin(ph + x))
                d.line([(x - rr, y), (x + rr, y)], fill=WHITE, width=8); d.line([(x, y - rr), (x, y + rr)], fill=WHITE, width=8)
                d.line([(x - rr * 0.6, y - rr * 0.6), (x + rr * 0.6, y + rr * 0.6)], fill=WHITE, width=6)


class SerifTitle:         # editorial serif title behind you ("I DIDN'T EDIT", magazine cover)
    behind = True
    def __init__(self, s):
        self.s = s; f = serif(s.get("size", 200))
        self.img = fit(shadow(text_block(s["text"].split("\n"), f, YELLOW if s.get("color") == "yellow" else (250, 246, 236, 255),
                                         pad=(10, 0), gap=0), 20, 120)[0], 1060)
    def draw(self, c, t):
        s = self.s
        if not window(s, t, 0.25): return
        k = ease_out((t - s["from"]) / 0.4) if s["from"] > 0.01 else 1
        if s.get("dim", 0.0):
            c.alpha_composite(Image.new("RGBA", (W, H_), (0, 0, 0, int(255 * s["dim"] * k * fade_out(s, t)))))
        place(c, self.img, W / 2, s.get("y", 380) + 60 * (1 - k), scale=1.06 - 0.06 * k, alpha=k * fade_out(s, t))


class MinimalCaptions:    # C5 small clean captions, current word underlined (reference style)
    def __init__(self, groups, y=1480, size=52, max_words=5, hide=()):
        self.y = y; self.f = font(size, "semi"); self.hide = hide; self.pages = H["Captions"](groups, y, size, max_words).pages
    def draw(self, c, t):
        if any(a <= t <= b for a, b in self.hide): return
        for ws, ts, end in self.pages:
            if ts[0] <= t < end + 0.04:
                d = ImageDraw.Draw(c); sp = d.textlength(" ", font=self.f)
                widths = [d.textlength(w, font=self.f) for w in ws]; x = (W - sum(widths) - sp * (len(ws) - 1)) / 2
                active = max([i for i, s in enumerate(ts) if s <= t] or [-1])
                for i, w in enumerate(ws):
                    d.text((x, self.y), w, font=self.f, fill=WHITE, stroke_width=3, stroke_fill=(0, 0, 0, 170))
                    if i == active:
                        d.rounded_rectangle([x, self.y + self.f.size * 1.18, x + widths[i], self.y + self.f.size * 1.18 + 7], 3, fill=YELLOW)
                    x += widths[i] + sp
                return


ELEMENTS.update({"header": SectionHeader, "build_card": BuildCard, "keyword": KeywordSlam, "typing_box": TypingBox,
                 "pop_bg": PopBackground, "serif_title": SerifTitle})
