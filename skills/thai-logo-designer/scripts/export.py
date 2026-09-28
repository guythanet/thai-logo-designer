#!/usr/bin/env python3
"""
ส่งออกโลโก้ SVG เป็น PNG หลายขนาด + favicon.ico
Export SVG logos to PNG at standard sizes, keeping the real aspect ratio.

Usage:
  export.py logos/export/logo.svg logos/export/
  export.py logos/export/logo.svg logos/export/ --icon logos/export/icon.svg
  export.py logo.svg out/ --sizes 64,256,1200

Renderer is picked automatically (first one found):
  resvg CLI → rsvg-convert → inkscape → cairosvg (Python)
Override with --renderer.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SIZES = [16, 32, 48, 192, 512, 1024, 2048]
INSTALL_HELP = """ไม่พบโปรแกรมแปลง SVG → PNG / no SVG renderer found. ติดตั้งอย่างใดอย่างหนึ่ง:
  pip install cairosvg              (ง่ายสุด ใช้ได้ทุกเครื่องที่มี Python)
  brew install resvg                (macOS, แม่นยำที่สุด)
  brew install librsvg              (macOS, ได้คำสั่ง rsvg-convert)
  sudo apt install librsvg2-bin     (Linux)"""


def has_cairosvg():
    try:
        import cairosvg  # noqa: F401
        return True
    except Exception:
        return False


def pick_renderer(forced=None):
    options = {
        "resvg": lambda: shutil.which("resvg"),
        "rsvg-convert": lambda: shutil.which("rsvg-convert"),
        "inkscape": lambda: shutil.which("inkscape"),
        "cairosvg": has_cairosvg,
    }
    if forced:
        if not options[forced]():
            sys.exit(f"ไม่พบ {forced}\n\n{INSTALL_HELP}")
        return forced
    for name, check in options.items():
        if check():
            return name
    sys.exit(INSTALL_HELP)


def viewbox_ratio(svg_path: Path) -> float:
    """height / width from the viewBox (or width/height attrs)."""
    head = svg_path.read_text(encoding="utf-8", errors="ignore")[:4000]
    m = re.search(r'viewBox\s*=\s*["\']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', head)
    if m:
        w, h = float(m.group(1)), float(m.group(2))
        return h / w if w else 1.0
    mw = re.search(r'<svg[^>]*\swidth\s*=\s*["\']([\d.]+)', head)
    mh = re.search(r'<svg[^>]*\sheight\s*=\s*["\']([\d.]+)', head)
    if mw and mh:
        return float(mh.group(1)) / float(mw.group(1))
    return 1.0


def render(renderer, src: Path, out: Path, width: int):
    if renderer == "resvg":
        cmd = ["resvg", "--width", str(width), str(src), str(out)]
    elif renderer == "rsvg-convert":
        cmd = ["rsvg-convert", "-w", str(width), "-o", str(out), str(src)]
    elif renderer == "inkscape":
        cmd = ["inkscape", str(src), "--export-type=png",
               f"--export-filename={out}", f"--export-width={width}"]
    else:
        import cairosvg
        cairosvg.svg2png(url=str(src), write_to=str(out), output_width=width)
        return
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{renderer} ล้มเหลว / failed:\n{r.stderr or r.stdout}")


def png_size(path: Path):
    with open(path, "rb") as f:
        head = f.read(24)
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def export_one(renderer, src: Path, out_dir: Path, base: str, sizes):
    ratio = viewbox_ratio(src)
    shape = "สี่เหลี่ยมจัตุรัส" if abs(ratio - 1) < 0.01 else f"แนวนอน {1/ratio:.2f}:1" if ratio < 1 else f"แนวตั้ง 1:{ratio:.2f}"
    print(f"\n{src.name} ({shape})")
    made = []
    for w in sizes:
        out = out_dir / f"{base}-{w}.png"
        render(renderer, src, out, w)
        rw, rh = png_size(out)
        print(f"  ✓ {out.name:18s} {rw}×{rh}")
        made.append(out)
    return made


def make_ico(pngs, out_dir: Path):
    try:
        from PIL import Image
    except ImportError:
        print("  (ข้าม favicon.ico — ต้องมี Pillow: pip install pillow)")
        return
    small = [p for p in pngs if png_size(p)[0] in (16, 32, 48)]
    if not small:
        return
    imgs = [Image.open(p).convert("RGBA") for p in small]
    ico = out_dir / "favicon.ico"
    imgs[-1].save(ico, sizes=[im.size for im in imgs], append_images=imgs[:-1])
    print(f"  ✓ favicon.ico ({', '.join(str(im.size[0]) for im in imgs)}px)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("svg")
    ap.add_argument("out_dir")
    ap.add_argument("--icon", help="ไอคอนสี่เหลี่ยมแยก (สำหรับโลโก้แบบไอคอน+ชื่อ)")
    ap.add_argument("--sizes", help="เช่น 64,256,1200 (ความกว้างเป็น px)")
    ap.add_argument("--renderer", choices=["resvg", "rsvg-convert", "inkscape", "cairosvg"])
    a = ap.parse_args()

    src = Path(a.svg)
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sizes = [int(s) for s in a.sizes.split(",")] if a.sizes else DEFAULT_SIZES
    renderer = pick_renderer(a.renderer)
    print(f"ใช้ / using: {renderer}")

    if src.resolve() != (out_dir / "logo.svg").resolve():
        shutil.copyfile(src, out_dir / "logo.svg")
    logo_pngs = export_one(renderer, src, out_dir, "logo", sizes)

    icon_pngs = []
    if a.icon:
        icon = Path(a.icon)
        if icon.resolve() != (out_dir / "icon.svg").resolve():
            shutil.copyfile(icon, out_dir / "icon.svg")
        icon_pngs = export_one(renderer, icon, out_dir, "icon", sizes)

    # favicon comes from the square icon if we have one, otherwise from a square logo
    fav_source = icon_pngs or (logo_pngs if abs(viewbox_ratio(src) - 1) < 0.01 else [])
    if fav_source:
        make_ico(fav_source, out_dir)
    else:
        print("\n  (ไม่ได้ทำ favicon.ico เพราะโลโก้ไม่ใช่สี่เหลี่ยมจัตุรัส — ใส่ --icon เพื่อสร้าง)")

    print(f"\nเสร็จแล้ว / done → {out_dir}")


if __name__ == "__main__":
    main()
