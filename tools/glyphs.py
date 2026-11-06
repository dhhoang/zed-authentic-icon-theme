"""Glyphs drawn for this theme, in Zed's file-icon style (see kit.py).

Each function returns the list of SVG elements for one 16x16 icon. The function name is
the glyph name used as `g:<name>` in tools/design/*.txt. Glyphs are deliberately generic
(a flask means "test", a cloud means "hosting/deploy") so one drawing can serve a whole
family of tools, the same way Zed uses one book icon for all documents.

House rules, taken from Zed's own icons:
  * content sits in the 2..14 box; outlines are 1.2px with round caps and joins;
  * curves are smooth Béziers or arcs, never polygons pretending to be curves;
  * category glyphs are outlines with at most one solid or 50% accent (Zed's package fills one
    face, its gear fills the hub, its book fills the spine band);
  * brand-like marks are solid silhouettes with details knocked out (Zed's C, terminal, info).
"""
import math

from kit import *
from kit import _WIDTH

G = {}


def glyph(f):
    G[f.__name__] = f
    return f


def _on(cx, cy, r, deg):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def _head(cx, cy, r, deg, sign=1, size=1.8):
    """Arrowhead sitting on a circle at `deg`, pointing clockwise (sign=1) or anticlockwise (-1)."""
    a = math.radians(deg)
    tip = _on(cx, cy, r, deg)
    tx, ty = -math.sin(a) * sign, math.cos(a) * sign  # direction of travel
    wings = []
    for rot in (math.radians(145), math.radians(-145)):
        wx, wy = tx * math.cos(rot) - ty * math.sin(rot), tx * math.sin(rot) + ty * math.cos(rot)
        wings.append((tip[0] + wx * size, tip[1] + wy * size))
    return line(wings[0], tip, wings[1])


# --- function glyphs: outline + one accent ------------------------------------------

@glyph
def flask():  # tests: the liquid is the accent
    wall = "M6.3 2.6V6.4L3.3 11.6C2.85 12.45 3.45 13.4 4.4 13.4H11.6C12.55 13.4 13.15 12.45 12.7 11.6L9.7 6.4V2.6"
    return [fill("M4.63 9.3H11.37L12.7 11.6C13.15 12.45 12.55 13.4 11.6 13.4H4.4C3.45 13.4 2.85 12.45 3.3 11.6Z"),
            stroke(wall), line((5.3, 2.6), (10.7, 2.6))]


@glyph
def check():  # linters / quality gates: a bold tick, no frame
    return [line((2.8, 8.6), (6.4, 12.2), (13.2, 4.2), w=1.9)]


_SHIELD_D = "M8 1.8C9.6 2.9 11.3 3.4 13 3.5V7.6C13 10.6 11 12.9 8 14.2C5 12.9 3 10.6 3 7.6V3.5C4.7 3.4 6.4 2.9 8 1.8Z"


@glyph
def shield():  # security scanners: outline shield, left half solid
    return [fill("M8 3V13.2C5.3 12 3 10.2 3 7.6V3.5C4.7 3.4 6.4 2.9 8 1.8Z"), stroke(_SHIELD_D)]


@glyph
def cloud():  # hosting / deploy
    return [stroke("M4.6 12.5C3.15 12.5 2 11.4 2 10C2 8.7 2.95 7.65 4.2 7.5C4.6 5.5 6.35 4 8.5 4"
                   "C10.85 4 12.75 5.75 12.95 8C13.9 8.3 14.5 9.2 14.5 10.2C14.5 11.5 13.45 12.5 12.15 12.5Z")]


@glyph
def pipeline():  # CI / CD: a loop with two arrowheads
    return [arc(8, 8, 5, 200, 320), _head(8, 8, 5, 320), arc(8, 8, 5, 20, 140), _head(8, 8, 5, 140)]


_HEX = regular(8, 8, 6, 6)  # pointy-top hexagon: 0 top, then clockwise


