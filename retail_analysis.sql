-- =============================================================================
-- Retail Business Performance & Profitability Analysis
-- SQLite-compatible business SQL
-- Source table: retail_orders  (loaded from cleaned_retail_data.csv)
-- Profit Margin % = (SUM(Profit) / SUM(Sales)) * 100
-- =============================================================================

-- -----------------------------------------------------------------------------
-- SECTION 1: Basic dataset exploration
-- -----------------------------------------------------------------------------
SELECT COUNT(*) AS total_line_items FROM retail_orders;

SELECT COUNT(DISTINCT "Order ID") AS total_orders FROM retail_orders;

SELECT
    MIN("Order Date") AS first_order_date,
    MAX("Order Date") AS last_order_date,
    COUNT(DISTINCT Category) AS categories,
    COUNT(DISTINCT "Sub-Category") AS sub_categories,
    COUNT(DISTINCT Region) AS regions,
    COUNT(DISTINCT Segment) AS segments,
    COUNT(DISTINCT "Product Name") AS products
FROM retail_orders;

PRAGMA table_info(retail_orders);

-- -----------------------------------------------------------------------------
-- SECTION 2: Total sales
-- -----------------------------------------------------------------------------
SELECT ROUND(SUM(Sales), 2) AS total_sales
FROM retail_orders;

-- -----------------------------------------------------------------------------
-- SECTION 3: Total profit
-- -----------------------------------------------------------------------------
SELECT ROUND(SUM(Profit), 2) AS total_profit
FROM retail_orders;

-- -----------------------------------------------------------------------------
-- SECTION 4: Total orders
-- -----------------------------------------------------------------------------
SELECT COUNT(DISTINCT "Order ID") AS total_orders
FROM retail_orders;

-- -----------------------------------------------------------------------------
-- SECTION 5: Total quantity sold
-- -----------------------------------------------------------------------------
SELECT SUM(Quantity) AS total_quantity_sold
FROM retail_orders;

-- -----------------------------------------------------------------------------
-- SECTION 6: Average order value
-- -----------------------------------------------------------------------------
SELECT ROUND(SUM(Sales) * 1.0 / COUNT(DISTINCT "Order ID"), 2) AS average_order_value
FROM retail_orders;

-- -----------------------------------------------------------------------------
-- SECTION 7: Overall profit margin
-- -----------------------------------------------------------------------------
SELECT
    ROUND(SUM(Sales), 2) AS total_sales,
    ROUND(SUM(Profit), 2) AS total_profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders;

-- -----------------------------------------------------------------------------
-- SECTION 8: Sales by category
-- -----------------------------------------------------------------------------
SELECT
    Category,
    ROUND(SUM(Sales), 2) AS sales,
    COUNT(DISTINCT "Order ID") AS orders,
    SUM(Quantity) AS quantity
FROM retail_orders
GROUP BY Category
ORDER BY sales DESC;

-- -----------------------------------------------------------------------------
-- SECTION 9: Profit by category
-- -----------------------------------------------------------------------------
SELECT
    Category,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY Category
ORDER BY profit DESC;

-- -----------------------------------------------------------------------------
-- SECTION 10: Sales by sub-category
-- -----------------------------------------------------------------------------
SELECT
    Category,
    "Sub-Category" AS sub_category,
    ROUND(SUM(Sales), 2) AS sales,
    SUM(Quantity) AS quantity
FROM retail_orders
GROUP BY Category, "Sub-Category"
ORDER BY sales DESC;

-- -----------------------------------------------------------------------------
-- SECTION 11: Profit by sub-category
-- -----------------------------------------------------------------------------
SELECT
    Category,
    "Sub-Category" AS sub_category,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY Category, "Sub-Category"
ORDER BY profit ASC;

-- -----------------------------------------------------------------------------
-- SECTION 12: Region-wise sales
-- -----------------------------------------------------------------------------
SELECT
    Region,
    ROUND(SUM(Sales), 2) AS sales,
    COUNT(DISTINCT "Order ID") AS orders
FROM retail_orders
GROUP BY Region
ORDER BY sales DESC;

-- -----------------------------------------------------------------------------
-- SECTION 13: Region-wise profit
-- -----------------------------------------------------------------------------
SELECT
    Region,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY Region
ORDER BY profit DESC;

-- -----------------------------------------------------------------------------
-- SECTION 14: Category-wise profit margin
-- -----------------------------------------------------------------------------
SELECT
    Category,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY Category
ORDER BY profit_margin_pct DESC;

-- -----------------------------------------------------------------------------
-- SECTION 15: Sub-category-wise profit margin
-- -----------------------------------------------------------------------------
SELECT
    Category,
    "Sub-Category" AS sub_category,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY Category, "Sub-Category"
ORDER BY profit_margin_pct ASC;

-- -----------------------------------------------------------------------------
-- SECTION 16: Top 10 products by profit
-- -----------------------------------------------------------------------------
SELECT
    "Product Name" AS product_name,
    Category,
    "Sub-Category" AS sub_category,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY "Product Name", Category, "Sub-Category"
ORDER BY profit DESC
LIMIT 10;

