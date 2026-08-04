---
name: species-basics-builder
description: Builds complete, formatted curriculum sections (Video, Muscle, Finish, Structure, Balance, Data/EPDs) for Swine, Sheep, and Goats in the Livestock Basics module, mirroring the Cattle section exact structure.
---

# Species Basics Builder Skill

This skill automates the creation of a comprehensive judging curriculum for Swine, Sheep, and Goats within the Livestock Basics module (`app/practice/livestock-judging/basics.tsx`).

The goal is to strictly replicate the 6-part structure established in the Cattle section for any new species, ensuring a consistent educational flow.

## The 6-Part Curriculum Structure

Whenever the user asks you to build out the basics for a specific species (e.g., "build the swine curriculum"), you MUST generate or compile resources that map EXACTLY to these 6 elements, in this specific order:

### 1. The Foundation (Video)

- **Format:** NotebookLM Summary Video (`type: 'video'`)
- **Action:** Ensure a summary video exists for the species weighing and grading principles. Route to `/practice/livestock-judging/video-viewer`.

### 2. Evaluating Muscle (Infographic + Slide Deck)

- **Format:** Infographic (`type: 'infographic'`) followed by a Slide Deck (`type: 'slidedeck'`).
- **Action:** Create or locate an infographic detailing muscle evaluation for the specific species (e.g., "Swine Muscle"). Create or locate a corresponding slide deck for an in-depth Masterclass. Route to `infographic-viewer` and `slidedeck-viewer`.

### 3. Finish & Condition (Infographic + Slide Deck)

- **Format:** Infographic (`type: 'infographic'`) followed by a Slide Deck (`type: 'slidedeck'`).
- **Action:** Create or locate an infographic covering fat thickness and condition scoring for the species. Pair it with an in-depth slide deck.

### 4. Structural Correctness (Infographic + Slide Deck)

- **Format:** Infographic (`type: 'infographic'`) followed by a Slide Deck (`type: 'slidedeck'`).
- **Action:** Create or locate an infographic on skeletal structure and common flaws for the species (e.g., "Swine Structural Correctness"). Pair it with a slide deck.

### 5. Balance & Eye Appeal (Infographic + Slide Deck)

- **Format:** Infographic (`type: 'infographic'`) followed by a Slide Deck (`type: 'slidedeck'`).
- **Action:** Create or locate an infographic demonstrating proportionality, lines, and balance. Pair it with a slide deck.

### 6. Data-Driven Selection (Slide Deck)

- **Format:** Slide Deck (`type: 'slidedeck'`)
- **Action:** Create or locate a slide deck explaining data evaluation (e.g., EPDs for Sheep/Cattle, SPI/TSI/MLI for Swine) and how to incorporate performance data into placing classes.

## Workflow Execution Steps

When invoked to build a species:

1. **Asset Verification & Generation:**
   - Check if the required infographics, video files, and slide deck data structures currently exist for the target species.
   - If they do NOT exist, proactively generate the image assets using the built-in image generation tool, format the markdown files, or prompt the user for necessary files (like the NotebookLM videos).

2. **Code Implementation (`basics.tsx`):**
   - Open `/Users/aaronfamilylivestock/ffa-app-clean/app/practice/livestock-judging/basics.tsx`.
   - Create a new array for the target species (e.g., `const swineResources = [ ... ];`), strictly following the 6-part chronological pattern defined above.
   - Update the `getResources` switch statement to return the new array when the target species is selected.

   ```typescript
   // Example mapping for getResources
   const getResources = () => {
     switch (selectedSpecies) {
       case 'Cattle': return cattleResources;
       case 'Swine': return swineResources; // Add this
       default: return [];
     }
   };
   ```

3. **Verification:**
   - Ensure the new array has exactly the same structure, route parameters, and icon styling conventions as the `cattleResources` array (e.g., `#2196F3` for infographics, `#9C27B0` for slide decks).
   - Ensure the `heroDesc` dynamically updates for the new species to provide a relevant welcoming message.
