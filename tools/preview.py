"""Write preview.html: every new icon at its real 16px size on Zed's dark and light backgrounds.

Zed draws an extension's icons as plain images, which is exactly what an <img> tag does, so
this page shows what the project panel shows, with no dependencies. Open it in a browser;
use the browser's zoom to see them bigger, but judge legibility at 100%.

usage: python3 -I tools/preview.py
"""
import glob
import html
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPS = [("Letter badges", lambda n: n.startswith("mark-")),
          ("Drawn glyphs", lambda n: not n.startswith(("mark-", "seti-"))),
          ("VS Code shapes", lambda n: n.startswith("seti-"))]
PANELS = [("dark", "#2f343e", "#a9afbc"), ("light", "#ebebec", "#58585a")]

sections = []
for folder, bg, fg in PANELS:
    all_names = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, "icons", folder, "*.svg")))
    body = []
    for title, belongs in GROUPS:
        names = [n for n in all_names if belongs(n)]
        cells = "".join(
            f'<figure><img src="icons/{folder}/{n}.svg" width="16" height="16" alt="{html.escape(n)}">'
            f"<figcaption>{html.escape(n)}</figcaption></figure>" for n in names)
        body.append(f"<h3>{title} <small>{len(names)}</small></h3><div class=grid>{cells}</div>")
    sections.append(f'<section style="background:{bg};color:{fg}"><h2>{folder}</h2>{"".join(body)}</section>')

page = f"""<!doctype html><meta charset=utf-8><title>Authentic Icons preview</title>
<style>
body{{margin:0;font:12px system-ui,sans-serif;display:grid;grid-template-columns:1fr 1fr}}
section{{padding:16px 20px}} h2,h3{{margin:.8em 0 .4em}} small{{opacity:.6;font-weight:400}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(84px,1fr));gap:10px 4px}}
figure{{margin:0;text-align:center}} figcaption{{font-size:10px;opacity:.7;margin-top:3px;overflow:hidden;text-overflow:ellipsis}}
</style>{"".join(sections)}"""
with open(os.path.join(ROOT, "preview.html"), "w", encoding="utf-8") as f:
    f.write(page)
print("wrote preview.html")
