from __future__ import annotations

from typing import Dict, List

import pandas as pd


def quality_checks(df: pd.DataFrame) -> Dict[str, int]:
    checks = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "empty_rows": int(df.isna().all(axis=1).sum()),
        "empty_columns": int(df.isna().all(axis=0).sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }
    return checks


def detect_ss_profile(sheet_names: List[str]) -> Dict[str, object]:
    expected = {"Summary", "Lists", "Product 1"}
    present = set(sheet_names)
    missing = sorted(expected - present)
    return {
        "is_ss_workbook": len(missing) == 0,
        "expected_sheets": sorted(expected),
        "missing_sheets": missing,
    }


def product_sheet_checks(df: pd.DataFrame) -> Dict[str, object]:
    cols = [str(c).strip() for c in df.columns]
    lowered = [c.lower() for c in cols]

    # Common columns often used in requirement trackers.
    expected_markers = ["require", "status", "owner", "priority", "category"]
    found_columns = []
    for marker in expected_markers:
        match = next((c for c in cols if marker in c.lower()), None)
        if match:
            found_columns.append(match)

    likely_header_row_present = sum(1 for c in cols if c and c.lower() != "unnamed") >= 3

    return {
        "likely_header_row_present": likely_header_row_present,
        "matched_tracker_columns": found_columns,
        "matched_tracker_column_count": len(found_columns),
        "total_columns": len(cols),
    }
