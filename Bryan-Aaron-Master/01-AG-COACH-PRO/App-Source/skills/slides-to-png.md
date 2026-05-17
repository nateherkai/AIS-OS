---
name: slides-to-png
description: Converts slide decks into individual PNG image files — one PNG per slide. Use this skill whenever the user wants to export, extract, convert, or save slides as images, PNGs, or pictures. Triggers include any mention of "slides to images", "export slides as PNG", "convert PowerPoint to images", "save each slide as a picture", "upload slides to app", or any request to turn a presentation file into image files. Supports .pptx (PowerPoint) and .pdf input formats. Google Slides users should first download as .pptx or .pdf. Always use this skill when the user uploads a presentation file and wants image output.
---

# Slides to PNG Skill

Converts slide deck files into individual PNG images (one per slide), ready for upload into apps, websites, or other tools.

## Supported Input Formats

| Format | Notes |
|--------|-------|
| `.pptx` | PowerPoint — converted via LibreOffice → PDF → PNG |
| `.pdf` | Direct render — skips the LibreOffice step |
| Google Slides | Download first: **File → Download → PowerPoint (.pptx)** or **PDF** |

---

## Workflow (Mac / Local)

### Step 1 — Identify the input file

```bash
ls "path/to/file.pdf"
```

### Step 2 — Run pdftoppm directly (fastest on Mac)

```bash
mkdir -p /tmp/slide_pngs
pdftoppm -r 150 -png "path/to/file.pdf" /tmp/slide_pngs/slide
ls -lh /tmp/slide_pngs/
```

Output will be `slide-01.png`, `slide-02.png`, etc.

**DPI guide:**
- `150` — Default. Good for app uploads, fast to generate.
- `200` — Sharper. Good for larger display sizes.
- `300` — High-res. Use for print or zoom-heavy viewing.

### Step 3 — Copy to destination

**IMPORTANT:** `pdftoppm -png` produces PNG files. If the destination folder uses `.jpg` filenames, you MUST convert to real JPEG first — Metro bundler breaks if the file extension doesn't match the actual format.

**If destination uses `.png` extension** (copy directly):
```bash
cp /tmp/slide_pngs/*.png "assets/images/target-folder/"
```

**If destination uses `.jpg` extension** (convert first):
```bash
python3 -c "
from PIL import Image
import glob, os
dest = 'assets/images/livestock/target-folder'
for i, src in enumerate(sorted(glob.glob('/tmp/slide_pngs/*.png')), 1):
    img = Image.open(src).convert('RGB')
    img.save(f'{dest}/slide-{i:02d}.jpg', 'JPEG', quality=88)
    print(f'slide-{i:02d}.jpg')
"
```

### Step 4 — Rename to convention (if needed)

Following project naming conventions:
- Cattle Balance: `cb1.png`, `cb2.png`, ...
- Cattle EPD: `cepd1.png`, `cepd2.png`, ...
- Cattle Muscle: `cm1.png`, `cm2.png`, ...
- EPD slide decks: `slide-01.jpg`, `slide-02.jpg`, ... (use JPEG conversion above)

```bash
for i in $(seq 1 N); do
  padded=$(printf "%02d" $i)
  cp "/tmp/slide_pngs/slide-${padded}.png" "assets/images/livestock/target-folder/prefix${i}.png"
done
```

---

## Alternative: Python Script

For `.pptx` files or when pdftoppm isn't available, use `skills/scripts/slides_to_png.py`:

```bash
python3 skills/scripts/slides_to_png.py your_file.pptx --out /tmp/slide_pngs --dpi 150
python3 skills/scripts/slides_to_png.py handout.pdf --out /tmp/slide_pngs --dpi 200
```

**Note:** Requires Python 3.10+ due to union type syntax. On Python 3.9, use `pdftoppm` directly.

---

## Dependencies

```bash
# Install via Homebrew (one-time)
brew install poppler        # provides pdftoppm for PDF → PNG
brew install libreoffice    # only needed for .pptx input
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Python script fails with `TypeError: unsupported operand type(s) for \|` | Use `pdftoppm` directly (requires Python 3.10+) |
| LibreOffice fails on `.pptx` | Download as PDF from Google Slides instead |
| Blank/white slides | Font substitution issue — use PDF export from original app |
| Wrong slide count | Check that the source file isn't password-protected |
| Low image quality | Increase `--dpi` to `200` or `300` |
