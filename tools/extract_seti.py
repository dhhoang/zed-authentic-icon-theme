"""Extract VS Code's Seti file-icon shapes into tools/seti.json (no dependencies).

VS Code's built-in file icons (extensions/theme-seti in microsoft/vscode, from Seti UI by
Jesse Weed, both MIT) ship as an icon font, seti.woff, plus a theme JSON that maps file names,
extensions and language ids to glyphs. This script reads the font's TrueType outlines and
writes each glyph as SVG path data, together with Seti's maps, so build.py can draw any Seti
shape in Zed's colours without the font or a font library.

usage: python3 -I tools/extract_seti.py <vscode checkout> tools/seti.json
"""
import json
import struct
import subprocess
import sys
import zlib

src, out = sys.argv[1:3]
seti_dir = f"{src}/extensions/theme-seti/icons"
woff = open(f"{seti_dir}/seti.woff", "rb").read()
theme = json.load(open(f"{seti_dir}/vs-seti-icon-theme.json", encoding="utf-8"))

# --- WOFF 1.0 container: a table directory of (optionally zlib-compressed) sfnt tables ---------
sig, flavor, _, num_tables = struct.unpack(">4sIIH", woff[:14])
if sig != b"wOFF" or flavor != 0x10000:
    sys.exit("expected a WOFF 1.0 font with TrueType outlines")
tables = {}
for i in range(num_tables):
    tag, off, comp, orig, _ = struct.unpack(">4sIIII", woff[44 + i * 20:64 + i * 20])
    data = woff[off:off + comp]
    tables[tag.decode()] = zlib.decompress(data) if comp < orig else data

head, maxp, loca_t, glyf = tables["head"], tables["maxp"], tables["loca"], tables["glyf"]
units_per_em = struct.unpack(">H", head[18:20])[0]
long_loca = struct.unpack(">h", head[50:52])[0] == 1
num_glyphs = struct.unpack(">H", maxp[4:6])[0]
if long_loca:
    loca = struct.unpack(f">{num_glyphs + 1}I", loca_t[:4 * (num_glyphs + 1)])
else:
    loca = [v * 2 for v in struct.unpack(f">{num_glyphs + 1}H", loca_t[:2 * (num_glyphs + 1)])]


def cmap_format4(cmap):
    """Unicode BMP -> glyph id, from the (3, 1) format-4 subtable icon fonts use."""
    n = struct.unpack(">H", cmap[2:4])[0]
    for i in range(n):
        plat, enc, off = struct.unpack(">HHI", cmap[4 + i * 8:12 + i * 8])
        if (plat, enc) == (3, 1) and struct.unpack(">H", cmap[off:off + 2])[0] == 4:
            sub = cmap[off:]
            segs = struct.unpack(">H", sub[6:8])[0] // 2
            ends = struct.unpack(f">{segs}H", sub[14:14 + 2 * segs])
            p = 16 + 2 * segs
            starts = struct.unpack(f">{segs}H", sub[p:p + 2 * segs])
            deltas = struct.unpack(f">{segs}h", sub[p + 2 * segs:p + 4 * segs])
            ro_at = p + 4 * segs
            ranges = struct.unpack(f">{segs}H", sub[ro_at:ro_at + 2 * segs])
            out = {}
            for s in range(segs):
                for c in range(starts[s], ends[s] + 1):
                    if c == 0xFFFF:
                        continue
                    if ranges[s] == 0:
                        g = (c + deltas[s]) & 0xFFFF
                    else:
                        at = ro_at + 2 * s + ranges[s] + 2 * (c - starts[s])
                        g = struct.unpack(">H", sub[at:at + 2])[0]
                        g = (g + deltas[s]) & 0xFFFF if g else 0
                    out[c] = g
            return out
    sys.exit("no (3,1) format-4 cmap subtable")


