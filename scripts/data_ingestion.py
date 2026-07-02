"""
Data Ingestion Module
Bluestock Fintech | Mutual Fund Analytics Capstone
"""

import os
from pathlib import Path
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_all_datasets(raw_data_dir):
    """
    Loads all 10 raw CSV datasets from the raw data directory.
    
    Parameters:
    -----------
    raw_data_dir : str or Path
        Path to the directory containing raw CSV files
        
    Returns:
    --------
    dict
        Dictionary of pandas DataFrames mapping key name to DataFrame
    """
    raw_path = Path(raw_data_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory does not exist: {raw_path}")
        
    files = {
        'fund_master': '01_fund_master.csv',
        'nav_history': '02_nav_history.csv',
        'aum_fund_house': '03_aum_by_fund_house.csv',
        'sip_inflows': '04_monthly_sip_inflows.csv',
        'category_inflows': '05_category_inflows.csv',
        'industry_holdings': '06_industry_folio_count.csv',
        'scheme_performance': '07_scheme_performance.csv',
        'investor_transactions': '08_investor_transactions.csv',
        'portfolio_holdings': '09_portfolio_holdings.csv',
        'benchmark_indices': '10_benchmark_indices.csv'
    }
    
    data = {}
    
    for key, filename in files.items():
        filepath = raw_path / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Required raw dataset missing: {filepath}")
            
        logger.info(f"Loading {filename}...")
        df = pd.read_csv(filepath)
        
        # Log metadata
        logger.info(f"  • Shape: {df.shape}")
        logger.info(f"  • Columns: {df.columns.tolist()}")
        logger.debug(f"  • Head:\n{df.head(2)}")
        
        data[key] = df
        
    logger.info("✓ All 10 raw datasets successfully ingested")
    return data

if __name__ == '__main__':
    # Test script execution
    import argparse
    parser = argparse.ArgumentParser(description="Test Ingestion Module")
    parser.add_argument('--raw_dir', type=str, default=str(Path(__file__).parent.parent / 'data' / 'raw'))
    args = parser.parse_args()
    
    try:
        load_all_datasets(args.raw_dir)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
