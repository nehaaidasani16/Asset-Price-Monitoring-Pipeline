import logging
import json
import pandas as pd
from config import RAW_FX_PATH, RAW_CRYPTO_PATH, TRANSFORMED_DATA_PATH, MAX_DAILY_MOVE_PCT


logger = logging.getLogger(__name__)


def load_raw_fx(filepath: str = RAW_FX_PATH) -> dict:
    with open(filepath) as f:
        return json.load(f)

def load_raw_crypto(filepath: str = RAW_CRYPTO_PATH) -> dict:
    with open(filepath) as f:
        return json.load(f)
    
def flatten_fx(raw: dict) -> pd.DataFrame:
    rows = []
    for currency, rate in raw.get('rates', {}).items():
        rows.append({
            "asset_type" : "fx",
            "asset_symbol": currency,
            "price": rate,
            "as_of_date": raw.get("date"),
            "fetched_at": raw.get("fetched_at"),
        })
    return pd.DataFrame(rows)
    
def flatten_crypto(raw: dict) -> pd.DataFrame:
    rows = []
    as_of_date = raw.get("fetched_at", "")[:10]
    
    for coin, price in raw.get("prices", {}).items():
        rows.append({
            "asset_type" : "crypto",
            "asset_symbol": coin,
            "price": price,
            "as_of_date": as_of_date,
            "fetched_at": raw.get("fetched_at"),
        })
    return pd.DataFrame(rows)
    
def validate(df: pd.DataFrame) -> pd.DataFrame:
    original_count = len(df)

    df = df.dropna(subset=["asset_symbol", "price"])
    df = df[df["price"] > 0]

    dropped = original_count - len(df)
    if dropped:
        logger.warning(f"Dropped {dropped} rows, failing basic validation")
    else:
        logger.info("All rows passed basic validation")

    return df

def flag_anomalies(df: pd.DataFrame, previous_prices: dict[str, float]):
    def check_row(row):
        prev = previous_prices.get(row["asset_symbol"])
        if prev is None or prev == 0:
            return False
        pct_move = abs(row["price"] - prev) / prev * 100
        return pct_move > MAX_DAILY_MOVE_PCT
    
    df["is_anomaly"] = df.apply(check_row, axis=1)

    anomaly_count = df["is_anomaly"].sum()
    if anomaly_count > 0:
        flagged = df[df["is_anomaly"]]["asset_symbol"].tolist()
        logger.warning(f"Flagged {anomaly_count} anomalous asset(s): {flagged}")
    else:
        logger.info("No anomalies detected")

    return df


def transform(raw_fx: dict, raw_crypto: dict, previous_prices: dict[str, float]| None = None) -> pd.DataFrame:
    
    fx_df = flatten_fx(raw_fx)
    crypto_df = flatten_crypto(raw_crypto)

    combined = pd.concat([fx_df, crypto_df], ignore_index=True)
    logger.info(f"Combined {len(fx_df)} FX rows & {len(crypto_df)} Crypto rows => {len(combined)} total")

    combined = validate(combined)
    combined = flag_anomalies(combined, previous_prices or {})
    return combined

if __name__ == "__main__":
    raw_fx = load_raw_fx()
    raw_crypto = load_raw_crypto()
    clean_df = transform(raw_fx, raw_crypto, previous_prices={})
    clean_df.to_csv(TRANSFORMED_DATA_PATH, index=False)
    print(f"Transformation Complete : {len(clean_df)} rows saved to {TRANSFORMED_DATA_PATH}")
    print(clean_df)