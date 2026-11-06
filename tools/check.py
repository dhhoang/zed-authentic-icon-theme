"""Self-check for the generated theme. Exits non-zero on the first broken promise.

It replays Zed's own icon lookup (crates/file_icons: get_icon) over Zed's default tables with
this theme merged on top, the way Zed loads an extension icon theme, and asserts:

  1. every name/extension Zed's default theme draws still gets exactly Zed's icon;
  2. every name/extension taken from vscode-icons-zed gets the icon its design asks for;
  3. the names Zed maps to its blank keys (.cs, .sln, .bak, ...) now get a real icon;
  4. every icon file the theme points at exists, is a 16x16 SVG, and none is left unused;
  5. icons carry a real colour: Zed shows an extension's icons as images in their own colours
     (only its built-in icons get tinted), so each icon folder must paint in exactly one baked
     colour, never black, with masks alone kept black/white;
  6. the kit puts horizontal and vertical strokes on pixel centres (see kit._snap).

usage: python3 -I tools/check.py
"""
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
cov = json.load(open(os.path.join(TOOLS, "coverage.json"), encoding="utf-8"))
family = json.load(open(os.path.join(ROOT, "icon_themes", "authentic-icons.json"), encoding="utf-8"))
zed = cov["zed_default"]
ZED_GENERIC = "zed:file.svg"


def resolver(theme):
    """Return name -> icon path, replaying Zed's lookup order."""
    stems = {**zed["stems"], **(theme or {}).get("file_stems", {})}  # extension tables extend Zed's
    suffixes = {**zed["suffixes"], **(theme or {}).get("file_suffixes", {})}
    icons = (theme or {}).get("file_icons", {})

    def icon_for_type(key):  # the theme's icon, else Zed's built-in one for that key
        if key in icons:
            return icons[key]["path"]
        return f"zed:{zed['icons'][key]}" if key in zed["icons"] else None

    def lookup(s):  # stems are consulted before suffixes, and a stem hit is final
        key = stems[s] if s in stems else suffixes.get(s)
        return icon_for_type(key) if key is not None else None

    def get_icon(name):
        if found := lookup(name):  # whole file name, e.g. eslint.config.js
            return found
        first_prefix, rest = None, name
        while "." in rest:  # each dotted suffix, longest first: a.d.ts -> d.ts -> ts
            prefix, rest = rest.split(".", 1)
            first_prefix = prefix if first_prefix is None else first_prefix
            if found := lookup(rest):
                return found
        if first_prefix is not None and (found := lookup(first_prefix)):  # Dockerfile.prod
            return found
        # Zed's remaining steps (multiple_extensions, extension, hidden name) only ever ask for
        # strings the loop above has already tried, so they cannot change the result.
        return icon_for_type("default")

    return get_icon


def sample(kind, entry):
    """A real file name that exercises the entry: stems are names, suffixes need a stem."""
    return entry if kind == "stems" else f"file.{entry}"


failures = []


def expect(ok, msg):
    if not ok:
        failures.append(msg)


zed_only = resolver(None)
themes = {t["name"]: t for t in family["themes"]}
base_name = family["name"]

for name, t in themes.items():
    get = resolver(t)
    icons = t["file_icons"]

    # 1. Zed's own entries are untouched
    for kind in ("stems", "suffixes"):
        for entry, key in zed[kind].items():
            if zed["icons"].get(key, "file.svg") == "file.svg":
                continue
            f = sample(kind, entry)
            expect(get(f) == zed_only(f), f"[{name}] {f}: Zed draws {zed_only(f)}, theme gives {get(f)}")
            expect(entry not in t["file_stems"] and entry not in t["file_suffixes"],
                   f"[{name}] theme re-maps Zed's own entry {entry!r}")

    # 2. every covered entry lands on its designed icon
    groups = dict(cov["keys"])
    if flavor := re.search(r"\((\w+)\)$", name):
        groups.update(cov["flavors"][flavor.group(1)])
    for key, grp in groups.items():
        for kind in ("stems", "suffixes"):
            for entry in grp[kind]:
                target = t[f"file_{kind}"].get(entry)
                want = icons[target]["path"] if target in icons else f"zed:{zed['icons'].get(target)}"
                f = sample(kind, entry)
                expect(get(f) == want and want != ZED_GENERIC,
                       f"[{name}] {f} ({key}): wanted {want}, Zed would show {get(f)}")

    # 3. Zed's blank keys are filled in
    for key in cov["zed_blank_keys"]:
        expect(key in icons, f"[{name}] Zed blank key {key!r} still has no icon")

# 4. icon files
used = {d["path"] for t in themes.values() for d in t["file_icons"].values()}
for path in used:
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        failures.append(f"missing icon file {path}")
        continue
    root = ET.parse(full).getroot()
    expect(root.get("viewBox") == "0 0 16 16", f"{path}: viewBox is {root.get('viewBox')}")
