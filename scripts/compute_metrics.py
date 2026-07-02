"""
Compute Metrics Module
======================

Computes advanced financial metrics for mutual fund analysis:
- VaR (Value at Risk) at 95% confidence
- CVaR (Conditional Value at Risk)
- Sharpe Ratio (risk-adjusted returns)
- Portfolio concentration (HHI Index)
- Performance attribution

Can be imported as a module or run as a script.

Usage:
    from compute_metrics import MetricsComputer
    mc = MetricsComputer('data/processed/02_nav_history.csv')
    mc.compute_var_cvar()
    mc.compute_rolling_sharpe()
"""

import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_PATH = Path(__file__).parent.parent
DB_PATH = BASE_PATH / 'data' / 'db' / 'bluestock_mf.db'
PROCESSED_PATH = BASE_PATH / 'data' / 'processed'


class MetricsComputer:
    """Compute advanced financial metrics"""
    
    def __init__(self, nav_file=None, db_path=None):
        self.nav_file = nav_file or PROCESSED_PATH / '02_nav_history.csv'
        self.db_path = db_path or DB_PATH
        self.nav_data = None
        self.fund_data = None
        
    def load_data(self):
        """Load NAV history and fund data"""
        logger.info("Loading NAV data...")
        self.nav_data = pd.read_csv(self.nav_file)
        self.nav_data['date'] = pd.to_datetime(self.nav_data['date'])
        logger.info(f"✓ Loaded {len(self.nav_data)} NAV records")
        
    def compute_var_cvar(self, confidence=0.95):
        """Compute VaR and CVaR"""
        logger.info(f"Computing VaR/CVaR at {confidence*100}% confidence...")
        
        percentile = (1 - confidence) * 100
        results = []
        
        for amfi in self.nav_data['amfi_code'].unique():
            returns = self.nav_data[self.nav_data['amfi_code'] == amfi]['daily_return'].dropna()
            
            if len(returns) > 0:
                var = np.percentile(returns, percentile)
                cvar = returns[returns <= var].mean() if len(returns[returns <= var]) > 0 else var
                
                results.append({
                    'amfi_code': amfi,
                    'var_95': var,
                    'cvar_95': cvar,
                    'num_obs': len(returns)
                })
        
        result_df = pd.DataFrame(results)
        logger.info(f"✓ Computed VaR/CVaR for {len(result_df)} funds")
        return result_df
    
    def compute_rolling_sharpe(self, window=90):
        """Compute rolling Sharpe ratio"""
        logger.info(f"Computing {window}-day rolling Sharpe ratio...")
        
        results = {}
        
        for amfi in self.nav_data['amfi_code'].unique():
            fund_data = self.nav_data[self.nav_data['amfi_code'] == amfi].sort_values('date')
            returns = fund_data['daily_return'].dropna()
            
            if len(returns) > window:
                roll_mean = returns.rolling(window).mean()
                roll_std = returns.rolling(window).std()
                rolling_sharpe = (roll_mean / roll_std) * np.sqrt(252)
                
                results[amfi] = {
                    'dates': fund_data[fund_data['daily_return'].notna()]['date'].values,
                    'rolling_sharpe': rolling_sharpe.values
                }
        
        logger.info(f"✓ Computed rolling Sharpe for {len(results)} funds")
        return results
    
    def compute_hhi_concentration(self, holdings_file=None):
        """Compute HHI sector concentration index"""
        logger.info("Computing HHI concentration indices...")
        
        holdings_file = holdings_file or PROCESSED_PATH / '09_portfolio_holdings.csv'
        holdings = pd.read_csv(holdings_file)
        
        hhi_results = []
        
        for amfi in holdings['amfi_code'].unique():
            fund_holdings = holdings[holdings['amfi_code'] == amfi]
            weights = fund_holdings['weight_pct'].values
            
            hhi = (weights ** 2).sum()
            hhi_results.append({
                'amfi_code': amfi,
                'hhi': hhi,
                'num_holdings': len(fund_holdings)
            })
        
        result_df = pd.DataFrame(hhi_results)
        logger.info(f"✓ Computed HHI for {len(result_df)} funds")
        return result_df
    
    def save_metrics(self, var_cvar_df, output_file=None):
        """Save metrics to CSV"""
        output_file = output_file or PROCESSED_PATH / 'computed_metrics.csv'
        var_cvar_df.to_csv(output_file, index=False)
        logger.info(f"✓ Metrics saved: {output_file}")
        
    def compute_all(self):
        """Compute all metrics"""
        self.load_data()
        var_cvar = self.compute_var_cvar()
        rolling_sharpe = self.compute_rolling_sharpe()
        hhi = self.compute_hhi_concentration()
        
        return {
            'var_cvar': var_cvar,
            'rolling_sharpe': rolling_sharpe,
            'hhi': hhi
        }


if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("🔢 Computing Advanced Metrics")
    logger.info("=" * 70)
    
    mc = MetricsComputer()
    metrics = mc.compute_all()
    mc.save_metrics(metrics['var_cvar'])
    
    logger.info("=" * 70)
    logger.info("✅ Metrics computation complete")
    logger.info("=" * 70)
