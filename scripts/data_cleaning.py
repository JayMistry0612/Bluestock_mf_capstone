"""
Data Cleaning Module
Bluestock Fintech | Mutual Fund Analytics Capstone
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_datasets(data):
    """
    Cleans and transforms all 10 raw datasets.
    
    Parameters:
    -----------
    data : dict
        Dictionary of raw pandas DataFrames
        
    Returns:
    --------
    dict
        Dictionary of cleaned pandas DataFrames
    """
    cleaned = {}
    
    # 1. Fund Master
    logger.info("Cleaning Fund Master...")
    df_fm = data['fund_master'].copy()
    df_fm['launch_date'] = pd.to_datetime(df_fm['launch_date'])
    df_fm['expense_ratio_pct'] = pd.to_numeric(df_fm['expense_ratio_pct'], errors='coerce')
    df_fm['exit_load_pct'] = pd.to_numeric(df_fm['exit_load_pct'], errors='coerce')
    cleaned['fund_master'] = df_fm

    # 2. NAV History (with weekends/holidays forward filled)
    logger.info("Cleaning NAV History...")
    df_nav = data['nav_history'].copy()
    df_nav['date'] = pd.to_datetime(df_nav['date'])
    df_nav = df_nav.drop_duplicates(subset=['amfi_code', 'date'])
    df_nav = df_nav[df_nav['nav'] > 0]
    df_nav = df_nav.sort_values(by=['amfi_code', 'date'])
    
    # Forward-fill missing dates for each scheme
    def reindex_scheme(group):
        group = group.set_index('date')
        full_range = pd.date_range(start=group.index.min(), end=group.index.max(), freq='D')
        group = group.reindex(full_range)
        group['amfi_code'] = group['amfi_code'].ffill()
        group['nav'] = group['nav'].ffill()
        group.index.name = 'date'
        return group.reset_index()
    
    df_nav = df_nav.groupby('amfi_code', group_keys=False).apply(reindex_scheme)
    df_nav['daily_return'] = df_nav.groupby('amfi_code')['nav'].pct_change().fillna(0.0)
    cleaned['nav_history'] = df_nav

    # 3. Investor Transactions & Dimension Extraction
    logger.info("Cleaning Investor Transactions & extracting Investor Dimension...")
    df_tx = data['investor_transactions'].copy()
    df_tx['transaction_date'] = pd.to_datetime(df_tx['transaction_date'])
    df_tx = df_tx[df_tx['amount_inr'] > 0]
    
    # Generate Transaction ID if not present
    if 'tx_id' not in df_tx.columns:
        df_tx['tx_id'] = [f"TX_{i+1:06d}" for i in range(len(df_tx))]
        
    df_tx = df_tx.sort_values(by=['transaction_date', 'amfi_code'])
    
    # Standardise transaction types and flags
    df_tx['transaction_type'] = df_tx['transaction_type'].str.strip().str.capitalize()
    
    df_tx['transaction_type_SIP'] = (df_tx['transaction_type'] == 'Sip').astype(int)
    df_tx['transaction_type_Lumpsum'] = (df_tx['transaction_type'] == 'Lumpsum').astype(int)
    df_tx['transaction_type_Redemption'] = (df_tx['transaction_type'] == 'Redemption').astype(int)
    
    df_tx['is_sip'] = df_tx['transaction_type_SIP']
    df_tx['is_lumpsum'] = df_tx['transaction_type_Lumpsum']
    df_tx['is_redemption'] = df_tx['transaction_type_Redemption']
    
    # Extract unique investor info for dim_investor
    df_investors = df_tx[[
        'investor_id', 'state', 'city', 'city_tier', 'age_group', 
        'gender', 'annual_income_lakh', 'payment_mode', 'kyc_status'
    ]].drop_duplicates(subset=['investor_id']).copy()
    
    # Keep transactions dataset focused on fact table columns
    # We will still retain the fields in raw files, but fact table will select appropriate columns
    cleaned['investor_transactions'] = df_tx
    cleaned['dim_investor'] = df_investors

    # 4. Scheme Performance
    logger.info("Cleaning Scheme Performance...")
    df_sp = data['scheme_performance'].copy()
    df_sp['return_1yr_pct'] = pd.to_numeric(df_sp['return_1yr_pct'], errors='coerce')
    df_sp['sharpe_ratio'] = pd.to_numeric(df_sp['sharpe_ratio'], errors='coerce')
    df_sp['sortino_ratio'] = pd.to_numeric(df_sp['sortino_ratio'], errors='coerce')
    df_sp['expense_ratio_pct'] = pd.to_numeric(df_sp['expense_ratio_pct'], errors='coerce')
    df_sp['aum_crore'] = pd.to_numeric(df_sp['aum_crore'], errors='coerce')
    df_sp['morningstar_rating'] = pd.to_numeric(df_sp['morningstar_rating'], errors='coerce')
    # Flag negative Sharpe ratios
    df_sp['negative_sharpe'] = (df_sp['sharpe_ratio'] < 0).astype(int)
    cleaned['scheme_performance'] = df_sp

    # 5. Portfolio Holdings
    logger.info("Cleaning Portfolio Holdings...")
    df_ph = data['portfolio_holdings'].copy()
    df_ph['portfolio_date'] = pd.to_datetime(df_ph['portfolio_date'])
    df_ph['weight_pct'] = pd.to_numeric(df_ph['weight_pct'], errors='coerce')
    df_ph['market_value_cr'] = pd.to_numeric(df_ph['market_value_cr'], errors='coerce')
    cleaned['portfolio_holdings'] = df_ph

    # 6. Benchmark Indices
    logger.info("Cleaning Benchmark Indices...")
    df_bi = data['benchmark_indices'].copy()
    df_bi['date'] = pd.to_datetime(df_bi['date'])
    df_bi['close_value'] = pd.to_numeric(df_bi['close_value'], errors='coerce')
    cleaned['benchmark_indices'] = df_bi

    # 7. Other data frames: load directly but ensure datetime formatting
    for key in ['aum_fund_house', 'sip_inflows', 'category_inflows', 'industry_holdings']:
        if key in data:
            df = data[key].copy()
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            if 'month' in df.columns:
                df['month'] = pd.to_datetime(df['month'])
            cleaned[key] = df

    # Generate Date Dimension
    logger.info("Generating Date Dimension...")
    # Gather all dates in the system
    all_dates = pd.concat([
        df_nav['date'],
        df_tx['transaction_date'],
        df_bi['date']
    ]).dropna().unique()
    
    date_range = pd.date_range(start=min(all_dates), end=max(all_dates), freq='D')
    df_date = pd.DataFrame({'date': date_range})
    df_date['year'] = df_date['date'].dt.year
    df_date['month'] = df_date['date'].dt.month
    df_date['quarter'] = df_date['date'].dt.quarter
    df_date['is_weekday'] = (df_date['date'].dt.weekday < 5).astype(int)
    # Format date as string for sqlite storage convenience, but keep column name
    cleaned['dim_date'] = df_date

    logger.info("✓ Data cleaning and dimension generation complete")
    return cleaned
