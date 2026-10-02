"""Build the internship 1–2 page PDF from computed insight JSON (not hardcoded KPIs)."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSIGHTS = PROJECT_ROOT / "outputs" / "insights" / "business_insights.json"
QUALITY = PROJECT_ROOT / "outputs" / "insights" / "data_quality_report.json"
OUT = PROJECT_ROOT / "report" / "Retail_Business_Performance_Report.pdf"

NAVY = HexColor("#1B3A6B")
SLATE = HexColor("#334155")


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    value = abs(float(value))
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:.1f}K"
    return f"{sign}${value:,.2f}"


def pct(value: float) -> str:
    return f"{float(value):.1f}%"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            fontName="Times-Bold",
            fontSize=14,
            leading=17,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSub",
            fontName="Times-Italic",
            fontSize=10,
            leading=13,
            textColor=SLATE,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H",
            fontName="Times-Bold",
            fontSize=11,
            leading=13,
            textColor=NAVY,
            spaceBefore=7,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyJ",
            fontName="Times-Roman",
            fontSize=9.5,
            leading=12,
            textColor=SLATE,
            alignment=TA_JUSTIFY,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="InsightBullet",
            fontName="Times-Roman",
            fontSize=9.5,
            leading=12,
            textColor=SLATE,
            leftIndent=12,
            bulletIndent=0,
            spaceAfter=2,
        )
    )
    return styles


def main() -> None:
    data = json.loads(INSIGHTS.read_text(encoding="utf-8"))
    quality = json.loads(QUALITY.read_text(encoding="utf-8"))
    k = data["kpis"]
    insights = data["insights"]
    recs = data["recommendations"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.5 * inch,
        title="Retail Business Performance & Profitability Analysis",
        author="Profitability Intelligence Project",
    )
    s = build_styles()
    story = []

    story.append(Paragraph("Retail Business Performance &amp; Profitability Analysis", s["CoverTitle"]))
    story.append(Paragraph("Turning Retail Data into Profitable Business Decisions", s["CoverSub"]))
    story.append(
        Paragraph(
            f"Analysis window: {k['date_min']} to {k['date_max']} &nbsp;|&nbsp; "
            f"{k['line_items']:,} line items &nbsp;|&nbsp; {k['total_orders']:,} orders",
            s["BodyJ"],
        )
    )

    story.append(Paragraph("1. Introduction", s["H"]))
    story.append(
        Paragraph(
            "Retail growth is easy to misread when teams optimize for sales instead of profit. "
            "This project analyzes U.S. Superstore transactional orders to separate high-revenue "
            "activity from economically healthy activity. The work is designed for management: "
            "it quantifies where margin is created, where it is destroyed, and which product, "
            "region, discount, and seasonal patterns should change first.",
            s["BodyJ"],
        )
    )

    story.append(Paragraph("2. Abstract", s["H"]))
    story.append(
        Paragraph(
            f"The cleaned dataset contains {k['line_items']:,} line items across "
            f"{k['total_orders']:,} orders, {k['customers']:,} customers, and {k['products']:,} products "
            f"({quality['date_range']['order_date_min']}–{quality['date_range']['order_date_max']}). "
            f"Total sales are {money(k['total_sales'])} with {money(k['total_profit'])} profit "
            f"({pct(k['profit_margin_pct'])} overall margin). {k['most_profitable_category']} is the "
            f"profit leader; {k['best_performing_region_by_profit']} leads on regional profit. "
            "SQL aggregations, Python/Pandas profitability intelligence, and a Tableau-ready "
            "dashboard specification were used to produce KPIs, a sales–profit performance matrix, "
            "and recommendations tied to measured leaks in discounting and loss-making categories.",
            s["BodyJ"],
        )
    )

    story.append(Paragraph("3. Tools Used", s["H"]))
    story.append(
        Paragraph(
            "Python (Pandas, NumPy, Matplotlib, Seaborn), SQLite SQL (CTEs, window functions, "
            "GROUP BY, CASE), Tableau Desktop for the interactive executive dashboard, and ReportLab "
            "for this report. All KPIs are computed from cleaned_retail_data.csv; none are typed in by hand.",
            s["BodyJ"],
        )
    )

    story.append(Paragraph("4. Steps Involved in Building the Project", s["H"]))
    story.append(
        Paragraph(
            "1) Profiled the raw extract (shape, types, missingness, duplicates, date range, IQR outliers). "
            "2) Cleaned conservatively: parsed dates, trimmed text, retained valid loss rows, removed one "
            "exact duplicate line item after investigation. 3) Loaded the cleaned table into SQLite and ran "
            "sectioned business queries including profit-margin, ranking, discount bands, and slow movers. "
            "4) Produced Python EDA charts that each answer a business question. 5) Built a median-split "
            "performance matrix (high/low sales × high/low profit) at product and sub-category grain. "
            "6) Calculated KPIs, seasonal peaks, and auto-generated insights. 7) Packaged a Tableau-ready "
            "file plus calculated-field and layout instructions for the interactive dashboard.",
            s["BodyJ"],
        )
    )

    story.append(Paragraph("5. Key Insights", s["H"]))
    for item in insights[:6]:
        story.append(Paragraph(f"• {item}", s["InsightBullet"]))

    story.append(Paragraph("6. Business Recommendations", s["H"]))
    for rec in recs[:6]:
        story.append(
            Paragraph(
                f"• <b>{rec['theme']}:</b> {rec['finding']} {rec['action']}",
                s["InsightBullet"],
            )
        )

    story.append(Paragraph("7. Conclusion", s["H"]))
    story.append(
        Paragraph(
            f"The business is profitable in aggregate ({pct(k['profit_margin_pct'])} margin), but that "
            "headline hides concentrated leaks: loss-making sub-categories, high-discount transactions, "
            "and high-sales/low-profit SKUs. Management should govern the portfolio with a profitability "
            "lens—protect "
            f"{k['most_profitable_category']} and {k['best_performing_region_by_profit']}, "
            "cap uneconomic promotions, and treat slow, unprofitable products as inventory risk. "
            "The accompanying SQL, Python outputs, and Tableau dashboard make these findings filterable "
            "for ongoing decision support rather than a one-time report.",
            s["BodyJ"],
        )
    )

    page_state = {"n": 0}

    def _count(canvas, _doc):
        page_state["n"] = max(page_state["n"], canvas.getPageNumber())

    doc.build(story, onFirstPage=_count, onLaterPages=_count)
    print(f"Wrote {OUT} ({page_state['n']} page(s))")


if __name__ == "__main__":
    main()
