"""
ETL Pipeline for Bluestock Mutual Fund Data
=============================================

Orchestrates the end-to-end Extract-Transform-Load process:
1. Ingest raw CSV files from data/raw/
2. Clean and transform data
3. Unify schema under SQLite database (data/db/bluestock_mf.db)
4. Populate dimension & fact tables
5. Create helper views for query compatibility
"""

import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
BASE_PATH = Path(__file__).parent.parent
RAW_DATA_PATH = BASE_PATH / 'data' / 'raw'
PROCESSED_DATA_PATH = BASE_PATH / 'data' / 'processed'
DB_PATH = BASE_PATH / 'data' / 'db' / 'bluestock_mf.db'
SCHEMA_PATH = BASE_PATH / 'sql' / 'schema.sql'

class MFETLPipeline:
    """ETL Pipeline for Mutual Fund Data"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.raw_path = RAW_DATA_PATH
        self.processed_path = PROCESSED_DATA_PATH
        
    def extract(self):
        """Extract data from raw CSV files using data_ingestion module"""
        logger.info("🔍 EXTRACT: Loading raw data files...")
        from data_ingestion import load_all_datasets
        return load_all_datasets(self.raw_path)
    
    def transform(self, data):
        """Transform and clean data using data_cleaning module"""
        logger.info("🔄 TRANSFORM: Cleaning and transforming data...")
        from data_cleaning import clean_datasets
        return clean_datasets(data)
    
    def load_to_sqlite(self, data):
        """Load cleaned data into normalized tables and views"""
        logger.info("💾 LOAD: Re-creating tables and inserting into SQLite...")
        
        # Ensure database folder exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run schema DDL script to create database tables
        if SCHEMA_PATH.exists():
            logger.info(f"  • Executing DDL from {SCHEMA_PATH.name}...")
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema_ddl = f.read()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Drop tables in reverse dependency order
            tables_to_drop = [
                'fact_benchmark_indices', 'fact_industry_folio_count', 'fact_category_inflows',
                'fact_sip_industry', 'fact_aum', 'fact_portfolio', 'fact_performance',
                'fact_transactions', 'fact_nav', 'dim_index', 'dim_investor', 'dim_date', 'dim_fund',
                'scheme_performance'
            ]
            for t in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {t}")
            conn.commit()
            conn.executescript(schema_ddl)
            conn.commit()
            conn.close()
            logger.info("  ✓ Schema tables created successfully")
        else:
            raise FileNotFoundError(f"Missing DDL schema script: {SCHEMA_PATH}")
            
        conn = sqlite3.connect(self.db_path)
        
        # 1. Populate dim_fund
        df_fm = data['fund_master'].copy()
        df_fm['launch_date'] = df_fm['launch_date'].dt.strftime('%Y-%m-%d')
        df_fm.to_sql('dim_fund', conn, if_exists='append', index=False)
        logger.info("  ✓ dim_fund table populated")
        
        # 2. Populate dim_date
        df_date = data['dim_date'].copy()
        df_date['date'] = df_date['date'].dt.strftime('%Y-%m-%d')
        # date_id is autoincrement, let's map columns correctly
        df_date[['date', 'year', 'month', 'quarter', 'is_weekday']].to_sql('dim_date', conn, if_exists='append', index=False)
        logger.info("  ✓ dim_date table populated")
        
        # 3. Populate dim_investor
        df_investors = data['dim_investor'].copy()
        df_investors.to_sql('dim_investor', conn, if_exists='append', index=False)
        logger.info("  ✓ dim_investor table populated")
        
        # 4. Populate dim_index
        df_bi = data['benchmark_indices'].copy()
        dim_index_df = pd.DataFrame({'index_name': df_bi['index_name'].unique()})
        dim_index_df.to_sql('dim_index', conn, if_exists='append', index=False)
        logger.info("  ✓ dim_index table populated")
        
        # 5. Populate fact_nav
        df_nav = data['nav_history'].copy()
        df_nav['nav_date'] = df_nav['date'].dt.strftime('%Y-%m-%d')
        # select columns matching DDL
        df_nav_db = df_nav[['amfi_code', 'nav_date', 'nav', 'daily_return']]
        df_nav_db.to_sql('fact_nav', conn, if_exists='append', index=False)
        logger.info("  ✓ fact_nav table populated")
        
        # 6. Populate fact_transactions
        df_tx = data['investor_transactions'].copy()
        df_tx['tx_date'] = df_tx['transaction_date'].dt.strftime('%Y-%m-%d')
        df_tx['amount'] = df_tx['amount_inr']
        df_tx_db = df_tx[[
            'tx_id', 'investor_id', 'amfi_code', 'tx_date', 'amount', 
            'transaction_type', 'is_lumpsum', 'is_redemption', 'is_sip'
        ]]
        df_tx_db.to_sql('fact_transactions', conn, if_exists='append', index=False)
        logger.info("  ✓ fact_transactions table populated")
        
        # 7. Populate fact_performance
        df_sp = data['scheme_performance'].copy()
        max_date_str = df_nav['nav_date'].max()
        df_sp['as_of_date'] = max_date_str
        df_sp['return_1yr'] = df_sp['return_1yr_pct']
        df_sp['sharpe'] = df_sp['sharpe_ratio']
        df_sp['max_dd'] = df_sp['max_drawdown_pct']
        df_sp_db = df_sp[['amfi_code', 'as_of_date', 'return_1yr', 'sharpe', 'alpha', 'max_dd']]
        df_sp_db.to_sql('fact_performance', conn, if_exists='append', index=False)
        logger.info("  ✓ fact_performance table populated")
        
        # Also populate scheme_performance table for queries.sql compatibility
        df_sp.to_sql('scheme_performance', conn, if_exists='replace', index=False)
        logger.info("  ✓ scheme_performance table populated")
        
        # 8. Populate fact_portfolio
        df_ph = data['portfolio_holdings'].copy()
        df_ph['nav_date'] = df_ph['portfolio_date'].dt.strftime('%Y-%m-%d')
        # Add stock_name placeholder if missing
        if 'stock_name' not in df_ph.columns:
            df_ph['stock_name'] = df_ph['stock_symbol']
        # Add market_value_cr placeholder if missing
        if 'market_value_cr' not in df_ph.columns:
            df_ph['market_value_cr'] = 0.0
        # Add current_price_inr placeholder if missing
        if 'current_price_inr' not in df_ph.columns:
            df_ph['current_price_inr'] = 0.0
            
        df_ph_db = df_ph[[
            'amfi_code', 'stock_symbol', 'stock_name', 'sector', 
            'weight_pct', 'market_value_cr', 'current_price_inr', 'nav_date'
        ]]
        df_ph_db.to_sql('fact_portfolio', conn, if_exists='append', index=False)
        logger.info("  ✓ fact_portfolio table populated")
        
        # 9. Populate fact_aum
        df_aum = data['aum_fund_house'].copy()
        df_aum['date'] = df_aum['date'].dt.strftime('%Y-%m-%d')
        df_aum_db = df_aum[['fund_house', 'date', 'aum_crore', 'num_schemes']]
        df_aum_db.to_sql('fact_aum', conn, if_exists='append', index=False)
        logger.info("  ✓ fact_aum table populated")
        
        # 10. Populate fact_sip_industry
        df_sip = data['sip_inflows'].copy()
        if 'month' in df_sip.columns:
            try:
                df_sip['month'] = pd.to_datetime(df_sip['month']).dt.strftime('%Y-%m')
            except Exception:
                pass
        df_sip_db = df_sip[['month', 'sip_inflow_crore', 'active_sip_accounts_crore', 'new_sip_accounts_lakh', 'sip_aum_lakh_crore', 'yoy_growth_pct']]
        df_sip_db.to_sql('fact_sip_industry', conn, if_exists='append', index=False)
        logger.info("  ✓ fact_sip_industry table populated")
        
        # 11. Populate fact_category_inflows
        df_cin = data['category_inflows'].copy()
        if 'month' in df_cin.columns:
            df_cin['month'] = pd.to_datetime(df_cin['month']).dt.strftime('%Y-%m')
        df_cin_db = df_cin[['month', 'category', 'net_inflow_crore']]
        df_cin_db.to_sql('fact_category_inflows', conn, if_exists='append', index=False)
        logger.info("  ✓ fact_category_inflows table populated")
        
        # 12. Populate fact_industry_folio_count
        df_fol = data['industry_holdings'].copy()
        if 'month' in df_fol.columns:
            df_fol['month'] = pd.to_datetime(df_fol['month']).dt.strftime('%Y-%m')
        df_fol_db = df_fol[['month', 'total_folios_crore', 'equity_folios_crore', 'debt_folios_crore', 'hybrid_folios_crore', 'others_folios_crore']]
        df_fol_db.to_sql('fact_industry_folio_count', conn, if_exists='append', index=False)
        logger.info("  ✓ fact_industry_folio_count table populated")
        
        # 13. Populate fact_benchmark_indices
        df_bi_db = df_bi[['date', 'index_name', 'close_value']].copy()
        df_bi_db['date'] = pd.to_datetime(df_bi_db['date']).dt.strftime('%Y-%m-%d')
        df_bi_db.to_sql('fact_benchmark_indices', conn, if_exists='append', index=False)
        logger.info("  ✓ fact_benchmark_indices table populated")

        # 14. Create Compatibility Views
        logger.info("Creating SQL Views for query compatibility...")
        views = {
            "funds": "SELECT amfi_code, fund_house, scheme_name, category, sub_category, plan, launch_date, benchmark, expense_ratio_pct, exit_load_pct, min_sip_amount, min_lumpsum_amount, fund_manager, risk_category, sebi_category_code FROM dim_fund",
            "nav_history": "SELECT amfi_code, nav_date AS date, nav, daily_return FROM fact_nav",
            "portfolio_holdings": "SELECT amfi_code, stock_symbol, stock_name, sector, weight_pct, market_value_cr, current_price_inr, nav_date AS portfolio_date FROM fact_portfolio",
            "benchmarks": "SELECT date, index_name, close_value FROM fact_benchmark_indices",
            "transactions": """
                SELECT 
                    t.tx_id,
                    t.investor_id,
                    t.amfi_code,
                    t.tx_date AS transaction_date,
                    t.amount AS amount_inr,
                    t.transaction_type,
                    t.is_sip AS transaction_type_SIP,
                    t.is_lumpsum AS transaction_type_Lumpsum,
                    t.is_redemption AS transaction_type_Redemption,
                    i.state,
                    i.city,
                    i.city_tier,
                    i.age_group,
                    i.gender,
                    i.annual_income_lakh,
                    i.payment_mode,
                    i.kyc_status
                FROM fact_transactions t
                JOIN dim_investor i ON t.investor_id = i.investor_id
            """
        }
        
        cursor = conn.cursor()
        for view_name, view_sql in views.items():
            cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
            cursor.execute(f"CREATE VIEW {view_name} AS {view_sql}")
            logger.info(f"  • View created: {view_name}")
            
        conn.commit()
        conn.close()
        logger.info(f"  ✓ Database load complete: {self.db_path}")
        return self.db_path
        
    def create_indices(self):
        """Create indices for optimization"""
        logger.info("📊 Creating database indices...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_nav_amfi ON fact_nav(amfi_code)",
            "CREATE INDEX IF NOT EXISTS idx_nav_date ON fact_nav(nav_date)",
            "CREATE INDEX IF NOT EXISTS idx_trans_investor ON fact_transactions(investor_id)",
            "CREATE INDEX IF NOT EXISTS idx_trans_fund ON fact_transactions(amfi_code)",
            "CREATE INDEX IF NOT EXISTS idx_trans_date ON fact_transactions(tx_date)",
            "CREATE INDEX IF NOT EXISTS idx_perf_amfi ON fact_performance(amfi_code)",
            "CREATE INDEX IF NOT EXISTS idx_holdings_fund ON fact_portfolio(amfi_code)",
        ]
        
        for idx_sql in indices:
            try:
                cursor.execute(idx_sql)
            except Exception as e:
                logger.warning(f"  ⚠ Index creation issue: {e}")
                
        conn.commit()
        conn.close()
        logger.info("  ✓ Optimization indices built")

    def run(self):
        """Execute full ETL pipeline"""
        logger.info("=" * 70)
        logger.info("🚀 STARTING ETL PIPELINE - Bluestock MF Capstone")
        logger.info("=" * 70)
        
        try:
            # Extract
            raw_data = self.extract()
            
            # Transform
            clean_data = self.transform(raw_data)
            
            # Load
            self.load_to_sqlite(clean_data)
            
            # Index
            self.create_indices()
            
            logger.info("=" * 70)
            logger.info("✅ ETL PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"❌ ETL Pipeline Failed: {e}", exc_info=True)
            raise

if __name__ == '__main__':
    pipeline = MFETLPipeline()
    pipeline.run()
