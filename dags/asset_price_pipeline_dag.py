from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def extract_fx_callback(**context):
    import extract_fx
    from storage import save_raw
    from config import RAW_FX_PATH

    raw = extract_fx.extract()
    if raw is None:
        raw = {"rates": {}, "date": None, "fetched_at": None}
    else:
        save_raw(raw, source_name="fx", local_path=RAW_FX_PATH)
    context['ti'].xcom_push(key="raw_fx", value=raw)


def extract_crypto_callback(**context):
    import extract_crypto
    from storage import save_raw
    from config import RAW_CRYPTO_PATH

    raw = extract_crypto.extract()
    if raw is None:
        raw = {"prices": {}, "fetched_at": None}
    else:
        save_raw(raw, source_name="crypto", local_path=RAW_CRYPTO_PATH)
    context['ti'].xcom_push(key="raw_crypto", value=raw)


def transform_callback(**context):
    from transform import transform
    from load import get_engine, get_previous_prices
    from config import TRANSFORMED_DATA_PATH

    ti = context['ti']
    raw_fx = ti.xcom_pull(task_ids="extract_fx_task", key="raw_fx")
    raw_crypto = ti.xcom_pull(task_ids="extract_crypto_task", key="raw_crypto")

    engine = get_engine()
    previous_prices = get_previous_prices(engine)

    clean_df = transform(raw_fx, raw_crypto, previous_prices=previous_prices)
    clean_df.to_csv(TRANSFORMED_DATA_PATH, index=False)
    ti.xcom_push(key="row_count", value=len(clean_df))


def load_callback(**context):
    import pandas as pd
    from load import get_engine, load
    from config import TRANSFORMED_DATA_PATH

    df = pd.read_csv(TRANSFORMED_DATA_PATH)
    engine = get_engine()
    inserted = load(df, engine)
    context["ti"].xcom_push(key="rows_inserted", value=inserted)


default_args = {
    "owner": "neha",
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}


with DAG(
    dag_id="asset_price_pipeline",
    description="Daily FX  & Crypto price ETL with anomaly detection",
    default_args=default_args,
    start_date=datetime(2026, 7, 1),
    schedule="@daily",
    catchup=False,
    tags=["etl", "fx", "crypto", "pipeline"],
) as dag:

    extract_fx_task = PythonOperator(
        task_id = "extract_fx_task",
        python_callable=extract_fx_callback,
    )

    extract_crypto_task = PythonOperator(
        task_id = "extract_crypto_task",
        python_callable=extract_crypto_callback,
    )

    transform_task = PythonOperator(
        task_id = "transform_task",
        python_callable=transform_callback,
    )

    load_task = PythonOperator(
        task_id = "load_task",
        python_callable=load_callback,
    )



    [extract_fx_task, extract_crypto_task] >> transform_task >> load_task