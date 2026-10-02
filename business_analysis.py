"""
Phases 5–7: Profitability intelligence, seasonal analysis, KPIs, SQL execution,
insight generation, and Tableau-ready exports.

All figures are calculated from cleaned_retail_data.csv.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_retail_data.csv"
SQL_PATH = PROJECT_ROOT / "sql" / "retail_analysis.sql"
DB_PATH = PROJECT_ROOT / "data" / "processed" / "retail_orders.sqlite"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
INSIGHTS_DIR = PROJECT_ROOT / "outputs" / "insights"
CHARTS_DIR = PROJECT_ROOT / "outputs" / "charts"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:.1f}K"
    return f"{sign}${value:,.2f}"


def pct(value: float) -> str:
    return f"{value:.1f}%"


def load() -> pd.DataFrame:
    return pd.read_csv(CLEANED_PATH, parse_dates=["Order Date", "Ship Date"])


def compute_kpis(df: pd.DataFrame) -> dict:
    total_sales = float(df["Sales"].sum())
    total_profit = float(df["Profit"].sum())
    total_orders = int(df["Order ID"].nunique())
    total_qty = int(df["Quantity"].sum())
    margin = (total_profit / total_sales) * 100 if total_sales else float("nan")
    aov = total_sales / total_orders if total_orders else float("nan")
    profit_per_order = total_profit / total_orders if total_orders else float("nan")

    cat = df.groupby("Category").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    region = df.groupby("Region").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    region["Margin"] = region["Profit"] / region["Sales"] * 100

    kpis = {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "profit_margin_pct": margin,
        "total_orders": total_orders,
        "total_quantity": total_qty,
        "average_order_value": aov,
        "average_profit_per_order": profit_per_order,
        "top_category_by_sales": str(cat["Sales"].idxmax()),
        "top_category_sales": float(cat["Sales"].max()),
        "most_profitable_category": str(cat["Profit"].idxmax()),
        "most_profitable_category_profit": float(cat["Profit"].max()),
        "best_performing_region_by_profit": str(region["Profit"].idxmax()),
        "best_region_profit": float(region["Profit"].max()),
        "best_region_sales": float(region.loc[region["Profit"].idxmax(), "Sales"]),
        "best_region_margin_pct": float(region.loc[region["Profit"].idxmax(), "Margin"]),
        "line_items": int(len(df)),
        "customers": int(df["Customer ID"].nunique()),
        "products": int(df["Product Name"].nunique()),
        "date_min": str(df["Order Date"].min().date()),
        "date_max": str(df["Order Date"].max().date()),
    }
    return kpis


def performance_matrix(df: pd.DataFrame, grain: str) -> pd.DataFrame:
    grouped = (
        df.groupby(grain, as_index=False)
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Quantity=("Quantity", "sum"),
            Orders=("Order ID", "nunique"),
        )
    )
    grouped["Profit Margin %"] = grouped["Profit"] / grouped["Sales"] * 100
    sales_cut = grouped["Sales"].median()
    profit_cut = grouped["Profit"].median()
    qty_cut = grouped["Quantity"].median()

    def classify(row: pd.Series) -> str:
        high_sales = row["Sales"] >= sales_cut
        high_profit = row["Profit"] >= profit_cut
        if high_sales and high_profit:
            return "A. High Sales + High Profit"
        if high_sales and not high_profit:
            return "B. High Sales + Low Profit"
        if (not high_sales) and high_profit:
            return "C. Low Sales + High Profit"
        return "D. Low Sales + Low Profit"

    grouped["Performance Segment"] = grouped.apply(classify, axis=1)
    grouped["Quantity Flag"] = np.where(grouped["Quantity"] < qty_cut, "Below-median quantity", "At/above-median quantity")
    grouped["Sales Cut (median)"] = sales_cut
    grouped["Profit Cut (median)"] = profit_cut
    return grouped.sort_values("Profit", ascending=False)


def seasonal_analysis(df: pd.DataFrame) -> dict:
    monthly = (
        df.groupby("Year Month", as_index=False)
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Orders=("Order ID", "nunique"),
            Quantity=("Quantity", "sum"),
        )
        .sort_values("Year Month")
    )
    monthly["Profit Margin %"] = monthly["Profit"] / monthly["Sales"] * 100

    calendar_month = (
        df.assign(MonthNum=df["Order Date"].dt.month, MonthName=df["Order Date"].dt.strftime("%B"))
        .groupby(["MonthNum", "MonthName"], as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
    )
    calendar_month["Profit Margin %"] = calendar_month["Profit"] / calendar_month["Sales"] * 100

    seasonal = (
        df.groupby("Season", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
    )
    seasonal["Profit Margin %"] = seasonal["Profit"] / seasonal["Sales"] * 100

    best_sales_row = monthly.loc[monthly["Sales"].idxmax()]
    worst_sales_row = monthly.loc[monthly["Sales"].idxmin()]
    best_profit_row = monthly.loc[monthly["Profit"].idxmax()]
    worst_profit_row = monthly.loc[monthly["Profit"].idxmin()]
    best_margin_row = monthly.loc[monthly["Profit Margin %"].idxmax()]
    worst_margin_row = monthly.loc[monthly["Profit Margin %"].idxmin()]

    return {
        "monthly": monthly,
        "calendar_month": calendar_month,
        "seasonal": seasonal,
        "best_sales_month": str(best_sales_row["Year Month"]),
        "best_sales_value": float(best_sales_row["Sales"]),
        "worst_sales_month": str(worst_sales_row["Year Month"]),
        "worst_sales_value": float(worst_sales_row["Sales"]),
        "best_profit_month": str(best_profit_row["Year Month"]),
        "best_profit_value": float(best_profit_row["Profit"]),
        "worst_profit_month": str(worst_profit_row["Year Month"]),
        "worst_profit_value": float(worst_profit_row["Profit"]),
        "highest_margin_month": str(best_margin_row["Year Month"]),
        "highest_margin_pct": float(best_margin_row["Profit Margin %"]),
        "lowest_margin_month": str(worst_margin_row["Year Month"]),
        "lowest_margin_pct": float(worst_margin_row["Profit Margin %"]),
        "best_season_sales": str(seasonal.loc[seasonal["Sales"].idxmax(), "Season"]),
        "best_season_profit": str(seasonal.loc[seasonal["Profit"].idxmax(), "Season"]),
    }


def supporting_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    def margin(g: pd.DataFrame) -> pd.DataFrame:
        out = g.copy()
        out["Profit Margin %"] = out["Profit"] / out["Sales"] * 100
        return out

    category = margin(
        df.groupby("Category", as_index=False).agg(
            Sales=("Sales", "sum"), Profit=("Profit", "sum"), Quantity=("Quantity", "sum"), Orders=("Order ID", "nunique")
        )
    )
    subcat = margin(
        df.groupby(["Category", "Sub-Category"], as_index=False).agg(
            Sales=("Sales", "sum"), Profit=("Profit", "sum"), Quantity=("Quantity", "sum"), Orders=("Order ID", "nunique")
        )
    )
    region = margin(
        df.groupby("Region", as_index=False).agg(
            Sales=("Sales", "sum"), Profit=("Profit", "sum"), Quantity=("Quantity", "sum"), Orders=("Order ID", "nunique")
        )
    )
    segment = margin(
        df.groupby("Segment", as_index=False).agg(
            Sales=("Sales", "sum"), Profit=("Profit", "sum"), Quantity=("Quantity", "sum"), Orders=("Order ID", "nunique")
        )
    )
    products = margin(
        df.groupby(["Product Name", "Category", "Sub-Category"], as_index=False).agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Quantity=("Quantity", "sum"),
            Orders=("Order ID", "nunique"),
            Avg_Discount=("Discount", "mean"),
        )
    )
    discount = margin(
        df.groupby("Discount Band", observed=True, as_index=False).agg(
            Sales=("Sales", "sum"), Profit=("Profit", "sum"), Line_Items=("Row ID", "count")
        )
    )
    yearly = margin(
        df.groupby("Year", as_index=False).agg(
            Sales=("Sales", "sum"), Profit=("Profit", "sum"), Quantity=("Quantity", "sum"), Orders=("Order ID", "nunique")
        )
    )

    slow = products[(products["Quantity"] <= products["Quantity"].median()) & (products["Orders"] <= products["Orders"].median())]
    high_rev_low_margin = products[
        (products["Sales"] >= products["Sales"].median()) & (products["Profit Margin %"] < products["Profit Margin %"].median())
    ].sort_values("Sales", ascending=False)
    strong_margin = products[products["Profit Margin %"] > products["Profit Margin %"].quantile(0.75)].sort_values(
        "Profit Margin %", ascending=False
    )
    profit_drain = products[products["Profit"] < 0].sort_values("Profit")
    discount_review = products[
        (products["Avg_Discount"] >= 0.2) & (products["Profit"] < 0)
    ].sort_values("Profit")

    return {
        "category_performance": category.sort_values("Profit", ascending=False),
        "subcategory_performance": subcat.sort_values("Profit"),
        "region_performance": region.sort_values("Profit", ascending=False),
        "segment_performance": segment.sort_values("Profit", ascending=False),
        "top10_products_profit": products.nlargest(10, "Profit"),
        "bottom10_products_profit": products.nsmallest(10, "Profit"),
        "top10_products_sales": products.nlargest(10, "Sales"),
        "loss_making_products": profit_drain,
        "slow_moving_products": slow.sort_values(["Quantity", "Orders"]),
        "high_revenue_low_margin_products": high_rev_low_margin,
        "strong_margin_products": strong_margin,
        "products_discount_review": discount_review,
        "discount_band_performance": discount,
        "yearly_performance": yearly,
        "product_metrics": products,
    }


def build_insights(df: pd.DataFrame, kpis: dict, tables: dict[str, pd.DataFrame], seasonal: dict) -> list[str]:
    cat = tables["category_performance"]
    sub = tables["subcategory_performance"]
    region = tables["region_performance"]
    discount = tables["discount_band_performance"]
    yearly = tables["yearly_performance"]

    top_profit_cat = cat.iloc[0]
    weakest_cat = cat.sort_values("Profit Margin %").iloc[0]
    loss_sub = sub[sub["Profit"] < 0].sort_values("Profit")
    best_region = region.iloc[0]
    weakest_region_margin = region.sort_values("Profit Margin %").iloc[0]
    high_disc = discount.sort_values("Profit Margin %")

    insights = [
        (
            f"{top_profit_cat['Category']} is the most profitable category, generating "
            f"{money(top_profit_cat['Profit'])} profit on {money(top_profit_cat['Sales'])} sales "
            f"({pct(top_profit_cat['Profit Margin %'])} margin)."
        ),
        (
            f"{weakest_cat['Category']} is the weakest-margin category at "
            f"{pct(weakest_cat['Profit Margin %'])}, despite {money(weakest_cat['Sales'])} in sales."
        ),
    ]

    if not loss_sub.empty:
        row = loss_sub.iloc[0]
        insights.append(
            f"{row['Sub-Category']} is a profit-draining sub-category: {money(row['Sales'])} sales "
            f"produced {money(row['Profit'])} profit ({pct(row['Profit Margin %'])} margin)."
        )
        if len(loss_sub) > 1:
            names = ", ".join(loss_sub["Sub-Category"].tolist())
            insights.append(f"Loss-making sub-categories overall: {names}.")

    insights.append(
        f"{best_region['Region']} is the strongest region by profit ({money(best_region['Profit'])}, "
        f"{pct(best_region['Profit Margin %'])} margin), while {weakest_region_margin['Region']} "
        f"has the weakest regional margin at {pct(weakest_region_margin['Profit Margin %'])} "
        f"on {money(weakest_region_margin['Sales'])} sales."
    )

    insights.append(
        f"Sales peaked in {seasonal['best_sales_month']} ({money(seasonal['best_sales_value'])}) "
        f"and were lowest in {seasonal['worst_sales_month']} ({money(seasonal['worst_sales_value'])}). "
        f"{seasonal['best_season_sales']} is the strongest season by sales."
    )

    insights.append(
        f"The highest monthly profit occurred in {seasonal['best_profit_month']} "
        f"({money(seasonal['best_profit_value'])}); the weakest profit month was "
        f"{seasonal['worst_profit_month']} ({money(seasonal['worst_profit_value'])}). "
        f"Highest monthly margin: {seasonal['highest_margin_month']} ({pct(seasonal['highest_margin_pct'])})."
    )

    if not high_disc.empty:
        worst_band = high_disc.iloc[0]
        best_band = high_disc.iloc[-1]
        insights.append(
            f"Discounting is a material profit risk: the {worst_band['Discount Band']} band delivered "
            f"{pct(worst_band['Profit Margin %'])} margin versus {pct(best_band['Profit Margin %'])} "
            f"in the {best_band['Discount Band']} band."
        )

    corr = df[["Sales", "Quantity", "Discount", "Profit"]].corr()
    insights.append(
        f"Discount is negatively correlated with profit (r = {corr.loc['Discount', 'Profit']:.2f}), "
        f"while sales and profit move together more weakly (r = {corr.loc['Sales', 'Profit']:.2f})."
    )

    if len(yearly) >= 2:
        first = yearly.sort_values("Year").iloc[0]
        last = yearly.sort_values("Year").iloc[-1]
        sales_cagr_note = (
            f"Annual sales moved from {money(first['Sales'])} in {int(first['Year'])} "
            f"to {money(last['Sales'])} in {int(last['Year'])}, with profit margin "
            f"{pct(first['Profit Margin %'])} vs {pct(last['Profit Margin %'])}."
        )
        insights.append(sales_cagr_note)

    loss_n = int((tables["loss_making_products"].shape[0]))
    insights.append(
        f"{loss_n:,} products are net loss-making over the period and should be treated as "
        "portfolio risk, not merely low-volume SKUs."
    )

    # keep 6–10 concise bullets for dashboard; store all
    return insights


def build_recommendations(tables: dict[str, pd.DataFrame], seasonal: dict, insights: list[str]) -> list[dict]:
    sub = tables["subcategory_performance"]
    loss_sub = sub[sub["Profit"] < 0]
    high_disc = tables["discount_band_performance"].sort_values("Profit Margin %")
    region = tables["region_performance"].sort_values("Profit Margin %")
    slow_n = len(tables["slow_moving_products"])
    drain_n = len(tables["loss_making_products"])
    review_n = len(tables["products_discount_review"])
    strong_cat = tables["category_performance"].iloc[0]["Category"]

    recs = []

    if not loss_sub.empty:
        names = ", ".join(loss_sub["Sub-Category"].tolist())
        recs.append(
            {
                "theme": "Product portfolio optimization",
                "finding": f"Sub-categories currently destroying profit: {names}.",
                "action": (
                    "Reprice, bundle, or delist chronic loss-makers after reviewing contribution "
                    "to customer baskets. Do not expand inventory in these families until margin is positive."
                ),
            }
        )

    if not high_disc.empty:
        worst = high_disc.iloc[0]
        recs.append(
            {
                "theme": "Discount optimization",
                "finding": (
                    f"{worst['Discount Band']} transactions produced {pct(worst['Profit Margin %'])} margin "
                    f"on {money(worst['Sales'])} sales."
                ),
                "action": (
                    "Cap deep discounts on already-negative-margin SKUs. Require a margin floor before "
                    "promotions above 20%, especially in Furniture."
                ),
            }
        )

    recs.append(
        {
            "theme": "Pricing optimization",
            "finding": f"{review_n:,} products combine average discount ≥ 20% with negative profit.",
            "action": (
                "Review list price and promotional eligibility for these SKUs. High-revenue, low-margin "
                "items should be repriced before further discounting."
            ),
        }
    )

    recs.append(
        {
            "theme": "Inventory optimization",
            "finding": (
                f"{slow_n:,} products sit at or below median quantity and order frequency "
                "(slow-moving candidates)."
            ),
            "action": (
                "Reduce replenishment on slow movers that are also low-profit. Keep inventory on "
                "high-sales/high-profit products that also move quickly."
            ),
        }
    )

    recs.append(
        {
            "theme": "Regional strategy",
            "finding": (
                f"{region.iloc[0]['Region']} has the weakest margin ({pct(region.iloc[0]['Profit Margin %'])}); "
                f"{region.iloc[-1]['Region']} has the strongest ({pct(region.iloc[-1]['Profit Margin %'])})."
            ),
            "action": (
                "Audit mix and discounting in the weakest-margin region. Replicate assortment and "
                "pricing discipline from the strongest-margin region."
            ),
        }
    )

    recs.append(
        {
            "theme": "Seasonal planning",
            "finding": (
                f"Demand and profit concentrate toward {seasonal['best_season_sales']}; "
                f"the weakest sales month in the series is {seasonal['worst_sales_month']}."
            ),
            "action": (
                "Align working capital and promotions with the peak season rather than pushing "
                "deep discounts in already-weak months if those months also show poor margins."
            ),
        }
    )

    seg = tables["segment_performance"].sort_values("Profit", ascending=False)
    top_seg = seg.iloc[0]
    weak_seg = tables["segment_performance"].sort_values("Profit Margin %").iloc[0]
    recs.append(
        {
            "theme": "Customer segment strategy",
            "finding": (
                f"{top_seg['Segment']} contributes the most profit ({money(top_seg['Profit'])} on "
                f"{money(top_seg['Sales'])}, {pct(top_seg['Profit Margin %'])} margin). "
                f"{weak_seg['Segment']} has the weakest segment margin at {pct(weak_seg['Profit Margin %'])}."
            ),
            "action": (
                f"Protect {top_seg['Segment']} share in {strong_cat}. Improve mix and discount discipline "
                f"for {weak_seg['Segment']} rather than chasing volume alone."
            ),
        }
    )

    recs.append(
        {
            "theme": "Risk control",
            "finding": f"{drain_n:,} products are net unprofitable.",
            "action": (
                "Create a monthly 'profit leak' watchlist of the worst 25 SKUs and assign owners "
                "for price, discount, or discontinuation decisions."
            ),
        }
    )
    return recs


def matrix_explainer() -> dict[str, str]:
    return {
        "A. High Sales + High Profit": (
            "Core engines of the business. Protect availability, avoid unnecessary discounting, "
            "and invest in inventory and visibility."
        ),
        "B. High Sales + Low Profit": (
            "Revenue-rich but economically weak. These SKUs inflate the top line while consuming "
            "working capital. Immediate pricing, discount, and cost review."
        ),
        "C. Low Sales + High Profit": (
            "Hidden margin gems. Consider targeted marketing, better placement, or bundling "
            "to grow volume without giving away margin."
        ),
        "D. Low Sales + Low Profit": (
            "Candidates for rationalization. If they are also slow-moving, reduce stock or exit "
            "unless they serve a strategic basket role."
        ),
    }


def export_tables(tables: dict[str, pd.DataFrame], product_matrix: pd.DataFrame, subcat_matrix: pd.DataFrame, seasonal: dict) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(TABLES_DIR / f"{name}.csv", index=False)
    product_matrix.to_csv(TABLES_DIR / "product_performance_matrix.csv", index=False)
    subcat_matrix.to_csv(TABLES_DIR / "subcategory_performance_matrix.csv", index=False)
    seasonal["monthly"].to_csv(TABLES_DIR / "monthly_trend.csv", index=False)
    seasonal["calendar_month"].to_csv(TABLES_DIR / "calendar_month_performance.csv", index=False)
    seasonal["seasonal"].to_csv(TABLES_DIR / "seasonal_performance.csv", index=False)

    summary = subcat_matrix.groupby("Performance Segment").size().rename("Count").reset_index()
    summary.to_csv(TABLES_DIR / "performance_matrix_counts.csv", index=False)


def strip_sql_comments(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        lines.append(re.sub(r"--.*$", "", line))
    return "\n".join(lines)


def split_sql_statements(sql: str) -> list[str]:
    cleaned = strip_sql_comments(sql)
    parts = [p.strip() for p in cleaned.split(";")]
    return [p for p in parts if p]


def run_sql(df: pd.DataFrame) -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    sql_out = TABLES_DIR / "sql_query_results"
    sql_out.mkdir(exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    export = df.copy()
    export["Order Date"] = pd.to_datetime(export["Order Date"]).dt.strftime("%Y-%m-%d")
    export["Ship Date"] = pd.to_datetime(export["Ship Date"]).dt.strftime("%Y-%m-%d")
    export.to_sql("retail_orders", conn, index=False)
    statements = split_sql_statements(SQL_PATH.read_text(encoding="utf-8"))
    ran = 0
    with_rows = 0
    for i, stmt in enumerate(statements, start=1):
        cur = conn.execute(stmt)
        if stmt.lstrip().upper().startswith("PRAGMA"):
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            pd.DataFrame(rows, columns=cols).to_csv(sql_out / f"query_{i:02d}.csv", index=False)
            with_rows += 1
        elif cur.description is not None:
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            pd.DataFrame(rows, columns=cols).to_csv(sql_out / f"query_{i:02d}.csv", index=False)
            with_rows += 1
        ran += 1
    conn.close()
    (INSIGHTS_DIR / "sql_execution_log.json").write_text(
        json.dumps({"statements_executed": ran, "result_sets_written": with_rows}, indent=2),
        encoding="utf-8",
    )


def executive_dashboard(df: pd.DataFrame, kpis: dict, tables: dict[str, pd.DataFrame], seasonal: dict, insights: list[str]) -> None:
    """Static executive preview used when Tableau Desktop is not available in this environment."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    navy, teal, coral, slate = "#1B3A6B", "#2A9D8F", "#E76F51", "#334155"
    fig = plt.figure(figsize=(18, 11.2), facecolor="#EEF2F7")
    fig.suptitle(
        "RETAIL BUSINESS PERFORMANCE & PROFITABILITY ANALYSIS",
        fontsize=18,
        fontweight="bold",
        color=navy,
        y=0.98,
    )
    fig.text(
        0.5,
        0.945,
        "Turning Retail Data into Profitable Decisions  |  Profitability Intelligence preview",
        ha="center",
        fontsize=10,
        color=slate,
    )

    kpi_items = [
        ("TOTAL SALES", money(kpis["total_sales"])),
        ("TOTAL PROFIT", money(kpis["total_profit"])),
        ("PROFIT MARGIN", pct(kpis["profit_margin_pct"])),
        ("TOTAL ORDERS", f"{kpis['total_orders']:,}"),
        ("AVG ORDER VALUE", money(kpis["average_order_value"])),
    ]
    for i, (label, value) in enumerate(kpi_items):
        ax = fig.add_axes([0.03 + i * 0.19, 0.84, 0.175, 0.08])
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color("#D0D7E2")
        ax.set_facecolor("white")
        ax.text(0.06, 0.68, label, fontsize=8, color="#64748B", transform=ax.transAxes)
        ax.text(0.06, 0.18, value, fontsize=16, fontweight="bold", color=navy, transform=ax.transAxes)

    monthly = seasonal["monthly"]
    ax1 = fig.add_axes([0.05, 0.52, 0.58, 0.28])
    ax1.plot(monthly["Year Month"], monthly["Sales"], color=navy, lw=2, label="Sales")
    ax1b = ax1.twinx()
    ax1b.plot(monthly["Year Month"], monthly["Profit"], color=teal, lw=2, label="Profit")
    ax1.set_title("Monthly Sales & Profit Trend", loc="left", fontsize=11, color=navy, pad=8)
    ax1.tick_params(axis="x", labelsize=6, rotation=90)
    ax1.set_facecolor("white")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1b.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

    cat = tables["category_performance"].sort_values("Sales")
    ax2 = fig.add_axes([0.68, 0.52, 0.28, 0.28])
    ax2.barh(cat["Category"], cat["Sales"], color=navy)
    ax2.set_title("Sales by Category", loc="left", fontsize=11, color=navy)
    ax2.set_facecolor("white")

    region = tables["region_performance"]
    ax3 = fig.add_axes([0.05, 0.28, 0.28, 0.20])
    ax3.bar(region["Region"], region["Sales"], color=navy, label="Sales")
    ax3.bar(region["Region"], region["Profit"], color=teal, label="Profit")
    ax3.set_title("Sales & Profit by Region", loc="left", fontsize=11, color=navy)
    ax3.legend(fontsize=7)
    ax3.set_facecolor("white")

    sub = tables["subcategory_performance"].sort_values("Profit Margin %")
    ax4 = fig.add_axes([0.37, 0.28, 0.28, 0.20])
    colors = [coral if v < 0 else teal for v in sub["Profit Margin %"]]
    ax4.barh(sub["Sub-Category"], sub["Profit Margin %"], color=colors)
    ax4.axvline(0, color=slate, lw=0.6)
    ax4.set_title("Profit Margin by Sub-Category", loc="left", fontsize=11, color=navy)
    ax4.tick_params(axis="y", labelsize=7)
    ax4.set_facecolor("white")

    top = tables["top10_products_profit"].sort_values("Profit")
    ax5 = fig.add_axes([0.69, 0.28, 0.28, 0.20])
    labels = [n if len(n) < 32 else n[:29] + "..." for n in top["Product Name"]]
    ax5.barh(labels, top["Profit"], color=teal)
    ax5.set_title("Top Products by Profit", loc="left", fontsize=11, color=navy)
    ax5.tick_params(axis="y", labelsize=7)
    ax5.set_facecolor("white")

    ax6 = fig.add_axes([0.05, 0.04, 0.92, 0.21])
    ax6.set_xticks([])
    ax6.set_yticks([])
    ax6.set_facecolor("white")
    for spine in ax6.spines.values():
        spine.set_color("#D0D7E2")
    ax6.text(0.015, 0.86, "WHAT THE DATA TELLS US", fontsize=11, fontweight="bold", color=navy, transform=ax6.transAxes)
    clipped = []
    for line in insights[:5]:
        clipped.append(line if len(line) <= 175 else line[:172] + "...")
    text = "\n".join(f"• {line}" for line in clipped).replace("$", r"\$")
    ax6.text(0.015, 0.72, text, fontsize=8.0, color=slate, va="top", transform=ax6.transAxes)

    out = CHARTS_DIR / "00_executive_dashboard_preview.png"
    fig.savefig(out, dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(SCREENSHOTS_DIR / "executive_dashboard_preview.png", dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def write_insight_docs(kpis: dict, insights: list[str], recs: list[dict], seasonal: dict, matrix_counts: pd.Series) -> None:
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "kpis": kpis,
        "seasonal_highlights": {
            k: v for k, v in seasonal.items() if k not in {"monthly", "calendar_month", "seasonal"}
        },
        "insights": insights,
        "recommendations": recs,
        "performance_matrix_counts": matrix_counts.to_dict(),
        "matrix_definitions": matrix_explainer(),
        "column_mapping": {
            "Order Date": "Order Date (transaction date)",
            "Sales": "line-item sales",
            "Profit": "line-item profit",
            "Discount": "line-item discount rate",
            "Quantity": "units sold",
            "Category / Sub-Category": "product hierarchy",
            "Region / Segment": "geography and customer type",
            "Season": "derived from Order Date month (US meteorological grouping)",
        },
    }
    (INSIGHTS_DIR / "business_insights.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    md = ["# Key Business Insights", "", "## KPIs", ""]
    md.append(f"- Total Sales: {money(kpis['total_sales'])}")
    md.append(f"- Total Profit: {money(kpis['total_profit'])}")
    md.append(f"- Profit Margin: {pct(kpis['profit_margin_pct'])}")
    md.append(f"- Total Orders: {kpis['total_orders']:,}")
    md.append(f"- Total Quantity: {kpis['total_quantity']:,}")
    md.append(f"- Average Order Value: {money(kpis['average_order_value'])}")
    md.append(f"- Average Profit per Order: {money(kpis['average_profit_per_order'])}")
    md.append(f"- Top Category (Sales): {kpis['top_category_by_sales']}")
    md.append(f"- Most Profitable Category: {kpis['most_profitable_category']}")
    md.append(f"- Best Performing Region (Profit): {kpis['best_performing_region_by_profit']}")
    md.extend(["", "## What the data tells us", ""])
    md.extend([f"- {x}" for x in insights])
    md.extend(["", "## Business recommendations", ""])
    for rec in recs:
        md.append(f"### {rec['theme']}")
        md.append(f"- Finding: {rec['finding']}")
        md.append(f"- Action: {rec['action']}")
        md.append("")
    md.extend(["", "## Performance matrix meaning", ""])
    for k, v in matrix_explainer().items():
        md.append(f"- **{k}:** {v}")
    (INSIGHTS_DIR / "business_insights.md").write_text("\n".join(md), encoding="utf-8")

    kpi_df = pd.DataFrame(
        [
            {"KPI": "Total Sales", "Value": kpis["total_sales"]},
            {"KPI": "Total Profit", "Value": kpis["total_profit"]},
            {"KPI": "Profit Margin %", "Value": kpis["profit_margin_pct"]},
            {"KPI": "Total Orders", "Value": kpis["total_orders"]},
            {"KPI": "Total Quantity", "Value": kpis["total_quantity"]},
            {"KPI": "Average Order Value", "Value": kpis["average_order_value"]},
            {"KPI": "Average Profit per Order", "Value": kpis["average_profit_per_order"]},
            {"KPI": "Top Category by Sales", "Value": kpis["top_category_by_sales"]},
            {"KPI": "Most Profitable Category", "Value": kpis["most_profitable_category"]},
            {"KPI": "Best Performing Region", "Value": kpis["best_performing_region_by_profit"]},
        ]
    )
    kpi_df.to_csv(TABLES_DIR / "kpi_summary.csv", index=False)


def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load()
    kpis = compute_kpis(df)
    tables = supporting_tables(df)
    seasonal = seasonal_analysis(df)
    product_matrix = performance_matrix(df, "Product Name")
    subcat_matrix = performance_matrix(df, "Sub-Category")
    export_tables(tables, product_matrix, subcat_matrix, seasonal)
    insights = build_insights(df, kpis, tables, seasonal)
    recs = build_recommendations(tables, seasonal, insights)
    write_insight_docs(kpis, insights, recs, seasonal, subcat_matrix["Performance Segment"].value_counts())
    run_sql(df)
    executive_dashboard(df, kpis, tables, seasonal, insights)
    print("KPIs")
    for k, v in kpis.items():
        print(f"  {k}: {v}")
    print(f"Insights written: {len(insights)}")
    print(f"SQL database: {DB_PATH}")


if __name__ == "__main__":
    main()
