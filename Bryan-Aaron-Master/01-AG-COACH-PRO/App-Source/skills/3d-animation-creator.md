---
name: 3d-animation-creator
description: >
  Takes a video file (e.g. a product deconstruction/assembly animation, before/after transformation)
  and builds a production-quality website with scroll-driven animation. The video plays forward and
  backward as the user scrolls, creating a mesmerizing Apple-style scroll-stopping effect. Uses
  frame extraction via FFmpeg, canvas-based rendering, and modern scroll-driven techniques. Includes:
  animated starscape background, annotation cards with snap-stop scroll, specs section with count-up
  animations, navbar with scroll-to-pill transform, loader, and full mobile responsiveness. Trigger
  when the user says "3D animation", "scroll-stop build", "scroll animation website", "scroll-driven
  video", "build the scroll-stop site", or provides a video file and asks to make it scroll-controlled.
  Also trigger for "Apple-style scroll animation" or "video on scroll".
---

# 3D Animation Creator — Scroll-Driven Video Websites

You take a video file and build a production-quality website where the video playback is
controlled by scroll position — creating a dramatic, Apple-style scroll-stopping effect.

The user gives you a video. You handle everything: frame extraction, website build, content
population, and serving it locally for preview.

---

## Step 0: The Interview (MANDATORY)

Before touching any code or extracting any frames, ask the user these questions.
Do not skip this step — the whole site is built from these answers.

### Required Questions

Ask these naturally, not as a numbered interrogation:

1. **Brand name** — "What's the brand or product name for this site?"
2. **Logo** — "Do you have a logo file I can use? (SVG or PNG preferred)"
3. **Accent color** — "What's your primary accent color? (hex code, or describe it and I'll suggest options)"
4. **Background color** — "What background color? (dark backgrounds work best for this effect)"
5. **Overall vibe** — "What feel are you going for? (e.g., premium tech launch, luxury, playful, minimal, bold)"

### Content Sourcing

Ask how they want to provide the website content:

- **Option A: From an existing website** — "Share the URL and I'll pull the real content (product name, features, specs, copy)."
- **Option B: Paste it in** — "Paste product descriptions, feature lists, specs, testimonials — whatever you have."

If they provide a URL, use `WebFetch` to retrieve the page and extract relevant copy, product details, features, specs, and any other usable content.

### Optional Sections

Ask whether they want these included:

- **Testimonials** — "Want a testimonials section? Provide them or I'll pull from the URL you shared."
- **Confetti** — "Want a confetti burst effect anywhere? (e.g., on CTA button click)"
- **Card Scanner** — "Want a 3D particle showcase section? (Three.js-based — good for showing off a card, device, or object)"

Only include these if the user explicitly opts in.

---

## Prerequisites

- **FFmpeg** must be installed (`brew install ffmpeg` if not)
- The user provides a video file (MP4, MOV, WebM, etc.)
- Video should be relatively short (3-10 seconds is ideal)
- **The first frame of the video MUST be on a white background.** If it isn't, let the user know and ask for a re-export or a separate white-background hero image.

---

## Design System (Built from User's Answers)

Once the interview is complete, construct the design system:

- **Fonts**: Space Grotesk (headings), Archivo (body), JetBrains Mono (code/mono)
- **Accent color**: From user's answer — used for buttons, glows, progress bars, highlights
- **Background color**: From user's answer — used for body, sections
- **Text colors**: Derived from background — dark bg gets white primary + muted secondary; light bg gets dark primary + muted secondary
- **Selection**: Accent color background with contrasting text
- **Scrollbar**: Dark track with gradient thumb using accent color, glow on hover
- **Cards**: Glass-morphism — semi-transparent bg, subtle border, `backdrop-filter: blur(20px)`, `border-radius: 20px`
- **Buttons**: Primary = accent color bg with contrasting text + accent glow; Secondary = transparent with border
- **Effects**: Floating background orbs (accent color tones, blurred), subtle grid overlay, animated starscape
- **Brand name & logo**: Used in navbar, footer, loader, and anywhere branding appears

---

## The Build Process

### Step 1: Analyze the Video

```bash
ffprobe -v quiet -print_format json -show_streams -show_format "{VIDEO_PATH}"
```

Extract duration, fps, resolution, total frame count. Target 60-150 frames total.

### Step 2: Extract Frames

```bash
mkdir -p "{OUTPUT_DIR}/frames"
ffmpeg -i "{VIDEO_PATH}" -vf "fps={TARGET_FPS},scale=1920:-2" -q:v 2 "{OUTPUT_DIR}/frames/frame_%04d.jpg"
```

Use `-q:v 2` for high quality JPEG. Use JPEG not PNG for smaller files.

### Step 3: Build the Website

Create a single HTML file. The site has these sections (top to bottom):

