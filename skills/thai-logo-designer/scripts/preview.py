#!/usr/bin/env python3
"""
สร้างหน้า preview.html เทียบโลโก้หลายแบบ พร้อมแถบเช็กขนาดเล็ก (64/32/16px)
Build logos/preview.html from every SVG in a folder.

Usage:
  preview.py logos/concepts            → logos/preview.html  (title: Concepts)
  preview.py logos/iterations          → logos/preview.html  (newest first)
  preview.py logos/iterations --icons logos/icons
      (--icons: folder of square icon SVGs named like the iterations,
       used for the small-size strip when the logo itself is wide)
  preview.py logos/concepts --inline   → embed SVGs in the HTML (one self-contained file)

The page has light / dark / brand-colour backgrounds so you can check contrast.
"""
import argparse
import html
import re
from pathlib import Path


def natural_key(p: Path):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p.stem)]


def note_of(svg_text: str) -> str:
    m = re.search(r"<!--\s*(.*?)\s*-->", svg_text, re.S)
    return m.group(1).strip() if m else ""


def is_square(svg_text: str) -> bool:
    m = re.search(r'viewBox\s*=\s*["\'][-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', svg_text)
    return bool(m) and abs(float(m.group(1)) - float(m.group(2))) < 0.5


def src_for(path: Path, out: Path, inline: bool) -> str:
    if inline:
        import base64
        data = base64.b64encode(path.read_bytes()).decode()
        return f"data:image/svg+xml;base64,{data}"
    return path.resolve().relative_to(out.parent.resolve()).as_posix() if path.resolve().is_relative_to(out.parent.resolve()) else path.resolve().as_uri()


PAGE = """<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ --bg:#f4f4f2; --card:#fff; --fg:#222; --line:rgba(0,0,0,.12); }}
body.dark {{ --bg:#161616; --card:#262626; --fg:#eee; --line:rgba(255,255,255,.14); }}
* {{ box-sizing:border-box; margin:0; }}
body {{ font-family: "IBM Plex Sans Thai", "Sarabun", system-ui, sans-serif; background:var(--bg); color:var(--fg); padding:24px; }}
header {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:20px; }}
h1 {{ font-size:20px; margin-right:auto; }}
h2 {{ font-size:16px; margin:32px 0 12px; }}
button, input[type=color] {{ border:1px solid var(--line); background:var(--card); color:var(--fg); border-radius:8px; padding:6px 12px; cursor:pointer; font:inherit; height:34px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; overflow:hidden; }}
.card.latest {{ outline:3px solid #f5a623; }}
.img {{ height:240px; display:flex; align-items:center; justify-content:center; padding:24px; background:var(--tile, transparent); }}
.img img {{ max-width:100%; max-height:100%; }}
.label {{ padding:10px 14px; border-top:1px solid var(--line); font-size:14px; }}
.label b {{ display:block; }}
.label span {{ opacity:.65; font-size:12.5px; }}
.strip {{ display:flex; flex-wrap:wrap; gap:24px; }}
.fav {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 14px; }}
.fav .row {{ display:flex; gap:14px; align-items:flex-end; margin-top:6px; }}
.fav small {{ display:block; text-align:center; opacity:.6; font-size:11px; }}
</style></head>
<body>
<header>
  <h1>{title}</h1>
  <button onclick="document.body.classList.toggle('dark')">🌗 สว่าง / มืด</button>
  <label>พื้นหลังการ์ด <input type="color" value="#ffffff" oninput="document.body.style.setProperty('--tile', this.value)"></label>
  <button onclick="document.body.style.removeProperty('--tile')">ล้างสีพื้น</button>
</header>
<div class="grid">{cards}</div>
<h2>เช็กขนาดเล็ก (favicon / ไอคอนแอป)</h2>
<div class="strip">{favs}</div>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--out", help="ค่าเริ่มต้น: <folder>/../preview.html")
    ap.add_argument("--icons", help="โฟลเดอร์ไอคอนสี่เหลี่ยม ใช้ในแถบขนาดเล็ก")
    ap.add_argument("--title")
    ap.add_argument("--inline", action="store_true", help="ฝัง SVG ในไฟล์ HTML เลย")
    a = ap.parse_args()

    folder = Path(a.folder)
    out = Path(a.out) if a.out else folder.parent / "preview.html"
    files = sorted(folder.glob("*.svg"), key=natural_key)
    newest_first = "iteration" in folder.name
    if newest_first:
        files.reverse()
    title = a.title or ("รอบปรับแก้ (ล่าสุดอยู่ซ้าย)" if newest_first else "แบบร่าง")

    icons = Path(a.icons) if a.icons else None
    cards, favs = [], []
    for i, f in enumerate(files):
        text = f.read_text(encoding="utf-8", errors="ignore")
        src = src_for(f, out, a.inline)
        cls = "card latest" if newest_first and i == 0 else "card"
        note = html.escape(note_of(text))
        cards.append(f'<div class="{cls}"><div class="img"><img src="{src}" alt="{f.stem}"></div>'
                     f'<div class="label"><b>{f.stem}</b><span>{note}</span></div></div>')

        fav = None
        if icons and (icons / f.name).exists():
            fav = icons / f.name
        elif is_square(text):
            fav = f
        if fav is not None:
            fsrc = src_for(fav, out, a.inline)
            sizes = "".join(f'<div><img src="{fsrc}" width="{s}" height="{s}"><small>{s}px</small></div>'
                            for s in (64, 32, 16))
            favs.append(f'<div class="fav"><b>{f.stem}</b><div class="row">{sizes}</div></div>')

    if not favs:
        favs.append('<p style="opacity:.65">โลโก้เป็นแนวนอน — สร้างไอคอนสี่เหลี่ยมแยกแล้วใส่ --icons เพื่อเช็กขนาดเล็ก</p>')

    out.write_text(PAGE.format(title=title, cards="".join(cards), favs="".join(favs)), encoding="utf-8")
    print(f"✓ {out}  ({len(files)} แบบ)")


if __name__ == "__main__":
    main()
