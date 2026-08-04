"""pricing.py — Single source of truth for AI API and subscription pricing.

All cost calculations in the dashboard should import from here.
"""

# ── Claude API token prices (USD per 1M tokens) ──────────────────────────────
# Source: Anthropic pricing page, 2026
# cache_read is ~10% of input rate; cache_creation is 125% of input rate

PRICES = {
    "claude-opus-4-7":    {"input": 5.0,  "output": 25.0, "cache_creation": 6.25,  "cache_read": 0.50},
    "claude-opus-4-6":    {"input": 5.0,  "output": 25.0, "cache_creation": 6.25,  "cache_read": 0.50},
    "claude-opus-4-5":    {"input": 5.0,  "output": 25.0, "cache_creation": 6.25,  "cache_read": 0.50},
    "claude-opus-4-1":    {"input": 15.0, "output": 75.0, "cache_creation": 18.75, "cache_read": 1.50},
    "claude-opus-4":      {"input": 15.0, "output": 75.0, "cache_creation": 18.75, "cache_read": 1.50},
    "claude-sonnet-4-7":  {"input": 3.0,  "output": 15.0, "cache_creation": 3.75,  "cache_read": 0.30},
    "claude-sonnet-4-6":  {"input": 3.0,  "output": 15.0, "cache_creation": 3.75,  "cache_read": 0.30},
    "claude-sonnet-4-5":  {"input": 3.0,  "output": 15.0, "cache_creation": 3.75,  "cache_read": 0.30},
    "claude-sonnet-4":    {"input": 3.0,  "output": 15.0, "cache_creation": 3.75,  "cache_read": 0.30},
    "claude-haiku-4-5":   {"input": 1.0,  "output": 5.0,  "cache_creation": 1.25,  "cache_read": 0.10},
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0, "cache_creation": 1.25, "cache_read": 0.10},
}
DEFAULT_PRICE = PRICES["claude-sonnet-4-6"]  # safe mid-tier fallback

# Keep legacy dict for any code that references MODEL_PRICES by key
MODEL_PRICES = {
    "claude-opus-4":   PRICES["claude-opus-4-7"],
    "claude-sonnet-4": PRICES["claude-sonnet-4-6"],
    "claude-haiku-4":  PRICES["claude-haiku-4-5"],
    "_default":        PRICES["claude-sonnet-4-6"],
}


def price_for_model(model: str) -> dict:
    """Return pricing dict {input, output, cache_creation, cache_read} per 1M tokens.

    Resolution order:
    1. Exact match in PRICES
    2. Substring / prefix match (handles version suffix variants)
    3. Tier guess from model name (opus/haiku/sonnet)
    4. Default (Sonnet rates)
    """
    if not model:
        return DEFAULT_PRICE
    # Exact match first
    if model in PRICES:
        return PRICES[model]
    # Substring match — handles 'claude-sonnet-4-6-20251001' style suffixes
    for key, p in PRICES.items():
        if key in model or model.startswith(key):
            return p
    # Tier guess from model name
    ml = model.lower()
    if "opus" in ml:
        return PRICES["claude-opus-4-7"]
    if "haiku" in ml:
        return PRICES["claude-haiku-4-5"]
    if "sonnet" in ml:
        return PRICES["claude-sonnet-4-6"]
    return DEFAULT_PRICE


# Backward-compat alias used by usage_tracker.py
get_model_prices = price_for_model


def compute_api_cost(
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int,
    cache_read_tokens: int,
    model_str: str,
) -> float:
    """Compute API cost in USD for a given token breakdown and model.

    cache_read_tokens are priced at the cheap cache-read rate (~10% of input),
    NOT at full input rate. cache_creation_tokens at 125% of input.
    """
    p = price_for_model(model_str)
    return (
        (input_tokens          / 1_000_000) * p["input"] +
        (output_tokens         / 1_000_000) * p["output"] +
        (cache_creation_tokens / 1_000_000) * p["cache_creation"] +
        (cache_read_tokens     / 1_000_000) * p["cache_read"]
    )


# ── Ag Coach Pro subscription tier pricing ───────────────────────────────────
# Annual prices → divide by 12 for monthly

TIER_PRICES = {
    "greenhand":        495,
    "blue_and_gold":    895,
    "blue-and-gold":    895,
    "blue and gold":    895,
    "blue & gold":      895,
    "blue_gold":        895,
    "lone_star_elite":  1495,
    "lone-star-elite":  1495,
    "lone star elite":  1495,
    "elite":            1495,
    "lse":              1495,   # short code
    "enterprise":       1495,   # Supabase stores "enterprise" for Lone Star Elite
    "_default":         1495,   # fallback — highest tier
}

# Legacy alias for code that imports TIER_ANNUAL_USD
TIER_ANNUAL_USD = TIER_PRICES

TIER_MONTHLY_DEFAULT = round(1495 / 12, 2)  # $124.58 — Lone Star Elite


# Canonical tier names for display (maps DB value → human label)
TIER_DISPLAY = {
    "greenhand":        "Greenhand ($495/yr)",
    "blue_and_gold":    "Blue & Gold ($895/yr)",
    "blue-and-gold":    "Blue & Gold ($895/yr)",
    "blue and gold":    "Blue & Gold ($895/yr)",
    "blue & gold":      "Blue & Gold ($895/yr)",
    "lone_star_elite":  "Lone Star Elite ($1,495/yr)",
    "lone-star-elite":  "Lone Star Elite ($1,495/yr)",
    "lone star elite":  "Lone Star Elite ($1,495/yr)",
    "elite":            "Lone Star Elite ($1,495/yr)",
    "lse":              "Lone Star Elite ($1,495/yr)",
    "enterprise":       "Lone Star Elite / Enterprise ($1,495/yr)",
}

# Set of recognized tier keys (does not include _default)
_RECOGNIZED_TIERS = {k for k in TIER_PRICES if k != "_default"}


def is_recognized_tier(tier_str: str) -> bool:
    """Return True if tier_str maps to a known tier name."""
    key = (tier_str or "").lower().strip()
    # Normalize separators
    for candidate in (key, key.replace(" ", "_"), key.replace(" ", "-"), key.replace("-", "_")):
        if candidate in _RECOGNIZED_TIERS:
            return True
    return False


def monthly_for_tier(tier: str | None) -> float:
    """Return monthly revenue in USD for a given subscription tier string."""
    if not tier:
        return TIER_MONTHLY_DEFAULT
    key = (tier or "").lower().strip()
    # Try direct, then normalized variants
    annual = (
        TIER_PRICES.get(key)
        or TIER_PRICES.get(key.replace(" ", "_"))
        or TIER_PRICES.get(key.replace(" ", "-"))
        or TIER_PRICES.get(key.replace("-", "_"))
        or TIER_PRICES["_default"]
    )
    return round(annual / 12, 2)


# Backward-compat alias
tier_monthly_usd = monthly_for_tier
