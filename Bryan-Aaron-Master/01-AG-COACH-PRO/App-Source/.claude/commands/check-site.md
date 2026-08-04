# Check & Fix agcoachpro.com

Run a full health check on the live site and automatically fix any deployment issues found.

## What this checks

1. **Homepage reachability** — agcoachpro.com returns HTTP 200
2. **SPA routing** — all key app routes return 200 (not 404), proving Vercel serves index.html as fallback
3. **JS bundle loads** — HTML references a valid JS bundle that also returns 200
4. **Env vars embedded** — Supabase URL baked into bundle (proves env vars set at build time)
5. **Feature integrity** — all critical features present in the bundle
6. **vercel.json SPA config** — `routes` array has filesystem + catch-all fallback

## Steps to execute

Run each check in sequence. If a check fails, apply the fix before continuing.

### Step 1 — Route reachability check (most critical)

Test the homepage AND key sub-routes. All must return 200:

```bash
python3 << 'PYEOF'
import urllib.request, urllib.error

routes = [
    "/",
    "/practice/livestock-judging",
    "/practice/meats-id",
    "/contest/test-route-spa-check",
    "/(tabs)/cde",
]

print(f"{'ROUTE':<45} {'STATUS'}")
print("-" * 55)
all_pass = True
for route in routes:
    # Use www — agcoachpro.com 307-redirects to www, test directly
    url = f"https://www.agcoachpro.com{route}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        res = urllib.request.urlopen(req, timeout=10)
        code = res.getcode()
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:
        code = f"ERR: {e}"
    ok = code == 200
    if not ok:
        all_pass = False
    print(f"{route:<45} {'✅ 200' if ok else f'❌ {code}'}")

print("-" * 55)
print("SPA ROUTING:", "✅ ALL ROUTES OK" if all_pass else "❌ ROUTES RETURNING 404 — vercel.json needs fix")

PYEOF
```

**If any route returns 404**, the vercel.json SPA routing is broken. Check and fix it immediately:

```bash
cat vercel.json
```

The file MUST use `routes` format (not `rewrites` + `cleanUrls`):

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "routes": [
    { "handle": "filesystem" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

If it doesn't match this exactly, overwrite it, commit, and push:

```bash
cat > vercel.json << 'EOF'
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "routes": [
    { "handle": "filesystem" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
EOF
git add vercel.json && git -c user.email="kdwhpgxgrc@privaterelay.appleid.com" -c user.name="FFA Deploy" commit -m "fix: restore SPA routing in vercel.json" && git push origin main
```

Then wait 3 minutes and re-run Step 1 before continuing.

### Step 2 — Fetch live HTML

```bash
curl -sL "https://www.agcoachpro.com" -o /tmp/agcoachpro_index.html
echo "HTTP status: $(curl -s -o /dev/null -w '%{http_code}' https://www.agcoachpro.com)"
```

If status is not 200, trigger a fresh deploy:

```bash
curl -s -X POST "https://api.vercel.com/v1/integrations/deploy/prj_dO4knmGHoPQSI7FM3L3ItYD7aNCx/uVjZIyhPp5"
```

### Step 3 — Extract and verify JS bundle

```bash
python3 -c "
import re
content = open('/tmp/agcoachpro_index.html').read()
match = re.search(r'src=[\"\'](/_expo/static/js/web/[^\"\']+)[\"\']\s*', content)
if match:
    print('BUNDLE:', match.group(1))
else:
    print('ERROR: No bundle script tag found in HTML')

"
```

Check the bundle itself returns 200:

```bash
BUNDLE_PATH=$(python3 -c "import re; content=open('/tmp/agcoachpro_index.html').read(); m=re.search(r'src=[\"\'](/_expo/static/js/web/[^\"\']+)[\"\']\s*', content); print(m.group(1) if m else '')")
echo "Bundle status: $(curl -s -o /dev/null -w '%{http_code}' https://www.agcoachpro.com${BUNDLE_PATH})"
```

If bundle returns 404, the build failed silently. Run `npm run build` locally to see errors.

### Step 4 — Download bundle and run feature checks

```bash
curl -sL "https://www.agcoachpro.com${BUNDLE_PATH}" -o /tmp/agcoachpro_bundle.js

python3 << 'PYEOF'
content = open('/tmp/agcoachpro_bundle.js').read()
size_mb = len(content) / 1_000_000

checks = [
    ("Bundle size > 1MB (not empty)",        len(content) > 1_000_000),
    ("Supabase URL embedded (env vars OK)",  "nkoyotdafqllgbpuklva.supabase.co" in content),
    ("Livestock hub routing by name",        "Livestock" in content and "livestock-judging" in content),
    ("Meats hub routing by name",            "meats-id" in content),
    ("Phenotype Drills present",             "Phenotype Drills" in content),
    ("Feeder Cattle Grading present",        "Feeder Cattle Grading" in content),
    ("Slaughter Cattle Grading present",     "Slaughter Cattle Grading" in content),
    ("Study by Category present",            "Study by Category" in content),
    ("Flashcards by Category present",       "Flashcards by Category" in content),
    ("Contest Mode present",                 "Contest Mode" in content),
    ("questionCount param present",          "questionCount" in content),
    ("Judging Classes REMOVED",              "Judging Classes" not in content),
]

print(f"\nBundle size: {size_mb:.1f} MB")
print(f"{'CHECK':<45} {'RESULT'}")
print("-" * 55)
all_pass = True
for label, result in checks:
    status = "✅ PASS" if result else "❌ FAIL"
    if not result:
        all_pass = False
    print(f"{label:<45} {status}")

print("-" * 55)
print("FEATURES:", "✅ ALL CHECKS PASSED" if all_pass else "❌ FAILURES DETECTED — see above")
PYEOF
```

**If "Supabase URL embedded" fails** — env vars missing at build time. Re-set them on the Vercel project via API, then trigger a fresh deploy.

**If any feature check fails** — code regression. Check `git log`, fix the file, commit, and push.

### Step 5 — Report

Print a clear summary: SPA routing status, bundle status, feature check results, and what (if anything) was fixed. End with the live URL and overall PASS/FAIL.
