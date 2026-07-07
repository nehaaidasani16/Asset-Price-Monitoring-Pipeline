<<<<<<< HEAD
# FX + Crypto Asset Price Monitoring Pipeline

**Automated ETL pipeline that fetches live FX rates and crypto prices from two public APIs daily, validates and anomaly-checks the data, loads it into PostgreSQL, archives raw data to AWS S3, and is orchestrated by Apache Airflow with full CI/CD via GitHub Actions.**

---

## Architecture

```
Frankfurter API ──┐
                   ├──► extract_fx.py  ──┐
CoinGecko API  ──┘                        │
                   extract_crypto.py ──┘
                                          │
                                          ▼
                               storage.py (save_raw)
                              ┌───────────┴───────────┐
                         Local disk               AWS S3
                        raw_fx.json           raw/fx/*.json
                      raw_crypto.json       raw/crypto/*.json
                                          │
                                          ▼
                               transform.py
                         flatten + validate + anomaly flag
                                          │
                                          ▼
                               load.py → PostgreSQL
                                  asset_prices table
                                          │
                               Orchestrated by Airflow DAG
                               Tested by pytest (12/12)
                               CI/CD via GitHub Actions
```

---

## Tech Stack

| Layer          | Technology            |
|----------------|-----------------------|
| Extraction     | Python, requests      |
| Storage (raw)  | AWS S3, boto3         |
| Transformation | pandas, NumPy         |
| Loading        | PostgreSQL, SQLAlchemy|
| Orchestration  | Apache Airflow 2.10.4 |
| Testing        | pytest (12 tests)     |
| CI/CD          | GitHub Actions        |
| Infrastructure | WSL2, Python 3.12     |

---

## Features

- **Dual-source extraction** — Frankfurter API (5 FX currencies) and CoinGecko API (3 crypto coins) called in parallel Airflow tasks
- **Raw data archiving** — both API responses saved to AWS S3 with timestamps before any processing, enabling full replay/reprocessing from the source
- **Data validation** — null checks, negative price checks, schema validation before any data reaches the database
- **Anomaly detection** — flags any asset whose price moved more than 5% vs. the previous day's stored value; anomalous rows are stored with `is_anomaly=True` rather than silently dropped
- **Idempotent loading** — composite primary key `(asset_symbol, as_of_date)` guarantees that running the pipeline twice on the same day never creates duplicates
- **Graceful degradation** — if one API fails, the pipeline continues with the other source rather than aborting entirely; failure is logged as WARNING, not a crash
- **Unified audit log** — `pipeline.log` captures every stage of every run regardless of whether it was triggered manually or by Airflow's scheduler
- **Full test coverage** — 12 pytest tests covering flatten, validate, anomaly detection, idempotency, and graceful degradation

---

## Setup & Running

### Prerequisites
- Python 3.10+
- PostgreSQL (running locally or accessible via network)
- AWS account with S3 bucket (optional — set `USE_S3=false` to skip)
- Apache Airflow 2.10.4


## Environment Variables

Create a `.env` file with:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=asset_rates
DB_USER=postgres
DB_PASSWORD=yourpassword

USE_S3=false 
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

---

## Data Schema

**Table: `asset_prices`**

|     Column     |   Type    | Description                                 |
|----------------|-----------|---------------------------------------------|
| `asset_symbol` |  VARCHAR  | Currency or coin symbol (e.g. INR, bitcoin) |
|  `asset_type`  |  VARCHAR  | `fx` or `crypto`                            |
|    `price`     |  DECIMAL  | Price in USD                                |
|  `as_of_date`  |    DATE   | Date the price is valid for                 |
|  `fetched_at`  | TIMESTAMP | UTC timestamp when data was fetched         |
|  `is_anomaly`  |  BOOLEAN  | True if price moved >5% vs. previous day    |

**Primary key:** `(asset_symbol, as_of_date)` — ensures idempotency.

---

## Key Engineering Decisions

**Why save raw data before processing?** If a bug is found in the transformation logic, the raw data can be reprocessed without re-calling the APIs. This also provides a complete audit trail of what the API returned on any given day.

**Why idempotent loading?** Pipelines fail and get retried. Without idempotency, a retry after a partial failure would insert duplicate rows and corrupt the dataset.

**Why flag anomalies instead of dropping them?** Silent data dropping is dangerous in financial data. A price that moved 15% might be a genuine market event, not bad data. Flagging preserves the row while signalling that human review is needed.

**Why feature-flag S3 with `USE_S3`?** Allows the pipeline to run in any environment (local dev, CI/CD, production) without code changes — only a config value changes.
=======
 # Asset Price Pipeline
>>>>>>> 0422c8fc4eba9f2633fdfd0fbfe56b8199d9cdd6
