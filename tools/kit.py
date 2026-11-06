"""Drawing kit for icons in Zed's own file-icon style.

Zed's file icons are 16x16, with 1.2px round-capped outlines, small solid accents, and an
optional 50% second tone. Everything here emits exactly that vocabulary, so every icon in
the theme is built from the same few moves and looks like it belongs to Zed.

Colour: Zed tints its *built-in* icons with the UI theme's muted text colour, but draws an
extension theme's icons as plain images in the colours the SVG contains. So every helper
paints with the INK token, and `svg(*elements, color=...)` bakes in the colour Zed would
have tinted with. Mask content is the exception: a mask must stay black/white (see `mask`).

Each helper returns one SVG element as a string; `svg(*elements)` wraps them.
"""

import math

SW = 1.2  # Zed's outline weight
INK = "currentColor"  # placeholder paint, replaced by the variant colour in svg()


def n(v):
    """Format a number: at most 2 decimals, no trailing zeros."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _pts(pts):
    return " ".join(f"{n(x)} {n(y)}" for x, y in pts)


def d_of(*pts, close=False):
    """Path data for a polyline through (x, y) points."""
    p = [f"{'M' if i == 0 else 'L'}{n(x)} {n(y)}" for i, (x, y) in enumerate(pts)]
    return "".join(p) + ("Z" if close else "")


def _op(opacity):
    return f' opacity="{n(opacity)}"' if opacity is not None else ""


def stroke(d, w=SW, opacity=None):
    """Outline from raw path data."""
    return (f'<path d="{d}" stroke="{INK}" stroke-width="{n(w)}" '
            f'stroke-linecap="round" stroke-linejoin="round"{_op(opacity)}/>')


def fill(d, opacity=None, evenodd=False):
    """Solid shape from raw path data."""
    eo = ' fill-rule="evenodd" clip-rule="evenodd"' if evenodd else ""
    return f'<path d="{d}" fill="{INK}"{eo}{_op(opacity)}/>'


def _snap(v):
    """The pixel centre (k + 0.5) nearest v. A 1.2px stroke centred there fills one pixel and spills 10%
    into its neighbours; centred on a pixel edge it is two 60% pixels, which is what looks blurry.
    A value that already sits on an edge moves a half pixel towards the middle of the icon."""
    if v != int(v):
        return math.floor(v) + 0.5
    return v + 0.5 if v < 8 else v - 0.5 if v > 8 else v


def _aligned(pts, close=False):
    """Move the ends of every horizontal or vertical segment onto pixel centres (across the segment only)."""
    pts = [list(p) for p in pts]
    for i, a in enumerate(pts):
        j = i + 1 if i + 1 < len(pts) else (0 if close else None)
        if j is None:
            break
        b = pts[j]
        if abs(a[1] - b[1]) < 1e-6:
            a[1] = b[1] = _snap(a[1])
        elif abs(a[0] - b[0]) < 1e-6:
            a[0] = b[0] = _snap(a[0])
    return [tuple(p) for p in pts]


def line(*pts, w=SW, opacity=None):
    return stroke(d_of(*_aligned(pts)), w, opacity)


def poly(*pts, w=SW, opacity=None):
    return stroke(d_of(*_aligned(pts, True), close=True), w, opacity)


def fpoly(*pts, opacity=None):
    return fill(d_of(*pts, close=True), opacity)


def circle(cx, cy, r, w=SW, opacity=None):
    return (f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" stroke="{INK}" '
            f'stroke-width="{n(w)}"{_op(opacity)}/>')


def dot(cx, cy, r=0.8, opacity=None):
    return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{INK}"{_op(opacity)}/>'


def rrect(x, y, w, h, r=1.5, sw=SW, opacity=None):
    x2, y2 = _snap(x + w), _snap(y + h)
    x, y = _snap(x), _snap(y)
    w, h = x2 - x, y2 - y
    return (f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(r)}" '
            f'stroke="{INK}" stroke-width="{n(sw)}"{_op(opacity)}/>')


def frect(x, y, w, h, r=1.5, opacity=None):
    return (f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(r)}" '
            f'fill="{INK}"{_op(opacity)}/>')


def arc(cx, cy, r, a0, a1, w=SW, opacity=None):
    """Circular arc from angle a0 to a1 in degrees (0 = right, 90 = down, clockwise)."""
    import math
    x0, y0 = cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))
    x1, y1 = cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return stroke(f"M{n(x0)} {n(y0)}A{n(r)} {n(r)} 0 {large} 1 {n(x1)} {n(y1)}", w, opacity)


def regular(cx, cy, r, sides, rot=-90):
    """Vertices of a regular polygon; rot=-90 puts the first vertex at the top."""
    import math
    return [(cx + r * math.cos(math.radians(rot + 360 * i / sides)),
             cy + r * math.sin(math.radians(rot + 360 * i / sides))) for i in range(sides)]


def svg(*elements, color="black"):
    body = "\n".join(elements).replace(INK, color)
    return ('<svg width="16" height="16" viewBox="0 0 16 16" fill="none" '
            f'xmlns="http://www.w3.org/2000/svg">\n{body}\n</svg>\n')


def mask(*knockout, id="m"):
    """Luminance mask that hides `knockout` (drawn with the usual helpers) from whatever uses it.

    Mask colours carry meaning (white shows, black hides), so they are pinned to literal
    white/black here and are never touched by the colour baking in svg().
    """
    body = "".join(knockout).replace(INK, "black")
    return (f'<mask id="{id}" maskUnits="userSpaceOnUse" x="0" y="0" width="16" height="16">'
            f'<rect width="16" height="16" fill="white"/>{body}</mask>')


# ---------------------------------------------------------------------------
# Letters. A smooth monoline typeface for badges and framework marks: caps, digits and '#'.
# Every glyph is a centre-line path with real curves in a unit box (x: 0 = left stem, 1 = right
# stem; y: 0 = cap line, 1 = baseline), so it is resolution independent and stays smooth on a
# 2x screen. text() stretches each glyph to its width, strokes it with round joins, and sets the
# cap line and baseline on whole pixels so the horizontals stay crisp at 16px.
# ---------------------------------------------------------------------------
_B = 0.5523  # Bézier circle constant, used to keep the hand-written curves round
_G = {
    "A": "M0 1L0.5 0L1 1M0.18 0.68H0.82",
    "B": "M0 0V1M0 0H0.55C0.85 0 0.95 0.12 0.95 0.25C0.95 0.38 0.85 0.5 0.55 0.5H0"
         "M0.55 0.5C0.9 0.5 1 0.62 1 0.75C1 0.9 0.9 1 0.55 1H0",
    "C": "M1 0.2C0.85 0.06 0.7 0 0.5 0C0.2 0 0 0.22 0 0.5C0 0.78 0.2 1 0.5 1C0.7 1 0.85 0.94 1 0.8",
    "D": "M0 0V1H0.4C0.8 1 1 0.78 1 0.5C1 0.22 0.8 0 0.4 0H0Z",
    "E": "M1 0H0V1H1M0 0.5H0.8",
    "F": "M1 0H0V1M0 0.5H0.8",
    "G": "M1 0.2C0.85 0.06 0.7 0 0.5 0C0.2 0 0 0.22 0 0.5C0 0.78 0.2 1 0.5 1C0.8 1 1 0.8 1 0.55V0.5H0.55",
    "H": "M0 0V1M1 0V1M0 0.5H1",
    "I": "M0 0H1M0.5 0V1M0 1H1",
    "J": "M1 0V0.65C1 0.88 0.8 1 0.5 1C0.25 1 0.05 0.88 0 0.7",
    "K": "M0 0V1M1 0L0.05 0.55M0.4 0.35L1 1",
    "L": "M0 0V1H1",
    "M": "M0 1V0L0.5 0.55L1 0V1",
    "N": "M0 1V0L1 1V0",
    "O": "M0.5 0C0.22 0 0 0.22 0 0.5C0 0.78 0.22 1 0.5 1C0.78 1 1 0.78 1 0.5C1 0.22 0.78 0 0.5 0Z",
    "P": "M0 1V0H0.55C0.85 0 1 0.14 1 0.3C1 0.46 0.85 0.6 0.55 0.6H0",
    "Q": "M0.5 0C0.22 0 0 0.22 0 0.5C0 0.78 0.22 1 0.5 1C0.78 1 1 0.78 1 0.5C1 0.22 0.78 0 0.5 0Z"
         "M0.62 0.72L0.98 1.05",
    "R": "M0 1V0H0.55C0.85 0 1 0.14 1 0.3C1 0.46 0.85 0.6 0.55 0.6H0M0.5 0.6L1 1",
    "S": "M0.95 0.16C0.8 0.05 0.65 0 0.48 0C0.2 0 0.05 0.14 0.05 0.28C0.05 0.42 0.2 0.48 0.5 0.52"
         "C0.8 0.56 0.95 0.62 0.95 0.76C0.95 0.9 0.8 1 0.5 1C0.3 1 0.14 0.94 0.03 0.84",
    "T": "M0 0H1M0.5 0V1",
    "U": "M0 0V0.62C0 0.85 0.2 1 0.5 1C0.8 1 1 0.85 1 0.62V0",
    "V": "M0 0L0.5 1L1 0",
    "W": "M0 0L0.25 1L0.5 0.3L0.75 1L1 0",
    "X": "M0 0L1 1M1 0L0 1",
    "Y": "M0 0L0.5 0.5L1 0M0.5 0.5V1",
    "Z": "M0 0H1L0 1H1",
    "0": "M0.5 0C0.22 0 0 0.22 0 0.5C0 0.78 0.22 1 0.5 1C0.78 1 1 0.78 1 0.5C1 0.22 0.78 0 0.5 0Z"
         "M0.8 0.18L0.2 0.82",
    "1": "M0 0.22L0.55 0V1M0 1H1",
    "2": "M0.05 0.2C0.15 0.07 0.3 0 0.5 0C0.8 0 0.97 0.14 0.97 0.3C0.97 0.5 0.75 0.65 0.5 0.8"
         "C0.3 0.9 0.12 0.95 0 1H1",
    "3": "M0 0.12C0.15 0.04 0.3 0 0.5 0C0.8 0 0.95 0.12 0.95 0.26C0.95 0.4 0.8 0.5 0.5 0.5"
         "C0.85 0.5 1 0.6 1 0.76C1 0.9 0.8 1 0.5 1C0.3 1 0.12 0.96 0 0.86",
    "4": "M0.75 1V0L0 0.7H1",
    "5": "M0.95 0H0.1L0 0.45C0.15 0.4 0.3 0.38 0.5 0.38C0.8 0.38 1 0.52 1 0.7C1 0.88 0.8 1 0.5 1"
         "C0.3 1 0.12 0.94 0 0.85",
    "6": "M0.9 0.1C0.78 0.03 0.65 0 0.5 0C0.2 0 0 0.3 0 0.62C0 0.85 0.2 1 0.5 1C0.8 1 1 0.85 1 0.68"
         "C1 0.5 0.8 0.4 0.5 0.4C0.25 0.4 0.08 0.5 0 0.62",
    "7": "M0 0H1L0.35 1",
    "8": "M0.5 0.5C0.2 0.5 0.05 0.38 0.05 0.25C0.05 0.1 0.22 0 0.5 0C0.78 0 0.95 0.1 0.95 0.25"
         "C0.95 0.38 0.8 0.5 0.5 0.5C0.15 0.5 0 0.62 0 0.76C0 0.9 0.2 1 0.5 1C0.8 1 1 0.9 1 0.76"
         "C1 0.62 0.85 0.5 0.5 0.5Z",
    "9": "M0.1 0.9C0.22 0.97 0.35 1 0.5 1C0.8 1 1 0.7 1 0.38C1 0.15 0.8 0 0.5 0C0.2 0 0 0.15 0 0.32"
         "C0 0.5 0.2 0.6 0.5 0.6C0.75 0.6 0.92 0.5 1 0.38",
    "#": "M0.2 0V1M0.8 0V1M0 0.22H1M0 0.78H1",
}
# Width of each letter's outline at a 6px cap height; everything else is 4. Wide letters are
# what limit a two-letter mark: a badge has about 10px between its rims.
_WIDTH = {"I": 3.0, "1": 3.4, "M": 4.8, "W": 5.0, "A": 4.4, "V": 4.4, "#": 5.2, "N": 4.2, "K": 4.2,
          "X": 4.2, "Y": 4.2, "Q": 4.2}
_STROKE = {"#": 0.88}  # x the run's stroke: a # needs open cells of about 1.6px, so it is drawn lighter and wider
_ARGS = {"M": "xy", "L": "xy", "H": "x", "V": "y", "C": "xyxyxy", "Q": "xyxy", "Z": ""}


def _place(d, sx, sy, dx, dy):
    """Scale and move path data (absolute M L H V C Q Z only)."""
    import re
    out, cmd, args = [], None, []
    for tok in re.findall(r"[A-Za-z]|-?\d*\.?\d+", d):
        if tok.isalpha():
            cmd, args = tok, []
            out.append(tok)
            continue
        args.append(float(tok))
        spec = _ARGS[cmd]
        if len(args) == len(spec):
            out.append(" ".join(n(v * sx + dx if a == "x" else v * sy + dy) for v, a in zip(args, spec)))
            args = []
    return "".join(o if o.isalpha() else (" " + o if out[i - 1][-1].isdigit() else o)
                   for i, o in enumerate(out)).strip()


def text(s, cx=8, cy=8, h=6.0, w=1.4, gap=0.9, max_w=10.0):
    """Letters in the monoline typeface, `h` px tall (outline to outline), stroked `w` px.

    Centred on (cx, cy). The left edge snaps to a whole pixel and, with h = 6 and cy = 8, the
    cap line and baseline land on whole pixels too. A run wider than `max_w` is squeezed
    horizontally only: the stroke keeps its weight, so the counters get tighter, not the lines
    thinner. Returns one stroked path per letter (as a single string).
    """
    s = s.upper()
    scale = h / 6
    outer = [_WIDTH.get(c, 4.0) * scale for c in s]
    span = sum(outer) + gap * (len(s) - 1)
    if span > max_w:
        k = (max_w - gap * (len(s) - 1)) / sum(outer)
        outer = [o * k for o in outer]
        span = max_w
    x = round(cx - span / 2)
    top = cy - h / 2
    out = []
    for c, ow in zip(s, outer):
        sw = w * _STROKE.get(c, 1.0)
        out.append(stroke(_place(_G[c], ow - sw, h - sw, x + sw / 2, top + sw / 2), sw))
        x += ow + gap
    return "".join(out)


BADGE = dict(h=6.0, w=1.3, gap=0.8, max_w=10.0, h1=7.0, w1=1.6)  # tuned against a detail-loss probe


def badge(s):
    """Letter badge: Zed's TS-badge square (12 x 12, radius 2) with the letters knocked out."""
    b = BADGE
    t = text(s, h=b["h1"], w=b["w1"]) if len(s) == 1 else text(s, h=b["h"], w=b["w"], gap=b["gap"], max_w=b["max_w"])
    return [mask(t), f'<rect x="2" y="2" width="12" height="12" rx="2" fill="{INK}" mask="url(#m)"/>']


def knock(shapes, *cut, id="m"):
    """Solid `shapes` with `cut` knocked out of them, the way Zed draws its solid logos (C, terminal)."""
    return [mask(*cut, id=id), f'<g mask="url(#{id})">', *shapes, "</g>"]
