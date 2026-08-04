---
name: notebooklm
description: Complete API for Google NotebookLM - full programmatic access including features not in the web UI. Create notebooks, add sources, generate all artifact types, download in multiple formats. Activates on explicit /notebooklm or intent like "create a podcast about X", "install notebooklm", "add notebooklm to cowork"
---
<!-- notebooklm-py v0.3.4 -->

# NotebookLM Automation

Complete programmatic access to Google NotebookLM—including capabilities not exposed in the web UI. Create notebooks, add sources (URLs, YouTube, PDFs, audio, video, images), chat with content, generate all artifact types, and download results in multiple formats.

## Step 0: Setup (Run Automatically on First Use)

When this skill is triggered and `notebooklm` is not yet installed or authenticated, complete setup first.

### Pre-flight: Check Python Version

`notebooklm-py` requires **Python 3.10+**. Check the available version before installing:

```bash
python3 --version
```

If Python is below 3.10 (e.g. 3.9.x which is the macOS default), install a compatible version:

**macOS (Homebrew):**
```bash
brew install python@3.12
```
Then use `/opt/homebrew/bin/python3.12` (Apple Silicon) or `/usr/local/bin/python3.12` (Intel) for the venv below.

**Linux (apt):**
```bash
sudo apt update && sudo apt install -y python3.12 python3.12-venv
```

### Install the CLI

Always use a virtual environment to avoid "externally-managed-environment" errors and PATH issues.

Determine which Python to use — if the system `python3` is 3.10+, use it directly. Otherwise use the one you just installed (e.g. `python3.12`):

```bash
# Set PYTHON to the correct binary (adjust if needed)
PYTHON=$(command -v python3.12 2>/dev/null || command -v python3.11 2>/dev/null || command -v python3.10 2>/dev/null || command -v python3)

# Verify it's 3.10+
$PYTHON -c "import sys; assert sys.version_info >= (3,10), f'Python {sys.version} is too old — need 3.10+'; print(f'Using Python {sys.version}')"

# Create venv and install
$PYTHON -m venv ~/.notebooklm-venv
source ~/.notebooklm-venv/bin/activate
pip install "notebooklm-py[browser]"
playwright install chromium
```

Then symlink so it's always on PATH:
```bash
mkdir -p ~/bin
ln -sf ~/.notebooklm-venv/bin/notebooklm ~/bin/notebooklm
export PATH="$HOME/bin:$PATH"
```

Verify the CLI works:
```bash
notebooklm --help
```

### Authenticate

**IMPORTANT:** The built-in `notebooklm login` command requires interactive terminal input (pressing Enter after sign-in). Claude Code's bash tool does NOT support interactive input, so `notebooklm login` will fail — the browser opens and closes instantly. Instead, use this custom login script.

Tell the user:

> I'm going to open a browser window — just sign into your Google account and navigate to notebooklm.google.com. Take your time, I'll wait for you to confirm before closing it.

Then write and run this login script:

```bash
cat > /tmp/nlm_login.py << 'PYEOF'
import json, os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

STORAGE_PATH = Path.home() / ".notebooklm" / "storage_state.json"
PROFILE_PATH = Path.home() / ".notebooklm" / "browser_profile"
SIGNAL_FILE = Path("/tmp/nlm_save_signal")

SIGNAL_FILE.unlink(missing_ok=True)
STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

print("Opening browser for Google login...")
print("Sign in to Google and navigate to notebooklm.google.com")

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_PATH),
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = browser.pages[0] if browser.pages else browser.new_page()
    page.goto("https://notebooklm.google.com/")

    print("Browser is open. Waiting for save signal...")
    while not SIGNAL_FILE.exists():
        time.sleep(1)

    print("Save signal received! Capturing session...")
    storage = browser.storage_state()
    with open(STORAGE_PATH, "w") as f:
        json.dump(storage, f)

    cookie_names = [c["name"] for c in storage.get("cookies", [])]
    print(f"Saved {len(cookie_names)} cookies: {cookie_names}")
    browser.close()

SIGNAL_FILE.unlink(missing_ok=True)
print(f"Authentication saved to: {STORAGE_PATH}")
PYEOF

# Run the login script in the background
source ~/.notebooklm-venv/bin/activate
python3 /tmp/nlm_login.py > /tmp/nlm_login_output.txt 2>&1 &
echo "Login started (PID=$!). Browser should open in a few seconds..."
```

