"""Tests for dream engine. Mocks Claude API to verify card structure."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.dream import (
    Card,
    DreamConfig,
    build_card_json,
    validate_cards,
    write_dream_output,
)


def test_card_dataclass_required_fields():
    c = Card(
        id="d1",
        dim="skill-perf",
        title="t",
        insight="i",
        action="a",
        estimated_value_minutes=30,
        status="open",
    )
    assert c.id == "d1"
    assert c.estimated_value_minutes == 30


def test_validate_cards_rejects_more_than_four():
    cards = [
        Card(id=f"d{i}", dim="conversation", title="t", insight="i", action="a", estimated_value_minutes=10, status="open")
        for i in range(5)
    ]
    with pytest.raises(ValueError, match="max 4 cards"):
        validate_cards(cards)


def test_validate_cards_accepts_four():
    cards = [
        Card(id=f"d{i}", dim="conversation", title="t", insight="i", action="a", estimated_value_minutes=10, status="open")
        for i in range(4)
    ]
    validate_cards(cards)  # no raise


def test_validate_cards_accepts_zero():
    validate_cards([])


def test_validate_cards_rejects_invalid_dim():
    cards = [Card(id="d1", dim="bogus", title="t", insight="i", action="a", estimated_value_minutes=10, status="open")]
    with pytest.raises(ValueError, match="invalid dim"):
        validate_cards(cards)


def test_validate_cards_rejects_duplicate_id():
    cards = [
        Card(id="d1", dim="cost", title="t", insight="i", action="a", estimated_value_minutes=10, status="open"),
        Card(id="d1", dim="cost", title="t", insight="i", action="a", estimated_value_minutes=10, status="open"),
    ]
    with pytest.raises(ValueError, match="duplicate"):
        validate_cards(cards)


def test_build_card_json_round_trip():
    cards = [
        Card(id="d1", dim="cost", title="t", insight="i", action="a", estimated_value_minutes=45, status="open")
    ]
    payload = build_card_json(cards, summary="s", date="2026-05-16", next_run="2026-05-17T02:00:00")
    parsed = json.loads(payload)
    assert parsed["date"] == "2026-05-16"
    assert len(parsed["cards"]) == 1
    assert parsed["cards"][0]["estimated_value_minutes"] == 45


def test_write_dream_output(tmp_path):
    out_dir = tmp_path / "dreams"
    out_dir.mkdir()
    cards = [Card(id="d1", dim="cost", title="t", insight="i", action="a", estimated_value_minutes=10, status="open")]
    path = write_dream_output(cards, out_dir=out_dir, summary="s", date="2026-05-16", next_run="2026-05-17T02:00:00")
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["summary"] == "s"
    assert len(data["cards"]) == 1


def test_dream_config_defaults():
    cfg = DreamConfig()
    assert cfg.max_cards == 4
    assert cfg.lookback_days == 7
