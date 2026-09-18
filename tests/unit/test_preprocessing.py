from collections import Counter

from app.ml.preprocessing import (
    assign_split,
    is_valid_price,
    normalize_category,
    normalize_text,
)


def test_normalize_text_collapses_whitespace_and_trims():
    assert normalize_text("  Echo   Dot   (5th\tgen)  ") == "Echo Dot (5th gen)"


def test_normalize_text_strips_control_chars():
    assert normalize_text("Echo\x00Dot\x07") == "EchoDot"


def test_normalize_text_none_becomes_empty_string():
    assert normalize_text(None) == ""


def test_normalize_category_blank_becomes_unknown():
    assert normalize_category("") == "Unknown"
    assert normalize_category("   ") == "Unknown"
    assert normalize_category(None) == "Unknown"


def test_normalize_category_preserves_case():
    assert normalize_category("  Hi-Fi Speakers ") == "Hi-Fi Speakers"


def test_is_valid_price_accepts_positive_numbers():
    assert is_valid_price(21.99) is True
    assert is_valid_price(0.01) is True


def test_is_valid_price_rejects_zero_negative_none_nan():
    assert is_valid_price(0) is False
    assert is_valid_price(-5) is False
    assert is_valid_price(None) is False
    assert is_valid_price(float("nan")) is False


def test_is_valid_price_rejects_unparseable():
    assert is_valid_price("not-a-number") is False


def test_assign_split_is_deterministic():
    for key in ["B09B96TG33", "B01HTH3C8S", "some-title-fallback"]:
        first = assign_split(key)
        for _ in range(20):
            assert assign_split(key) == first


def test_assign_split_distribution_roughly_matches_percentages():
    counts = Counter(assign_split(f"asin-{i}") for i in range(50_000))
    total = sum(counts.values())
    train_pct = counts["train"] / total * 100
    val_pct = counts["val"] / total * 100
    test_pct = counts["test"] / total * 100
    # hash-based bucketing, generous tolerance
    assert 77 <= train_pct <= 83
    assert 7 <= val_pct <= 13
    assert 7 <= test_pct <= 13
