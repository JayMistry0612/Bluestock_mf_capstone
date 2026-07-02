#!/usr/bin/env python3
"""
Master ETL Pipeline Execution Script
Bluestock Fintech | Mutual Fund Analytics Capstone

This script orchestrates the complete ETL pipeline:
1. Load raw data
2. Clean and validate
3. Create SQLite database
4. Compute metrics
5. Export processed files

Usage:
    python run_pipeline.py --all           # Run full pipeline
    python run_pipeline.py --extract       # Extract only
    python run_pipeline.py --load          # Load only
    python run_pipeline.py --metrics       # Compute metrics

Run from project root directory.
"""

import os
import sys
import argparse
from pathlib import Path
import logging
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
BASE_PATH = Path(__file__).parent
RAW_DATA_PATH = BASE_PATH / 'data' / 'raw'
PROCESSED_DATA_PATH = BASE_PATH / 'data' / 'processed'
DB_PATH = BASE_PATH / 'data' / 'db' / 'bluestock_mf.db'
SCRIPTS_PATH = BASE_PATH / 'scripts'


class MFPipeline:
    """Master ETL Pipeline"""
    
    def __init__(self):
        """Initialize pipeline"""
        self.base_path = BASE_PATH
        self.raw_path = RAW_DATA_PATH
        self.processed_path = PROCESSED_DATA_PATH
        self.db_path = DB_PATH
        
    def print_header(self, text):
        """Print formatted header"""
        print("\n" + "="*70)
        print(f"  {text}")
        print("="*70 + "\n")
    
    def step_extract(self):
        """Step 1: Extract raw data"""
        self.print_header("STEP 1: EXTRACT - Loading raw CSV files")
        
        try:
            sys.path.insert(0, str(SCRIPTS_PATH))
            from data_ingestion import load_all_datasets
            
            data = load_all_datasets(self.raw_path)
            logger.info(f"✓ Extracted {len(data)} datasets")
            logger.info(f"  • Total records loaded: {sum(len(df) for df in data.values())}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            return None
    
    def step_clean(self, data):
        """Step 2: Clean and validate data"""
        self.print_header("STEP 2: TRANSFORM - Cleaning & validating data")
        
        try:
            sys.path.insert(0, str(SCRIPTS_PATH))
            from data_cleaning import clean_datasets
            
            cleaned_data = clean_datasets(data)
            logger.info(f"✓ Cleaned {len(cleaned_data)} datasets")
            
            # Save to processed
            for name, df in cleaned_data.items():
                filepath = self.processed_path / f"{name}.csv"
                df.to_csv(filepath, index=False)
                logger.info(f"  • Saved: {filepath.name} ({len(df)} rows)")
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"❌ Cleaning failed: {e}")
            return None
    
    def step_load(self, data):
        """Step 3: Load into SQLite database"""
        self.print_header("STEP 3: LOAD - Creating SQLite database")
        
        try:
            sys.path.insert(0, str(SCRIPTS_PATH))
            from etl_pipeline import MFETLPipeline
            
            pipeline = MFETLPipeline()
            pipeline.load_to_sqlite(data)
            pipeline.create_indices()
            
            logger.info(f"✓ Database created successfully")
            logger.info(f"  • Location: {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Load failed: {e}")
            return False
    
    def step_metrics(self):
        """Step 4: Compute metrics"""
        self.print_header("STEP 4: ANALYTICS - Computing performance metrics")
        
        try:
            sys.path.insert(0, str(SCRIPTS_PATH))
            from compute_metrics import MetricsComputer
            
            mc = MetricsComputer()
            mc.load_data()
            
            # Compute VaR/CVaR
            logger.info("  • Computing VaR & CVaR...")
            var_cvar = mc.compute_var_cvar()
            mc.save_metrics(var_cvar, self.processed_path / 'var_cvar_report.csv')
            
            # Compute rolling Sharpe
            logger.info("  • Computing rolling Sharpe ratios...")
            rolling_sharpe = mc.compute_rolling_sharpe()
            
            # Compute HHI
            logger.info("  • Computing HHI concentration index...")
            hhi = mc.compute_hhi_concentration()
            hhi.to_csv(self.processed_path / 'hhi_report.csv', index=False)
            
            logger.info(f"✓ Metrics computed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Metrics computation failed: {e}")
            return False
    
    def print_summary(self):
        """Print execution summary"""
        self.print_header("PIPELINE EXECUTION COMPLETE ✓")
        
        print("📊 DELIVERABLES CREATED:\n")
        
        # Raw data
        raw_files = list(self.raw_path.glob("*.csv"))
        print(f"  📁 data/raw/              {len(raw_files)} files")
        
        # Processed data
        processed_files = list(self.processed_path.glob("*.csv"))
        print(f"  📁 data/processed/        {len(processed_files)} files")
        
        # Database
        if self.db_path.exists():
            db_size = self.db_path.stat().st_size / 1024 / 1024
            print(f"  🗄️ data/db/bluestock_mf.db  {db_size:.1f} MB")
        
        print("\n🚀 NEXT STEPS:\n")
        print("  1. Open Jupyter:  jupyter lab")
        print("     → notebooks/03_eda_analysis.ipynb (for analysis)")
        print("     → notebooks/05_advanced_analytics.ipynb (for advanced insights)")
        print("")
        print("  2. View Dashboard:")
        print("     → dashboard/bluestock_mf.pbix (in Power BI Desktop)")
        print("")
        print("  3. Query Database:")
        print("     → sqlite3 data/db/bluestock_mf.db")
        print("     → .read sql/queries.sql")
        print("")
        print("  4. Review Reports:")
        print("     → reports/Final_Report.pdf")
        print("     → reports/Presentation.pptx")
        print("")
        print("="*70)
        print(f"✅ Pipeline completed successfully on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")
    
    def run_all(self):
        """Execute full pipeline"""
        self.print_header("BLUESTOCK MF CAPSTONE - ETL PIPELINE")
        print("Full pipeline execution: Extract → Transform → Load → Metrics\n")
        
        # Extract
        raw_data = self.step_extract()
        if not raw_data:
            return False
        
        # Clean
        clean_data = self.step_clean(raw_data)
        if not clean_data:
            return False
        
        # Load
        success = self.step_load(clean_data)
        if not success:
            return False
        
        # Metrics
        success = self.step_metrics()
        if not success:
            return False
        
        # Summary
        self.print_summary()
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Bluestock MF Capstone - ETL Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --all              # Full pipeline
  python run_pipeline.py --extract          # Extract only
  python run_pipeline.py --load             # Load only
  python run_pipeline.py --metrics          # Compute metrics
        """
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        default=True,
        help='Run full pipeline (default)'
    )
    parser.add_argument(
        '--extract',
        action='store_true',
        help='Extract data only'
    )
    parser.add_argument(
        '--load',
        action='store_true',
        help='Load to database only'
    )
    parser.add_argument(
        '--metrics',
        action='store_true',
        help='Compute metrics only'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = MFPipeline()
    
    # Execute
    if args.extract:
        pipeline.step_extract()
    elif args.load:
        pipeline.step_load({})
    elif args.metrics:
        pipeline.step_metrics()
    else:
        # Run full pipeline
        success = pipeline.run_all()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
