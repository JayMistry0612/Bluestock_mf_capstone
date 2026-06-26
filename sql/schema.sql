CREATE TABLE dim_fund (
    amfi_code TEXT PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT,
    category TEXT,
    sub_category TEXT,
    plan TEXT,
    launch_date DATE,
    benchmark TEXT,
    expense_ratio_pct REAL,
    exit_load_pct REAL,
    min_sip_amount INTEGER,
    min_lumpsum_amount INTEGER,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    is_weekday INTEGER NOT NULL
);

CREATE TABLE dim_investor (
    investor_id TEXT PRIMARY KEY,
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT
);

CREATE TABLE dim_index (
    index_name TEXT PRIMARY KEY
);

CREATE TABLE fact_nav (
    amfi_code TEXT NOT NULL,
    nav_date DATE NOT NULL,
    nav REAL,
    daily_return REAL,
    PRIMARY KEY (amfi_code, nav_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (nav_date) REFERENCES dim_date(date)
);

CREATE TABLE fact_transactions (
    tx_id TEXT PRIMARY KEY,
    investor_id TEXT NOT NULL,
    amfi_code TEXT NOT NULL,
    tx_date DATE NOT NULL,
    amount REAL,
    transaction_type TEXT,
    is_lumpsum INTEGER,
    is_redemption INTEGER,
    is_sip INTEGER,
    FOREIGN KEY (investor_id) REFERENCES dim_investor(investor_id),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (tx_date) REFERENCES dim_date(date)
);

CREATE TABLE fact_performance (
    amfi_code TEXT NOT NULL,
    as_of_date DATE NOT NULL,
    return_1yr REAL,
    sharpe REAL,
    alpha REAL,
    max_dd REAL,
    PRIMARY KEY (amfi_code, as_of_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (as_of_date) REFERENCES dim_date(date)
);

CREATE TABLE fact_portfolio (
    amfi_code TEXT NOT NULL,
    stock_symbol TEXT NOT NULL,
    stock_name TEXT,
    sector TEXT,
    weight_pct REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    nav_date DATE NOT NULL,
    PRIMARY KEY (amfi_code, stock_symbol, nav_date),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (nav_date) REFERENCES dim_date(date)
);

CREATE TABLE fact_aum (
    fund_house TEXT NOT NULL,
    date DATE NOT NULL,
    aum_crore REAL,
    num_schemes INTEGER,
    PRIMARY KEY (fund_house, date),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);

CREATE TABLE fact_sip_industry (
    month TEXT PRIMARY KEY,
    sip_inflow_crore REAL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh REAL,
    sip_aum_lakh_crore REAL,
    yoy_growth_pct REAL
);

CREATE TABLE fact_category_inflows (
    month TEXT NOT NULL,
    category TEXT NOT NULL,
    net_inflow_crore REAL,
    PRIMARY KEY (month, category)
);

CREATE TABLE fact_industry_folio_count (
    month TEXT PRIMARY KEY,
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);

CREATE TABLE fact_benchmark_indices (
    date DATE NOT NULL,
    index_name TEXT NOT NULL,
    close_value REAL,
    PRIMARY KEY (date, index_name),
    FOREIGN KEY (index_name) REFERENCES dim_index(index_name),
    FOREIGN KEY (date) REFERENCES dim_date(date)
);