def contours(gid):
    """TrueType glyph -> list of contours, each a list of (x, y, on_curve); composites flattened."""
    data = glyf[loca[gid]:loca[gid + 1]]
    if not data:
        return []
    n = struct.unpack(">h", data[:2])[0]
    if n < 0:  # composite: components placed by x/y offsets (icon fonts use no transforms)
        result, p = [], 10
        while True:
            flags, comp = struct.unpack(">HH", data[p:p + 4])
            p += 4
            if flags & 1:
                dx, dy = struct.unpack(">hh", data[p:p + 4])
                p += 4
            else:
                dx, dy = struct.unpack(">bb", data[p:p + 2])
                p += 2
            if not flags & 2 or flags & (8 | 0x40 | 0x80):
                sys.exit(f"glyph {gid}: composite with transforms is not supported")
            result += [[(x + dx, y + dy, on) for x, y, on in c] for c in contours(comp)]
            if not flags & 0x20:
                return result
    ends = struct.unpack(f">{n}H", data[10:10 + 2 * n])
    count = ends[-1] + 1
    p = 10 + 2 * n
    p += 2 + struct.unpack(">H", data[p:p + 2])[0]  # skip hinting instructions
    flags = []
    while len(flags) < count:
        f = data[p]
        p += 1
        flags.append(f)
        if f & 8:  # repeat
            flags += [f] * data[p]
            p += 1
    coords = {}
    for axis, short_bit, same_bit in (("x", 2, 16), ("y", 4, 32)):
        v, vals = 0, []
        for f in flags:
            if f & short_bit:
                d = data[p]
                p += 1
                v += d if f & same_bit else -d
            elif not f & same_bit:
                v += struct.unpack(">h", data[p:p + 2])[0]
                p += 2
            vals.append(v)
        coords[axis] = vals
    pts = list(zip(coords["x"], coords["y"], [bool(f & 1) for f in flags]))
    out, start = [], 0
    for end in ends:
        out.append(pts[start:end + 1])
        start = end + 1
    return out


def path(cs):
    """Contours -> SVG path data (y flipped to point down), quadratic curves as Q."""
    fmt = lambda v: f"{v:.1f}".rstrip("0").rstrip(".")
    pt = lambda x, y: f"{fmt(x)} {fmt(-y)}"
    d = []
    for c in cs:
        if not c:
            continue
        # start on an on-curve point; between two off-curve points the on-curve point is implied
        i0 = next((i for i, p in enumerate(c) if p[2]), None)
        if i0 is None:
            a, b = c[0], c[1]
            c = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, True)] + c
            i0 = 0
        c = c[i0:] + c[:i0]
        d.append(f"M{pt(*c[0][:2])}")
        ctrl = None
        for x, y, on in c[1:] + [c[0]]:
            if on:
                d.append(f"Q{pt(*ctrl)} {pt(x, y)}" if ctrl else f"L{pt(x, y)}")
                ctrl = None
            else:
                if ctrl:
                    mx, my = (ctrl[0] + x) / 2, (ctrl[1] + y) / 2
                    d.append(f"Q{pt(*ctrl)} {pt(mx, my)}")
                ctrl = (x, y)
        d.append("Z")
    return "".join(d)


cmap = cmap_format4(tables["cmap"])
glyphs, icons = {}, {}
for icon_id, spec in theme["iconDefinitions"].items():
    char = spec["fontCharacter"].lstrip("\\").upper()
    icons[icon_id] = char
    if char in glyphs:
        continue
    cs = contours(cmap[int(char, 16)])
    xs = [p[0] for c in cs for p in c]
    ys = [-p[1] for c in cs for p in c]
    glyphs[char] = {"d": path(cs), "bbox": [min(xs), min(ys), max(xs), max(ys)]}

sha = subprocess.check_output(["git", "-C", src, "rev-parse", "HEAD"], text=True).strip()
json.dump({
    "source": {"microsoft/vscode": sha, "seti-ui": theme.get("version", "")},
    "license": "MIT: Seti UI (c) 2014 Jesse Weed; packaging (c) Microsoft Corporation. See THIRD_PARTY_NOTICES.md",
    "units_per_em": units_per_em,
    "glyphs": dict(sorted(glyphs.items())),
    "icons": dict(sorted(icons.items())),
    "file_names": theme["fileNames"],
    "file_extensions": theme["fileExtensions"],
    "language_ids": theme["languageIds"],
}, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(out, "a").write("\n")
print(f"{len(glyphs)} glyphs, {len(icons)} icon ids, {units_per_em} units/em -> {out}")
