---
name: ui-ux
description: Builds and maintains all visual UI components, screens, navigation, theming, and animations for the FFA Training App. Use when the user asks to create a screen, fix styling, adjust layout, update navigation, improve a component, or anything related to how the app looks and feels.
---

# UI/UX Agent

## When to use this skill

- Creating or modifying a screen
- Fixing styling, layout, or spacing issues
- Adding/changing navigation or tab structure
- Building reusable components
- Improving animations or transitions
- Reviewing a screen for brand consistency or accessibility

## Files Owned

```text
app/(tabs)/_layout.tsx
app/(admin)/_layout.tsx
app/(auth)/_layout.tsx
app/_layout.tsx
components/**/*
constants/colors.ts
constants/theme.ts
components/landing/*
```

## Tech Stack

- Expo SDK 52 / React Native 0.76
- **StyleSheet.create()** — this is mandatory. NativeWind is NOT installed.
- Expo Router for navigation
- @expo/vector-icons (Ionicons)
- expo-linear-gradient
- react-native-reanimated for animations
- react-native-safe-area-context

## Brand Identity

### Colors

| Token | Value | Usage |
| :--- | :--- | :--- |
| Primary Green | `#004B23` | FFA official green, primary buttons |
| Gold/Accent | `#FFB800` / `#F2A900` | Active tabs, highlights, CTAs |
| Background | `#000000` | Screen backgrounds |
| Surface | `#0A0A0A` / `#111111` | Elevated surfaces |
| Card BG | `rgba(255,255,255,0.03-0.08)` | Cards, list items |
| Border | `rgba(255,255,255,0.06-0.1)` | Subtle dividers |
| Text Primary | `#FFFFFF` | Headings, body text |
| Text Secondary | `rgba(255,255,255,0.5-0.7)` | Subtitles, captions |

### Typography

- Headings: fontWeight `800`, letterSpacing `-0.5`
- Labels/buttons: fontWeight `600`
- Body: fontWeight `400`
- System fonts (no custom font files loaded)

### Spacing & Radii

- Spacing scale: 4, 8, 12, 16, 20, 24, 32
- Cards: borderRadius `16-20`
- Buttons: borderRadius `12`
- Small elements: borderRadius `8-10`
- Pill shapes: borderRadius `20-24`

## Design Patterns & Examples

Refer to the following examples for standard UI patterns:

- [Screen Template & Cards](examples/screen-template.tsx)
- [Tab Bar Configuration](app/(tabs)/_layout.tsx)

## Instructions

1. **Layouts**: Use `SafeAreaView` from `react-native-safe-area-context`.
2. **Lists**: Use `FlatList` with `keyExtractor` for lists > 10 items.
3. **Styling**: Always use `StyleSheet.create()` outside the component.
4. **Icons**: Use Ionicons from `@expo/vector-icons`.

## Rules

1. **NEVER** use NativeWind/Tailwind `className` — use `StyleSheet.create()`
2. **NEVER** change FFA brand colors without explicit approval
3. All screens must handle: loading, error, and empty states
4. Always use `SafeAreaView` from react-native-safe-area-context
5. All touchable elements need minimum 44pt hit targets
6. Use `Platform.OS` checks for platform-specific styling
7. `StyleSheet.create()` must be outside the component (not inline)
8. Prefer `react-native-reanimated` over the basic `Animated` API
9. Use `FlatList` with `keyExtractor` for any list longer than ~10 items
10. Icons: use Ionicons from `@expo/vector-icons`

## Review Checklist

When reviewing any screen or component:

- [ ] Colors match brand tokens above
- [ ] Proper loading/error/empty states
- [ ] SafeAreaView wrapping
- [ ] 44pt minimum hit targets
- [ ] StyleSheet outside component body
- [ ] No inline function defs in JSX
- [ ] Platform.OS handling where needed
- [ ] Keyboard avoidance for any forms
