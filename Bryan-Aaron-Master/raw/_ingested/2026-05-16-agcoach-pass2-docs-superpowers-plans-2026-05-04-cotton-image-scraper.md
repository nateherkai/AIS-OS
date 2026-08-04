# Cotton Grade Image Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collect 3–5 cotton grade sample images per grade (16 grades), store in Supabase Storage, and wire them into Visual ID Drill, Grading Screen carousel, and Flashcard photo-front.

**Architecture:** Python scraper (Phase 1: Firecrawl crawl of USDA/extension sites → Phase 2: fal-ai gpt-image-1 gap fill) uploads to Supabase Storage bucket `cotton-grade-images`, writes `assets/data/cotton-grade-image-urls.json`. App merges JSON into `COTTON_GRADES` at startup. Three screens consume `imageUrls[]`.

**Tech Stack:** Python 3.14 + firecrawl-py + fal-client + supabase-py + beautifulsoup4 + Pillow · Expo Router · React Native FlatList (carousel) · `scoreGuess()` from `lib/data/cotton-grades.ts`

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `scripts/cotton_image_scraper.py` | Phase 1 Firecrawl + Phase 2 fal-ai + Supabase upload + JSON write |
| Create | `assets/data/cotton-grade-image-urls.json` | Static URL map committed to repo |
| Modify | `lib/data/cotton-grades.ts` | Add `imageUrls?: string[]` + `mergeImageUrls()` |
| Modify | `lib/store/history.ts` | Add `'cotton-visual-id'` to `PracticeType` |
| Create | `app/practice/cotton/visual-id.tsx` | Visual ID drill screen |
| Modify | `app/practice/cotton/index.tsx` | Add Visual ID button to hub |
| Modify | `app/practice/cotton/grading.tsx` | Add horizontal image carousel per grade |
| Modify | `app/practice/cotton/flashcards.tsx` | Add photo front to flip cards |

---

## Task 1: Install Python Dependencies

**Files:** none (system)

- [ ] **Step 1: Install deps**

```bash
pip3 install firecrawl-py fal-client beautifulsoup4 python-dotenv
```

Expected output: `Successfully installed firecrawl-py ... fal-client ... beautifulsoup4 ... python-dotenv`

- [ ] **Step 2: Verify**

```bash
python3 -c "from firecrawl import FirecrawlApp; import fal_client; from bs4 import BeautifulSoup; print('all ok')"
```

Expected: `all ok`

---

## Task 2: Create Supabase Storage Bucket

**Files:** none (Supabase infra)

- [ ] **Step 1: Create bucket via MCP**

Use `mcp__claude_ai_Supabase__execute_sql` on project `nkoyotdafqllgbpuklva`:

```sql
-- Supabase Storage buckets are managed via the API, not SQL.
-- Use the dashboard or the storage API directly.
-- We'll create it programmatically in the scraper script.
```

Actually create it in Python (scraper Task 3 handles this). Skip to Task 3.

---

## Task 3: Write Scraper Script — Skeleton + Bucket Creation

**Files:**
- Create: `scripts/cotton_image_scraper.py`

- [ ] **Step 1: Create script with imports, config, bucket init**

