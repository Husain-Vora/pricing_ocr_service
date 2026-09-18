"""
Reusable, pure preprocessing functions for the product dataset pipeline.

Pure functions only — no file I/O here. scripts/build_dataset.py is the
CLI entrypoint that streams the file and calls into these; this module is
what gets unit tested directly.
"""
import hashlib
import re
import unicodedata
from typing import Optional

# Deterministic split boundaries (percent, out of 100). No RNG involved —
# same product_id always lands in the same split on every run, which is
# what "reproducible pipeline" / "no leakage across splits" requires.
TRAIN_PCT = 80
VAL_PCT = 10
# remaining (100 - TRAIN_PCT - VAL_PCT) = test

_WHITESPACE_RE = re.compile(r"\s+")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalize_text(value: Optional[str]) -> str:
    """
    Normalize free text (product title): Unicode NFKC normalization,
    strip control characters, collapse internal whitespace, trim ends.
    Does not change case — titles are naturally mixed-case and altering
    it loses information (brand names, model numbers).
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = _CONTROL_CHARS_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def normalize_category(value: Optional[str]) -> str:
    """
    Normalize a category label. Lighter-touch than normalize_text: this
    dataset's categories come from a controlled taxonomy (Amazon's), so we
    only strip stray whitespace — we do not lowercase/retitle, since that
    would be guessing at a taxonomy that's already consistent.
    """
    if value is None:
        return "Unknown"
    text = normalize_text(value)
    return text if text else "Unknown"


def is_valid_price(price: Optional[float]) -> bool:
    """A valid training price is a finite, strictly positive number."""
    if price is None:
        return False
    try:
        price = float(price)
    except (TypeError, ValueError):
        return False
    if price != price:  # NaN
        return False
    return price > 0


def assign_split(group_key: str) -> str:
    """
    Deterministically assign a row to train/val/test based on a stable
    hash of its group key (product id). Same key -> same split, every
    run, forever — this is what makes the pipeline reproducible without
    needing to persist a random seed or a set of "already assigned" ids.
    """
    digest = hashlib.md5(group_key.encode("utf-8")).hexdigest()
    bucket = int(digest, 16) % 100
    if bucket < TRAIN_PCT:
        return "train"
    if bucket < TRAIN_PCT + VAL_PCT:
        return "val"
    return "test"
