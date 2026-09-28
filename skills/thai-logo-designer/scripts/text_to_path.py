#!/usr/bin/env python3
"""
แปลงข้อความ (ไทย/อังกฤษ) เป็น SVG <path> ที่ไม่ต้องพึ่งฟอนต์ในเครื่อง
Convert text into an SVG <path> so the logo renders the same everywhere.

Uses HarfBuzz for shaping, so Thai vowels and tone marks (สระบน/ล่าง, วรรณยุกต์)
land in the right place — the thing plain SVG <text> gets wrong.

Usage:
  text_to_path.py "ข้าวหอม" --font kanit-bold --size 160 --fill "#1B5E20"
  text_to_path.py "Moonbeam" --font /path/to/Any.ttf --size 120 --x 512 --y 300 --anchor middle
  text_to_path.py --list-fonts

Output: a <g> element on stdout (or --out file). Paste it into the logo SVG.
Pass --svg to get a complete standalone SVG instead (for quick checks).
"""
import argparse
import sys
from pathlib import Path

try:
    import uharfbuzz as hb
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
except ImportError:
    sys.exit("ต้องติดตั้งก่อน / install first:  pip install uharfbuzz fonttools")

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONTS = {
    "kanit-bold": "Kanit-Bold.ttf",
    "kanit-regular": "Kanit-Regular.ttf",
    "prompt-bold": "Prompt-Bold.ttf",
    "plex-thai-bold": "IBMPlexSansThai-Bold.ttf",
    "plex-thai-regular": "IBMPlexSansThai-Regular.ttf",
}


def resolve_font(name: str) -> Path:
    if name in FONTS:
        return FONT_DIR / FONTS[name]
    p = Path(name).expanduser()
    if p.is_file():
        return p
    sys.exit(f"ไม่พบฟอนต์ / font not found: {name}\nใช้ --list-fonts เพื่อดูรายชื่อ")


def shape(text: str, font_path: Path, letter_spacing: float):
    blob = hb.Blob.from_file_path(str(font_path))
    face = hb.Face(blob)
    font = hb.Font(face)
    upem = face.upem
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    return buf.glyph_infos, buf.glyph_positions, upem


def text_to_path(text, font_path, size, letter_spacing=0.0):
    """Return (path_d, width, ascent, descent) in pixel units, baseline at y=0."""
    tt = TTFont(str(font_path))
    glyph_set = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    infos, positions, upem = shape(text, font_path, letter_spacing)
    scale = size / upem
    spacing_units = letter_spacing * upem / size if size else 0

    # Count clusters so spacing applies between visible letters, not to marks
    pen = SVGPathPen(glyph_set)
    x = 0.0
    last_cluster = None
    for info, pos in zip(infos, positions):
        if last_cluster is not None and info.cluster != last_cluster and pos.x_advance > 0:
            x += spacing_units
        gname = order[info.codepoint]
        # flip Y (font units go up, SVG goes down) and scale
        tpen = TransformPen(pen, (scale, 0, 0, -scale,
                                  (x + pos.x_offset) * scale,
                                  -pos.y_offset * scale))
        glyph_set[gname].draw(tpen)
        x += pos.x_advance
        last_cluster = info.cluster

    hhea = tt["hhea"]
    width = x * scale
    return pen.getCommands(), width, hhea.ascent * scale, -hhea.descent * scale


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?")
    ap.add_argument("--font", default="kanit-bold", help="ชื่อฟอนต์ในตัว หรือ path ไฟล์ .ttf/.otf")
    ap.add_argument("--size", type=float, default=120, help="ขนาดตัวอักษร (px)")
    ap.add_argument("--x", type=float, default=0, help="ตำแหน่ง x")
    ap.add_argument("--y", type=float, default=0, help="ตำแหน่ง y ของเส้นฐาน (baseline)")
    ap.add_argument("--anchor", choices=["start", "middle", "end"], default="start")
    ap.add_argument("--fill", default="#111111")
    ap.add_argument("--letter-spacing", type=float, default=0, help="ระยะห่างตัวอักษร (px)")
    ap.add_argument("--max-width", type=float, help="ถ้ากว้างเกินนี้ จะลดขนาดตัวอักษรให้พอดีอัตโนมัติ")
    ap.add_argument("--id", default="wordmark")
    ap.add_argument("--svg", action="store_true", help="ออกเป็นไฟล์ SVG เต็ม (ไว้ทดสอบ)")
    ap.add_argument("--out", help="เขียนลงไฟล์แทน stdout")
    ap.add_argument("--list-fonts", action="store_true")
    a = ap.parse_args()

    if a.list_fonts:
        for k, v in FONTS.items():
            print(f"{k:20s} {v}")
        return
    if not a.text:
        ap.error("ต้องใส่ข้อความ / text is required")

    font_path = resolve_font(a.font)
    d, width, asc, desc = text_to_path(a.text, font_path, a.size, a.letter_spacing)
    if a.max_width and width > a.max_width:
        a.size = a.size * a.max_width / width
        d, width, asc, desc = text_to_path(a.text, font_path, a.size, a.letter_spacing)
        print(f"ลดขนาดเป็น / shrunk to size={a.size:.1f} to fit max-width", file=sys.stderr)
    dx = {"start": 0, "middle": -width / 2, "end": -width}[a.anchor]
    tx, ty = a.x + dx, a.y

    group = (f'<g id="{a.id}" fill="{a.fill}" transform="translate({tx:.2f} {ty:.2f})">\n'
             f'  <!-- "{a.text}" · {font_path.name} · {a.size:g}px · width≈{width:.1f} -->\n'
             f'  <path d="{d}"/>\n</g>')

    if a.svg:
        pad = a.size * 0.25
        W = width + pad * 2
        H = asc + desc + pad * 2
        group = (f'<g id="{a.id}" fill="{a.fill}" transform="translate({pad:.2f} {pad + asc:.2f})">\n'
                 f'  <path d="{d}"/>\n</g>')
        out = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}">\n{group}\n</svg>\n'
    else:
        out = group + "\n"
    print(f"size={a.size:.1f} width={width:.1f} ascent={asc:.1f} descent={desc:.1f}", file=sys.stderr)

    if a.out:
        Path(a.out).write_text(out, encoding="utf-8")
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
