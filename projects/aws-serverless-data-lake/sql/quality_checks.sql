-- Replace analytics_db and curated_orders with your Glue Catalog names.

-- 1. Total orders and revenue by currency.
SELECT currency,
       COUNT(*) AS order_count,
       SUM(amount) AS total_revenue
FROM analytics_db.curated_orders
GROUP BY currency
ORDER BY currency;

-- 2. Check for duplicate order IDs (expected: zero rows).
SELECT order_id, COUNT(*) AS row_count
FROM analytics_db.curated_orders
GROUP BY order_id
HAVING COUNT(*) > 1;

-- 3. Check for invalid required values (expected: zero rows).
SELECT *
FROM analytics_db.curated_orders
WHERE order_id IS NULL
   OR customer_id IS NULL
   OR order_ts IS NULL
   OR amount IS NULL
   OR amount < 0
   OR currency IS NULL;

-- 4. Inspect partition distribution.
SELECT order_year, order_month, order_day, COUNT(*) AS row_count
FROM analytics_db.curated_orders
GROUP BY order_year, order_month, order_day
ORDER BY order_year, order_month, order_day;
