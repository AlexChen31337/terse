#!/usr/bin/env python3
"""
CSV Analysis Script
-------------------
Performs basic inspection and data-quality checks on all CSV files
in a target directory.

Usage:
    uv run python scripts/analyze_csv.py [--dir /path/to/csv_data] [--output report.txt]

Checks performed per file:
  - File-level: size, encoding, empty file guard
  - Schema: dtypes, nulls, duplicate rows/columns
  - Numeric: describe() stats, outlier flags (IQR)
  - Categorical: cardinality, top-value frequency
  - Date/time columns: range, gap detection
"""

import argparse
import sys
import os
import io
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Dependency check — helpful error before pandas import fails
# ---------------------------------------------------------------------------
try:
    import pandas as pd
    import numpy as np
except ImportError as exc:
    print(f"[ERROR] Missing dependency: {exc}")
    print("Install with:  uv pip install pandas numpy")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sep(title: str, width: int = 72) -> str:
    bar = "=" * width
    return f"\n{bar}\n  {title}\n{bar}"


def _subsep(title: str, width: int = 60) -> str:
    return f"\n--- {title} " + "-" * max(0, width - len(title) - 5)


def _format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def inspect_file(path: Path) -> str:
    """Return a full inspection report for a single CSV file."""
    out = io.StringIO()

    def w(line: str = "") -> None:
        out.write(line + "\n")

    w(_sep(f"FILE: {path.name}"))
    w(f"  Path : {path}")
    w(f"  Size : {_format_bytes(path.stat().st_size)}")

    # ── Guard: empty file ──────────────────────────────────────────────────
    if path.stat().st_size == 0:
        w("\n  [SKIP] File is empty (0 bytes). No analysis performed.")
        return out.getvalue()

    # ── Load ───────────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(path, low_memory=False)
    except pd.errors.EmptyDataError:
        w("\n  [SKIP] File has no data (EmptyDataError). Possibly only whitespace.")
        return out.getvalue()
    except pd.errors.ParserError as exc:
        w(f"\n  [ERROR] Could not parse CSV: {exc}")
        return out.getvalue()
    except UnicodeDecodeError:
        # Retry with latin-1 fallback
        try:
            df = pd.read_csv(path, encoding="latin-1", low_memory=False)
            w("  Encoding: latin-1 (UTF-8 failed — check for special characters)")
        except Exception as exc:
            w(f"\n  [ERROR] Encoding error, could not load file: {exc}")
            return out.getvalue()
    except Exception as exc:
        w(f"\n  [ERROR] Unexpected error loading file: {exc}")
        return out.getvalue()

    # ── Guard: no rows ─────────────────────────────────────────────────────
    if df.empty:
        w(f"\n  [WARN] DataFrame is empty after loading (0 rows × {len(df.columns)} columns).")
        if len(df.columns):
            w(f"  Columns: {list(df.columns)}")
        return out.getvalue()

    n_rows, n_cols = df.shape
    w(f"  Shape: {n_rows:,} rows × {n_cols} columns")

    # ── 1. Head ────────────────────────────────────────────────────────────
    w(_subsep("HEAD (first 5 rows)"))
    try:
        w(df.head().to_string())
    except Exception as exc:
        w(f"  [WARN] Could not render head: {exc}")

    # ── 2. Info / dtypes ──────────────────────────────────────────────────
    w(_subsep("COLUMN INFO"))
    info_buf = io.StringIO()
    df.info(buf=info_buf, verbose=True, show_counts=True)
    w(info_buf.getvalue())

    # ── 3. Describe ────────────────────────────────────────────────────────
    w(_subsep("NUMERIC DESCRIBE"))
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols):
        try:
            w(df[numeric_cols].describe().to_string())
        except Exception as exc:
            w(f"  [WARN] describe() failed: {exc}")
    else:
        w("  No numeric columns found.")

    w(_subsep("CATEGORICAL / OBJECT DESCRIBE"))
    cat_cols = df.select_dtypes(include=["object", "str", "category", "bool"]).columns
    if len(cat_cols):
        try:
            w(df[cat_cols].describe().to_string())
        except Exception as exc:
            w(f"  [WARN] object describe() failed: {exc}")
    else:
        w("  No categorical / object columns found.")

    # ── 4. Data-quality checks ─────────────────────────────────────────────
    w(_subsep("DATA QUALITY CHECKS"))

    # 4a. Missing values
    null_counts = df.isnull().sum()
    null_pct = (null_counts / n_rows * 100).round(2)
    has_nulls = null_counts[null_counts > 0]
    if has_nulls.empty:
        w("  ✓ No missing values.")
    else:
        w(f"  ⚠ Missing values found in {len(has_nulls)} column(s):")
        for col in has_nulls.index:
            w(f"      {col!r:40s} {null_counts[col]:>6,} missing  ({null_pct[col]:.1f}%)")

    # 4b. Duplicate rows
    n_dupes = int(df.duplicated().sum())
    if n_dupes == 0:
        w("  ✓ No duplicate rows.")
    else:
        w(f"  ⚠ {n_dupes:,} duplicate row(s) ({n_dupes / n_rows * 100:.1f}% of data)")

    # 4c. Duplicate column names
    dup_cols = [c for c in df.columns if list(df.columns).count(c) > 1]
    if dup_cols:
        w(f"  ⚠ Duplicate column names: {list(dict.fromkeys(dup_cols))}")
    else:
        w("  ✓ No duplicate column names.")

    # 4d. Constant / near-constant columns
    const_cols = []
    for col in df.columns:
        try:
            if df[col].nunique(dropna=False) <= 1:
                const_cols.append(col)
        except TypeError:
            pass
    if const_cols:
        w(f"  ⚠ Constant columns (single unique value): {const_cols}")
    else:
        w("  ✓ No constant columns.")

    # 4e. High-cardinality object columns (possible ID leaks or data issues)
    high_card = []
    for col in cat_cols:
        try:
            nu = df[col].nunique()
            if nu > 0.9 * n_rows and n_rows > 20:
                high_card.append((col, nu))
        except TypeError:
            pass
    if high_card:
        w("  ⚠ High-cardinality object columns (>90% unique — may be IDs or free text):")
        for col, nu in high_card:
            w(f"      {col!r}: {nu:,} unique values")

    # 4f. Numeric outliers (IQR method, flag only)
    w(_subsep("NUMERIC OUTLIER SUMMARY  (IQR × 1.5)"))
    outlier_found = False
    for col in numeric_cols:
        try:
            series = df[col].dropna()
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            n_out = int(((series < lo) | (series > hi)).sum())
            if n_out > 0:
                outlier_found = True
                pct = n_out / len(series) * 100
                w(f"  {col!r:40s} {n_out:>6,} outlier(s)  ({pct:.1f}%)  "
                  f"bounds=[{lo:.3g}, {hi:.3g}]")
        except (TypeError, ValueError):
            pass
    if not outlier_found:
        w("  ✓ No outliers detected in numeric columns (or no numeric columns).")

    # 4g. Potential datetime columns
    w(_subsep("DATETIME DETECTION"))
    dt_candidates = []
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().head(100)
            try:
                parsed = pd.to_datetime(sample, infer_datetime_format=True, errors="coerce")
                if parsed.notna().sum() / max(len(sample), 1) > 0.8:
                    dt_candidates.append(col)
            except Exception:
                pass
    if dt_candidates:
        w(f"  Possible datetime columns: {dt_candidates}")
        for col in dt_candidates:
            try:
                parsed_col = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
                w(f"    {col!r}: min={parsed_col.min()}, max={parsed_col.max()}, "
                  f"nulls={parsed_col.isna().sum()}")
            except Exception:
                pass
    else:
        w("  No obvious datetime columns detected.")

    # ── 5. Value counts for low-cardinality columns ────────────────────────
    w(_subsep("TOP VALUE COUNTS  (categorical, ≤20 unique)"))
    shown = 0
    for col in cat_cols:
        try:
            nu = df[col].nunique()
            if nu <= 20:
                w(f"\n  Column: {col!r}  ({nu} unique values)")
                vc = df[col].value_counts(dropna=False).head(10)
                for val, cnt in vc.items():
                    w(f"    {str(val)!r:35s} {cnt:>6,}  ({cnt / n_rows * 100:.1f}%)")
                shown += 1
        except TypeError:
            pass
    if shown == 0:
        w("  No low-cardinality categorical columns to display.")

    return out.getvalue()


