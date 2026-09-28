---
name: thai-logo-designer
description: Design logos as SVG through a short interview, several distinct concepts, round-by-round refinement, and PNG/favicon export — with correct Thai text (vowels and tone marks placed properly) by converting all lettering to paths. Use this skill whenever the user asks to create, design, redesign or iterate on a logo, icon, app icon, favicon, wordmark, brand mark or ตราสัญลักษณ์/โลโก้ — in Thai or English, with or without Thai text — even if they only say "ทำโลโก้ให้หน่อย" or "make me an icon".
---

# Thai Logo Designer

Design logos as hand-written SVG, refine them with the user, and export clean files.
The key difference from generic logo skills: **every piece of lettering becomes a `<path>`**
via `scripts/text_to_path.py`, which uses HarfBuzz shaping. Plain SVG `<text>` breaks Thai
(floating or colliding สระ/วรรณยุกต์, tofu boxes) and depends on fonts the viewer may not have.

Talk to the user in their language (Thai if they write Thai). Keep explanations plain and short.

## Setup (once per session)

```bash
pip install uharfbuzz fonttools cairosvg pillow   # add --break-system-packages if pip refuses
```

`SKILL_DIR` below means the folder this file lives in. Scripts:

| Script | What it does |
|---|---|
| `scripts/text_to_path.py` | Text → SVG path (Thai-safe). Bundled fonts: `--list-fonts` |
| `scripts/check_svg.py` | Finds problems: Thai in `<text>`, artwork cut off at the edge, thin strokes, missing viewBox, external links |
| `scripts/preview.py` | Builds `logos/preview.html` comparing all versions + 64/32/16px strip |
| `scripts/export.py` | PNGs at 16–2048px keeping true aspect ratio, plus `favicon.ico` |

## Phase 1 — Interview

If the user points at a project, website or brand material, look at it first (name, purpose,
existing colours, fonts, tone) and summarise what you found, so you only ask what's missing.

Then ask what's still unknown — at most one round, batched. Use a tappable-options /
ask-user tool if one is available; otherwise ask in one short message.

1. **Format** — icon only (square) · wordmark only · icon + name (combination)
2. **Name language** — Thai · English · both (and exact spelling)
3. **Feel** — minimal/geometric · friendly/rounded · bold/corporate · traditional Thai touch
4. **Colours** — their brand colours · you choose

If they say "just make something", use: combination mark, their stated name, minimal, you choose colours.

## Design rules (apply to every SVG)

- `viewBox` only, no fixed width/height. Icons `0 0 512 512`; wordmark/combination `0 0 1024 512`
  Always pass `--max-width` to `text_to_path.py` (the space actually available for that line);
  it shrinks the size to fit instead of letting the name run off the edge.
- **No `<text>` in anything shown to the user as a candidate.** Generate lettering with
  `text_to_path.py` and paste the returned `<g>` in. It prints `width`, `ascent`, `descent` —
  use them to centre and size things instead of guessing.
- Thai needs vertical room: marks above (ั ิ ี ่ ้ ๊ ๋) and below (ุ ู) extend past the letter body.
  Leave headroom equal to the printed ascent above the baseline and descent below it.
  Don't crop, overlap, or tightly box Thai lettering.
- Self-contained: no external images, fonts, or links. Gradients only if the style asks for them.
- Group parts with ids: `<g id="icon">`, `<g id="wordmark">`, `<g id="tagline">` — makes
  "make the icon bigger" a one-group edit.
- Must survive 32px: solid shapes over fine lines, stroke-width ≥ ~6 in a 512 box, few details.
  2–4 colours is usually right.
- Start each SVG with a one-line comment describing the idea — the preview shows it as a caption:
  `<!-- concept-2: rice grain forming a leaf, Kanit Bold -->`

### Choosing a bundled font