-- -----------------------------------------------------------------------------
-- SECTION 17: Bottom 10 products by profit
-- -----------------------------------------------------------------------------
SELECT
    "Product Name" AS product_name,
    Category,
    "Sub-Category" AS sub_category,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY "Product Name", Category, "Sub-Category"
ORDER BY profit ASC
LIMIT 10;

-- -----------------------------------------------------------------------------
-- SECTION 18: Top 10 products by sales
-- -----------------------------------------------------------------------------
SELECT
    "Product Name" AS product_name,
    Category,
    "Sub-Category" AS sub_category,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY "Product Name", Category, "Sub-Category"
ORDER BY sales DESC
LIMIT 10;

-- -----------------------------------------------------------------------------
-- SECTION 19: Low-profit / loss-making products
-- -----------------------------------------------------------------------------
SELECT
    "Product Name" AS product_name,
    Category,
    "Sub-Category" AS sub_category,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct,
    SUM(Quantity) AS quantity
FROM retail_orders
GROUP BY "Product Name", Category, "Sub-Category"
HAVING SUM(Profit) < 0
ORDER BY profit ASC;

-- -----------------------------------------------------------------------------
-- SECTION 20: Monthly sales trend
-- -----------------------------------------------------------------------------
SELECT
    strftime('%Y-%m', "Order Date") AS year_month,
    ROUND(SUM(Sales), 2) AS sales,
    COUNT(DISTINCT "Order ID") AS orders
FROM retail_orders
GROUP BY strftime('%Y-%m', "Order Date")
ORDER BY year_month;

-- -----------------------------------------------------------------------------
-- SECTION 21: Monthly profit trend
-- -----------------------------------------------------------------------------
SELECT
    strftime('%Y-%m', "Order Date") AS year_month,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY strftime('%Y-%m', "Order Date")
ORDER BY year_month;

-- -----------------------------------------------------------------------------
-- SECTION 22: Year-wise performance
-- -----------------------------------------------------------------------------
SELECT
    CAST(strftime('%Y', "Order Date") AS INTEGER) AS year,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    COUNT(DISTINCT "Order ID") AS orders,
    SUM(Quantity) AS quantity,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct,
    ROUND(SUM(Sales) * 1.0 / COUNT(DISTINCT "Order ID"), 2) AS average_order_value
FROM retail_orders
GROUP BY CAST(strftime('%Y', "Order Date") AS INTEGER)
ORDER BY year;

-- -----------------------------------------------------------------------------
-- SECTION 23: Seasonal performance
-- -----------------------------------------------------------------------------
WITH seasonal AS (
    SELECT
        CASE
            WHEN CAST(strftime('%m', "Order Date") AS INTEGER) IN (12, 1, 2) THEN 'Winter'
            WHEN CAST(strftime('%m', "Order Date") AS INTEGER) IN (3, 4, 5) THEN 'Spring'
            WHEN CAST(strftime('%m', "Order Date") AS INTEGER) IN (6, 7, 8) THEN 'Summer'
            ELSE 'Fall'
        END AS season,
        CAST(strftime('%m', "Order Date") AS INTEGER) AS month_num,
        Sales,
        Profit,
        "Order ID"
    FROM retail_orders
)
SELECT
    season,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    COUNT(DISTINCT "Order ID") AS orders,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM seasonal
GROUP BY season
ORDER BY
    CASE season
        WHEN 'Winter' THEN 1
        WHEN 'Spring' THEN 2
        WHEN 'Summer' THEN 3
        ELSE 4
    END;

-- -----------------------------------------------------------------------------
-- SECTION 24: Discount vs profitability analysis
-- -----------------------------------------------------------------------------
SELECT
    CASE
        WHEN Discount = 0 THEN 'No Discount'
        WHEN Discount <= 0.20 THEN 'Low (0-20%)'
        WHEN Discount <= 0.40 THEN 'Medium (20-40%)'
        ELSE 'High (>40%)'
    END AS discount_band,
    COUNT(*) AS line_items,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND(AVG(Discount) * 100, 2) AS avg_discount_pct,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY
    CASE
        WHEN Discount = 0 THEN 'No Discount'
        WHEN Discount <= 0.20 THEN 'Low (0-20%)'
        WHEN Discount <= 0.40 THEN 'Medium (20-40%)'
        ELSE 'High (>40%)'
    END
ORDER BY avg_discount_pct;

SELECT
    Category,
    ROUND(AVG(Discount) * 100, 2) AS avg_discount_pct,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY Category
ORDER BY avg_discount_pct DESC;

-- -----------------------------------------------------------------------------
-- SECTION 25: High-sales but low-profit products
-- -----------------------------------------------------------------------------
WITH product_metrics AS (
    SELECT
        "Product Name" AS product_name,
        Category,
        "Sub-Category" AS sub_category,
        SUM(Sales) AS sales,
        SUM(Profit) AS profit,
        (SUM(Profit) / SUM(Sales)) * 100 AS profit_margin_pct
    FROM retail_orders
    GROUP BY "Product Name", Category, "Sub-Category"
),
thresholds AS (
    SELECT
        (SELECT AVG(sales) FROM product_metrics) AS avg_sales,
        (SELECT AVG(profit_margin_pct) FROM product_metrics) AS avg_margin
)
SELECT
    p.product_name,
    p.Category,
    p.sub_category,
    ROUND(p.sales, 2) AS sales,
    ROUND(p.profit, 2) AS profit,
    ROUND(p.profit_margin_pct, 2) AS profit_margin_pct
