# FFA Training App - Key Notes

## Test Environment
- **ts-jest hangs indefinitely** on `require('ts-jest')` - DO NOT use ts-jest
- Fixed `jest.config.js` to use `babel-jest` with `configFile: false` and `@babel/preset-typescript`
- `babel-plugin-module-resolver` is NOT installed; use `Module._resolveFilename` hook or jest `moduleNameMapper`
- Jest startup is very slow on this machine (~60+ seconds) - use synchronous bash calls with `timeout >= 120000`
- `tsconfig.json` uses `"module": "esnext", "moduleResolution": "bundler"` (incompatible with jest/node directly)
- Created `tsconfig.jest.json` for jest-specific settings

## Error Handling Issues Fixed (gemini.ts)
- Retry logic now handles 429/rate-limit in addition to 503/overloaded
- `generateAnalysis` now throws on error instead of returning fake score 85

## Key Files
- AI layer: `lib/ai/gemini.ts`, `lib/ai/claude.ts`, `lib/ai/whisper.ts`
- Scoring: `lib/scoring/creed.ts`, `lib/scoring/spanish-creed.ts`
- Tests: `lib/scoring/creed.test.ts`, `lib/scoring/spanish-creed.test.ts`
- Custom test runner: `scripts/run-scoring-tests.js` (babel-based, no jest)

## Architecture
- Expo React Native app with Supabase backend
- Gemini 1.5 Flash for AI grading (with retry logic)
- LCS-based word matching for creed scoring accuracy
