---
name: qa-performance
description: Owns testing, performance optimization, bug fixing, bundle auditing, and build pipeline for the FFA Training App. Use when the user reports a bug, asks to run tests, wants a performance audit, needs to reduce bundle size, fix crashes, or improve app speed.
---

# QA & Performance Agent

## When to use this skill
- User reports a bug or crash
- Running or writing tests
- Performance audit or optimization
- Bundle size analysis
- Build or deployment issues
- Reviewing code for anti-patterns

## Files Owned
```
scripts/run-scoring-tests.js
scripts/test-*.ts
lib/scoring/*.test.ts
jest.config.js
tsconfig.jest.json
babel.config.js
metro.config.js
```

## Testing Stack

### CRITICAL: Known Environment Issues
- **ts-jest HANGS indefinitely** on `require('ts-jest')` — NEVER use ts-jest
- Use `babel-jest` with `configFile: false` and `@babel/preset-typescript`
- Jest startup is very slow (~60s) — set `timeout >= 120000`
- Module aliases (`@/`) need `moduleNameMapper` in jest.config.js
- Custom test runner exists: `scripts/run-scoring-tests.js` (babel-based, no jest)
- `tsconfig.json` uses `"module": "esnext"` which is incompatible with jest/node
- Created `tsconfig.jest.json` for jest-specific settings

### Working Jest Config
```javascript
// jest.config.js
module.exports = {
  transform: {
    '^.+\\.tsx?$': ['babel-jest', {
      configFile: false,
      presets: ['@babel/preset-typescript'],
    }],
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testTimeout: 120000,
};
```

### Test Types

**Unit Tests** (`lib/scoring/*.test.ts`):
- Every scoring function must have tests
- Test: empty input, max score, partial answers, edge cases
- Test AI response parsing with mock data
- Existing: `creed.test.ts`, `spanish-creed.test.ts`

**Integration Scripts** (`scripts/`):
- `test-creed-scoring.ts`: End-to-end creed scoring
- `test-radio-ai-only.ts`: Radio broadcasting AI grading
- `stress-test-ai.ts`: AI rate limiting and reliability
- Run with: `npx ts-node scripts/{name}.ts` or the custom runner

**Manual Test Flows** (per contest):
1. Navigation: Can reach from contest list and return
2. Instructions: Clear, complete, match official FFA rules
3. Practice: Recording/quiz/upload functions correctly
4. Scoring: Accurate, consistent, handles edge cases
5. Results: Display correctly with category breakdowns + feedback
6. Retry: Can restart without state leaks
7. State: Progress saved correctly to history store

## Performance Targets
| Metric | Target |
|--------|--------|
| App launch to interactive | < 3 seconds |
| Screen transition | < 300ms |
| AI scoring response | < 5 seconds |
| Audio recording start | < 500ms |
| Quiz question load | Instant (local data) |
| List scrolling | 60 FPS |

## Bundle Audit: Suspected Bloat

These are in `package.json` and may not be needed for the core app:

| Package | Size Impact | Likely Used For | Recommendation |
|---------|------------|-----------------|----------------|
| `three` + `@react-three/fiber` + `@react-three/drei` + `expo-three` + `expo-gl` | ~500KB+ | Landing page 3D? | Remove if web-only |
| `gsap` + `@gsap/react` | ~100KB | Web landing animations? | Remove if web-only |
| `framer-motion` | ~150KB | Web animations (not RN compatible) | Remove |
| `@0no-co/graphql.web` + `@urql/core` | ~50KB | GraphQL? | Check if used at all |
| `react-native-markdown-display` | ~30KB | AI feedback display? | Keep if used |
| `csv-parse` | ~20KB | Data import scripts? | Move to devDeps |

**Audit command**: Search for actual imports of each package across the codebase before removing.

## Performance Anti-Pattern Checklist

Scan all files in `app/` and `components/` for:

### Re-render Issues
- [ ] Inline function definitions in JSX: `onPress={() => doSomething(id)}`
- [ ] Missing `React.memo` on FlatList item components
- [ ] Creating new objects/arrays in render: `style={[styles.a, { color: 'red' }]}`
- [ ] Zustand subscriptions selecting too much state

### List Performance
- [ ] `FlatList` without `keyExtractor`
- [ ] `FlatList` without `getItemLayout` (causes janky scroll)
- [ ] Using `ScrollView` for long lists instead of `FlatList`
- [ ] Missing `windowSize` optimization on large lists

### Memory & Resources
- [ ] Audio recording not cleaned up in `useEffect` return
- [ ] Supabase subscriptions not unsubscribed
- [ ] Large images not resized/compressed
- [ ] Missing `useCallback` for event handlers passed as props

### Code Issues
- [ ] `StyleSheet.create` inside component body (recreated each render)
- [ ] `console.log` in production code
- [ ] Unhandled promise rejections
- [ ] Missing error boundaries

## Bug Triage Process
1. **Reproduce**: Get exact steps to trigger the issue
2. **Isolate**: Determine if it's UI, data, AI, or platform-specific
3. **Root cause**: Check if it's a known Expo SDK 52 issue first
4. **Fix**: Implement with minimal surface area
5. **Test**: Verify fix and check for regressions
6. **Document**: Note in MEMORY.md if it's a gotcha

## Build & Deploy Checklist
- [ ] `npx expo export` succeeds without errors
- [ ] No TypeScript errors (`npx tsc --noEmit`)
- [ ] All environment variables set in `.env`
- [ ] API keys NOT in client code (only in API routes)
- [ ] Bundle size reasonable (< 10MB JS bundle)
- [ ] Test on real device (not just simulator)
- [ ] Test on both iOS and Android