@glyph
def box():  # packages: isometric box, the lid face in the second tone
    v = _HEX
    return [fpoly(v[5], v[0], v[1], (8, 8), opacity=0.5), poly(*v), line(v[5], (8, 8), v[1]), line((8, 8), v[3])]


@glyph
def archive():  # zip / jar / vsix: a zipper down a rounded sleeve
    return [rrect(3.5, 2, 9, 12, 2), line((8, 3.4), (8, 7.4), w=1.4), frect(6.5, 8, 3, 4, 1.1)]


@glyph
def bundle():  # bundlers: stacked layers, the top one solid
    top = ((8, 2.3), (13.6, 5.3), (8, 8.3), (2.4, 5.3))
    return [fpoly(*top), poly(*top), line((2.4, 8.1), (8, 11.1), (13.6, 8.1)), line((2.4, 10.9), (8, 13.9), (13.6, 10.9))]


@glyph
def docs():  # documentation sites: a page of text
    return [rrect(3, 2, 10, 12, 2), line((5.5, 5.5), (10.5, 5.5)), line((5.5, 8), (10.5, 8)), line((5.5, 10.5), (8.5, 10.5))]


@glyph
def api():  # APIs / HTTP: request and response
    return [line((3, 5.5), (12.5, 5.5)), line((10, 3), (12.5, 5.5), (10, 8)),
            line((13, 10.5), (3.5, 10.5)), line((6, 8), (3.5, 10.5), (6, 13))]


@glyph
def commit():  # git hooks / commit tooling
    return [circle(8, 8, 2.6), line((2.4, 8), (5.4, 8)), line((10.6, 8), (13.6, 8))]


@glyph
def schema():  # IDL / schema languages: a tree, root solid
    return [frect(6, 2.2, 4, 3.4, 1), rrect(2.5, 10.4, 4, 3.4, 1), rrect(9.5, 10.4, 4, 3.4, 1),
            stroke("M8 5.6V8M4.5 10.4V9C4.5 8.45 4.95 8 5.5 8H10.5C11.05 8 11.5 8.45 11.5 9V10.4")]


@glyph
def graph():  # graphs / diagrams: three nodes, one solid
    def edge(a, ra, b, rb):
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy)
        return line((a[0] + dx / d * ra, a[1] + dy / d * ra), (b[0] - dx / d * rb, b[1] - dy / d * rb))
    top, left, right = (8, 4.2), (4, 11.8), (12, 11.8)
    return [dot(*top, 2.1), circle(*left, 1.8), circle(*right, 1.8),
            edge(top, 3, left, 2.8), edge(top, 3, right, 2.8), edge(left, 2.8, right, 2.8)]


@glyph
def cube3d():  # 3D models: wireframe cube, front face in the second tone
    front = ((3, 6), (10, 6), (10, 13), (3, 13))
    return [fpoly(*front, opacity=0.5), poly(*front), line((3, 6), (6, 3), (13, 3), (13, 10), (10, 13)), line((10, 6), (13, 3))]


@glyph
def key():  # keys / secrets
    return [circle(5, 11, 2.7), line((6.95, 9.05), (13, 3)), line((11, 5), (12.9, 6.9)), line((9.2, 6.8), (10.6, 8.2))]


@glyph
def cert():  # certificates: a page with two lines and a solid seal, all clear of the border
    return [rrect(2.5, 2.5, 11, 10.5, 1.8), line((5, 5.4), (11, 5.4)), line((5, 7.7), (8.2, 7.7)), dot(10.3, 10, 1.4)]


_STAR = "M7 2.5C7.4 6 8.6 7.3 12 7.8C8.6 8.3 7.4 9.6 7 13.1C6.6 9.6 5.4 8.3 2 7.8C5.4 7.3 6.6 6 7 2.5Z"
_STAR_S = ("M12.4 1.8C12.55 3.1 13 3.55 14.3 3.7C13 3.85 12.55 4.3 12.4 5.6C12.25 4.3 11.8 3.85 10.5 3.7"
           "C11.8 3.55 12.25 3.1 12.4 1.8Z")


