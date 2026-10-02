"""
Phase 4: Exploratory data analysis.

Every chart answers a business question. Values are computed from
cleaned_retail_data.csv — nothing is hardcoded.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_retail_data.csv"
CHARTS_DIR = PROJECT_ROOT / "outputs" / "charts"

NAVY = "#1B3A6B"
INDIGO = "#2F4F8A"
STEEL = "#4A7BA7"
TEAL = "#2A9D8F"
AMBER = "#E9C46A"
CORAL = "#E76F51"
SLATE = "#334155"
BG = "#F7F9FC"


def style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": BG,
            "axes.edgecolor": "#D6DEE8",
            "axes.labelcolor": SLATE,
            "text.color": SLATE,
            "axes.titlesize": 13,
            "axes.titleweight": "semibold",
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    path = CHARTS_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def load() -> pd.DataFrame:
    df = pd.read_csv(CLEANED_PATH, parse_dates=["Order Date", "Ship Date"])
    return df


def chart_distributions(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    sns.histplot(np.log10(df["Sales"].clip(lower=0.01)), ax=axes[0], color=NAVY, bins=40)
    axes[0].set_title("Sales Distribution (log10) — How concentrated is revenue?")
    axes[0].set_xlabel("log10(Sales)")

    sns.histplot(df["Profit"], ax=axes[1], color=STEEL, bins=50)
    axes[1].set_title("Profit Distribution — Are losses frequent?")
    axes[1].set_xlabel("Profit")

    sns.countplot(x="Quantity", data=df, ax=axes[2], color=INDIGO)
    axes[2].set_title("Quantity Distribution — Typical units per line?")
    axes[2].set_xlabel("Quantity")
    save(fig, "01_distributions_sales_profit_quantity.png")


def chart_category(df: pd.DataFrame) -> None:
    cat = (
        df.groupby("Category", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .sort_values("Sales", ascending=True)
    )
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(cat["Category"], cat["Sales"], color=NAVY)
    ax.set_title("Sales by Category — Where does revenue concentrate?")
    ax.set_xlabel("Sales")
    save(fig, "02_sales_by_category.png")

    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = [CORAL if v < 0 else TEAL for v in cat.set_index("Category").loc[cat["Category"], "Profit"]]
    # align profit to same category order
    profit_vals = cat["Profit"]
    ax.barh(cat["Category"], profit_vals, color=[CORAL if v < 0 else TEAL for v in profit_vals])
    ax.set_title("Profit by Category — Does revenue convert to profit?")
    ax.set_xlabel("Profit")
    ax.axvline(0, color=SLATE, linewidth=0.8)
    save(fig, "03_profit_by_category.png")


def chart_subcategory(df: pd.DataFrame) -> None:
    sub = (
        df.groupby("Sub-Category", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .sort_values("Sales")
    )
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(sub["Sub-Category"], sub["Sales"], color=INDIGO)
    ax.set_title("Sales by Sub-Category — Which product families drive revenue?")
    ax.set_xlabel("Sales")
    save(fig, "04_sales_by_subcategory.png")

    sub_p = sub.sort_values("Profit")
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(
        sub_p["Sub-Category"],
        sub_p["Profit"],
        color=[CORAL if v < 0 else TEAL for v in sub_p["Profit"]],
    )
    ax.axvline(0, color=SLATE, linewidth=0.8)
    ax.set_title("Profit by Sub-Category — Which families create or destroy profit?")
    ax.set_xlabel("Profit")
    save(fig, "05_profit_by_subcategory.png")


def chart_region_segment(df: pd.DataFrame) -> None:
    region = (
        df.groupby("Region", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .sort_values("Sales", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    x = np.arange(len(region))
    w = 0.38
    ax.bar(x - w / 2, region["Sales"], width=w, color=NAVY, label="Sales")
    ax.bar(x + w / 2, region["Profit"], width=w, color=TEAL, label="Profit")
    ax.set_xticks(x)
    ax.set_xticklabels(region["Region"])
    ax.set_title("Regional Performance — Revenue vs profit by region")
    ax.legend()
    save(fig, "06_regional_performance.png")

    seg = (
        df.groupby("Segment", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .sort_values("Sales", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(seg))
    ax.bar(x - w / 2, seg["Sales"], width=w, color=NAVY, label="Sales")
    ax.bar(x + w / 2, seg["Profit"], width=w, color=TEAL, label="Profit")
    ax.set_xticks(x)
    ax.set_xticklabels(seg["Segment"])
    ax.set_title("Segment Performance — Which customer segment is most profitable?")
    ax.legend()
    save(fig, "07_segment_performance.png")


def chart_time(df: pd.DataFrame) -> None:
    monthly = (
        df.groupby("Year Month", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
        .sort_values("Year Month")
    )
    fig, ax = plt.subplots(figsize=(14, 4.8))
    ax.plot(monthly["Year Month"], monthly["Sales"], color=NAVY, linewidth=2, label="Sales")
    ax.set_title("Monthly Sales Trend — When does demand peak?")
    ax.set_ylabel("Sales")
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    save(fig, "08_monthly_sales_trend.png")

    fig, ax = plt.subplots(figsize=(14, 4.8))
    ax.plot(monthly["Year Month"], monthly["Profit"], color=TEAL, linewidth=2, label="Profit")
    ax.axhline(0, color=CORAL, linewidth=0.8)
    ax.set_title("Monthly Profit Trend — Is growth profitable?")
    ax.set_ylabel("Profit")
    ax.tick_params(axis="x", rotation=90, labelsize=7)
    save(fig, "09_monthly_profit_trend.png")

    season_order = ["Winter", "Spring", "Summer", "Fall"]
    seasonal = (
        df.groupby("Season", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    )
    seasonal["Season"] = pd.Categorical(seasonal["Season"], season_order, ordered=True)
    seasonal = seasonal.sort_values("Season")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(seasonal))
    w = 0.38
    ax.bar(x - w / 2, seasonal["Sales"], width=w, color=NAVY, label="Sales")
    ax.bar(x + w / 2, seasonal["Profit"], width=w, color=TEAL, label="Profit")
    ax.set_xticks(x)
    ax.set_xticklabels(seasonal["Season"])
    ax.set_title("Seasonal Performance — Which season is strongest?")
    ax.legend()
    save(fig, "10_seasonal_performance.png")


def chart_relationships(df: pd.DataFrame) -> None:
    sample = df.sample(n=min(2500, len(df)), random_state=42)
    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.scatter(sample["Discount"], sample["Profit"], alpha=0.35, s=18, c=INDIGO, edgecolors="none")
    ax.axhline(0, color=CORAL, linewidth=0.8)
    ax.set_title("Discount vs Profit — Do deeper discounts destroy margin?")
    ax.set_xlabel("Discount")
    ax.set_ylabel("Profit")
    save(fig, "11_discount_vs_profit.png")

    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.scatter(sample["Sales"], sample["Profit"], alpha=0.35, s=18, c=NAVY, edgecolors="none")
    ax.axhline(0, color=CORAL, linewidth=0.8)
    ax.set_title("Sales vs Profit — Does higher revenue guarantee profit?")
    ax.set_xlabel("Sales")
    ax.set_ylabel("Profit")
    save(fig, "12_sales_vs_profit.png")

    corr = df[["Sales", "Quantity", "Discount", "Profit"]].corr()
    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="Blues", ax=ax, vmin=-1, vmax=1)
    ax.set_title("Correlation Matrix — How do core measures move together?")
    save(fig, "13_correlation_matrix.png")


def chart_products(df: pd.DataFrame) -> None:
    products = (
        df.groupby("Product Name", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Quantity=("Quantity", "sum"))
    )
    top = products.nlargest(10, "Profit").sort_values("Profit")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(top["Product Name"], top["Profit"], color=TEAL)
    ax.set_title("Top 10 Products by Profit — Where should we protect share?")
    ax.set_xlabel("Profit")
    save(fig, "14_top10_products_profit.png")

    bottom = products.nsmallest(10, "Profit").sort_values("Profit", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(bottom["Product Name"], bottom["Profit"], color=CORAL)
    ax.set_title("Bottom 10 Products by Profit — Where is value leaking?")
    ax.set_xlabel("Profit")
    save(fig, "15_bottom10_products_profit.png")

    loss = products[products["Profit"] < 0].nsmallest(15, "Profit").sort_values("Profit")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(loss["Product Name"], loss["Profit"], color=CORAL)
    ax.set_title("Largest Loss-Making Products — Profit-draining SKUs")
    ax.set_xlabel("Profit")
    save(fig, "16_loss_making_products.png")


def chart_outliers(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    sns.boxplot(y=df["Sales"], ax=axes[0], color=STEEL)
    axes[0].set_title("Sales Outliers")
    sns.boxplot(y=df["Profit"], ax=axes[1], color=TEAL)
    axes[1].set_title("Profit Outliers")
    sns.boxplot(y=df["Discount"], ax=axes[2], color=AMBER)
    axes[2].set_title("Discount Outliers")
    fig.suptitle("Outlier Analysis — Extreme transactions that skew totals", fontsize=13, y=1.02)
    save(fig, "17_outlier_boxplots.png")

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    band = (
        df.groupby("Discount Band", observed=True)
        .agg(Profit=("Profit", "sum"), Sales=("Sales", "sum"))
        .reset_index()
    )
    band["Margin"] = band["Profit"] / band["Sales"] * 100
    ax.bar(band["Discount Band"].astype(str), band["Margin"], color=NAVY)
    ax.axhline(0, color=CORAL, linewidth=0.8)
    ax.set_title("Profit Margin by Discount Band — Pricing risk")
    ax.set_ylabel("Profit Margin %")
    ax.tick_params(axis="x", rotation=15)
    save(fig, "18_margin_by_discount_band.png")


def main() -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    style()
    df = load()
    chart_distributions(df)
    chart_category(df)
    chart_subcategory(df)
    chart_region_segment(df)
    chart_time(df)
    chart_relationships(df)
    chart_products(df)
    chart_outliers(df)
    print(f"Wrote EDA charts to {CHARTS_DIR}")


if __name__ == "__main__":
    main()