Wait ~10 seconds for the browser to open, then ask the user if they can see the browser and are signed in.

Once the user confirms they are on the NotebookLM homepage, save the session:

```bash
touch /tmp/nlm_save_signal
sleep 8
cat /tmp/nlm_login_output.txt
```

Then verify authentication:

```bash
export PATH="$HOME/bin:$PATH"
notebooklm auth check
notebooklm list
```

If auth passes (SID cookie present), confirm to the user that NotebookLM is set up and ready. Clean up the temp script:

```bash
rm -f /tmp/nlm_login.py /tmp/nlm_login_output.txt /tmp/nlm_save_signal
```

If auth fails (SID cookie missing), the user may not have fully signed in. Delete the browser profile and retry:

```bash
rm -rf ~/.notebooklm/browser_profile ~/.notebooklm/storage_state.json
```

Then run the login script again from the top.

---

## Adding NotebookLM to Co-work

When the user asks to "add this to Co-work", "use this in Co-work", or "make this work in Co-work":

### Step 1: Check auth exists

```bash
cat ~/.notebooklm/storage_state.json > /dev/null 2>&1
```

If it doesn't exist, run the install and authenticate steps above first.

### Step 2: Generate the Co-work skill file

Read the contents of this skill file you are currently using. Then read the contents of `~/.notebooklm/storage_state.json`.

**IMPORTANT — Strip cookies before embedding:** Co-work is sandboxed and can't read local files, so cookies must be inlined. But the full storage_state.json contains duplicate cookies across multiple Google domains (.google.ae, .google.co.uk, .youtube.com, etc.) that are NOT needed. Strip them to save ~55% of tokens.

Run this to generate the minimal auth JSON:
```bash
python3 << 'PYEOF'
import json

with open("$HOME/.notebooklm/storage_state.json") as f:
    data = json.load(f)

# Only these domains are needed for NotebookLM auth
essential_domains = {".google.com", "notebooklm.google.com", "accounts.google.com"}
# Skip analytics/tracking cookies
skip_names = {"_gcl_au", "_ga", "_ga_W0LDH41ZCB", "OTZ", "ACCOUNT_CHOOSER"}

stripped = {
    "cookies": [c for c in data["cookies"] if c["domain"] in essential_domains and c["name"] not in skip_names],
    "origins": [o for o in data.get("origins", []) if "notebooklm" in o.get("origin", "")]
}
print(json.dumps(stripped, separators=(',',':')))
PYEOF
```

Create a MODIFIED copy of this skill file where you replace the entire "Step 0: Setup" section and "Adding NotebookLM to Co-work" section with this:

```markdown
## Auto-Authentication (Co-work)

This skill runs in a sandboxed Co-work environment. Before running ANY notebooklm command, run these setup commands:

\`\`\`bash
pip install notebooklm-py 2>/dev/null
export NOTEBOOKLM_AUTH_JSON='<STRIPPED MINIMAL AUTH JSON FROM ABOVE>'
\`\`\`

Then verify:
\`\`\`bash
notebooklm auth check
notebooklm list
\`\`\`

If auth fails, the cookies may have expired. Ask the user to re-run `notebooklm login` in Claude Code and regenerate this file.
```

### Step 3: Save and instruct

Save the file to the user's Desktop as `NotebookLMSkill-Cowork.md`.

Tell the user:

