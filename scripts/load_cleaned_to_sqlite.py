import pathlib
import pandas as pd
from sqlalchemy import create_engine

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "bluestock_mf.db"

TABLE_MAP = {
    "01_fund_master.csv": "dim_fund",
    "02_nav_history.csv": "fact_nav",
    "03_aum_by_fund_house.csv": "fact_aum",
    "04_monthly_sip_inflows.csv": "fact_sip_industry",
    "05_category_inflows.csv": "fact_category_inflows",
    "06_industry_folio_count.csv": "fact_industry_folio_count",
    "07_scheme_performance.csv": "fact_performance",
    "08_investor_transactions.csv": "fact_transactions",
    "09_portfolio_holdings.csv": "fact_portfolio",
    "10_benchmark_indices.csv": "fact_benchmark_indices",
}


def load_csv_to_sqlite(csv_path: pathlib.Path, table_name: str, engine) -> None:
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"Loaded {csv_path.name} -> {table_name} ({len(df):,} rows)")


def main() -> None:
    engine = create_engine(f"sqlite:///{DB_PATH}")
    DB_PATH.unlink(missing_ok=True)
    print(f"Creating SQLite database at: {DB_PATH}")

    for csv_name, table_name in TABLE_MAP.items():
        csv_path = PROCESSED_DIR / csv_name
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing processed CSV: {csv_path}")
        load_csv_to_sqlite(csv_path, table_name, engine)

    print("All cleaned datasets loaded into SQLite database.")


if __name__ == "__main__":
    main()
