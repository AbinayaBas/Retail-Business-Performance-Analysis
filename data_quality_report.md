# Data Quality Report

- **Total Records:** 9,994
- **Total Columns:** 21
- **Missing Values:** 0
- **Duplicate Records (exact rows):** 0
- **Duplicate Records (excluding Row ID):** 1
- **Date Range:** 2014-01-03 to 2017-12-30
- **Numerical Features:** Row ID, Postal Code, Sales, Quantity, Discount, Profit
- **Categorical Features:** Order ID, Order Date, Ship Date, Ship Mode, Customer ID, Customer Name, Segment, Country, City, State, Region, Product ID, Category, Sub-Category, Product Name

## Missing values by column

- Row ID: 0
- Order ID: 0
- Order Date: 0
- Ship Date: 0
- Ship Mode: 0
- Customer ID: 0
- Customer Name: 0
- Segment: 0
- Country: 0
- City: 0
- State: 0
- Postal Code: 0
- Region: 0
- Product ID: 0
- Category: 0
- Sub-Category: 0
- Product Name: 0
- Sales: 0
- Quantity: 0
- Discount: 0
- Profit: 0

## Unique values by column

- Row ID: 9,994
- Order ID: 5,009
- Order Date: 1,237
- Ship Date: 1,334
- Ship Mode: 4
- Customer ID: 793
- Customer Name: 793
- Segment: 3
- Country: 1
- City: 531
- State: 49
- Postal Code: 631
- Region: 4
- Product ID: 1,862
- Category: 3
- Sub-Category: 17
- Product Name: 1,850
- Sales: 5,825
- Quantity: 14
- Discount: 12
- Profit: 7,287

## IQR outlier counts

- Sales: 1,167
- Quantity: 170
- Discount: 856
- Profit: 1,881

## Invalid numeric flags

- negative_quantity: 0
- zero_or_negative_sales: 0
- discount_outside_0_1: 0
- negative_profit_rows: 1871