1. **Starscape** — Fixed canvas behind everything with ~180 twinkling animated stars
2. **Loader** — Full-screen with brand logo, "Loading" text, accent-colored progress bar
3. **Scroll Progress Bar** — Fixed top, accent gradient, 3px tall
4. **Navbar** — Brand logo + name, transforms from full-width to centered pill on scroll
5. **Hero** — Title, subtitle, CTA buttons, scroll hint, background orbs + grid
6. **Scroll Animation** — Sticky canvas with frame sequence, annotation cards with snap-stop
7. **Specs** — Four stat numbers with count-up animation on scroll
8. **Features** — Glass-morphism cards in a grid
9. **CTA** — Call to action section
10. **Testimonials** — *(only if user opted in)* Horizontal drag-to-scroll testimonial cards
11. **Card Scanner** — *(only if user opted in)* Three.js particle showcase
12. **Footer** — Brand name and links

**Reference:** For the exact CSS/JS implementation of every section (structure, styling, JavaScript, mobile
adaptations, and animation patterns), see `references/sections-guide.md`. This file will be created and populated
as a separate artifact once the interview and core build are complete.

### Step 4: Key Implementation Patterns

**Canvas rendering with Retina support:**
```javascript
canvas.width = window.innerWidth * window.devicePixelRatio;
canvas.height = window.innerHeight * window.devicePixelRatio;
canvas.style.width = window.innerWidth + 'px';
canvas.style.height = window.innerHeight + 'px';
```

**Cover-fit drawing (desktop) — zoomed contain-fit (mobile):**
On desktop, use cover-fit so the frame fills edge-to-edge. On mobile, use a slightly zoomed
contain-fit approach so the object stays centered and visible.

**Annotation cards with snap-stop scroll:**
Annotation cards appear at specific scroll progress points (data-show/data-hide attributes).
The scroll FREEZES briefly at each card position — creating a "boom, boom, boom" effect where
each card pops up as you stop. Uses JS-based snap: detects when scroll progress enters a snap zone,
scrolls to the exact position, locks the body overflow for ~600ms, then releases.
The number of annotation cards is flexible — match it to the content the user provides.

**Navbar scroll-to-pill transform:**
The navbar starts full-width, then on scroll shrinks to a centered pill shape (max-width ~820px)
with rounded corners and glass-morphism background.

**Count-up animation:**
Spec numbers animate from 0 to target with easeOutExpo easing, staggered 200ms apart.
Numbers get an accent-color glow pulse while counting. Triggered by IntersectionObserver.

**Animated starscape:**
A fixed canvas behind everything with ~180 stars that slowly drift and twinkle. Each star has
random drift speed, twinkle speed/phase, and opacity. Creates a subtle living background.

### Step 5: Customize Content

All content comes from the interview (Step 0). Use the real brand name, real product details,
and real copy — never use placeholder "Lorem ipsum" text. If content came from a website URL,
use the actual text from that site. Populate:

- Hero title and subtitle
- Annotation card labels, descriptions, and stats
- Spec numbers and labels
- Feature cards
- CTA text
- Testimonials (if included)

### Step 6: Serve & Test

```bash
cd "{OUTPUT_DIR}" && python3 -m http.server 8080
```

Open `http://localhost:8080` and test. Then open the browser URL for the user.

---

## Mobile Responsiveness

Key mobile adaptations:

- **Annotation cards**: Compact single-line design — hide paragraph text, stat numbers, and labels. Show only card number + title in a flex row. Position at bottom of viewport (`bottom: 1.5vh`)
- **Scroll animation height**: `350vh` desktop, `300vh` tablet, `250vh` phone
- **Navbar**: Hide links on mobile, show only logo + pill shape
- **Testimonials** (if included): Touch-scrollable, snap to card edges
- **Feature cards**: Stack to single column
- **Specs**: 2x2 grid on mobile

---

## Best Practices

1. **`requestAnimationFrame` for drawing** — Never draw directly in scroll handler
2. **`{ passive: true }` on scroll listener** — Enables browser scroll optimizations
3. **Canvas with `devicePixelRatio`** — Crisp on Retina displays
4. **Preload all frames before showing** — No pop-in during scroll
5. **Frame deduplication** — Only call `drawFrame` when frame index actually changes
6. **No `scroll-behavior: smooth`** — Would interfere with frame-accurate scroll mapping
7. **No heavy JS libraries** — Pure vanilla JS except Three.js for card scanner (if included)
8. **Sticky canvas** — `position: sticky` keeps canvas viewport-fixed while scroll container moves
9. **White first frame** — The video must start on a clean white background

---

## Error Recovery

| Issue | Solution |
|---|---|
| FFmpeg not installed | Tell user to run `brew install ffmpeg` |
| Frames don't load | Check file paths, ensure local server is running (can't load from `file://`) |
| Animation is choppy | Reduce frame count, ensure JPEG not PNG, check file sizes (<100KB each) |
| Canvas is blurry | Ensure `devicePixelRatio` scaling is applied |
| Scroll feels too fast/slow | Adjust `.scroll-animation` height (200vh=fast, 500vh=slow, 800vh=cinematic) |
| Mobile cards overlap content | Use compact single-line card design, position at `bottom: 1.5vh` |
| Snap-stop feels jarring | Reduce HOLD_DURATION to 400ms or increase SNAP_ZONE |
| Stars too bright/dim | Adjust starscape canvas opacity (default 0.6) |
| First frame isn't white | Ask user to re-export video with white opening frame |
| Video too long (>10s) | Recommend trimming to 3-6 seconds for optimal scroll feel |
