# Preferred Tech Stack & Implementation Rules

When generating code or UI components for this brand, you **MUST** strictly adhere to the following technology choices.

## Core Stack
* **Framework:** Expo/React Native (TypeScript preferred)
* **Styling Engine:** Tailwind CSS / NativeWind (Mandatory. Do not use plain CSS or styled-components unless explicitly asked.)
* **Component Library:** Custom primitives or shadcn-inspired components for React Native.
* **Icons:** Lucide React / Lucide React Native

## Implementation Guidelines

### 1. Tailwind Usage
* Use utility classes directly in `className` (via NativeWind).
* Utilize the color tokens defined in `design-tokens.json` (e.g., use `bg-primary text-primary-foreground` instead of hardcoded hex values).
* **Dark Mode:** Support dark mode using Tailwind's `dark:` variant modifier.

### 2. Component Patterns
* **Buttons:** Primary actions must use the solid Primary color. Secondary actions should use the 'Ghost' or 'Outline' variants.
* **Forms:** Labels must always be placed *above* input fields. Use standard Tailwind spacing (e.g., `gap-4` between form items).
* **Layout:** Use Flexbox via Tailwind/NativeWind utilities for all layout structures.

### 3. Forbidden Patterns
* Do NOT use jQuery.
* Do NOT use Bootstrap classes.
* Do NOT create new CSS files; keep styles located within component files via Tailwind.