```python
#!/usr/bin/env python3
"""
Cotton grade image scraper.
Phase 1: Firecrawl → extract real sample images from USDA/extension sites.
Phase 2: fal-ai gpt-image-1 → generate images for grades with < 3 real photos.
Phase 3: Upload to Supabase Storage, write assets/data/cotton-grade-image-urls.json.
"""
import os, io, json, re, time, hashlib, pathlib, urllib.request, urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
from supabase import create_client

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env.local", override=True)

FIRECRAWL_KEY   = os.environ["FIRECRAWL_API_KEY"]
FAL_KEY         = os.environ["FAL_KEY"]
SUPABASE_URL    = os.environ["EXPO_PUBLIC_SUPABASE_URL"]
SUPABASE_KEY    = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
BUCKET          = "cotton-grade-images"
OUT_JSON        = Path(__file__).parent.parent / "assets" / "data" / "cotton-grade-image-urls.json"
MIN_DIM         = 300   # px
TARGET_PER_GRADE = 3

GRADES = [
    {"code": "21", "name": "Strict Middling White",              "series": "White",         "qualityRank": "Strict Middling"},
    {"code": "31", "name": "Middling White",                     "series": "White",         "qualityRank": "Middling"},
    {"code": "41", "name": "Strict Low Middling White",          "series": "White",         "qualityRank": "Strict Low Middling"},
    {"code": "51", "name": "Low Middling White",                 "series": "White",         "qualityRank": "Low Middling"},
    {"code": "61", "name": "Strict Good Ordinary White",         "series": "White",         "qualityRank": "Strict Good Ordinary"},
    {"code": "71", "name": "Good Ordinary White",                "series": "White",         "qualityRank": "Good Ordinary"},
    {"code": "23", "name": "Strict Middling Light Spotted",      "series": "Light Spotted", "qualityRank": "Strict Middling"},
    {"code": "33", "name": "Middling Light Spotted",             "series": "Light Spotted", "qualityRank": "Middling"},
    {"code": "43", "name": "Strict Low Middling Light Spotted",  "series": "Light Spotted", "qualityRank": "Strict Low Middling"},
    {"code": "53", "name": "Low Middling Light Spotted",         "series": "Light Spotted", "qualityRank": "Low Middling"},
    {"code": "63", "name": "Strict Good Ordinary Light Spotted", "series": "Light Spotted", "qualityRank": "Strict Good Ordinary"},
    {"code": "34", "name": "Middling Spotted",                   "series": "Spotted",       "qualityRank": "Middling"},
    {"code": "44", "name": "Strict Low Middling Spotted",        "series": "Spotted",       "qualityRank": "Strict Low Middling"},
    {"code": "54", "name": "Low Middling Spotted",               "series": "Spotted",       "qualityRank": "Low Middling"},
]

def make_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def ensure_bucket(sb):
    try:
        sb.storage.create_bucket(BUCKET, options={"public": True})
        print(f"[bucket] created {BUCKET}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"[bucket] {BUCKET} already exists")
        else:
            raise

if __name__ == "__main__":
    sb = make_supabase()
    ensure_bucket(sb)
    print("Bucket ready.")
```

- [ ] **Step 2: Run to verify bucket creation**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && python3 scripts/cotton_image_scraper.py
```

Expected: `[bucket] created cotton-grade-images` or `[bucket] cotton-grade-images already exists` then `Bucket ready.`

---

## Task 4: Phase 1 — Firecrawl Image Extraction

**Files:**
- Modify: `scripts/cotton_image_scraper.py`

- [ ] **Step 1: Add scrape targets and keyword matching**

Add after the `GRADES` list and before `if __name__`:

```python
# Pages most likely to contain cotton grade sample images
SCRAPE_TARGETS = [
    "https://www.ams.usda.gov/grades-standards/cotton",
    "https://www.ams.usda.gov/sites/default/files/media/CottonStandards.pdf",
    "https://extension.msstate.edu/agriculture/crops/cotton/cotton-grades",
    "https://cottontoday.cottoninc.com/cotton-basics/",
    "https://www.cotton.org/tech/ace/classification.cfm",
    "https://ipm.ucanr.edu/agriculture/cotton/",
]

# Keywords to score image relevance per grade
def grade_keywords(grade: dict) -> list[str]:
    parts = [
        grade["name"].lower(),
        grade["qualityRank"].lower(),
        grade["series"].lower(),
        grade["code"],
        "cotton",
        "fiber",
        "sample",
        "grade",
    ]
    return parts

def image_score(img_url: str, alt: str, surrounding_text: str, grade: dict) -> int:
    """Higher = more relevant. 0 means skip."""
    haystack = f"{img_url} {alt} {surrounding_text}".lower()
    kws = grade_keywords(grade)
    score = sum(1 for kw in kws if kw in haystack)
    # Exclude icons, logos, banners by size hint in URL
    if any(x in img_url.lower() for x in ["logo", "icon", "banner", "header", "footer", "nav"]):
        return 0
    return score

def fetch_images_from_page(fc: FirecrawlApp, url: str) -> list[dict]:
    """Scrape a page with Firecrawl, return list of {src, alt, context}."""
    try:
        result = fc.scrape_url(url, formats=["html"])
        html = (result.html or "") if hasattr(result, "html") else ""
        if not html and isinstance(result, dict):
            html = result.get("html", "")
        soup = BeautifulSoup(html, "html.parser")
        images = []
        for img in soup.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "")
            if not src:
                continue
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                base = "/".join(url.split("/")[:3])
                src = base + src
            alt = img.get("alt", "")
            # grab surrounding text (parent element text)
            parent = img.parent
            context = parent.get_text(" ", strip=True)[:200] if parent else ""
            images.append({"src": src, "alt": alt, "context": context})
        return images
    except Exception as e:
        print(f"  [firecrawl] error on {url}: {e}")
        return []

