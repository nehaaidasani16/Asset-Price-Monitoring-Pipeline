import requests
import logging
from datetime import datetime, timezone
from config import BASE_CURRENCY, TARGET_CURRENCIES, RAW_FX_PATH
from storage import save_raw

logger = logging.getLogger(__name__)

API_URL = "https://api.frankfurter.dev/v1/latest"

def fetch_rates(base: str, symbols: list[str]) -> dict:
    params = {"base": base, "symbols": ",".join(symbols)} 
    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json()

def extract() -> dict | None:
    try:
        data = fetch_rates(BASE_CURRENCY, TARGET_CURRENCIES)
        data["fetched_at"] = datetime.now(timezone.utc).isoformat()
        data["source"] = "fx"
        logger.info(f"Fetched FX rates for base={BASE_CURRENCY}:{data['rates']}")
        return data
    except requests.RequestException as e:
        logger.error(f"Failed to fetch FX rates: {e}")
        return None


if __name__ == "__main__":
    raw = extract()
    if raw:
        save_raw(raw, source_name="fx", local_path=RAW_FX_PATH)
        print(f"FX extraction completed. Currencies fetched: {list(raw['rates'].keys())}")
    else:
        print("FX extraction failed -- check LOGS.")
    