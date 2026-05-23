"""Tests for promote.py — covers resolve, render, smoke, install, log, mark."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Make package import work when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import promote


SAMPLE_CARD = {
    "id": "d1",
    "dim": "repeated-task",
    "title": "Saw similar prompt 30x — promote to skill",
    "insight": "Same prompt seen 30 times in the last week.",
    "action": "Promote to skill or memory",
    "estimated_value_minutes": 30,
    "status": "open",
}


def _write_dream(tmp_path: Path, cards: list[dict]) -> Path:
    path = tmp_path / "2026-05-21.json"
    path.write_text(json.dumps({
        "date": "2026-05-21",
        "generated_at": "2026-05-21T02:00:00",
        "cards": cards,
    }))
    return path


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(promote.slugify("Saw similar prompt 30x — promote to skill"),
                         "saw-similar-prompt-30x-promote-to-skill")

    def test_empty_falls_back(self):
        self.assertEqual(promote.slugify("!!!"), "promoted-skill")

    def test_max_len(self):
        self.assertLessEqual(len(promote.slugify("a" * 200)), 50)


class TestResolveCard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dreams = Path(self.tmp.name)
        self._patch = mock.patch.object(promote, "DREAMS_DIR", self.dreams)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self.tmp.cleanup()

    def test_resolve_found(self):
        _write_dream(self.dreams, [SAMPLE_CARD])
        rc = promote.resolve_card("d1")
        self.assertEqual(rc.card["id"], "d1")
        self.assertEqual(rc.dream_date, "2026-05-21")

    def test_resolve_missing(self):
        _write_dream(self.dreams, [SAMPLE_CARD])
        with self.assertRaises(LookupError):
            promote.resolve_card("d99")

    def test_no_dream_files(self):
        with self.assertRaises(FileNotFoundError):
            promote.resolve_card("d1")


class TestInferKind(unittest.TestCase):
    def test_repeated_task_to_skill(self):
        self.assertEqual(promote.infer_kind({"dim": "repeated-task"}, None), "skill")

    def test_memory_health_to_memory(self):
        self.assertEqual(promote.infer_kind({"dim": "memory-health"}, None), "memory")

    def test_override(self):
        self.assertEqual(promote.infer_kind({"dim": "repeated-task"}, "doc"), "doc")

    def test_unknown_defaults_skill(self):
        self.assertEqual(promote.infer_kind({"dim": "wat"}, None), "skill")


class TestRenderAndSmoke(unittest.TestCase):
    def setUp(self):
        self.rc = promote.ResolvedCard(
            card=SAMPLE_CARD,
            source_path=Path("/tmp/x.json"),
            dream_date="2026-05-21",
            generated_at="2026-05-21T02:00:00",
        )

    def test_render_no_unfilled_templates(self):
        out = promote.render_skill(self.rc, "test-skill")
        self.assertNotIn("{{", out)
        self.assertIn("name: test-skill", out)

    def test_smoke_passes_on_valid(self):
        out = promote.render_skill(self.rc, "test-skill")
        ok, report = promote.smoke_test_skill(out)
        self.assertTrue(ok, f"smoke should pass, report: {report}")

    def test_smoke_fails_on_unfilled(self):
        bad = "---\nname: x\ndescription: y\n---\n\nLeftover {{token}} here."
        ok, report = promote.smoke_test_skill(bad)
        self.assertFalse(ok)

    def test_smoke_fails_on_no_frontmatter(self):
        ok, _ = promote.smoke_test_skill("# no frontmatter")
        self.assertFalse(ok)


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.dreams = self.tmp_path / "dreams"
        self.dreams.mkdir()
        self.skills = self.tmp_path / "skills"
        self.quarantine = self.skills / "_quarantine"
        self.log = self.tmp_path / "promote.log"
        self.patches = [
            mock.patch.object(promote, "DREAMS_DIR", self.dreams),
            mock.patch.object(promote, "SKILLS_INSTALL_DIR", self.skills),
            mock.patch.object(promote, "QUARANTINE_DIR", self.quarantine),
            mock.patch.object(promote, "PROMOTE_LOG", self.log),
        ]
        for p in self.patches:
            p.start()
        self.dream_path = _write_dream(self.dreams, [dict(SAMPLE_CARD)])

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_promote_ships(self):
        rc = promote.promote("d1", None, force=False)
        self.assertEqual(rc, 0)
        # Skill installed
        installed = list(self.skills.rglob("SKILL.md"))
        self.assertEqual(len(installed), 1)
        self.assertNotIn("_quarantine", str(installed[0]))
        # Log written
        self.assertTrue(self.log.exists())
        entries = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(entries[-1]["verdict"], "shipped")
        # Card marked promoted
        data = json.loads(self.dream_path.read_text())
        self.assertEqual(data["cards"][0]["status"], "promoted")

    def test_promote_missing_card_logs_error(self):
        rc = promote.promote("d99", None, force=False)
        self.assertEqual(rc, 2)
        entries = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(entries[-1]["verdict"], "error")

    def test_promote_idempotent_without_force(self):
        promote.promote("d1", None, force=False)
        rc = promote.promote("d1", None, force=False)
        self.assertEqual(rc, 0)
        entries = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(entries[-1]["verdict"], "skipped")

    def test_promote_force_reruns(self):
        promote.promote("d1", None, force=False)
        rc = promote.promote("d1", None, force=True)
        self.assertEqual(rc, 0)
        entries = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(entries[-1]["verdict"], "shipped")

    def test_unsupported_kind_quarantine(self):
        # Card with memory-health dim -> kind=memory -> not yet supported -> needs-fix
        cards = [dict(SAMPLE_CARD, id="d2", dim="memory-health")]
        _write_dream(self.dreams, cards)
        # rewrite so resolve picks the right one — we wrote same filename, overwrites
        rc = promote.promote("d2", None, force=False)
        self.assertEqual(rc, 3)
        entries = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(entries[-1]["verdict"], "needs-fix")


if __name__ == "__main__":
    unittest.main()