> Done! I've saved the Co-work skill to your Desktop as `NotebookLMSkill-Cowork.md`. Upload it as a skill in Claude Co-work and you'll have full NotebookLM access there too.
>
> I've stripped the cookies down to only the 21 essential ones (~1,400 tokens instead of ~3,100). When they expire, just come back to Claude Code and say "regenerate my Co-work NotebookLM skill" and I'll make a fresh one.

---

## When This Skill Activates

**Explicit:** User says "/notebooklm", "use notebooklm", "install notebooklm", or mentions the tool by name

**Intent detection:** Recognize requests like:
- "Create a podcast about [topic]"
- "Summarize these URLs/documents"
- "Generate a quiz from my research"
- "Turn this into an audio overview"
- "Create flashcards for studying"
- "Generate a video explainer"
- "Make an infographic"
- "Create a mind map of the concepts"
- "Download the quiz as markdown"
- "Add these sources to NotebookLM"
- "Add this to Co-work" / "Make this work in Co-work"

## Autonomy Rules

**Run automatically (no confirmation):**
- `notebooklm status` - check context
- `notebooklm auth check` - diagnose auth issues
- `notebooklm list` - list notebooks
- `notebooklm source list` - list sources
- `notebooklm artifact list` - list artifacts
- `notebooklm language list` - list supported languages
- `notebooklm language get` - get current language
- `notebooklm language set` - set language (global setting)
- `notebooklm artifact wait` - wait for artifact completion
- `notebooklm source wait` - wait for source processing
- `notebooklm research status` - check research status
- `notebooklm research wait` - wait for research
- `notebooklm use <id>` - set context
- `notebooklm create` - create notebook
- `notebooklm ask "..."` - chat queries (without `--save-as-note`)
- `notebooklm history` - display conversation history (read-only)
- `notebooklm source add` - add sources

**Ask before running:**
- `notebooklm delete` - destructive
- `notebooklm generate *` - long-running, may fail
- `notebooklm download *` - writes to filesystem
- `notebooklm ask "..." --save-as-note` - writes a note
- `notebooklm history --save` - writes a note

## Quick Reference

| Task | Command |
|------|---------|
| List notebooks | `notebooklm list` |
| Create notebook | `notebooklm create "Title"` |
| Set context | `notebooklm use <notebook_id>` |
| Show context | `notebooklm status` |
| Add URL source | `notebooklm source add "https://..."` |
| Add file | `notebooklm source add ./file.pdf` |
| Add YouTube | `notebooklm source add "https://youtube.com/..."` |
| List sources | `notebooklm source list` |
| Wait for source processing | `notebooklm source wait <source_id>` |
| Web research (fast) | `notebooklm source add-research "query"` |
| Web research (deep) | `notebooklm source add-research "query" --mode deep --no-wait` |
| Check research status | `notebooklm research status` |
| Wait for research | `notebooklm research wait --import-all` |
| Chat | `notebooklm ask "question"` |
| Chat (specific sources) | `notebooklm ask "question" -s src_id1 -s src_id2` |
| Chat (with references) | `notebooklm ask "question" --json` |
| Chat (save answer as note) | `notebooklm ask "question" --save-as-note` |
| Show conversation history | `notebooklm history` |
| Save all history as note | `notebooklm history --save` |
| Get source fulltext | `notebooklm source fulltext <source_id>` |
| Generate podcast | `notebooklm generate audio "instructions"` |
| Generate video | `notebooklm generate video "instructions"` |
| Generate report | `notebooklm generate report --format briefing-doc` |
| Generate quiz | `notebooklm generate quiz` |
| Generate flashcards | `notebooklm generate flashcards` |
| Generate infographic | `notebooklm generate infographic` |
| Generate mind map | `notebooklm generate mind-map` |
| Generate slide deck | `notebooklm generate slide-deck` |
| Revise a slide | `notebooklm generate revise-slide "prompt" --artifact <id> --slide 0` |
| Check artifact status | `notebooklm artifact list` |
| Wait for completion | `notebooklm artifact wait <artifact_id>` |
| Download audio | `notebooklm download audio ./output.mp3` |
| Download video | `notebooklm download video ./output.mp4` |
| Download slide deck (PDF) | `notebooklm download slide-deck ./slides.pdf` |
| Download slide deck (PPTX) | `notebooklm download slide-deck ./slides.pptx --format pptx` |
| Download report | `notebooklm download report ./report.md` |
| Download mind map | `notebooklm download mind-map ./map.json` |
| Download data table | `notebooklm download data-table ./data.csv` |
| Download quiz | `notebooklm download quiz quiz.json` |
| Download flashcards | `notebooklm download flashcards cards.json` |
| List languages | `notebooklm language list` |
| Set language | `notebooklm language set zh_Hans` |

