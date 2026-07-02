
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from config import DB_CONFIG, TRANSFORMED_DATA_PATH

logger = logging.getLogger(__name__)

TABLE_NAME = "asset_prices"

def get_engine(connection_url:str | None = None) -> Engine:
    if connection_url is None:
        connection_url = (
            f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
        )
    return create_engine(connection_url)

def create_table(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
                asset_type      VARCHAR(10),
                asset_symbol    VARCHAR(20), 
                price           FLOAT,
                as_of_date      VARCHAR(20),
                fetched_at      VARCHAR(40),
                is_anomaly      BOOLEAN,
                PRIMARY KEY (asset_symbol, as_of_date)
            )
"""))
    logger.info(f"Ensured table '{TABLE_NAME}' exists")


def get_previous_prices(engine: Engine) -> dict[str, float]:
    create_table(engine)
    query = text(f"""
        SELECT asset_symbol, price
        FROM  {TABLE_NAME} t1
        WHERE as_of_date = (
            SELECT MAX(as_of_date) FROM {TABLE_NAME} t2
            WHERE  t2.asset_symbol = t1.asset_symbol
        )
""")
    with engine.connect() as conn:
        result = conn.execute(query)
        prices = {row.asset_symbol: row.price for row in result}
    logger.info(f"Loaded {len(prices)} previous price(s) for anomaly comparison")
    return prices

def load(df: pd.DataFrame, engine: Engine) -> int:
    create_table(engine)

    inserted, skipped = 0, 0
    for _, row in df.iterrows():
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(f"""
                        INSERT INTO {TABLE_NAME}
                        (asset_type, asset_symbol, price, as_of_date, fetched_at, is_anomaly)
                        VALUES (:asset_type, :asset_symbol, :price, :as_of_date, :fetched_at, :is_anomaly)
                        """),
                        {
                            "asset_type"    : row["asset_type"],
                            "asset_symbol"  : row["asset_symbol"],
                            "price"         : row["price"],
                            "as_of_date"    : row["as_of_date"],
                            "fetched_at"    : row["fetched_at"],
                            "is_anomaly"    : bool(row["is_anomaly"]),
                        },
                )
            inserted += 1

        except Exception:
            skipped +=1

    logger.info(f"Load complete: {inserted} inserted, {skipped} duplicate skipped")
    return inserted

if __name__ == "__main__":
    df=pd.read_csv(TRANSFORMED_DATA_PATH)
    engine = get_engine()
    load(df, engine)