@glyph
def sparkle():  # AI tooling: two solid four-point stars
    return [fill(_STAR), stroke(_STAR, w=0.8), fill(_STAR_S), stroke(_STAR_S, w=0.7)]


@glyph
def chart():  # coverage / metrics
    return [frect(3, 9, 2, 4, 0.8), frect(7, 6, 2, 7, 0.8), frect(11, 3, 2, 10, 0.8)]  # 2px bars, 2px gaps, on whole pixels


@glyph
def users():  # people / owners
    return [circle(6, 5.5, 2.1), stroke("M2.5 13.2C2.5 10.8 4 9.6 6 9.6C8 9.6 9.5 10.8 9.5 13.2"),
            circle(11.1, 6.1, 1.6), stroke("M11 9.6C12.6 9.6 13.7 10.7 13.7 12.9")]


@glyph
def link():  # links: two interlocked capsules
    cap = lambda cx, cy: (f'<rect x="{n(cx - 3.6)}" y="{n(cy - 2.1)}" width="7.2" height="4.2" rx="2.1" '
                          f'transform="rotate(-45 {n(cx)} {n(cy)})" stroke="{INK}" stroke-width="1.3"/>')
    return [cap(5.9, 10.1), cap(10.1, 5.9)]


@glyph
def globe():  # locales / geo data
    return [circle(8, 8, 5.8), stroke("M8 2.2C5.4 4.6 5.4 11.4 8 13.8C10.6 11.4 10.6 4.6 8 2.2Z"),
            line((2.2, 8), (13.8, 8))]  # a wide meridian: three cells of at least 1.6px instead of a thin centre one


@glyph
def mail():
    return [rrect(2.3, 3.5, 11.4, 9, 1.8), stroke("M2.9 4.6L7.15 8.1C7.65 8.5 8.35 8.5 8.85 8.1L13.1 4.6")]


@glyph
def sliders():  # env / tuning
    return [line((2.5, 4), (13.5, 4)), line((2.5, 8), (13.5, 8)), line((2.5, 12), (13.5, 12)),
            dot(5, 4, 1.8), dot(10.5, 8, 1.8), dot(6.5, 12, 1.8)]


@glyph
def server():  # two solid units with a clear gap between them and a knocked-out LED each
    return knock([frect(2, 3, 12, 4, 1.5), frect(2, 9, 12, 4, 1.5)], dot(5, 5, 1), dot(5, 11, 1))  # whole-pixel edges


@glyph
def chip():  # hardware / assembly: outline die, solid core, pins
    pins = []
    for v in (6.5, 9.5):
        pins += [line((v, 2), (v, 4.6)), line((v, 11.4), (v, 14)), line((2, v), (4.6, v)), line((11.4, v), (14, v))]
    return [rrect(4.6, 4.6, 6.8, 6.8, 1.4), frect(6.6, 6.6, 2.8, 2.8, 0.6)] + pins


@glyph
def shader():  # shader languages: a shaded sphere
    return [fill("M8 2.5A5.5 5.5 0 0 1 8 13.5Z", opacity=0.5), circle(8, 8, 5.5)]


@glyph
def swatch():  # design tokens
    return [rrect(2.5, 2.5, 4, 4, 1.2), frect(9, 2, 5, 5, 1.3), frect(2, 9, 5, 5, 1.3, opacity=0.5),
            rrect(9.5, 9.5, 4, 4, 1.2)]  # solid cells on whole pixels, outlined cells centred on pixels, 2px apart


@glyph
def license():  # licences: a rosette
    return [circle(8, 6.3, 3.7), dot(8, 6.3, 1.6), stroke("M5.9 9.4L5 13.9L8 12.5L11 13.9L10.1 9.4")]


@glyph
def spell():  # spell checkers
    return [text("A", cx=6, cy=6, w=1.4), line((7.8, 11.4), (9.7, 13.3), (13.6, 9.2), w=1.4)]


