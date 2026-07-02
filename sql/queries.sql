-- SQL Queries for Bluestock MF Analytics
-- ========================================

-- 1. Fund Master Data Queries
-- ============================

-- Get all active funds with risk categories
SELECT amfi_code, scheme_name, fund_house, category, risk_category
FROM funds
ORDER BY fund_house, scheme_name;

-- Get funds by risk category count
SELECT risk_category, COUNT(*) as fund_count
FROM funds
GROUP BY risk_category
ORDER BY fund_count DESC;


-- 2. NAV History Queries
-- =======================

-- Latest NAV for all funds
SELECT DISTINCT
    f.amfi_code,
    f.scheme_name,
    n.date,
    n.nav,
    n.daily_return
FROM funds f
INNER JOIN nav_history n ON f.amfi_code = n.amfi_code
WHERE n.date = (SELECT MAX(date) FROM nav_history WHERE amfi_code = f.amfi_code)
ORDER BY f.scheme_name;

-- Daily return statistics by fund
SELECT
    f.amfi_code,
    f.scheme_name,
    COUNT(*) as trading_days,
    AVG(n.daily_return) as avg_daily_return,
    STDDEV(n.daily_return) as daily_volatility,
    MIN(n.daily_return) as min_return,
    MAX(n.daily_return) as max_return
FROM nav_history n
INNER JOIN funds f ON n.amfi_code = f.amfi_code
WHERE n.daily_return IS NOT NULL
GROUP BY f.amfi_code, f.scheme_name
ORDER BY daily_volatility DESC;


-- 3. Performance Analytics
-- =========================

-- Top performers by Sharpe ratio
SELECT
    amfi_code,
    scheme_name,
    sharpe_ratio,
    sortino_ratio,
    return_1yr_pct,
    return_3yr_pct,
    max_drawdown_pct,
    risk_grade
FROM scheme_performance
ORDER BY sharpe_ratio DESC
LIMIT 10;

-- Worst performers
SELECT
    amfi_code,
    scheme_name,
    sharpe_ratio,
    return_3yr_pct,
    max_drawdown_pct
FROM scheme_performance
WHERE sharpe_ratio IS NOT NULL
ORDER BY sharpe_ratio ASC
LIMIT 10;


-- 4. Investor Transaction Analysis
-- =================================

-- Total investors by cohort year
SELECT
    YEAR(transaction_date) as cohort_year,
    COUNT(DISTINCT investor_id) as num_investors,
    COUNT(*) as transactions,
    SUM(CASE WHEN transaction_type_SIP = 1 THEN 1 ELSE 0 END) as sip_count
FROM transactions
GROUP BY YEAR(transaction_date)
ORDER BY cohort_year DESC;

-- Top fund preferences
SELECT
    f.scheme_name,
    COUNT(*) as transaction_count,
    SUM(t.amount_inr) as total_amount
FROM transactions t
INNER JOIN funds f ON t.amfi_code = f.amfi_code
GROUP BY f.scheme_name
ORDER BY transaction_count DESC
LIMIT 15;

-- Investor SIP patterns
SELECT
    investor_id,
    COUNT(*) as sip_count,
    MIN(transaction_date) as first_sip,
    MAX(transaction_date) as last_sip,
    SUM(amount_inr) as total_invested,
    AVG(amount_inr) as avg_sip_amount
FROM transactions
WHERE transaction_type_SIP = 1
GROUP BY investor_id
HAVING COUNT(*) >= 6
ORDER BY sip_count DESC;


-- 5. Portfolio Concentration Analysis
-- ====================================

-- Fund sector holdings
SELECT
    f.scheme_name,
    ph.sector,
    ph.weight_pct,
    COUNT(*) as num_holdings
FROM portfolio_holdings ph
INNER JOIN funds f ON ph.amfi_code = f.amfi_code
GROUP BY f.scheme_name, ph.sector
ORDER BY f.scheme_name, ph.weight_pct DESC;

-- Top holdings by fund
SELECT
    f.scheme_name,
    ph.stock_name,
    ph.weight_pct,
    ph.sector,
    ph.market_value_cr
FROM portfolio_holdings ph
INNER JOIN funds f ON ph.amfi_code = f.amfi_code
WHERE ph.weight_pct > 2.0
ORDER BY f.scheme_name, ph.weight_pct DESC;


-- 6. Benchmark Comparison
-- ========================

-- Fund performance vs benchmark
SELECT
    sp.scheme_name,
    sp.return_1yr_pct as fund_1yr,
    sp.benchmark_3yr_pct as bench_3yr,
    sp.alpha,
    sp.beta,
    sp.sharpe_ratio,
    CASE
        WHEN sp.alpha > 0 THEN 'Outperformer'
        ELSE 'Underperformer'
    END as performance_category
FROM scheme_performance sp
ORDER BY sp.alpha DESC;


-- 7. Risk Analysis
-- =================

-- Funds by risk category and AUM
SELECT
    f.risk_category,
    COUNT(*) as fund_count,
    AVG(sp.aum_crore) as avg_aum,
    SUM(sp.aum_crore) as total_aum,
    AVG(sp.max_drawdown_pct) as avg_max_drawdown
FROM funds f
LEFT JOIN scheme_performance sp ON f.amfi_code = sp.amfi_code
GROUP BY f.risk_category
ORDER BY total_aum DESC;


-- 8. Custom Analysis Queries
-- ============================

-- Calculate fund flow trends
SELECT
    YEAR(transaction_date) as year,
    MONTH(transaction_date) as month,
    COUNT(*) as transaction_count,
    SUM(amount_inr) as total_flow
FROM transactions
GROUP BY YEAR(transaction_date), MONTH(transaction_date)
ORDER BY year DESC, month DESC;

-- Investor demographics
SELECT
    age_group,
    gender,
    COUNT(DISTINCT investor_id) as investor_count,
    SUM(amount_inr) as total_invested,
    AVG(amount_inr) as avg_transaction
FROM transactions
GROUP BY age_group, gender
ORDER BY total_invested DESC;
