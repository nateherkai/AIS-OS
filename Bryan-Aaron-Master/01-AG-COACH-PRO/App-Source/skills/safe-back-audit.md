# Skill: Safe Back Audit

## Purpose

`router.back()` on deep-linkable / refreshable screens → blank white page when `canGoBack()` is false. Already partial in `no-blank-pages` skill. This expands: also audits `router.replace` patterns + missing fallbacks.

---

## When to Use

- Pre-merge UI PR
- After scaffold of new screens
- Bug report: "blank screen after refresh"

---

## Pattern

`lib/navigation.ts` exports `safeBack(router, fallback)`. Always use this — never raw `router.back()`.

### Wrong

```ts
import { useRouter } from 'expo-router';
const router = useRouter();
<Button onPress={() => router.back()} />
```

### Right

```ts
import { useRouter } from 'expo-router';
import { safeBack } from '@/lib/navigation';
const router = useRouter();
<Button onPress={() => safeBack(router, '/')} />
```

`fallback` = sensible parent route (`/`, `/(tabs)/cde`, `/practice/[name]`).

---

## Scan

### Raw `router.back()` calls

```bash
grep -rEn --include="*.tsx" --include="*.ts" \
  "router\.back\(\)" app/ components/ \
  | grep -v "safeBack" \
  | grep -v "// safe-back"
```

Every hit = bug.

### Missing fallback in deep-linkable routes

Deep-linkable screens (have route params or under `/practice/`, `/contest/`, `/study/`, `/(super-admin)/`):

```bash
grep -rEln --include="*.tsx" "useLocalSearchParams\|\[id\]\|\[name\]" app/ \
  | while read f; do
    grep -l "router.back\|safeBack" "$f" || echo "MISSING BACK: $f"
  done
```

### Hardcoded `navigation.goBack`

```bash
grep -rEn --include="*.tsx" "navigation\.goBack" app/ components/
```

Should not exist — Expo Router uses `router`.

---

## Fix Template

For each offender:

```diff
-import { useRouter } from 'expo-router';
+import { useRouter } from 'expo-router';
+import { safeBack } from '@/lib/navigation';

 const router = useRouter();
-onPress={() => router.back()}
+onPress={() => safeBack(router, '/(tabs)/cde')}
```

Pick fallback by route family:
- `/practice/<x>/*` → `/(tabs)/cde`
- `/contest/<id>` → `/(tabs)/cde`
- `/study/<x>` → `/(tabs)/study`
- `/(admin)/*` → `/(admin)/dashboard`
- `/(super-admin)/*` → `/(super-admin)/crm`
- `/(auth)/*` → `/(auth)/signup`

---

## Verification

```bash
# Should return zero
grep -rEn --include="*.tsx" --include="*.ts" "router\.back\(\)" app/ components/ \
  | grep -v "safeBack"
```

Manual test: open deep URL `https://www.agcoachpro.com/practice/forages/quiz`, hit back. Must land on fallback, not blank.

---

## Related

- `no-blank-pages` — broader audit including `<Stack.Screen options={...}>` missing
- `lib/navigation.ts` — source of `safeBack`
