#!/usr/bin/env python3
"""
ตรวจโลโก้ SVG หาปัญหาที่เจอบ่อย ก่อนส่งออกหรือส่งให้ผู้ใช้ดู
Lint logo SVGs for the problems that break logos in real use.

Usage:
  check_svg.py logos/iterations/iteration-4.svg
  check_svg.py logos/concepts/*.svg

Exit code 1 if any ERROR is found (WARN does not fail).
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

THAI = re.compile(r"[\u0E00-\u0E7F]")
NS = "{http://www.w3.org/2000/svg}"


def edge_clip(path: Path):
    """Render small and report sides where opaque pixels hit the border.
    A full-bleed background (all four sides filled) is treated as intentional."""
    try:
        import cairosvg, io
        from PIL import Image
    except ImportError:
        return None
    try:
        png = cairosvg.svg2png(url=str(path), output_width=400)
    except Exception:
        return None
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    a = im.getchannel("A")
    w, h = im.size
    def hit(box):
        return a.crop(box).getextrema()[1] > 40
    def full(box):
        return a.crop(box).getextrema()[0] > 200
    sides = {"บน": (0, 0, w, 1), "ล่าง": (0, h - 1, w, h), "ซ้าย": (0, 0, 1, h), "ขวา": (w - 1, 0, w, h)}
    if all(full(b) for b in sides.values()):
        return None  # full-bleed background tile
    touched = [name for name, b in sides.items() if hit(b) and not full(b)]
    return " ".join(touched) if touched else None


def check(path: Path):
    issues = []
    err = lambda m: issues.append(("ERROR", m))
    warn = lambda m: issues.append(("WARN", m))

    raw = path.read_text(encoding="utf-8", errors="ignore")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        return [("ERROR", f"XML เสีย เปิดไม่ได้: {e}")]

    if root.tag != f"{NS}svg":
        err('ไม่มี xmlns="http://www.w3.org/2000/svg" — บางโปรแกรมจะเปิดไม่ขึ้น')

    vb = root.get("viewBox")
    if not vb:
        err("ไม่มี viewBox — ย่อขยายแล้วจะเพี้ยน")
    if root.get("width") or root.get("height"):
        warn("มี width/height ตายตัวที่ <svg> — ควรใช้แค่ viewBox")

    # text elements = font dependency
    for t in root.iter(f"{NS}text"):
        content = "".join(t.itertext())
        if THAI.search(content):
            err(f'ตัวอักษรไทยอยู่ใน <text> ("{content[:20]}") — สระ/วรรณยุกต์จะเพี้ยนหรือกลายเป็นกล่อง '
                f"ให้แปลงด้วย scripts/text_to_path.py")
        else:
            fam = t.get("font-family") or ""
            if not re.search(r"sans-serif|serif|monospace", fam):
                warn(f'<text> "{content[:20]}" ไม่มีฟอนต์สำรอง (sans-serif) — ถ้าเป็นตัวจริงควรแปลงเป็น path')
            else:
                warn(f'<text> "{content[:20]}" ยังพึ่งฟอนต์ในเครื่อง — ก่อนส่งออกตัวจริงควรแปลงเป็น path')

    # external references
    for el in root.iter():
        for k, v in el.attrib.items():
            if k.endswith("href") and v and not v.startswith("#") and not v.startswith("data:"):
                err(f"อ้างไฟล์ภายนอก ({v[:40]}) — SVG ต้องอยู่ได้ด้วยตัวเอง")
    if "@import" in raw or "url(http" in raw:
        err("โหลดอะไรจากอินเทอร์เน็ต (@import / url(http…)) — ต้องฝังในไฟล์")

    # scale of details vs favicon size
    if vb:
        try:
            _, _, w, h = [float(x) for x in re.split(r"[\s,]+", vb.strip())]
            base = min(w, h)
            thin = set()
            for el in root.iter():
                sw = el.get("stroke-width")
                if sw and el.get("stroke") not in (None, "none"):
                    try:
                        val = float(re.sub(r"[a-z%]+$", "", sw))
                    except ValueError:
                        continue
                    # at 32px, this stroke would be val * 32 / base px wide
                    if val * 32 / base < 0.75:
                        thin.add(val)
            if thin:
                warn(f"เส้นบางเกิน ({', '.join(f'{v:g}' for v in sorted(thin))}) — ย่อเหลือ 32px จะหายไป "
                     f"(ควรหนาอย่างน้อย {base * 0.75 / 32:.0f})")
        except ValueError:
            err(f"viewBox อ่านไม่ออก: {vb}")

    # count colours
    colours = set(c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", raw))
    if len(colours) > 6:
        warn(f"ใช้สีเยอะ ({len(colours)} สี) — โลโก้ที่ดีส่วนใหญ่ใช้ 2–4 สี")

    # render and look for artwork touching the edge = probably cut off
    clipped = edge_clip(path)
    if clipped:
        err(f"ภาพชนขอบ/ถูกตัด ด้าน{clipped} — ตัวอักษรหรือรูปล้นกรอบ ให้ย่อ/ขยับเข้า "
            f"(text_to_path.py มี --max-width ช่วยได้)")

    size_kb = len(raw.encode()) / 1024
    if size_kb > 200:
        warn(f"ไฟล์ใหญ่ ({size_kb:.0f} KB) — น่าจะมีรายละเอียดเกินจำเป็น")

    if not root.findall(f".//{NS}g[@id]"):
        warn('ไม่มีกลุ่ม <g id="..."> — แก้ทีละส่วนยาก (ควรมี id="icon", id="wordmark")')

    return issues


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    any_error = False
    for p in sys.argv[1:]:
        path = Path(p)
        issues = check(path)
        if not issues:
            print(f"✓ {path.name}  ผ่าน")
            continue
        print(f"• {path.name}")
        for level, msg in issues:
            mark = "✗" if level == "ERROR" else "!"
            print(f"   {mark} {msg}")
            any_error |= level == "ERROR"
    sys.exit(1 if any_error else 0)


if __name__ == "__main__":
    main()