on_disk = {"./" + os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "icons", "*", "*.svg"))}
expect(not on_disk - used, f"unused icon files: {sorted(on_disk - used)}")

# 5. colours: one baked colour per folder outside masks, black/white inside masks
PAINT = re.compile(r'(?:fill|stroke)="([^"]+)"')
colours = {}
for folder in sorted(glob.glob(os.path.join(ROOT, "icons", "*"))):
    paints = set()
    for path in glob.glob(os.path.join(folder, "*.svg")):
        text = open(path, encoding="utf-8").read()
        masks = "".join(re.findall(r"<mask.*?</mask>", text, re.S))
        outside = re.sub(r"<mask.*?</mask>", "", text, flags=re.S)
        paints |= set(PAINT.findall(outside)) - {"none"}
        expect(set(PAINT.findall(masks)) <= {"black", "white"}, f"{path}: mask is not black/white")
    expect(len(paints) == 1 and not paints & {"black", "currentColor"},
           f"icons/{os.path.basename(folder)}: expected one baked colour, found {sorted(paints)}")
    colours[os.path.basename(folder)] = paints
expect(set(colours) == {"dark", "light"} and colours["dark"] != colours["light"],
       f"expected distinct dark and light colours, got {colours}")
files_per = {k: {os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "icons", k, "*.svg"))} for k in colours}
expect(len({frozenset(v) for v in files_per.values()}) == 1, "dark and light icon sets differ")
for t in themes.values():
    folder = "light" if t["appearance"] == "light" else "dark"
    expect(all(d["path"].startswith(f"./icons/{folder}/") for d in t["file_icons"].values()),
           f"[{t['name']}] ({t['appearance']}) points at icons outside icons/{folder}/")

# Worked examples, readable at a glance.
base, angular = resolver(themes[base_name]), resolver(themes[f"{base_name} (Angular)"])
light = resolver(themes[f"{base_name} Light"])
expect(light("package.json") == "./icons/light/box.svg", "light theme should use the light icons")
for f, want in [
    ("main.rs", "zed:rust.svg"),           # Zed already draws it: unchanged
    ("README.md", "zed:book.svg"),
    ("Dockerfile.prod", "zed:docker.svg"),
    ("Cargo.toml", "zed:rust.svg"),         # new name, reuses Zed's icon for the same language
    ("Gemfile", "zed:ruby.svg"),            # upstream only lists "gemfile"; Zed is case-sensitive
    ("Taskfile.yml", "./icons/dark/mark-tf.svg"),
    ("CLAUDE.md", "./icons/dark/sparkle.svg"),  # upstream only lists "claude.md"
    ("CODEOWNERS", "./icons/dark/users.svg"),
    ("Program.cs", "./icons/dark/hash-c.svg"),  # Zed maps .cs to its generic icon; now real
    ("App.sln", "./icons/dark/mark-vs.svg"),
    ("package.json", "./icons/dark/box.svg"),      # a new file type gets a new icon
    ("webpack.config.js", "./icons/dark/webpack.svg"),
    ("vite.config.ts", "./icons/dark/seti-vite.svg"),  # a VS Code (Seti) shape that stays legible at 16px
    ("index.twig", "zed:html.svg"),               # reuses Zed's own template icon
    ("user.test.ts", "./icons/dark/flask.svg"),
    (".env", "./icons/dark/sliders.svg"),
    ("LICENSE", "./icons/dark/license.svg"),
    ("main.adb", "zed:file.svg"),           # nothing claims .adb: Zed's default file icon
]:
    expect(base(f) == want, f"example {f}: wanted {want}, got {base(f)}")
expect(angular("app.component.ts") == "./icons/dark/angular-c.svg", "Angular flavour misses *.component.ts")
expect(base("app.component.ts") == "zed:typescript.svg", "base theme should leave *.component.ts to Zed")

# 6. pixel centres: a 1.2px stroke centred on k + 0.5 is one crisp pixel, on a pixel edge it is two blurry ones
sys.path.insert(0, TOOLS)
import kit  # noqa: E402

expect([kit._snap(v) for v in (3.2, 4.6, 12.9, 3, 13, 8)] == [3.5, 4.5, 12.5, 3.5, 12.5, 8],
       "kit._snap should land on pixel centres, and pull an edge towards the middle")
expect('d="M2 3.5L9.5 3.5L9.5 12.8"' in kit.line((2, 3.3), (9.2, 3.3), (9.2, 12.8)),
       "kit.line should move a segment across its direction only: y of the flat one, x of the upright one")
expect('d="M2 2L9 4"' in kit.line((2, 2), (9, 4)), "kit.line should leave a diagonal alone")
expect('x="2.5" y="2.5" width="11" height="11"' in kit.rrect(2.3, 2.7, 11.2, 10.9), "kit.rrect edges should sit on pixel centres")

if failures:
    print(f"{len(failures)} problems:", *failures[:40], sep="\n  ")
    sys.exit(1)
print(f"ok: {len(themes)} themes, {len(used)} icon files, Zed's own icons untouched")