| key | character | good for |
|---|---|---|
| `kanit-bold` | modern, geometric, loopless (ไม่มีหัว), strong | tech, food brands, startups |
| `kanit-regular` | same, lighter | taglines |
| `prompt-bold` | round, friendly, loopless | consumer apps, kids, cafés |
| `plex-thai-bold` | clean, corporate, very readable small | enterprise, finance, government |
| `plex-thai-regular` | same, lighter | taglines, small text |

These fonts also contain Latin, so mixed Thai–English names work in one call.
A user-supplied `.ttf/.otf` path also works — prefer it if they have a brand font.

Example:
```bash
python3 $SKILL_DIR/scripts/text_to_path.py "ข้าวหอม" --font kanit-bold --size 150 \
  --x 512 --y 330 --anchor middle --max-width 900 --fill "#1B5E20" --id wordmark
```

## Phase 2 — Explore

Make **3–5 genuinely different** concepts: vary the core idea (letterform, symbol, mascot,
badge/emblem, abstract), not just colours. Write them to `logos/concepts/concept-N.svg`.

- If you can run sub-agents in parallel (e.g. Claude Code's Task tool), give each one the full
  brief, these design rules, the text_to_path command to use, one creative direction, and its
  output path. They don't share context — include everything.
- Otherwise write them one after another yourself.

Then:
```bash
python3 $SKILL_DIR/scripts/check_svg.py logos/concepts/*.svg
python3 $SKILL_DIR/scripts/preview.py logos/concepts
```
Fix any ✗ ERROR before showing. Show the concepts (open/present `logos/preview.html`, or
display the SVGs inline if the interface can render them), give each a one-line description,
and ask which direction to push — or what they like/dislike across them.

## Phase 3 — Refine

- Save every change as a new file: `logos/iterations/iteration-1.svg`, `-2`, … Never overwrite —
  the user may say "go back to 3".
- Specific feedback ("ตัวอักษรใหญ่ขึ้น", "เปลี่ยนเขียวเป็นน้ำเงิน") → one new iteration.
- Open-ended ("ลองหลาย ๆ โทนสี") → 3–5 variations at once (parallel if possible), each a new file.
- Keep group ids consistent between iterations.
- For combination marks, also keep a square icon-only version at
  `logos/icons/iteration-N.svg` (same filename) so the small-size check is meaningful.
- After each round:
  ```bash
  python3 $SKILL_DIR/scripts/check_svg.py logos/iterations/iteration-N.svg
  python3 $SKILL_DIR/scripts/preview.py logos/iterations --icons logos/icons
  ```
  Say in one or two lines what changed. If the 16/32px strip shows mush, say so and suggest
  what to remove or thicken — that saves rounds.

## Phase 4 — Export

When the user is happy ("เอาอันนี้", "export", "this is the one"), confirm which iteration, then:

```bash
mkdir -p logos/export
cp logos/iterations/iteration-N.svg logos/export/logo.svg
# combination mark: also the square icon
cp logos/icons/iteration-N.svg logos/export/icon.svg
python3 $SKILL_DIR/scripts/check_svg.py logos/export/*.svg
python3 $SKILL_DIR/scripts/export.py logos/export/logo.svg logos/export/ --icon logos/export/icon.svg
```
(Drop `--icon` for an icon-only logo — the favicon is made from the logo itself.)

Output: `logo.svg`, `logo-{16…2048}.png` (true aspect ratio), `icon.svg`, `icon-{…}.png`,
`favicon.ico`. Hand over the folder (present the files if the interface supports it) and
list which file to use where: `logo.svg` for web/print, `icon-512.png` for app stores and
social avatars, `favicon.ico` for websites, `logo-2048.png` for slides.

## Troubleshooting

- **"No SVG renderer found"** → `pip install cairosvg` works everywhere; `resvg` is the most
  accurate if installed.
- **Thai looks wrong in the PNG** → there's still a `<text>` element; `check_svg.py` will flag it.
- **Lettering is off-centre** → use `--anchor middle` with `--x` at the centre, and place `--y`
  at the baseline, not the top.