@glyph
def sourcemap():  # source maps: folded map, middle panel in the second tone
    return [fpoly((6, 3), (10, 4.5), (10, 13), (6, 11.5), opacity=0.5),
            poly((2.5, 4.3), (6, 3), (10, 4.5), (13.5, 3.2), (13.5, 11.7), (10, 13), (6, 11.5), (2.5, 12.8)),
            line((6, 3), (6, 11.5)), line((10, 4.5), (10, 13))]


@glyph
def backup():  # .bak and friends: rewind clock
    return [arc(8, 8, 5.4, 200, 160), _head(8, 8, 5.4, 200, sign=-1), line((8, 5.3), (8, 8), (10.1, 9.3))]


@glyph
def vsproj():  # Visual Studio style projects: a window with a solid title bar
    return [fill("M4.5 2.5H11.5C12.6 2.5 13.5 3.4 13.5 4.5V5.9H2.5V4.5C2.5 3.4 3.4 2.5 4.5 2.5Z"),
            rrect(2.5, 2.5, 11, 11, 2), line((5, 8.7), (9, 8.7)), line((5, 11), (11, 11))]


@glyph
def bot():  # automation bots
    return [rrect(3, 5.6, 10, 7.9, 2.2), line((8, 5.6), (8, 3.7)), dot(8, 2.9, 1), dot(6, 9.5, 1.1), dot(10, 9.5, 1.1)]


@glyph
def heart():  # funding
    return [fill("M8 13.6C3 10.3 2.4 7.7 2.7 6C3.1 3.9 5.5 3.1 7 4.1C7.5 4.4 7.8 4.8 8 5.2"
                 "C8.2 4.8 8.5 4.4 9 4.1C10.5 3.1 12.9 3.9 13.3 6C13.6 7.7 13 10.3 8 13.6Z")]


@glyph
def rss():  # feeds
    return [dot(4, 12, 1.3), stroke("M3 7.4A5.6 5.6 0 0 1 8.6 13"), stroke("M3 3A10 10 0 0 1 13 13")]


@glyph
def gamepad():  # game engines: solid pad, knocked-out d-pad and buttons
    body = ("M5.2 4.8H10.8C12.8 4.8 14.5 6.3 14.7 8.3L15 11.4C15.1 12.6 14.2 13.4 13.1 13.2"
            "C12.3 13.1 11.8 12.6 11.4 12L10.3 10.5H5.7L4.6 12C4.2 12.6 3.7 13.1 2.9 13.2C1.8 13.4 0.9 12.6 1 11.4L1.3 8.3"
            "C1.5 6.3 3.2 4.8 5.2 4.8Z")
    return knock([fill(body)], line((3.6, 8), (6.4, 8), w=1.3), line((5, 6.6), (5, 9.4), w=1.3),
                 dot(10.6, 7.1, 0.9), dot(12, 8.9, 0.9))


# --- tool / brand glyphs: solid silhouettes with knocked-out detail ------------------

_BOLT = "M9.4 1.9L3.9 9.3H7.7L6.7 14.1L12.1 6.7H8.3L9.4 1.9Z"


@glyph
def bolt():  # vite, bolt.new, StackBlitz
    return [fill(_BOLT), stroke(_BOLT, w=1)]


@glyph
def flame():  # Firebase, Mojo: solid flame with a knocked-out inner flame
    outer = ("M8 1.6C8.6 4.2 12.3 5.9 12.3 9.9C12.3 12.4 10.4 14.4 8 14.4C5.6 14.4 3.7 12.5 3.7 10.1"
             "C3.7 8.5 4.6 7.3 5.5 6.3C5.7 7.6 6.4 8.3 7.1 8.5C6.8 6.1 6.9 3.6 8 1.6Z")
    inner = "M8 8.9C8.3 9.9 9.6 10.4 9.6 11.8C9.6 12.7 8.9 13.2 8 13.2C7.1 13.2 6.4 12.7 6.4 11.8C6.4 10.8 7.2 10.3 8 8.9Z"
    return knock([fill(outer)], fill(inner))



@glyph
def esbuild():  # double chevron, no frame
    return [line((2.8, 3.4), (7, 8), (2.8, 12.6), w=1.8), line((8.6, 3.4), (12.8, 8), (8.6, 12.6), w=1.8)]