## Generation Types

All generate commands support:
- `-s, --source` to use specific source(s) instead of all sources
- `--language` to set output language (defaults to 'en')
- `--json` for machine-readable output
- `--retry N` to automatically retry on rate limits

| Type | Command | Options | Download |
|------|---------|---------|----------|
| Podcast | `generate audio` | `--format [deep-dive\|brief\|critique\|debate]`, `--length [short\|default\|long]` | .mp3 |
| Video | `generate video` | `--format [explainer\|brief]`, `--style [auto\|classic\|whiteboard\|kawaii\|anime\|watercolor\|retro-print\|heritage\|paper-craft]` | .mp4 |
| Slide Deck | `generate slide-deck` | `--format [detailed\|presenter]`, `--length [default\|short]` | .pdf / .pptx |
| Slide Revision | `generate revise-slide "prompt" --artifact <id> --slide N` | `--wait`, `--notebook` | *(re-downloads parent deck)* |
| Infographic | `generate infographic` | `--orientation [landscape\|portrait\|square]`, `--detail [concise\|standard\|detailed]` | .png |
| Report | `generate report` | `--format [briefing-doc\|study-guide\|blog-post\|custom]`, `--append "extra instructions"` | .md |
| Mind Map | `generate mind-map` | *(sync, instant)* | .json |
| Data Table | `generate data-table` | description required | .csv |
| Quiz | `generate quiz` | `--difficulty [easy\|medium\|hard]`, `--quantity [fewer\|standard\|more]` | .json/.md/.html |
| Flashcards | `generate flashcards` | `--difficulty [easy\|medium\|hard]`, `--quantity [fewer\|standard\|more]` | .json/.md/.html |

## Common Workflows

### Research to Podcast
1. `notebooklm create "Research: [topic]"`
2. `notebooklm source add` for each URL/document
3. Wait for sources: `notebooklm source list --json` until all status=READY
4. `notebooklm generate audio "Focus on [specific angle]"`
5. Check `notebooklm artifact list` for status
6. `notebooklm download audio ./podcast.mp3` when complete

### Document Analysis
1. `notebooklm create "Analysis: [project]"`
2. `notebooklm source add ./doc.pdf` (or URLs)
3. `notebooklm ask "Summarize the key points"`
4. Continue chatting as needed

## Output Formats (--json)

```json
// notebooklm list --json
{"notebooks": [{"id": "...", "title": "...", "created_at": "..."}]}

// notebooklm source list --json
{"sources": [{"id": "...", "title": "...", "status": "ready|processing|error"}]}

// notebooklm artifact list --json
{"artifacts": [{"id": "...", "title": "...", "type": "Audio Overview", "status": "in_progress|pending|completed|unknown"}]}
```

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| Auth/cookie error | Session expired | Re-run `notebooklm login` |
| "No notebook context" | Context not set | Run `notebooklm use <id>` |
| Rate limiting | Google throttle | Wait 5-10 min, retry |
| Download fails | Generation incomplete | Check `artifact list` for status |

## Known Limitations

- Audio, video, quiz, flashcard, infographic, and slide deck generation may fail due to Google rate limits
- Generation times: audio 10-20 min, video 15-45 min, quiz/flashcards 5-15 min
- This is an unofficial API — Google can change things without warning