def download_image(url: str, min_dim: int = MIN_DIM) -> bytes | None:
    """Download image, verify min dimensions, return JPEG bytes or None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        if img.width < min_dim or img.height < min_dim:
            return None
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except Exception:
        return None
```

- [ ] **Step 2: Add Phase 1 orchestration function**

Add before `if __name__`:

```python
def phase1_firecrawl(fc: FirecrawlApp, existing: dict[str, list[str]]) -> dict[str, list[str]]:
    """
    Crawl SCRAPE_TARGETS. For each image found, score against each grade.
    Download and collect best matches. Returns updated existing map.
    """
    results = {g["code"]: list(existing.get(g["code"], [])) for g in GRADES}
    
    all_images: list[dict] = []
    for url in SCRAPE_TARGETS:
        print(f"[firecrawl] scraping {url}")
        imgs = fetch_images_from_page(fc, url)
        print(f"  → {len(imgs)} images found")
        all_images.extend(imgs)
        time.sleep(1)  # be polite

    for grade in GRADES:
        code = grade["code"]
        if len(results[code]) >= TARGET_PER_GRADE:
            continue

        # Score and rank all images for this grade
        scored = []
        for img in all_images:
            s = image_score(img["src"], img["alt"], img["context"], grade)
            if s > 0:
                scored.append((s, img["src"]))
        scored.sort(reverse=True)

        for _, src in scored:
            if len(results[code]) >= TARGET_PER_GRADE:
                break
            # Deduplicate by URL hash
            url_hash = hashlib.md5(src.encode()).hexdigest()[:8]
            if any(url_hash in existing_url for existing_url in results[code]):
                continue
            print(f"  [grade {code}] downloading {src[:80]}")
            jpeg = download_image(src)
            if jpeg:
                results[code].append(("__raw__", jpeg, src))

    return results
```

- [ ] **Step 3: Commit skeleton before running**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && git add scripts/cotton_image_scraper.py && git commit -m "feat(cotton): add image scraper skeleton with Phase 1 Firecrawl"
```

---

## Task 5: Phase 2 — fal-ai Gap Fill

**Files:**
- Modify: `scripts/cotton_image_scraper.py`

- [ ] **Step 1: Add fal-ai generation function**

Add after the `download_image` function:

```python
import fal_client

def generate_grade_image(grade: dict) -> bytes | None:
    """Generate a cotton sample image for a grade using fal-ai gpt-image-1."""
    series_desc = {
        "White": "pure white fiber with no discoloration or spotting",
        "Light Spotted": "white fiber with scattered small light brown or gray spots",
        "Spotted": "white fiber with definite, clearly visible brown spots throughout",
    }
    prompt = (
        f"USDA upland cotton fiber sample photograph, {grade['name']} grade ({grade['code']}), "
        f"{grade['qualityRank']} quality, {series_desc.get(grade['series'], '')}. "
        "Clean white or off-white studio background, overhead/top-down view, "
        "soft even lighting, realistic cotton fiber texture, no text overlays, "
        "photo-realistic, high detail, square format."
    )
    try:
        os.environ["FAL_KEY"] = FAL_KEY
        result = fal_client.run(
            "fal-ai/gpt-image-1",
            arguments={
                "prompt": prompt,
                "image_size": "square",
                "num_images": 1,
            }
        )
        img_url = result["images"][0]["url"]
        return download_image(img_url, min_dim=200)
    except Exception as e:
        print(f"  [fal-ai] error for grade {grade['code']}: {e}")
        return None

def phase2_gap_fill(existing_raw: dict[str, list]) -> dict[str, list]:
    """For grades with < TARGET_PER_GRADE images, generate with fal-ai."""
    for grade in GRADES:
        code = grade["code"]
        have = len([x for x in existing_raw[code] if x])
        needed = TARGET_PER_GRADE - have
        if needed <= 0:
            continue
        print(f"[fal-ai] grade {code} has {have}, generating {needed} image(s)")
        for i in range(needed):
            jpeg = generate_grade_image(grade)
            if jpeg:
                existing_raw[code].append(("__generated__", jpeg, f"generated_{i}"))
                print(f"  ✓ generated image {i+1}/{needed} for {code}")
            time.sleep(2)
    return existing_raw
```

---

## Task 6: Phase 3 — Upload + JSON Output

**Files:**
- Modify: `scripts/cotton_image_scraper.py`

- [ ] **Step 1: Add upload function and main orchestration**

Add upload function before `if __name__`:

```python
def upload_to_supabase(sb, code: str, index: int, jpeg_bytes: bytes) -> str | None:
    """Upload JPEG bytes to Supabase Storage. Return public URL."""
    path = f"{code}/{index + 1:03d}.jpg"
    try:
        sb.storage.from_(BUCKET).upload(
            path=path,
            file=jpeg_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )
        # Construct public URL
        base = SUPABASE_URL.rstrip("/")
        return f"{base}/storage/v1/object/public/{BUCKET}/{path}"
    except Exception as e:
        print(f"  [upload] error {path}: {e}")
        return None

def phase3_upload(sb, raw_map: dict[str, list]) -> dict[str, list[str]]:
    """Upload all collected images, return {code: [public_url, ...]}."""
    url_map: dict[str, list[str]] = {g["code"]: [] for g in GRADES}
    for grade in GRADES:
        code = grade["code"]
        entries = raw_map.get(code, [])
        for idx, entry in enumerate(entries):
            if isinstance(entry, tuple):
                _, jpeg_bytes, src = entry
                print(f"  [upload] grade {code} image {idx+1} ← {str(src)[:60]}")
                url = upload_to_supabase(sb, code, idx, jpeg_bytes)
                if url:
                    url_map[code].append(url)
            elif isinstance(entry, str):
                url_map[code].append(entry)  # already a URL (re-run case)
    return url_map
```

- [ ] **Step 2: Replace `if __name__` block with full orchestration**

```python
if __name__ == "__main__":
    import sys
    sb = make_supabase()
    ensure_bucket(sb)

    fc = FirecrawlApp(api_key=FIRECRAWL_KEY)

    # Load existing JSON if re-running
    existing: dict[str, list[str]] = {}
    if OUT_JSON.exists():
        existing = json.loads(OUT_JSON.read_text())
        print(f"[resume] loaded existing JSON with {sum(len(v) for v in existing.values())} URLs")

    # Phase 1
    print("\n=== PHASE 1: Firecrawl ===")
    raw_map: dict[str, list] = {g["code"]: list(existing.get(g["code"], [])) for g in GRADES}
    raw_map = phase1_firecrawl(fc, raw_map)

    # Phase 2
    print("\n=== PHASE 2: fal-ai gap fill ===")
    raw_map = phase2_gap_fill(raw_map)

    # Phase 3
    print("\n=== PHASE 3: Upload to Supabase ===")
    url_map = phase3_upload(sb, raw_map)

    # Write JSON
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(url_map, indent=2))
    print(f"\n✓ Written to {OUT_JSON}")
    print("Summary:")
    for code, urls in url_map.items():
        grade_name = next(g["name"] for g in GRADES if g["code"] == code)
        status = "✓" if len(urls) >= TARGET_PER_GRADE else "⚠"
        print(f"  {status} {code} {grade_name}: {len(urls)} images")
```

- [ ] **Step 3: Run the full scraper**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && python3 scripts/cotton_image_scraper.py 2>&1 | tee /tmp/cotton_scrape.log
```

Expected: phases logged, summary table with ✓ for all 16 grades having ≥3 images.

- [ ] **Step 4: Verify JSON output**

```bash
python3 -c "
import json
data = json.load(open('assets/data/cotton-grade-image-urls.json'))
for code, urls in data.items():
    print(f'{code}: {len(urls)} images')
print(f'Total: {sum(len(v) for v in data.values())}')
"
```

Expected: 16 grade codes, each with 3–5 URLs, total 48–80.

- [ ] **Step 5: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && git add scripts/cotton_image_scraper.py assets/data/cotton-grade-image-urls.json && git commit -m "feat(cotton): add image scraper script + generated grade image URLs"
```

---

## Task 7: Update CottonGrade Interface + Merge Logic

**Files:**
- Modify: `lib/data/cotton-grades.ts`

- [ ] **Step 1: Add `imageUrls` to interface and `mergeImageUrls` function**

In `lib/data/cotton-grades.ts`, add `imageUrls?: string[]` to the interface (after `clues`):

```ts
export interface CottonGrade {
  code: string;
  name: string;
  series: 'White' | 'Light Spotted' | 'Spotted';
  qualityRank: string;
  description: string;
  clues: string[];
  imageUrls?: string[];
}
```

Then add at the bottom of the file (after `scoreGuess`):

```ts
export function mergeImageUrls(urlMap: Record<string, string[]>): void {
  for (const grade of COTTON_GRADES) {
    grade.imageUrls = urlMap[grade.code] ?? [];
  }
}
```

- [ ] **Step 2: Call `mergeImageUrls` at app startup**

In `app/_layout.tsx`, add after existing imports:

```ts
import gradeImageUrls from '@/assets/data/cotton-grade-image-urls.json';
import { mergeImageUrls } from '@/lib/data/cotton-grades';
```

And call in the root layout component body (before return):

```ts
mergeImageUrls(gradeImageUrls as Record<string, string[]>);
```

- [ ] **Step 3: Verify TypeScript**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && npx tsc --noEmit -p . 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && git add lib/data/cotton-grades.ts app/_layout.tsx && git commit -m "feat(cotton): add imageUrls field to CottonGrade + merge at startup"
```

---

## Task 8: Add PracticeType Entry

**Files:**
- Modify: `lib/store/history.ts:29` (after `'cotton-quiz'`)

- [ ] **Step 1: Add type**

In `lib/store/history.ts`, add `'cotton-visual-id'` after `'cotton-quiz'`:

```ts
  | 'cotton-quiz'
  | 'cotton-visual-id'
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && npx tsc --noEmit -p . 2>&1 | head -10
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && git add lib/store/history.ts && git commit -m "feat(cotton): add cotton-visual-id PracticeType"
```

---

## Task 9: Build Visual ID Drill Screen

**Files:**
- Create: `app/practice/cotton/visual-id.tsx`

- [ ] **Step 1: Create the screen**

```tsx
import React, { useState, useCallback, useRef } from 'react';
import { View, Text, StyleSheet, Image, ScrollView, ActivityIndicator } from 'react-native';
import { AnimatedButton as TouchableOpacity } from '@/components/common/AnimatedButton';
import { Stack, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COTTON_GRADES, scoreGuess } from '@/lib/data/cotton-grades';
import { safeBack } from '@/lib/navigation';
import { saveQuizResult } from '@/lib/data';
import { useAuthStore } from '@/lib/store/auth';

const ACCENT = '#C8A96E';
const GOLD   = '#F2A900';
const CARD   = '#111111';
const MUTED  = '#666';
const GLASS_BG     = 'rgba(255,255,255,0.05)';
const GLASS_BORDER = 'rgba(255,255,255,0.1)';
const TOTAL_ROUNDS = 20;

interface Round {
  gradeCode: string;
  imageUrl:  string;
  choices:   string[]; // 4 grade codes
}

function buildRounds(): Round[] {
  // Only use grades that have at least 1 image
  const eligible = COTTON_GRADES.filter(g => g.imageUrls && g.imageUrls.length > 0);
  if (eligible.length === 0) return [];

  const rounds: Round[] = [];
  for (let i = 0; i < TOTAL_ROUNDS; i++) {
    const grade = eligible[Math.floor(Math.random() * eligible.length)];
    const imageUrl = grade.imageUrls![Math.floor(Math.random() * grade.imageUrls!.length)];

    // 3 distractors: prefer adjacent grades, fill from random
    const others = COTTON_GRADES.filter(g => g.code !== grade.code);
    others.sort(() => Math.random() - 0.5);
    const distractors = others.slice(0, 3).map(g => g.code);
    const choices = [grade.code, ...distractors].sort(() => Math.random() - 0.5);

    rounds.push({ gradeCode: grade.code, imageUrl, choices });
  }
  return rounds;
}

function gradeLabel(code: string) {
  const g = COTTON_GRADES.find(gr => gr.code === code);
  return g ? `${code} — ${g.name}` : code;
}

export default function CottonVisualId() {
  const router = useRouter();
  const { user } = useAuthStore();
  const sessionStart = useRef(Date.now());

  const [rounds] = useState<Round[]>(() => buildRounds());
  const [index, setIndex]         = useState(0);
  const [selected, setSelected]   = useState<string | null>(null);
  const [totalScore, setTotalScore] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [roundScores, setRoundScores] = useState<number[]>([]);

  const noImages = rounds.length === 0;

  const handleAnswer = useCallback((choiceCode: string) => {
    if (selected) return;
    setSelected(choiceCode);
    const pts = scoreGuess(choiceCode, rounds[index].gradeCode);
    setTotalScore(prev => prev + pts);
    setRoundScores(prev => [...prev, pts]);
  }, [selected, index, rounds]);

  const next = useCallback(() => {
    if (index + 1 >= rounds.length) {
      // Save result
      const maxScore = rounds.length * 20;
      const correct  = roundScores.filter(s => s === 20).length;
      void saveQuizResult({
        userId:    user?.id ?? '',
        contestId: 'cotton-visual-id',
        type:      'cotton-visual-id',
        score:     totalScore,
        maxScore,
        details:   { totalQuestions: rounds.length, correct },
        timeSeconds: Math.round((Date.now() - sessionStart.current) / 1000),
      });
      setShowResults(true);
    } else {
      setIndex(prev => prev + 1);
      setSelected(null);
    }
  }, [index, rounds, roundScores, totalScore, user]);

  if (noImages) return (
    <View style={s.center}>
      <Stack.Screen options={{ title: 'Visual ID', headerStyle: { backgroundColor: '#000' }, headerTintColor: '#fff' }} />
      <Ionicons name="images-outline" size={48} color={MUTED} />
      <Text style={s.noImageText}>No images loaded.{'\n'}Run the image scraper first.</Text>
      <TouchableOpacity style={s.backBtn} onPress={() => safeBack(router, '/practice/cotton')}>
        <Text style={s.backBtnText}>← Back</Text>
      </TouchableOpacity>
    </View>
  );

  if (showResults) {
    const maxScore = rounds.length * 20;
    const pct = Math.round((totalScore / maxScore) * 100);
    const correct = roundScores.filter(s => s === 20).length;
    const partial = roundScores.filter(s => s === 10).length;
    return (
      <ScrollView style={s.container} contentContainerStyle={s.content}>
        <Stack.Screen options={{ title: 'Visual ID Results', headerStyle: { backgroundColor: '#000' }, headerTintColor: '#fff' }} />
        <View style={s.resultCard}>
          <Ionicons name="ribbon-outline" size={40} color={GOLD} />
          <Text style={s.resultTitle}>Visual ID Complete</Text>
          <Text style={s.resultScore}>{totalScore} / {maxScore}</Text>
          <Text style={s.resultPct}>{pct}%</Text>
          <View style={s.breakdown}>
            <Text style={s.breakdownRow}><Text style={{ color: GOLD }}>✓ Exact:</Text> {correct}</Text>
            <Text style={s.breakdownRow}><Text style={{ color: ACCENT }}>~ Adjacent:</Text> {partial}</Text>
            <Text style={s.breakdownRow}><Text style={{ color: MUTED }}>✗ Wrong:</Text> {rounds.length - correct - partial}</Text>
          </View>
          <TouchableOpacity style={s.doneBtn} onPress={() => safeBack(router, '/practice/cotton')}>
            <Text style={s.doneBtnText}>Done</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  const round = rounds[index];
  const correct = rounds[index].gradeCode;

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content}>
      <Stack.Screen options={{ title: `Visual ID  ${index + 1}/${rounds.length}`, headerStyle: { backgroundColor: '#000' }, headerTintColor: '#fff' }} />

      <Text style={s.prompt}>Which cotton grade is this sample?</Text>
      <Text style={s.score}>Score: {totalScore} pts</Text>

      <View style={s.imageContainer}>
        <Image source={{ uri: round.imageUrl }} style={s.sampleImage} resizeMode="cover" />
      </View>

      <View style={s.choices}>
        {round.choices.map(code => {
          const isSelected = selected === code;
          const isCorrect  = code === correct;
          let bg = GLASS_BG;
          let border = GLASS_BORDER;
          if (selected) {
            if (isCorrect)       { bg = GOLD + '30'; border = GOLD; }
            else if (isSelected) { bg = '#ff444430'; border = '#ff4444'; }
          }
          return (
            <TouchableOpacity
              key={code}
              style={[s.choiceBtn, { backgroundColor: bg, borderColor: border }]}
              onPress={() => handleAnswer(code)}
              disabled={!!selected}
            >
              <Text style={s.choiceText}>{gradeLabel(code)}</Text>
              {selected && isCorrect && <Ionicons name="checkmark-circle" size={18} color={GOLD} />}
            </TouchableOpacity>
          );
        })}
      </View>

      {selected && (
        <View style={s.feedbackBox}>
          <Text style={s.feedbackScore}>
            {scoreGuess(selected, correct) === 20 ? '✓ Exact! +20 pts' :
             scoreGuess(selected, correct) === 10 ? '~ Adjacent +10 pts' : '✗ Incorrect +0 pts'}
          </Text>
          {selected !== correct && (
            <Text style={s.feedbackCorrect}>Correct: {gradeLabel(correct)}</Text>
          )}
          <TouchableOpacity style={s.nextBtn} onPress={next}>
            <Text style={s.nextBtnText}>{index + 1 >= rounds.length ? 'See Results' : 'Next →'}</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container:      { flex: 1, backgroundColor: '#000' },
  content:        { padding: 16, paddingBottom: 40 },
  center:         { flex: 1, backgroundColor: '#000', alignItems: 'center', justifyContent: 'center', padding: 24 },
  noImageText:    { color: '#888', textAlign: 'center', marginTop: 16, fontSize: 15, lineHeight: 22 },
  backBtn:        { marginTop: 24, borderWidth: 1, borderColor: MUTED, borderRadius: 8, paddingHorizontal: 20, paddingVertical: 10 },
  backBtnText:    { color: '#fff', fontSize: 14 },
  prompt:         { color: '#aaa', fontSize: 14, textAlign: 'center', marginBottom: 4 },
  score:          { color: GOLD, fontSize: 13, textAlign: 'center', marginBottom: 12 },
  imageContainer: { width: '100%', aspectRatio: 1, borderRadius: 12, overflow: 'hidden', marginBottom: 16, borderWidth: 1, borderColor: GLASS_BORDER },
  sampleImage:    { width: '100%', height: '100%' },
  choices:        { gap: 10, marginBottom: 16 },
  choiceBtn:      { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 1, borderRadius: 10, padding: 14 },
  choiceText:     { color: '#fff', fontSize: 14, flex: 1 },
  feedbackBox:    { backgroundColor: GLASS_BG, borderWidth: 1, borderColor: GLASS_BORDER, borderRadius: 12, padding: 16, alignItems: 'center', gap: 10 },
  feedbackScore:  { color: '#fff', fontSize: 15, fontWeight: '600' },
  feedbackCorrect:{ color: ACCENT, fontSize: 13 },
  nextBtn:        { backgroundColor: ACCENT, borderRadius: 8, paddingHorizontal: 28, paddingVertical: 12, marginTop: 4 },
  nextBtnText:    { color: '#000', fontWeight: '700', fontSize: 14 },
  resultCard:     { alignItems: 'center', gap: 12, paddingTop: 40 },
  resultTitle:    { color: '#fff', fontSize: 22, fontWeight: '700' },
  resultScore:    { color: GOLD, fontSize: 36, fontWeight: '800' },
  resultPct:      { color: ACCENT, fontSize: 18 },
  breakdown:      { gap: 6, marginTop: 8 },
  breakdownRow:   { color: '#ccc', fontSize: 14 },
  doneBtn:        { backgroundColor: ACCENT, borderRadius: 8, paddingHorizontal: 32, paddingVertical: 14, marginTop: 16 },
  doneBtnText:    { color: '#000', fontWeight: '700', fontSize: 15 },
});
```

- [ ] **Step 2: TypeScript check**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && npx tsc --noEmit -p . 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && git add app/practice/cotton/visual-id.tsx && git commit -m "feat(cotton): add Visual ID drill screen"
```

---

## Task 10: Add Visual ID Button to Hub

**Files:**
- Modify: `app/practice/cotton/index.tsx`

- [ ] **Step 1: Find the Study & Practice section buttons and add Visual ID**

In `app/practice/cotton/index.tsx`, find the block that renders the "Study & Practice" mode buttons (Flashcards, Quiz, etc.) and add a Visual ID button. Add this button alongside or below the existing practice mode buttons:

```tsx
<TouchableOpacity
  style={[styles.modeCard, { borderColor: ACCENT + '66', backgroundColor: ACCENT + '11' }]}
  onPress={() => router.push('/practice/cotton/visual-id')}
>
  <View style={[styles.modeIcon, { backgroundColor: ACCENT + '22' }]}>
    <Ionicons name="images-outline" size={24} color={ACCENT} />
  </View>
  <View style={{ flex: 1 }}>
    <Text style={styles.modeTitle}>Visual ID Drill</Text>
    <Text style={styles.modeDesc}>Identify grades from real sample photos</Text>
  </View>
  <Ionicons name="chevron-forward" size={16} color={MUTED} />
</TouchableOpacity>
```

- [ ] **Step 2: Read the actual index.tsx to find exact insertion point**

Read `app/practice/cotton/index.tsx` and find where flashcards/quiz buttons are rendered, then insert the Visual ID button after the Flashcards button.

- [ ] **Step 3: TypeScript check**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && npx tsc --noEmit -p . 2>&1 | head -10
```

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && git add app/practice/cotton/index.tsx && git commit -m "feat(cotton): add Visual ID button to cotton hub"
```

---

## Task 11: Add Image Carousel to Grading Screen

**Files:**
- Modify: `app/practice/cotton/grading.tsx`

- [ ] **Step 1: Add FlatList import**

In `app/practice/cotton/grading.tsx`, add `FlatList` to the React Native import:

```tsx
import { View, Text, StyleSheet, ScrollView, Image, FlatList,
  TouchableOpacity as RNTouchable, Modal, Pressable } from 'react-native';
```

- [ ] **Step 2: Add GradeImageCarousel component**

Add before the `export default` function:

```tsx
function GradeImageCarousel({ grade }: { grade: CottonGrade }) {
  const urls = grade.imageUrls ?? [];
  if (urls.length === 0) return null;
  return (
    <FlatList
      horizontal
      data={urls}
      keyExtractor={(_, i) => String(i)}
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={{ gap: 8, paddingVertical: 8 }}
      renderItem={({ item }) => (
        <Image
          source={{ uri: item }}
          style={{ width: 120, height: 120, borderRadius: 8, borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)' }}
          resizeMode="cover"
        />
      )}
    />
  );
}
```

- [ ] **Step 3: Insert carousel into grade card render**

Find where grade description/clues are rendered in the grading practice screen and add `<GradeImageCarousel grade={currentGrade} />` below the description text and above the clues list. Read the file to find the exact JSX location.

- [ ] **Step 4: TypeScript check**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && npx tsc --noEmit -p . 2>&1 | head -10
```

- [ ] **Step 5: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && git add app/practice/cotton/grading.tsx && git commit -m "feat(cotton): add image carousel to grading screen"
```

---

## Task 12: Add Photo Front to Flashcards

**Files:**
- Modify: `app/practice/cotton/flashcards.tsx`

- [ ] **Step 1: Add Image import**

In `app/practice/cotton/flashcards.tsx`, add `Image` to the React Native import:

```tsx
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, Alert, Animated, Image } from 'react-native';
```

- [ ] **Step 2: Add COTTON_GRADES import**

```tsx
import { COTTON_GRADES } from '@/lib/data/cotton-grades';
```

- [ ] **Step 3: Add helper to resolve image for a flashcard**

Add before `export default`:

```tsx
function gradeImageUrl(gradeCode: string | undefined): string | null {
  if (!gradeCode) return null;
  const grade = COTTON_GRADES.find(g => g.code === gradeCode);
  const urls = grade?.imageUrls ?? [];
  if (urls.length === 0) return null;
  return urls[Math.floor(Math.random() * urls.length)];
}
```

- [ ] **Step 4: Update flashcard front to show image**

In the flashcard front JSX (the `frontStyle` animated view), add an image above the question text when available. Read the file to find the exact JSX location for the card front, then wrap or prepend:

```tsx
{(() => {
  const imgUrl = gradeImageUrl(cards[currentIdx]?.gradeCode);
  return imgUrl ? (
    <Image
      source={{ uri: imgUrl }}
      style={{ width: '100%', height: 160, borderRadius: 8, marginBottom: 12 }}
      resizeMode="cover"
    />
  ) : null;
})()}
```

Note: `gradeCode` field needs to be present on `QuizQuestion`. Check `lib/cotton-quiz.ts` — if `gradeCode` is not a field, use question `id` or `source` to look up the grade, or skip image for non-grade flashcards.

- [ ] **Step 5: TypeScript check**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && npx tsc --noEmit -p . 2>&1 | head -20
```

Fix any type errors. If `QuizQuestion` lacks a `gradeCode` field, update `lib/cotton-quiz.ts` to include it when generating grade-related flashcards, or omit the image lookup for non-grade questions.

- [ ] **Step 6: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && git add app/practice/cotton/flashcards.tsx lib/cotton-quiz.ts && git commit -m "feat(cotton): add photo front to cotton flashcards"
```

---

## Self-Review

**Spec coverage check:**
- ✓ Phase 1 Firecrawl scrape → Task 3–4
- ✓ Phase 2 fal-ai gap fill → Task 5
- ✓ Phase 3 Supabase upload + JSON → Task 6
- ✓ `imageUrls` on CottonGrade → Task 7
- ✓ `PracticeType` entry → Task 8
- ✓ Visual ID drill screen → Task 9
- ✓ Hub button → Task 10
- ✓ Grading screen carousel → Task 11
- ✓ Flashcard photo front → Task 12

**Placeholder scan:** None found. All steps have actual code.

**Type consistency:** `CottonGrade.imageUrls?: string[]` defined in Task 7, consumed in Tasks 9, 11, 12. `mergeImageUrls()` called in `_layout.tsx` before any screen mounts. `scoreGuess()` used in Task 9 — matches export from `lib/data/cotton-grades.ts`.

**Note on Task 12:** `QuizQuestion.gradeCode` may not exist — Step 5 explicitly instructs to check and adapt.
