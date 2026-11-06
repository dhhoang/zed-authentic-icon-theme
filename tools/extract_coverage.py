"""Work out which file names / extensions this theme must add on top of Zed's defaults.

Inputs (both are plain checkouts; nothing is executed from them):
  <zed>      zed-industries/zed         (reads crates/theme/src/icon_theme.rs)
  <vsicons>  vscode-icons/vscode-icons-zed (reads icon_themes/vsicons-icon-theme-zed.json)

Rule: a name or extension that Zed's default theme already maps to a real icon is left
alone. Everything else the vscode-icons theme covers is "missing" and goes to
coverage.json, grouped by the vscode-icons icon key so each group can be given a design.

usage: python3 -I extract_coverage.py <zed> <vsicons> <out.json>
"""
import json
import re
import subprocess
import sys

zed, vs, out = sys.argv[1:4]
rs = open(f"{zed}/crates/theme/src/icon_theme.rs").read()


def parse_assoc(name):
    body = re.search(rf"const {name}[^=]*=\s*&\[(.*?)\n\];", rs, re.S).group(1)
    pairs = {}
    for key, vals in re.findall(r'\(\s*"([^"]+)",\s*&\[(.*?)\]\s*,?\s*\)', body, re.S):
        for v in re.findall(r'"([^"]+)"', vals):
            pairs[v] = key
    return pairs


zed_stems = parse_assoc("FILE_STEMS_BY_ICON_KEY")
zed_suffixes = parse_assoc("FILE_SUFFIXES_BY_ICON_KEY")
zed_icons = dict(re.findall(r'\("([^"]+)",\s*"icons/file_icons/([^"]+)"\)', rs))

# Keys Zed maps names to but draws nothing real for (generic file.svg, or no icon at all).
used = set(zed_stems.values()) | set(zed_suffixes.values())
zed_blank = sorted(k for k in used if zed_icons.get(k, "file.svg") == "file.svg")

themes = {t["name"]: t for t in json.load(open(f"{vs}/icon_themes/vsicons-icon-theme-zed.json"))["themes"]}
theme = themes["VSCode Icons for Zed (Dark)"]

zed_names = set(zed_stems) | set(zed_suffixes)


def group(pairs):
    """{name: kind, key} -> {key: {stems: [...], suffixes: [...]}}, skipping names Zed already maps."""
    keys = {}
    for name, (kind, key) in pairs.items():
        if name in zed_names:
            continue  # Zed already has this exact entry: inherit it untouched
        keys.setdefault(key.removeprefix("_f_"), {"stems": [], "suffixes": []})[kind].append(name)
    for k in keys.values():
        k["stems"].sort()
        k["suffixes"].sort()
    return dict(sorted(keys.items()))


def entries(t):
    # vscode-icons lists 11 names as both stem and suffix; Zed looks stems up first, so the stem wins.
    out = {n: ("suffixes", k) for n, k in t["file_suffixes"].items()}
    out.update({n: ("stems", k) for n, k in t["file_stems"].items()})
    return out


base = entries(theme)
keys = group(base)

# Angular / NestJS flavours re-map role-named files (*.service.ts, ...) that clash with each other,
# so they ship as separate theme variants. Only their framework entries matter here: the
# "_official" swaps only change JS/TS/YAML logos, which this theme leaves to Zed's own icons.
flavors = {}
for flavor in ("Angular", "NestJS"):
    f = entries(themes[f"VSCode Icons for Zed (Dark {flavor})"])
    flavors[flavor] = group({n: v for n, v in f.items()
                             if v != base.get(n) and not v[1].endswith("_official")})

sha = lambda d: subprocess.check_output(["git", "-C", d, "rev-parse", "HEAD"], text=True).strip()
json.dump({
    "source": {"vscode-icons-zed": sha(vs), "zed": sha(zed)},
    "zed_blank_keys": zed_blank,
    # Zed's built-in tables, so build/check never need a Zed checkout
    "zed_default": {"stems": dict(sorted(zed_stems.items())), "suffixes": dict(sorted(zed_suffixes.items())),
                    "icons": dict(sorted(zed_icons.items()))},
    "keys": keys,
    "flavors": flavors,
}, open(out, "w"), indent=1, ensure_ascii=False, sort_keys=False)
open(out, "a").write("\n")
count = lambda ks: sum(len(v["stems"]) + len(v["suffixes"]) for v in ks.values())
print(f"{len(keys)} icon keys, {count(keys)} entries; Zed blank keys: {zed_blank}")
for name, ks in flavors.items():
    print(f"flavour {name}: {len(ks)} keys, {count(ks)} entries")