# ---------------------------------------------------------------------------
# Directory runner
# ---------------------------------------------------------------------------

def analyze_directory(data_dir: Path, output_path: Optional[Path] = None) -> None:
    csv_files = sorted(data_dir.glob("*.csv"))

    if not csv_files:
        msg = f"[INFO] No CSV files found in: {data_dir}"
        print(msg)
        if output_path:
            output_path.write_text(msg + "\n")
        return

    print(f"Found {len(csv_files)} CSV file(s) in {data_dir}")

    all_reports = []
    for fpath in csv_files:
        print(f"  Analysing: {fpath.name} …")
        try:
            report = inspect_file(fpath)
        except Exception as exc:
            report = _sep(f"FILE: {fpath.name}") + f"\n  [FATAL] Unexpected error: {exc}\n"
        all_reports.append(report)

    full_report = "\n".join(all_reports)
    full_report += f"\n\n{'=' * 72}\n  Analysis complete. {len(csv_files)} file(s) processed.\n{'=' * 72}\n"

    if output_path:
        output_path.write_text(full_report, encoding="utf-8")
        print(f"\nReport written to: {output_path}")
    else:
        print(full_report)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect and quality-check CSV files in a directory."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("/home/bowen/.openclaw/workspace/csv_data"),
        help="Directory containing CSV files (default: workspace/csv_data/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the report (prints to stdout if omitted)",
    )
    args = parser.parse_args()

    if not args.dir.exists():
        print(f"[ERROR] Directory not found: {args.dir}")
        print("Create it and place CSV files inside, then re-run.")
        sys.exit(1)

    if not args.dir.is_dir():
        print(f"[ERROR] Path is not a directory: {args.dir}")
        sys.exit(1)

    analyze_directory(args.dir, args.output)


if __name__ == "__main__":
    main()
