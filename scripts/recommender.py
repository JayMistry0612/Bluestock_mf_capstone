"""
Fund Recommender System
=======================

A simple fund recommendation engine that suggests top 3 mutual funds based on 
investor's risk appetite (Low / Moderate / High). Recommendations are ranked 
by Sharpe ratio (risk-adjusted returns) within the matching risk category.

Usage:
------
from recommender import FundRecommender

recommender = FundRecommender('path/to/scheme_performance.csv', 'path/to/fund_master.csv')
recommendations = recommender.recommend('Moderate', top_n=3)
print(recommendations)

Or from command line:
python recommender.py --risk Moderate
"""

import pandas as pd
import numpy as np
import sys
import argparse
from pathlib import Path


class FundRecommender:
    """
    Fund Recommendation Engine
    
    Recommends mutual funds based on investor's risk appetite and Sharpe ratio ranking.
    """
    
    def __init__(self, scheme_performance_path, fund_master_path=None):
        """
        Initialize the recommender with fund data.
        
        Parameters:
        -----------
        scheme_performance_path : str
            Path to scheme_performance.csv containing Sharpe ratios and fund metrics
        fund_master_path : str, optional
            Path to fund_master.csv for additional fund details
        """
        self.scheme_performance = pd.read_csv(scheme_performance_path)
        self.fund_master = pd.read_csv(fund_master_path) if fund_master_path else None
        
    def recommend(self, risk_appetite, top_n=3):
        """
        Get fund recommendations for given risk appetite.
        
        Parameters:
        -----------
        risk_appetite : str
            Investor's risk profile: 'Low', 'Moderate', or 'High'
        top_n : int
            Number of recommendations to return (default: 3)
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with top N fund recommendations sorted by Sharpe ratio
        """
        
        risk_appetite = risk_appetite.strip().capitalize()
        
        if risk_appetite not in ['Low', 'Moderate', 'High', 'Very high']:
            raise ValueError(f"Invalid risk appetite '{risk_appetite}'. "
                           f"Use 'Low', 'Moderate', or 'High'.")
        
        # Map risk appetite to matching risk grades
        risk_mapping = {
            'Low': ['Low'],
            'Moderate': ['Low', 'Moderate'],
            'High': ['Moderate', 'High', 'Very High']
        }
        
        risk_grades = risk_mapping.get(risk_appetite, [])
        
        # Filter funds matching risk grade
        matching_funds = self.scheme_performance[
            self.scheme_performance['risk_grade'].isin(risk_grades)
        ].copy()
        
        if len(matching_funds) == 0:
            raise ValueError(f"No funds found for risk appetite '{risk_appetite}'")
        
        # Sort by Sharpe ratio (descending) and return top N
        recommendations = matching_funds.nlargest(top_n, 'sharpe_ratio')[
            ['scheme_name', 'fund_house', 'risk_grade', 'sharpe_ratio', 
             'sortino_ratio', 'return_1yr_pct', 'return_3yr_pct', 'std_dev_ann_pct', 
             'aum_crore', 'expense_ratio_pct', 'max_drawdown_pct']
        ].reset_index(drop=True)
        
        recommendations.index = recommendations.index + 1
        recommendations.index.name = 'Rank'
        
        return recommendations
    
    def print_recommendation(self, risk_appetite, top_n=3):
        """
        Print formatted recommendation table.
        
        Parameters:
        -----------
        risk_appetite : str
            Investor's risk profile
        top_n : int
            Number of recommendations
        """
        recommendations = self.recommend(risk_appetite, top_n)
        
        print("\n" + "="*120)
        print(f"FUND RECOMMENDATIONS - {risk_appetite.upper()} RISK PROFILE")
        print("="*120)
        print(recommendations.to_string())
        print("="*120)
        
        return recommendations


def main():
    """Command line interface for the recommender."""
    
    parser = argparse.ArgumentParser(
        description='Mutual Fund Recommendation Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python recommender.py --risk Low
  python recommender.py --risk Moderate --top 5
  python recommender.py --risk High --csv /path/to/scheme_performance.csv
        """
    )
    
    parser.add_argument(
        '--risk',
        type=str,
        default='Moderate',
        choices=['Low', 'Moderate', 'High'],
        help='Risk appetite: Low, Moderate, or High (default: Moderate)'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=3,
        help='Number of recommendations to return (default: 3)'
    )
    
    parser.add_argument(
        '--csv',
        type=str,
        default=None,
        help='Path to scheme_performance.csv (default: looks in ../data/processed/)'
    )
    
    args = parser.parse_args()
    
    # Default path if not specified
    if args.csv is None:
        script_dir = Path(__file__).parent
        args.csv = script_dir / '../data/processed/07_scheme_performance.csv'
    
    if not Path(args.csv).exists():
        print(f"❌ Error: File not found: {args.csv}")
        sys.exit(1)
    
    # Create recommender and print recommendations
    recommender = FundRecommender(args.csv)
    recommender.print_recommendation(args.risk, args.top)


if __name__ == '__main__':
    main()
