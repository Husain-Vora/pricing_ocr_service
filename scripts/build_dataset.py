"""
Phase 2 pipeline: turn the currency-converted product dataset into a
clean, split, model-ready dataset.

Run order:
    1. python scripts/convert_gbp_to_inr_ppp.py   (raw GBP -> price_inr)
    2. python scripts/build_dataset.py             (this script)

Deterministic: same input file -> byte-identical train/val/test output
every run (split assignment is a stable hash of `asin`, not random).

Single pass, chunked — safe for the real 620MB / 2.2M-row file.
"""
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Allow running as `python scripts/build_dataset.py` from the repo root
# without needing PYTHONPATH set manually.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.preprocessing import (
    TRAIN_PCT,
    VAL_PCT,
    assign_split,
    is_valid_price,
    normalize_category,
    normalize_text,
)

# --- file locations ---
INPUT_FILE = Path("data/processed/products_inr.csv")
OUTPUT_DIR = Path("data/processed")
TRAIN_FILE = OUTPUT_DIR / "train.csv"
VAL_FILE = OUTPUT_DIR / "val.csv"
TEST_FILE = OUTPUT_DIR / "test.csv"
QUALITY_REPORT_FILE = OUTPUT_DIR / "dataset_quality_report.json"
PARAMS_FILE = OUTPUT_DIR / "preprocessing_params.json"

# --- real column names, from the profiled dataset ---
ID_COLUMN = "asin"
NAME_COLUMN = "title"
CATEGORY_COLUMN = "categoryName"
PRICE_COLUMN = "price_inr"

# Columns carried through to the cleaned output, beyond the required ones.
# Not used by the baseline pricing model, but cheap to keep for later use
# (stars/reviews as future features, isBestSeller for analysis).
PASSTHROUGH_COLUMNS = ["stars", "reviews", "isBestSeller", "boughtInLastMonth"]

CHUNKSIZE = 200_000

OUTPUT_COLUMNS = [
    ID_COLUMN,
    "product_name",
    "product_name_raw",
    "category",
    "category_raw",
    "price",
] + PASSTHROUGH_COLUMNS


def fail_if_unconfigured():
    if not INPUT_FILE.exists():
        print(f"INPUT_FILE not found: {INPUT_FILE}")
        print("Run scripts/convert_gbp_to_inr_ppp.py first, or edit INPUT_FILE above.")
        raise SystemExit(1)
    missing_passthrough = []
    return missing_passthrough


