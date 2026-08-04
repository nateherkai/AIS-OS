---
name: "Slaughter Cattle Image Generator"
description: "A specialized skill for generating highly accurate, photorealistic images of slaughter cattle representing specific Yield and Quality grades."
---

# Slaughter Cattle Generator Skill

This skill provides constraints and prompting strategies for creating accurate images for the livestock grading module.

## Core Directives
1. **Photorealism & Style**: All images MUST use the phrase "A high-quality, ultra-realistic full-body side-profile photo of a [Breed] steer standing on green pasture in an agricultural setting."
2. **Lighting & Focus**: "Bright daytime, natural lighting, sharp focus, professional livestock judging photography style."

## Yield Grade (YG) Physical Traits (Quantity & Cutability)
Yield grades determine the lean meat yield. The physical traits focus on muscling and external fat cover.

*   **Yield Grade 1 (Highest Cutability)**: Exceptionally lean, heavily muscled, very trim, thick-topped, with very little external fat over the ribs and loin. Appears hard and firm.
*   **Yield Grade 2**: Highly muscled, trim, slight fat cover noticeable but not excessive. Still very lean appearances overall.
*   **Yield Grade 3 (Average)**: Average muscling, moderate fat thickness. Smooth appearance over the ribs and loin.
*   **Yield Grade 4**: Light to moderate muscling, thick fat cover, appearing somewhat smooth and blocky, signs of fat deposits around the brisket, flank, and tailhead.
*   **Yield Grade 5 (Lowest Cutability)**: Heavy fat cover, "wasty", patchy fat deposits, visibly thick fat layer over the ribs, loin, and rump. Can appear lighter muscled due to excessive fat hiding definition.

## Quality Grade (QG) Visual Indicators (Quality & Marbling)
Quality grades are determined post-slaughter by intramuscular fat (marbling). *However*, in visual live judging (which these images approximate), we correlate QG with overall finish/condition (fatness) and breed type.

*   **Prime (Highest Quality)**: Requires abundant marbling. In live appearance, the animal typically carries a high degree of finish (fat cover). They often look smooth, full, and can look slightly "wasty" if YG is high. Often British breeds (Angus).
*   **Choice (Average/Excellent)**: Modest to moderate marbling. Good finish, smooth appearance. A very standard market-ready look.
*   **Select (Leaner)**: Slight marbling. Typically lean in appearance, potentially less finish, prioritizing growth and muscling over fat deposition (often Continental breeds like Charolais/Limousin).
*   **Standard (Lowest)**: Practically devoid of marbling. Very under-finished, thin, often dairy breeds or very poor quality beef breeds. (Not used in this batch).

**Note on High/Low modifiers within QG**: "High" means closer to the next grade up, "Low" means closer to the next grade down. Translating this to an image requires subtle adjustments to the "finish" of the animal. A "High Prime" might look slightly softer/fatter than a "Low Prime".

## Breed Specific Traits
Combine these physical descriptions with the YG/QG traits:
*   **Angus / Angus Cross**: Solid black hide, polled (no horns), generally moderate frame, naturally tends toward higher Quality Grades (Choice/Prime).
*   **Hereford**: Red body with a distinct white face, white underline, crest, switch (tail), and often white legs. Can be polled or horned.
*   **Limousin**: Solid golden-red or black hide. Known for extreme muscling, leanness, and larger frame. Often correlates with excellent Yield Grades (1 or 2) but lower Quality Grades (Select).
*   **Charolais**: Solid white or creamy white hide, pink skin/nose. Large frame, heavy muscling, lean.
*   **Brahman / Brahman Cross**: Distinctive hump over the shoulders, large drooping ears, excess skin (dewlap/brisket), slick grayish/reddish coat. High heat tolerance.

## Prompt Generation Example

To generate a **Yield Grade 3 Low Choice Hereford steer**:
> "A high-quality, ultra-realistic full-body side-profile photo of a Hereford steer standing on green pasture in an agricultural setting. It represents a Yield Grade 3 and Low Choice beef, meaning the animal has average muscling and moderate fat thickness with a smooth appearance over the ribs and loin. It is a red steer with a distinct white face and white underline. It has a standard market-ready look with adequate finish. Bright daytime, natural lighting, sharp focus, professional livestock judging photography style."
