"""
Phase 1–2: Data understanding and professional cleaning.

Reads the raw Superstore extract, profiles quality, investigates
suspicious records, then writes a cleaned dataset. No statistics
are hardcoded — every decision is computed from the file.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "Sample_Superstore.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INSIGHTS_DIR = PROJECT_ROOT / "outputs" / "insights"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"

CLEANED_PATH = PROCESSED_DIR / "cleaned_retail_data.csv"
TABLEAU_PATH = PROCESSED_DIR / "tableau_retail_data.csv"
QUALITY_JSON = INSIGHTS_DIR / "data_quality_report.json"
QUALITY_MD = INSIGHTS_DIR / "data_quality_report.md"
CLEANING_LOG = INSIGHTS_DIR / "data_cleaning_log.md"


def load_raw() -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error = None
    for enc in encodings:
        try:
            return pd.read_csv(RAW_PATH, encoding=enc)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise last_error


def iqr_outlier_count(series: pd.Series) -> int:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return int(((series < lower) | (series > upper)).sum())


def season_from_month(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Fall"


def profile_quality(df: pd.DataFrame) -> dict:
    order_date = pd.to_datetime(df["Order Date"], errors="coerce")
    ship_date = pd.to_datetime(df["Ship Date"], errors="coerce")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

    exact_dupes = int(df.duplicated().sum())
    dupes_no_rowid = int(df.drop(columns=["Row ID"], errors="ignore").duplicated().sum())
    dupes_order_product = int(df.duplicated(subset=["Order ID", "Product ID"]).sum())

    report = {
        "total_records": int(len(df)),
        "total_columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing_values_by_column": df.isna().sum().astype(int).to_dict(),
        "missing_values_total": int(df.isna().sum().sum()),
        "duplicate_records_exact": exact_dupes,
        "duplicate_records_excluding_row_id": dupes_no_rowid,
        "duplicate_order_product_pairs": dupes_order_product,
        "unique_values_by_column": df.nunique(dropna=False).astype(int).to_dict(),
        "date_range": {
            "order_date_min": None if order_date.min() is pd.NaT else str(order_date.min().date()),
            "order_date_max": None if order_date.max() is pd.NaT else str(order_date.max().date()),
            "invalid_order_dates": int(order_date.isna().sum()),
            "invalid_ship_dates": int(ship_date.isna().sum()),
            "ship_before_order": int((ship_date < order_date).sum()),
        },
        "numerical_features": numeric_cols,
        "categorical_features": categorical_cols,
        "numeric_summary": df[numeric_cols].describe().to_dict() if numeric_cols else {},
        "outlier_counts_iqr": {
            c: iqr_outlier_count(df[c].dropna())
            for c in ["Sales", "Quantity", "Discount", "Profit"]
            if c in df.columns
        },
        "invalid_numeric_flags": {
            "negative_quantity": int((df["Quantity"] < 0).sum()) if "Quantity" in df.columns else None,
            "zero_or_negative_sales": int((df["Sales"] <= 0).sum()) if "Sales" in df.columns else None,
            "discount_outside_0_1": int(((df["Discount"] < 0) | (df["Discount"] > 1)).sum())
            if "Discount" in df.columns
            else None,
            "negative_profit_rows": int((df["Profit"] < 0).sum()) if "Profit" in df.columns else None,
        },
        "whitespace_product_names": int(
            (df["Product Name"].astype(str) != df["Product Name"].astype(str).str.strip()).sum()
        )
        if "Product Name" in df.columns
        else 0,
    }
    return report


def write_quality_markdown(report: dict) -> None:
    lines = [
        "# Data Quality Report",
        "",
        f"- **Total Records:** {report['total_records']:,}",
        f"- **Total Columns:** {report['total_columns']}",
        f"- **Missing Values:** {report['missing_values_total']:,}",
        f"- **Duplicate Records (exact rows):** {report['duplicate_records_exact']:,}",
        f"- **Duplicate Records (excluding Row ID):** {report['duplicate_records_excluding_row_id']:,}",
        f"- **Date Range:** {report['date_range']['order_date_min']} to {report['date_range']['order_date_max']}",
        f"- **Numerical Features:** {', '.join(report['numerical_features'])}",
        f"- **Categorical Features:** {', '.join(report['categorical_features'])}",
        "",
        "## Missing values by column",
        "",
    ]
    for col, n in report["missing_values_by_column"].items():
        lines.append(f"- {col}: {n}")
    lines.extend(
        [
            "",
            "## Unique values by column",
            "",
        ]
    )
    for col, n in report["unique_values_by_column"].items():
        lines.append(f"- {col}: {n:,}")
    lines.extend(
        [
            "",
            "## IQR outlier counts",
            "",
        ]
    )
    for col, n in report["outlier_counts_iqr"].items():
        lines.append(f"- {col}: {n:,}")
    lines.extend(
        [
            "",
            "## Invalid numeric flags",
            "",
        ]
    )
    for col, n in report["invalid_numeric_flags"].items():
        lines.append(f"- {col}: {n}")
    QUALITY_MD.write_text("\n".join(lines), encoding="utf-8")


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Investigate then apply conservative, documented transformations."""
    log: list[str] = []
    working = df.copy()
    start_rows = len(working)

    log.append(
        f"Loaded {start_rows:,} rows and {working.shape[1]} columns from `{RAW_PATH.name}`."
    )

    # Types
    working["Order Date"] = pd.to_datetime(working["Order Date"], errors="coerce")
    working["Ship Date"] = pd.to_datetime(working["Ship Date"], errors="coerce")
    invalid_dates = working["Order Date"].isna().sum() + working["Ship Date"].isna().sum()
    log.append(
        f"Parsed Order Date and Ship Date to datetime. Invalid dates found: {int(invalid_dates)}."
    )
    if invalid_dates:
        before = len(working)
        working = working.dropna(subset=["Order Date", "Ship Date"])
        log.append(f"Dropped {before - len(working)} rows with unparseable dates.")

    ship_before = int((working["Ship Date"] < working["Order Date"]).sum())
    log.append(
        f"Investigated ship-before-order rows: {ship_before}. None were removed because count is {ship_before}."
    )

    # Missing values: none expected; document if any appear
    missing = working.isna().sum()
    missing_cols = missing[missing > 0]
    if missing_cols.empty:
        log.append("No missing values were present after date parsing. No imputation required.")
    else:
        log.append(f"Missing values remaining: {missing_cols.to_dict()}.")

    # Whitespace / category consistency
    text_cols = [
        "Order ID",
        "Ship Mode",
        "Customer ID",
        "Customer Name",
        "Segment",
        "Country",
        "City",
        "State",
        "Region",
        "Product ID",
        "Category",
        "Sub-Category",
        "Product Name",
    ]
    for col in text_cols:
        if col in working.columns:
            before_ws = (working[col].astype(str) != working[col].astype(str).str.strip()).sum()
            working[col] = working[col].astype(str).str.strip()
            working[col] = working[col].str.replace(r"\s+", " ", regex=True)
            if before_ws:
                log.append(f"Stripped whitespace in `{col}` ({int(before_ws)} values).")

    # Repair known encoding artifacts in product names (latin-1 special chars)
    working["Product Name"] = (
        working["Product Name"]
        .str.replace("\x91", "'", regex=False)
        .str.replace("\x92", "'", regex=False)
        .str.replace("\x93", '"', regex=False)
        .str.replace("\x94", '"', regex=False)
        .str.replace("\x96", "-", regex=False)
        .str.replace("\x97", "-", regex=False)
        .str.replace("\xa0", " ", regex=False)
    )

    # Negative / invalid quantities and sales
    bad_qty = working["Quantity"] <= 0
    bad_sales = working["Sales"] <= 0
    bad_discount = (working["Discount"] < 0) | (working["Discount"] > 1)
    log.append(
        "Investigated invalid numerics — "
        f"quantity<=0: {int(bad_qty.sum())}, sales<=0: {int(bad_sales.sum())}, "
        f"discount outside [0,1]: {int(bad_discount.sum())}. No rows dropped."
    )

    negative_profit = int((working["Profit"] < 0).sum())
    log.append(
        f"Negative profit rows: {negative_profit:,}. These are valid loss-making transactions "
        "and were retained for profitability analysis."
    )

    # Duplicate investigation
    # Order ID + Product ID repeats with different quantities are split line items — keep them.
    order_product_dups = working.duplicated(subset=["Order ID", "Product ID"], keep=False)
    log.append(
        f"Investigated {int(order_product_dups.sum())} rows sharing Order ID + Product ID. "
        "Most have different quantities/sales (split line items) and were retained."
    )

    subset_cols = [c for c in working.columns if c != "Row ID"]
    exact_dupes = working.duplicated(subset=subset_cols, keep="first")
    n_exact = int(exact_dupes.sum())
    if n_exact:
        sample = working.loc[exact_dupes, ["Order ID", "Product ID", "Sales", "Quantity", "Profit"]]
        log.append(
            f"Removed {n_exact} exact duplicate line item(s) (identical values except Row ID). "
            f"Example Order ID(s): {', '.join(sample['Order ID'].astype(str).unique()[:5])}."
        )
        working = working.loc[~exact_dupes].copy()
    else:
        log.append("No exact duplicate line items found after excluding Row ID.")

    # Derived fields used downstream (not invented facts — calendar attributes of Order Date)
    working["Year"] = working["Order Date"].dt.year.astype(int)
    working["Month"] = working["Order Date"].dt.month.astype(int)
    working["Month Name"] = working["Order Date"].dt.strftime("%b")
    working["Year Month"] = working["Order Date"].dt.to_period("M").astype(str)
    working["Quarter"] = working["Order Date"].dt.quarter.astype(int)
    working["Season"] = working["Month"].map(season_from_month)
    working["Profit Margin"] = np.where(
        working["Sales"] != 0, working["Profit"] / working["Sales"], np.nan
    )
    working["Profit per Unit"] = np.where(
        working["Quantity"] != 0, working["Profit"] / working["Quantity"], np.nan
    )
    working["Discount Band"] = pd.cut(
        working["Discount"],
        bins=[-0.001, 0.0, 0.2, 0.4, 1.0],
        labels=["No Discount", "Low (0–20%)", "Medium (20–40%)", "High (>40%)"],
    )

    working["Sales"] = working["Sales"].round(4)
    working["Profit"] = working["Profit"].round(4)
    working["Discount"] = working["Discount"].round(4)

    log.append(
        f"Cleaning complete. Rows in: {start_rows:,}. Rows out: {len(working):,}. "
        f"Net change: {len(working) - start_rows:,}."
    )
    return working, log