def build():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in (TRAIN_FILE, VAL_FILE, TEST_FILE):
        if f.exists():
            f.unlink()

    total_rows = 0
    dropped_invalid_price = 0
    kept_rows = 0
    split_counts = Counter()
    category_counts = Counter()
    asin_seen = set()
    duplicate_asin_count = 0
    missing_asin_count = 0
    title_lengths = []
    price_values_for_stats = []  # capped sample, not the full column — memory bound
    PRICE_SAMPLE_CAP = 500_000

    files_ready = {"train": False, "val": False, "test": False}
    file_handles = {"train": TRAIN_FILE, "val": VAL_FILE, "test": TEST_FILE}

    reader = pd.read_csv(INPUT_FILE, chunksize=CHUNKSIZE, dtype=str, keep_default_na=False)

    for chunk in reader:
        for col in [ID_COLUMN, NAME_COLUMN, CATEGORY_COLUMN, PRICE_COLUMN]:
            if col not in chunk.columns:
                raise KeyError(f"Expected column '{col}' not found. Got: {list(chunk.columns)}")

        total_rows += len(chunk)

        price_numeric = pd.to_numeric(chunk[PRICE_COLUMN], errors="coerce")
        valid_mask = price_numeric.apply(is_valid_price)
        dropped_invalid_price += int((~valid_mask).sum())

        kept = chunk.loc[valid_mask].copy()
        kept["_price_numeric"] = price_numeric.loc[valid_mask]

        out_rows = {"train": [], "val": [], "test": []}

        for row, price in zip(kept.itertuples(index=False), kept["_price_numeric"]):
            row_dict = row._asdict()
            asin = row_dict[ID_COLUMN].strip()

            if not asin:
                missing_asin_count += 1
                group_key = row_dict[NAME_COLUMN]  # fallback grouping key
            else:
                group_key = asin
                h = hash(asin)
                if h in asin_seen:
                    duplicate_asin_count += 1
                else:
                    asin_seen.add(h)

            name_clean = normalize_text(row_dict[NAME_COLUMN])
            category_clean = normalize_category(row_dict[CATEGORY_COLUMN])

            split = assign_split(group_key)
            split_counts[split] += 1
            category_counts[category_clean] += 1
            title_lengths.append(len(name_clean))
            if len(price_values_for_stats) < PRICE_SAMPLE_CAP:
                price_values_for_stats.append(float(price))

            out_row = {
                ID_COLUMN: asin,
                "product_name": name_clean,
                "product_name_raw": row_dict[NAME_COLUMN],
                "category": category_clean,
                "category_raw": row_dict[CATEGORY_COLUMN],
                "price": float(price),
            }
            for pc in PASSTHROUGH_COLUMNS:
                out_row[pc] = row_dict.get(pc, "")

            out_rows[split].append(out_row)
            kept_rows += 1

        for split, rows in out_rows.items():
            if not rows:
                continue
            df_out = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
            path = file_handles[split]
            write_header = not files_ready[split]
            df_out.to_csv(
                path,
                mode="w" if write_header else "a",
                header=write_header,
                index=False,
                quoting=csv.QUOTE_MINIMAL,
            )
            files_ready[split] = True

    price_series = pd.Series(price_values_for_stats)
    quality_report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_FILE),
        "total_rows_in": total_rows,
        "dropped_invalid_price": dropped_invalid_price,
        "kept_rows": kept_rows,
        "missing_id_count": missing_asin_count,
        "duplicate_id_count": duplicate_asin_count,
        "split_counts": dict(split_counts),
        "split_percentages": {
            k: round(v / kept_rows * 100, 2) for k, v in split_counts.items()
        } if kept_rows else {},
        "category_cardinality": len(category_counts),
        "top_20_categories": category_counts.most_common(20),
        "category_imbalance_warning": (
            category_counts.most_common(1)[0]
            if category_counts and category_counts.most_common(1)[0][1] / kept_rows > 0.20
            else None
        ),
        "price_stats_sampled": {
            "sample_size": len(price_series),
            "min": float(price_series.min()) if len(price_series) else None,
            "max": float(price_series.max()) if len(price_series) else None,
            "mean": float(price_series.mean()) if len(price_series) else None,
            "std": float(price_series.std()) if len(price_series) else None,
            "median": float(price_series.median()) if len(price_series) else None,
        },
        "title_length_stats": {
            "min": min(title_lengths) if title_lengths else None,
            "max": max(title_lengths) if title_lengths else None,
            "mean": round(sum(title_lengths) / len(title_lengths), 1) if title_lengths else None,
        },
        "known_limitations": [
            "No date/observed_at column in source data — split is grouped by "
            "product id (asin), not time-aware.",
            "Category imbalance: see category_imbalance_warning if present — "
            "one category may dominate the dataset.",
            "price is INR converted from GBP via a Numbeo cost-of-living PPP "
            "rate (London vs Mumbai specifically) — see "
            "products_inr.metadata.json for the exact rate/source used.",
        ],
    }
    with open(QUALITY_REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2, default=str)

    params = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "id_column": ID_COLUMN,
        "name_column": NAME_COLUMN,
        "category_column": CATEGORY_COLUMN,
        "price_column": PRICE_COLUMN,
        "train_pct": TRAIN_PCT,
        "val_pct": VAL_PCT,
        "test_pct": 100 - TRAIN_PCT - VAL_PCT,
        "split_method": "deterministic hash of id_column (md5 % 100)",
        "invalid_price_rule": "price must be a finite number > 0",
    }
    with open(PARAMS_FILE, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)

    print(f"Rows in:              {total_rows:,}")
    print(f"Dropped (bad price):  {dropped_invalid_price:,}")
    print(f"Kept:                 {kept_rows:,}")
    print(f"Split counts:         {dict(split_counts)}")
    print(f"Duplicate asin count: {duplicate_asin_count:,}")
    print(f"\nWrote: {TRAIN_FILE}")
    print(f"Wrote: {VAL_FILE}")
    print(f"Wrote: {TEST_FILE}")
    print(f"Wrote: {QUALITY_REPORT_FILE}")
    print(f"Wrote: {PARAMS_FILE}")


if __name__ == "__main__":
    fail_if_unconfigured()
    build()
