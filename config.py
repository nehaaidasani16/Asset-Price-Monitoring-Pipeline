import os
from dotenv import load_dotenv

load_dotenv()

# FX
BASE_CURRENCY = "USD"
TARGET_CURRENCIES = ["INR", "EUR", "GBP", "JPY", "AED"]

# CRYPTO

TARGET_COINS = ["bitcoin", "ethereum", "solana"]
CRYPTO_VS_CURRENCY = "usd"

# Database configuration
DB_CONFIG = {
    "host" : os.getenv("DB_HOST", "localhost"),
    "port" : os.getenv("DB_PORT", "5432"),
    "dbname" : os.getenv("DB_NAME", "asset_rates"),
    "user" : os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
}

AWS_CONFIG = {
    "bucket_name": os.getenv("S3_BUCKET_NAME", "your_assets_pipeline_raw_data"),
    "region" : os.getenv("AWS_REGION", "ap-south-1")
}

USE_S3 =  os.getenv("USE_S3", "false").lower() == "true"

RAW_FX_PATH = "raw_fx_rates.json"
RAW_CRYPTO_PATH = "raw_crypto_rates.json"
TRANSFORMED_DATA_PATH = "transformed_combined_rates.csv"

MAX_DAILY_MOVE_PCT = 5.0

LOG_FILE = "logs/pipeline.log"