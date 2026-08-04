---
name: anatomy-alignment
description: Provides a rigorous workflow for verifying and correcting anatomical marker alignment in the Livestock Anatomy module. Use this skill whenever markers appear misaligned or when image dimensions change.
---

# Anatomy Alignment Skill

## When to use this skill
- When anatomical markers (dots) do not align with physical anatomical features in photography.
- After making changes to image display sizes or aspect ratios.
- After adding new anatomical parts or images.

## Core Concepts
- **Standardized Grid**: Markers use a percentage-based (0-100) coordinate system.
- **Aspect Ratio Locking**: For bulletproof alignment, images MUST be displayed in a container with a fixed aspect ratio (e.g., 3:2) using `resizeMode: "stretch"`.
- **Anatomy Anchors**:
  - Cattle: Side profile, facing LEFT.
  - Head: ~10-20% X
  - Tail: ~90-95% X
  - Topline: ~25-35% Y
  - Ground: ~95-100% Y

## Verification Workflow

### Step 1: Local Environment Setup
1. Start the development server (`npm run dev`).
2. Ensure the `browser_subagent` can access the local instance.

### Step 2: Visual Inspection (Infographic Mode)
1. Navigate to `/practice/livestock-anatomy/infographic`.
2. Select each species (Cattle, Swine, Sheep, Goat).
3. Use the `browser_subagent` to take high-resolution screenshots of EACH species.
4. **Overlay Analysis**: Compare marker positions against the following anatomical landmarks:
   - **Poll**: Top of the head between ears.
   - **Hock**: Rear leg joint (elbow of the back leg).
   - **Muzzle**: Nose/mouth area.
   - **Pins**: Bony prominences near the tail.
   - **Brisket**: Chest area between front legs.

### Step 3: Comparative Check (All Modes)
Navigate to **Study**, **Test**, and **Flashcard** modes to ensure the markers are identically positioned. Since the grid is standardized, they MUST match.

## Troubleshooting Drift & Layout Bugs

### 1. The `flex: 1` ScrollView Trap (Critical)
- **Problem**: If a `ScrollView` is placed inside a container with `flex: 1`, or if the `ScrollView` mapping itself has `flexGrow: 1` while its parent has strict limits, the scrollbar will not activate, and content (like test answers) will be pushed off the screen, permanently inaccessible.
- **Solution**: 
  - The `ScrollView` should use `style={{ flex: 1 }}`. 
  - Internal padding/margins should be applied via `contentContainerStyle={{ paddingBottom: 40 }}` within the `ScrollView`, NEVER on the `style` prop directly.

### 2. Dynamic Image Height Constraints
- **Problem**: Images loading at `100%` width on desktop monitors often become so tall they push all multiple-choice testing buttons into the void.
- **Solution**: Always constrain `imageSize` using the viewport's height:
  ```tsx
  const { width, height } = useWindowDimensions();
  const imageSize = Math.min(width - 40, height * 0.45, 600); // Max 45% of screen height
  ```

### 3. Safe Back Navigation Fallbacks
- **Problem**: Calling `router.back()` will simply do nothing if the user landed directly on the page via refresh (no history stack).
- **Solution**: Always use a safe fallback on back arrows across all anatomy screens:
  ```tsx
  onPress={() => router.canGoBack() ? router.back() : router.replace('/practice/livestock-anatomy')}
  ```

### 4. Anatomy Containment Shift
- **Problem**: If `resizeMode: "contain"` is used without a matching aspect ratio container, markers will drift proportional to the "pillar-boxing" or "letter-boxing".
- **Solution**: Ensure the parent `View` (e.g., `imageWrapper`) has the exact same `aspectRatio` as the data was calibrated for.

## Files Involved
- `lib/data/livestock-anatomy.ts` (The coordinate source of truth)
- `app/practice/livestock-anatomy/infographic.tsx`
- `app/practice/livestock-anatomy/study.tsx`
- `app/practice/livestock-anatomy/test.tsx`
- `app/practice/livestock-anatomy/flashcards.tsx`
