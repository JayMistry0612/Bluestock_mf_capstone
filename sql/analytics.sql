-- 1. Top 5 funds by AUM
SELECT amfi_code, scheme_name, fund_house, aum_crore
FROM fact_performance
WHERE aum_crore IS NOT NULL
ORDER BY aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT strftime('%Y-%m', nav_date) AS month, AVG(nav) AS avg_nav
FROM fact_nav
GROUP BY month
ORDER BY month;

-- 3. SIP inflow YoY growth
SELECT cur.month,
       cur.sip_inflow_crore AS current_inflow,
       prv.sip_inflow_crore AS prior_year_inflow,
       CASE
           WHEN prv.sip_inflow_crore = 0 THEN NULL
           ELSE (cur.sip_inflow_crore - prv.sip_inflow_crore) / prv.sip_inflow_crore * 100
       END AS yoy_pct_change
FROM fact_sip_industry AS cur
JOIN fact_sip_industry AS prv
  ON substr(cur.month, 6, 2) = substr(prv.month, 6, 2)
 AND CAST(substr(cur.month, 1, 4) AS INTEGER) = CAST(substr(prv.month, 1, 4) AS INTEGER) + 1
ORDER BY cur.month;

-- 4. Transactions by state
SELECT state,
       COUNT(*) AS num_transactions,
       SUM(amount) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;

-- 5. Funds with expense_ratio < 1%
SELECT amfi_code, scheme_name, fund_house, category, expense_ratio_pct
FROM fact_performance
WHERE expense_ratio_pct < 1
ORDER BY expense_ratio_pct ASC;

-- 6. Top 10 funds by 1-year return
SELECT amfi_code, scheme_name, fund_house, return_1yr_pct
FROM fact_performance
ORDER BY return_1yr_pct DESC
LIMIT 10;

-- 7. Sector exposure by fund
SELECT amfi_code, sector, SUM(weight_pct) AS total_weight_pct
FROM fact_portfolio
GROUP BY amfi_code, sector
ORDER BY amfi_code, total_weight_pct DESC;

-- 8. Average daily return per fund over the last 30 days
SELECT amfi_code, AVG(daily_return) AS avg_daily_return_30d
FROM fact_nav
WHERE nav_date >= date((SELECT MAX(nav_date) FROM fact_nav), '-29 day')
GROUP BY amfi_code
ORDER BY avg_daily_return_30d DESC;

-- 9. Latest benchmark index close values
SELECT index_name, close_value, date
FROM fact_benchmark_indices
WHERE date = (SELECT MAX(date) FROM fact_benchmark_indices)
ORDER BY index_name;

-- 10. Average expense ratio by category
SELECT category, AVG(expense_ratio_pct) AS avg_expense_ratio
FROM fact_performance
GROUP BY category
ORDER BY avg_expense_ratio ASC;
