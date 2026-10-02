# Data Cleaning Log

- Loaded 9,994 rows and 21 columns from `Sample_Superstore.csv`.
- Parsed Order Date and Ship Date to datetime. Invalid dates found: 0.
- Investigated ship-before-order rows: 0. None were removed because count is 0.
- No missing values were present after date parsing. No imputation required.
- Stripped whitespace in `Product Name` (16 values).
- Investigated invalid numerics — quantity<=0: 0, sales<=0: 0, discount outside [0,1]: 0. No rows dropped.
- Negative profit rows: 1,871. These are valid loss-making transactions and were retained for profitability analysis.
- Investigated 16 rows sharing Order ID + Product ID. Most have different quantities/sales (split line items) and were retained.
- Removed 1 exact duplicate line item(s) (identical values except Row ID). Example Order ID(s): US-2014-150119.
- Cleaning complete. Rows in: 9,994. Rows out: 9,993. Net change: -1.