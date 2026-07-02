import os
import logging
import extract_fx
import extract_crypto
from transform import transform
from load import get_engine, get_previous_prices, load
from storage import save_raw
from config import LOG_FILE, RAW_FX_PATH, RAW_CRYPTO_PATH, TRANSFORMED_DATA_PATH


os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)

def run_pipeline() -> None:
    logger.info("=" * 60)
    logger.info("Pipeline Running\n")

# => Extract
    raw_fx = extract_fx.extract()
    raw_crypto = extract_crypto.extract()
    
    if raw_fx is None and raw_crypto is None:
        logger.error("Both extractions failed -- aborting pipeline run")
        return
    if raw_fx is None: 
        logger.warning("FX extraction failed; continuing with crypto data only")
        raw_fx = {"rates": {}, "date": None, "fetched_at": None}
    if raw_crypto is None:
        logger.warning("Crypto extraction failed; continuing with FX data only")
        raw_crypto = {"prices": {}, "fetched_at": None}

    save_raw(raw_fx, source_name="FX", local_path=RAW_FX_PATH)
    save_raw(raw_crypto, source_name="Crypto", local_path=RAW_CRYPTO_PATH)

# => Transform

    engine = get_engine()
    previous_prices = get_previous_prices(engine)

    clean_df = transform(raw_fx, raw_crypto, previous_prices=previous_prices)
    clean_df.to_csv(TRANSFORMED_DATA_PATH, index=False)
    logger.info(f"\nTransform stage produced {len(clean_df)} clean rows\n")


# => Load

    inserted = load(clean_df,engine)
    logger.info(f"\nPipeline run completed: {inserted} new rows loaded\n")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()