@glyph
def vercel():
    return [fpoly((8, 3.2), (13.6, 12.8), (2.4, 12.8)), poly((8, 3.2), (13.6, 12.8), (2.4, 12.8), w=1)]


_WAVE_HI = ("M2.2 7.6C3.1 4.7 5.4 3.9 7.4 5.3C8.9 6.4 10.7 7.1 13.8 4.6"
            "C13 7.6 10.8 8.5 8.6 7.1C7 6.1 5.1 5.7 2.2 7.6Z")
_WAVE_LO = ("M2.2 12.2C3.1 9.3 5.4 8.5 7.4 9.9C8.9 11 10.7 11.7 13.8 9.2"
            "C13 12.2 10.8 13.1 8.6 11.7C7 10.7 5.1 10.3 2.2 12.2Z")


@glyph
def tailwind():  # two tapered waves
    return [fill(_WAVE_HI), stroke(_WAVE_HI, w=0.6), fill(_WAVE_LO), stroke(_WAVE_LO, w=0.6)]


@glyph
def pnpm():  # a grid of blocks, bigger blocks and wider gaps than 1px so they stay separate
    out = []
    for r in range(3):
        for c in range(3):
            if (r, c) == (1, 1):
                continue
            out.append(frect(2 + c * 4, 2 + r * 4, 3, 3, 0.8, opacity=0.5 if (r, c) in ((1, 2), (2, 2)) else None))  # 3px blocks, 1px apart
    return out




def _bare(s):  # letters with no frame around them, so they get the whole icon: one fills it, two share it
    return [text(s, h=10, w=1.8)] if len(s) == 1 else [text(s, h=9, w=1.6, gap=1.2, max_w=13)]


@glyph
def next():
    return _bare("N")


@glyph
def angular(role="Ng"):  # Angular: the file's role in the flavour (C, S, ...), or "Ng" on its own
    return _bare(role)


@glyph
def nest(role="Ns"):  # NestJS: the file's role in the flavour, or "Ns" on its own
    return _bare(role)


@glyph
def ansible():
    return _bare("A")


@glyph
def hash(letter="C"):  # C#, Q#: no frame, so the # has room; it is smaller than the letter, which keeps a normal width
    cw = _WIDTH.get(letter, 4.0) * 1.5
    x = round((16 - (cw + 0.8 + 5.6)) / 2)
    return [text(letter, cx=x + cw / 2, h=9, w=1.7), text("#", cx=x + cw + 0.8 + 2.8, h=7.5, w=1.7, max_w=5.6)]


@glyph
def atom():  # two orbits and a solid nucleus
    orbit = lambda deg: (f'<ellipse cx="8" cy="8" rx="6.6" ry="2.6" transform="rotate({deg} 8 8)" '
                         f'stroke="{INK}" stroke-width="1.2"/>')
    return [orbit(45), orbit(-45), dot(8, 8, 1.9)]


@glyph
def arduino():  # two tall loops that overlap, with the minus and the plus (a round loop is too small for the plus at 16px)
    loop = lambda cx: f'<ellipse cx="{cx}" cy="7.5" rx="3.25" ry="4.3" stroke="{INK}" stroke-width="1.3"/>'
    # y = 7.5 and x = 10.5 are pixel centres, so the signs are one crisp pixel wide instead of two 55% ones
    return [loop(5.25), loop(10.75), line((3.5, 7.5), (7, 7.5), w=1.1), line((9, 7.5), (12.5, 7.5), w=1.1),
            line((10.5, 6), (10.5, 9), w=1.1)]


@glyph
def webpack():  # an outline hexagon around a solid cube, its three faces in three tones
    c, v = (8, 8), regular(8, 8, 3.4, 6)
    return [poly(*_HEX), fpoly(v[5], v[0], v[1], c, opacity=0.45), fpoly(v[5], c, v[3], v[4]),
            fpoly(c, v[1], v[2], v[3], opacity=0.72)]