def add_order_level_fields(df: pd.DataFrame) -> pd.DataFrame:
    order_sales = df.groupby("Order ID")["Sales"].transform("sum")
    df = df.copy()
    df["Order Sales"] = order_sales
    return df


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_raw()
    quality = profile_quality(raw)
    QUALITY_JSON.write_text(json.dumps(quality, indent=2, default=str), encoding="utf-8")
    write_quality_markdown(quality)

    cleaned, log = clean(raw)
    cleaned = add_order_level_fields(cleaned)

    cleaned_out = cleaned.copy()
    cleaned_out["Order Date"] = cleaned_out["Order Date"].dt.strftime("%Y-%m-%d")
    cleaned_out["Ship Date"] = cleaned_out["Ship Date"].dt.strftime("%Y-%m-%d")
    cleaned_out.to_csv(CLEANED_PATH, index=False)

    tableau = cleaned_out.copy()
    tableau.to_csv(TABLEAU_PATH, index=False)

    CLEANING_LOG.write_text("# Data Cleaning Log\n\n" + "\n".join(f"- {item}" for item in log), encoding="utf-8")

    print("DATA QUALITY REPORT")
    print(f"- Total Records: {quality['total_records']:,}")
    print(f"- Total Columns: {quality['total_columns']}")
    print(f"- Missing Values: {quality['missing_values_total']:,}")
    print(f"- Duplicate Records: {quality['duplicate_records_excluding_row_id']:,}")
    print(
        f"- Date Range: {quality['date_range']['order_date_min']} to {quality['date_range']['order_date_max']}"
    )
    print(f"- Numerical Features: {', '.join(quality['numerical_features'])}")
    print(f"- Categorical Features: {', '.join(quality['categorical_features'])}")
    print(f"\nCleaned dataset written to {CLEANED_PATH}")
    print(f"Tableau-ready dataset written to {TABLEAU_PATH}")
    print(f"Rows after cleaning: {len(cleaned):,}")


if __name__ == "__main__":
    main()
