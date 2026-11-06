"""Generate the theme: icons/<variant>/*.svg and icon_themes/authentic-icons.json.

Inputs, all in tools/:
  coverage.json   names / extensions vscode-icons-zed covers and Zed does not (extract_coverage.py)
  design/*.txt    which design each vscode-icons key gets
                  (zed:<key> | s:<seti icon> | g:<glyph>[:args] | m:<AB>)
  seti.json       VS Code's Seti file-icon shapes (extract_seti.py)
  glyphs.py       the drawn glyphs; kit.py the drawing style

The theme only *adds* to Zed: Zed merges an extension theme's name/extension tables on top of
its own and falls back to its own icon for any key the theme does not define. So everything
Zed already draws stays exactly as Zed draws it, and `zed:<key>` designs just point new names
at an icon Zed already has.

Colour: Zed tints its own icons with the UI theme's muted text colour, but shows an extension's
icons as images in their own colours. Each new icon is therefore written twice, once in the
muted colour of Zed's default dark theme (One Dark) and once in the default light theme's
(One Light). Pass --dark / --light to match another UI theme's `text.muted` colour instead.

usage: python3 -I tools/build.py [--dark '#a9afbc'] [--light '#58585a']
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
from glyphs import G  # noqa: E402
from kit import INK, _G, _place, badge, fill, svg  # noqa: E402

NAME = "Authentic Icons"
AUTHOR = "Huy Hoang"
THEME_FILE = os.path.join(ROOT, "icon_themes", "authentic-icons.json")
ICONS_DIR = os.path.join(ROOT, "icons")
PREFIX = "zai-"  # our icon keys never shadow a current or future Zed key
HEX = re.compile(r"#[0-9a-fA-F]{6}")

args = argparse.ArgumentParser(description=__doc__.split("\n")[0])
args.add_argument("--dark", default="#a9afbc", help="icon colour for dark UI themes (One Dark text.muted)")
args.add_argument("--light", default="#58585a", help="icon colour for light UI themes (One Light text.muted)")
args = args.parse_args()
# (theme name, appearance, icon colour, icons/ subfolder). The dark variant keeps the plain
# name so an existing `"icon_theme": "Authentic Icons"` setting keeps working.
VARIANTS = [(NAME, "dark", args.dark, "dark"), (f"{NAME} Light", "light", args.light, "light")]


def fail(msg):
    sys.exit(f"build: {msg}")


for _, _, color, _ in VARIANTS:
    if not HEX.fullmatch(color):
        fail(f"colours must look like #a9afbc, got {color!r}")


def load_designs():
    """design/*.txt -> ({key: (design, where)}, {zed_blank_key: (design, where)})."""
    designs, blanks = {}, {}
    for path in sorted(glob.glob(os.path.join(TOOLS, "design", "*.txt"))):
        for no, raw in enumerate(open(path, encoding="utf-8"), 1):
            line = raw.strip()
            if not line or line.startswith("#"):  # comments are whole lines: '#' is legal in m:C#
                continue
            parts = line.split()
            where = f"{os.path.basename(path)}:{no}"
            if len(parts) != 2:
                fail(f"{where}: expected '<key> <design>', got {line!r}")
            key, design = parts
            table = blanks if key.startswith("@") else designs
            key = key.lstrip("@")
            if key in table:
                fail(f"{where}: {key} is designed twice (also {table[key][1]})")
            table[key] = (design, where)
    return designs, blanks


cov = json.load(open(os.path.join(TOOLS, "coverage.json"), encoding="utf-8"))
zed_icons = cov["zed_default"]["icons"]
zed_real = {k for k, f in zed_icons.items() if f != "file.svg"}  # keys Zed draws a real icon for
zed_blank = set(cov["zed_blank_keys"])  # keys Zed maps names to but draws nothing real for
designs, blank_designs = load_designs()

wanted = set(cov["keys"]).union(*cov["flavors"].values())
if missing := sorted(wanted - set(designs)):
    fail(f"no design for {len(missing)} keys: {missing}")
if extra := sorted(set(designs) - wanted - zed_blank):
    fail(f"designs for keys nothing uses (typo?): {extra}")

seti = json.load(open(os.path.join(TOOLS, "seti.json"), encoding="utf-8"))
SETI_BOX = 12.0  # every Seti glyph is fitted to Zed's 12px content box, like Zed's own icons



def seti_glyph(icon_id, where):
    """A VS Code (Seti) glyph as one solid shape, centred in the 16 x 16 icon."""
    if icon_id not in seti["icons"]:
        fail(f"{where}: unknown Seti icon {icon_id!r}")
    g = seti["glyphs"][seti["icons"][icon_id]]
    x0, y0, x1, y1 = g["bbox"]
    k = SETI_BOX / max(x1 - x0, y1 - y0)
    return [fill(_place(g["d"], k, k, 8 - (x0 + x1) / 2 * k, 8 - (y0 + y1) / 2 * k))]


drawings = {}  # file slug -> svg elements (colour not yet baked in)
slugs = {}  # icon key -> file slug


def realise(design, where):
    """design string -> icon key, registering the drawing when we draw one."""
    kind, _, rest = design.partition(":")
    if kind == "zed":
        if rest not in zed_real and rest not in zed_blank:
            fail(f"{where}: zed:{rest} is not a key Zed draws an icon for")
        return rest
    if kind == "g":
        name, _, arg = rest.partition(":")
        if name not in G:
            fail(f"{where}: unknown glyph {name!r}")
        params = arg.split(",") if arg else []
        slug = "-".join([name, *params]).lower()
        elements = G[name](*params)
    elif kind == "s":
        slug = "seti-" + rest.lstrip("_").lower()
        elements = seti_glyph(rest, where)
    elif kind == "m":
        if not 1 <= len(rest) <= 2 or any(c.upper() not in _G for c in rest):
            fail(f"{where}: letter mark must be 1-2 drawable characters, got {rest!r}")
        slug = "mark-" + rest.lower().replace("#", "sharp").replace("+", "plus")
        elements = badge(rest)
    else:
        fail(f"{where}: unknown design kind in {design!r}")
    drawings[slug] = elements
    slugs[PREFIX + slug] = slug
    return PREFIX + slug


# Zed's blank keys (csharp, vs_sln, backup, ...) get a real icon under Zed's own key name, which
# lights up every name Zed already maps to them (.cs, .sln, .bak, ...).
blank_slugs = {}
for key in sorted(zed_blank):
    design, where = blank_designs.get(key) or designs.get(key) or (None, None)
    if design is None:
        fail(f"Zed blank key {key!r} has no design: add '@{key} <design>' to design/")
    if design.startswith("zed:"):
        fail(f"{where}: Zed blank key {key!r} needs a drawn design, not {design}")
    blank_slugs[key] = slugs[realise(design, where)]

FILE_STEM = re.compile(r"[a-z][a-z0-9]*file([.-].+)?")
UPPER_CASE_NAMES = {"agents.md", "claude.md", "claude.local.md", "codeowners", "copying", "copying.md",
                    "copying.rst", "copying.txt", "skill.md", "warp.md"}
zed_names = set(cov["zed_default"]["stems"]) | set(cov["zed_default"]["suffixes"])


def maps(groups):
    stems, suffixes = {}, {}
    for key, grp in groups.items():
        target = realise(*designs[key])
        stems.update(dict.fromkeys(grp["stems"], target))
        suffixes.update(dict.fromkeys(grp["suffixes"], target))
    # vscode-icons lists some "*file" names only in lower case (gemfile, vagrantfile, gulpfile.js)
    # because VS Code matches case-insensitively; Zed does not, so add the conventional
    # Capitalised spelling (Gemfile, Vagrantfile, Gulpfile.js) unless something already maps it.
    # A few names are conventionally written in capitals but listed in lower case upstream.
    for stem, target in list(stems.items()):
        head, dot, rest = stem.partition(".")
        variant = (stem[0].upper() + stem[1:] if FILE_STEM.fullmatch(stem) else
                   head.upper() + dot + rest if stem in UPPER_CASE_NAMES else None)
        if variant and variant not in stems and variant not in suffixes and variant not in zed_names:
            stems[variant] = target
    return stems, suffixes


def theme(name, appearance, folder, stems, suffixes):
    used = set(stems.values()) | set(suffixes.values())
    file_icons = {k: slug for k, slug in slugs.items() if k in used}
    file_icons.update(blank_slugs)
    return {
        "name": name,
        "appearance": appearance,
        "file_stems": dict(sorted(stems.items())),
        "file_suffixes": dict(sorted(suffixes.items())),
        "file_icons": {k: {"path": f"./icons/{folder}/{s}.svg"} for k, s in sorted(file_icons.items())},
    }


base = maps(cov["keys"])
flavors = {f: maps(groups) for f, groups in cov["flavors"].items()}
themes = []
for name, appearance, _, folder in VARIANTS:
    themes.append(theme(name, appearance, folder, *base))
    for flavor, (stems, suffixes) in flavors.items():
        themes.append(theme(f"{name} ({flavor})", appearance, folder,
                            {**base[0], **stems}, {**base[1], **suffixes}))

shutil.rmtree(ICONS_DIR, ignore_errors=True)  # icons/ is fully generated
for _, _, color, folder in VARIANTS:
    os.makedirs(os.path.join(ICONS_DIR, folder))
    for slug, elements in drawings.items():
        with open(os.path.join(ICONS_DIR, folder, f"{slug}.svg"), "w", encoding="utf-8") as f:
            f.write(svg(*elements, color=color))

os.makedirs(os.path.dirname(THEME_FILE), exist_ok=True)
with open(THEME_FILE, "w", encoding="utf-8") as f:
    json.dump({"$schema": "https://zed.dev/schema/icon_themes/v0.3.0.json", "name": NAME,
               "author": AUTHOR, "themes": themes}, f, indent=2, ensure_ascii=False)
    f.write("\n")

kinds = {}
for d, _ in designs.values():
    kinds[d.partition(":")[0]] = kinds.get(d.partition(":")[0], 0) + 1
print(f"{len(drawings)} icons x {len(VARIANTS)} colours "
      f"({', '.join(f'{folder} {color}' for _, _, color, folder in VARIANTS)}); designs by kind {kinds}")
for t in themes:
    print(f"  {t['name']}: {len(t['file_stems']) + len(t['file_suffixes'])} names/extensions, "
          f"{len(t['file_icons'])} icon keys")
