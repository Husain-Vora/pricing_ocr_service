"""
Convert GBP prices in the raw product dataset to INR using a Purchasing
Power Parity (PPP) conversion factor — not a market FX rate. See the
Phase 2 conversation for why PPP was chosen over FX for this use case.

This never touches the original file. It reads INPUT_FILE and writes a
NEW file at OUTPUT_FILE, plus a metadata sidecar JSON recording exactly
which rate/source/date was used — required for Phase 10's traceability
gate ("every prediction traceable to ... metadata").

Usage:
    1. Fill in PPP_RATE, RATE_SOURCE_URL, RATE_AS_OF below with a real,
       looked-up number. Do not guess — see instructions in the chat
       message this script came with.
    2. Set INPUT_FILE / PRICE_COLUMN_GBP to match your actual file.
    3. python scripts/convert_gbp_to_inr_ppp.py
"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# --- fill these in from a real, current source before running ---
PPP_RATE = 29.67  # Numbeo cost-of-living comparison: London vs Mumbai
RATE_SOURCE_URL = "https://www.numbeo.com/cost-of-living/compare_cities.jsp?country1=United+Kingdom&city1=London&country2=India&city2=Mumbai"  # verify this matches the exact page you used
RATE_AS_OF = "2026-09"  # replace with the date you actually pulled this from Numbeo

# --- file locations ---
INPUT_FILE = Path("data/raw/products.csv")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "products_inr.csv"
METADATA_FILE = OUTPUT_DIR / "products_inr.metadata.json"

PRICE_COLUMN_GBP = "price"          # column holding the raw GBP price
PRICE_COLUMN_GBP_KEPT_AS = "price_gbp"  # original values preserved under this name
PRICE_COLUMN_INR = "price_inr"      # new column this script adds

CHUNKSIZE = 200_000


def fail_if_unconfigured():
    problems = []
    if PPP_RATE is None:
        problems.append("PPP_RATE is not set.")
    if not RATE_SOURCE_URL:
        problems.append("RATE_SOURCE_URL is not set.")
    if not RATE_AS_OF:
        problems.append("RATE_AS_OF is not set.")
    if not INPUT_FILE.exists():
        problems.append(f"INPUT_FILE does not exist: {INPUT_FILE}")
    if problems:
        print("Not configured yet:")
        for p in problems:
            print(f"  - {p}")
        print("\nEdit the constants at the top of this script, then re-run.")
        sys.exit(1)


def convert():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    converted_count = 0
    unparseable_count = 0

    reader = pd.read_csv(INPUT_FILE, chunksize=CHUNKSIZE, dtype=str, keep_default_na=False)
    first_chunk = True

    for chunk in reader:
        if PRICE_COLUMN_GBP not in chunk.columns:
            raise KeyError(
                f"Column '{PRICE_COLUMN_GBP}' not found. Actual columns: {list(chunk.columns)}"
            )

        total_rows += len(chunk)

        gbp_numeric = pd.to_numeric(chunk[PRICE_COLUMN_GBP], errors="coerce")
        unparseable_count += gbp_numeric.isna().sum()

        chunk[PRICE_COLUMN_GBP_KEPT_AS] = chunk[PRICE_COLUMN_GBP]
        chunk[PRICE_COLUMN_INR] = gbp_numeric * PPP_RATE
        converted_count += gbp_numeric.notna().sum()

        # drop the original bare "price" column name — price_gbp/price_inr
        # are now explicit so nothing downstream accidentally treats the
        # GBP figure as the training target.
        chunk = chunk.drop(columns=[PRICE_COLUMN_GBP])

        chunk.to_csv(
            OUTPUT_FILE,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False,
            quoting=csv.QUOTE_MINIMAL,
        )
        first_chunk = False

    metadata = {
        "script": "convert_gbp_to_inr_ppp.py",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_FILE),
        "conversion_method": "ppp",  # not market FX — see Phase 2 discussion
        "ppp_rate_gbp_to_inr": PPP_RATE,
        "rate_source_url": RATE_SOURCE_URL,
        "rate_as_of": RATE_AS_OF,
        "source_column": PRICE_COLUMN_GBP,
        "kept_original_as": PRICE_COLUMN_GBP_KEPT_AS,
        "new_column": PRICE_COLUMN_INR,
        "total_rows": int(total_rows),
        "converted_rows": int(converted_count),
        "unparseable_rows": int(unparseable_count),
        "known_limitation": (
            "Rate is a Numbeo cost-of-living comparison for London vs Mumbai "
            "specifically, not a national PPP average — receipts from other "
            "Indian cities may have a different real cost-of-living ratio to "
            "the UK. Also, this is a whole-basket consumer PPP, not "
            "category-specific: import duty and category-level retail "
            "structure differences between UK and India aren't separately "
            "corrected. Document both in Phase 10's evaluation report."
        ),
    }
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Rows read:          {total_rows:,}")
    print(f"Converted:          {converted_count:,}")
    print(f"Unparseable price:  {unparseable_count:,}  (became null in {PRICE_COLUMN_INR})")
    print(f"\nWrote: {OUTPUT_FILE}")
    print(f"Wrote: {METADATA_FILE}")


if __name__ == "__main__":
    fail_if_unconfigured()
    convert()