FROM product_metrics p
CROSS JOIN thresholds t
WHERE p.sales > t.avg_sales
  AND p.profit_margin_pct < t.avg_margin
ORDER BY p.sales DESC
LIMIT 25;

-- -----------------------------------------------------------------------------
-- SECTION 26: Low-sales but high-profit products
-- -----------------------------------------------------------------------------
WITH product_metrics AS (
    SELECT
        "Product Name" AS product_name,
        Category,
        "Sub-Category" AS sub_category,
        SUM(Sales) AS sales,
        SUM(Profit) AS profit,
        (SUM(Profit) / SUM(Sales)) * 100 AS profit_margin_pct
    FROM retail_orders
    GROUP BY "Product Name", Category, "Sub-Category"
),
thresholds AS (
    SELECT
        (SELECT AVG(sales) FROM product_metrics) AS avg_sales,
        (SELECT AVG(profit_margin_pct) FROM product_metrics) AS avg_margin
)
SELECT
    p.product_name,
    p.Category,
    p.sub_category,
    ROUND(p.sales, 2) AS sales,
    ROUND(p.profit, 2) AS profit,
    ROUND(p.profit_margin_pct, 2) AS profit_margin_pct
FROM product_metrics p
CROSS JOIN thresholds t
WHERE p.sales < t.avg_sales
  AND p.profit_margin_pct > t.avg_margin
ORDER BY p.profit_margin_pct DESC
LIMIT 25;

-- -----------------------------------------------------------------------------
-- SECTION 27: Potential slow-moving products
-- Low order frequency and below-median quantity across the full date range
-- -----------------------------------------------------------------------------
WITH product_velocity AS (
    SELECT
        "Product Name" AS product_name,
        Category,
        "Sub-Category" AS sub_category,
        COUNT(DISTINCT "Order ID") AS order_count,
        SUM(Quantity) AS quantity,
        ROUND(SUM(Sales), 2) AS sales,
        ROUND(SUM(Profit), 2) AS profit
    FROM retail_orders
    GROUP BY "Product Name", Category, "Sub-Category"
),
medians AS (
    SELECT
        (SELECT quantity FROM product_velocity ORDER BY quantity LIMIT 1 OFFSET
            (SELECT COUNT(*) FROM product_velocity) / 2) AS median_qty,
        (SELECT order_count FROM product_velocity ORDER BY order_count LIMIT 1 OFFSET
            (SELECT COUNT(*) FROM product_velocity) / 2) AS median_orders
)
SELECT
    v.product_name,
    v.Category,
    v.sub_category,
    v.order_count,
    v.quantity,
    v.sales,
    v.profit
FROM product_velocity v
CROSS JOIN medians m
WHERE v.quantity <= m.median_qty
  AND v.order_count <= m.median_orders
ORDER BY v.quantity ASC, v.order_count ASC
LIMIT 40;

-- -----------------------------------------------------------------------------
-- SECTION 28: Ranking categories / sub-categories with window functions
-- -----------------------------------------------------------------------------
WITH subcat AS (
    SELECT
        Category,
        "Sub-Category" AS sub_category,
        SUM(Sales) AS sales,
        SUM(Profit) AS profit,
        (SUM(Profit) / SUM(Sales)) * 100 AS profit_margin_pct
    FROM retail_orders
    GROUP BY Category, "Sub-Category"
)
SELECT
    Category,
    sub_category,
    ROUND(sales, 2) AS sales,
    ROUND(profit, 2) AS profit,
    ROUND(profit_margin_pct, 2) AS profit_margin_pct,
    RANK() OVER (ORDER BY profit DESC) AS profit_rank_overall,
    RANK() OVER (PARTITION BY Category ORDER BY profit DESC) AS profit_rank_in_category,
    RANK() OVER (ORDER BY profit_margin_pct DESC) AS margin_rank_overall,
    RANK() OVER (ORDER BY sales DESC) AS sales_rank_overall
FROM subcat
ORDER BY profit_rank_overall;

-- Segment contribution (supporting KPI / dashboard)
SELECT
    Segment,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    COUNT(DISTINCT "Order ID") AS orders,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY Segment
ORDER BY profit DESC;

-- Profit-draining sub-categories (negative total profit)
SELECT
    Category,
    "Sub-Category" AS sub_category,
    ROUND(SUM(Sales), 2) AS sales,
    ROUND(SUM(Profit), 2) AS profit,
    ROUND((SUM(Profit) / SUM(Sales)) * 100, 2) AS profit_margin_pct
FROM retail_orders
GROUP BY Category, "Sub-Category"
HAVING SUM(Profit) < 0
ORDER BY profit ASC;
