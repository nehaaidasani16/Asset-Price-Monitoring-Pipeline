import logging
import requests
from datetime import datetime, timezone
from config import TARGET_COINS, CRYPTO_VS_CURRENCY, RAW_CRYPTO_PATH
from storage import save_raw

logger = logging.getLogger(__name__)

API_URL = "https://api.coingecko.com/api/v3/simple/price"


def fetch_prices(coin_ids: list[str], vs_currency:str) -> dict:
    params = {"ids": ",".join(coin_ids), "vs_currencies": vs_currency}
    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json()

def extract() -> dict | None:
    try:
        raw_prices = fetch_prices(TARGET_COINS, CRYPTO_VS_CURRENCY)
        data = {
            "vs_currencies": CRYPTO_VS_CURRENCY,
            "prices": {coin: values.get(CRYPTO_VS_CURRENCY) for coin, values in raw_prices.items()},
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source": "crypto",
        }
        logger.info(f"Fetched crypto prices: {data['prices']}")
        return data
    except requests.RequestException as e:
        logger.error(f"Failed to fetch crypto prices: {e}")
        return None

if __name__ == "__main__":
    raw = extract()
    if raw:
        save_raw(raw, source_name="crypto", local_path= RAW_CRYPTO_PATH)
        print(f"Crypto extraction complete. Coins fetched: {list(raw['prices'].keys())}")
    else:
        print("Crypto extraction failed -- check LOGS.")