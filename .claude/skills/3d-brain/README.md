# 3D Brain skill

Build a named, interactive globe from an AIOS's saved knowledge. The skill asks for the brain's display name and main categories, maps them to selected local folders, and creates the bundled app under `apps/3d-brain/`.

- Claude Code: `/3d-brain`
- Codex: select **3D Brain**, or type `$3d-brain`
- Natural language: “Build a 3D brain from my AIOS.”

Node.js 22+ is required. The renderer is included, so generated apps run with `node serve.mjs` without an npm install. Building a modified renderer requires `npm ci` and `npm run build:js` in the generated app.

The app includes a spherical layout, central orb, colored categories, search, a note reader, source filters, inventory, Cinema, and interactive growth replay. Drag and zoom remain available during growth. Connections come from the selected notes; the animation illustrates connectivity, not historical creation dates.

Markdown/text and curated Codex memory are supported directly. Claude memory uses its selected Markdown folder. Meeting and video knowledge can come from saved Markdown exports. Other formats and online services require an export or a tested adapter.

To install separately, copy this entire folder, including `assets`, `scripts`, `references`, and `agents`, to the target AIOS's canonical skill folder, `.claude/skills`, as `3d-brain`. In AIS-OS, run `bash scripts/sync-codex-skills.sh 3d-brain` to generate the Codex copy. Do not copy only `SKILL.md` or include a generated user's config/data.

Package validation: `node scripts/test-package.mjs`. For a larger fictional visual fixture, add `--keep --demo --out <scratch-folder>`.

See [SKILL.md](SKILL.md) for the workflow, [the portable spec](references/portable-spec.md) for the implementation contract, and [the config guide](references/config.md) for adapters and limits.
