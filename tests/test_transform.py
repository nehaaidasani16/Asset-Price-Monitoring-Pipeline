import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transform import flatten_fx, flatten_crypto, validate, flag_anomalies, transform

def test_flatten_fx_produces_one_row_per_currency():
    raw_fx = {
        "base": "USD", "date": "2026-06-24",
        "rates": {"INR": 83.42, "EUR": 0.93},
        "fetched_at": "2026-06-24T07:00:00+00:00",
    }
    df = flatten_fx(raw_fx)
    assert len(df) == 2
    assert set(df["asset_symbol"]) == {"INR", "EUR"}
    assert set(df["asset_type"]) == {"fx"}


def test_flatten_crypto_produces_one_row_per_coin():
    raw_crypto = {
        "vs_currency": "usd",
        "prices": {"bitcoin": 68000.0, "ethereum": 3500.0},
        "fetched_at": "2026-06-24T07:00:00+00:00",
    }
    df = flatten_crypto(raw_crypto)
    assert len(df) == 2
    assert set(df["asset_symbol"]) == {"bitcoin", "ethereum"}
    assert set(df["asset_type"]) == {"crypto"}


def test_validate_drops_rows_with_missing_critical_fields():
    raw_fx = {
        "base": "USD", "date": "2026-06-24",
        "rates": {"INR": 83.42},
        "fetched_at": "2026-06-24T07:00:00+00:00",
    }
    df = flatten_fx(raw_fx)
    df.loc[0, "asset_symbol"] = None
    result = validate(df)
    assert len(result) == 0


def test_validate_drops_non_positive_prices():
    raw_fx = {
        "base": "USD", "date": "2026-06-24",
        "rates": {"INR": -5.0, "EUR": 0.93},
        "fetched_at": "2026-06-24T07:00:00+00:00",
    }
    df = flatten_fx(raw_fx)
    result = validate(df)
    assert len(result) == 1
    assert result.iloc[0]["asset_symbol"] == "EUR"


def test_anomaly_detection_flags_large_move():
    raw_fx = {
        "base": "USD", "date": "2026-06-25",
        "rates": {"INR": 95.00, "EUR": 0.935},  # INR +13.9%, EUR +0.5%
        "fetched_at": "2026-06-25T07:00:00+00:00",
    }
    previous_prices = {"INR": 83.42, "EUR": 0.93}
    df = flatten_fx(raw_fx)
    result = flag_anomalies(df, previous_prices)

    inr_row = result[result["asset_symbol"] == "INR"].iloc[0]
    eur_row = result[result["asset_symbol"] == "EUR"].iloc[0]

    assert inr_row["is_anomaly"] == True
    assert eur_row["is_anomaly"] == False


def test_anomaly_detection_handles_first_ever_run():
    raw_fx = {
        "base": "USD", "date": "2026-06-24",
        "rates": {"INR": 83.42},
        "fetched_at": "2026-06-24T07:00:00+00:00",
    }
    df = flatten_fx(raw_fx)
    result = flag_anomalies(df, previous_prices={})
    assert result.iloc[0]["is_anomaly"] == False


def test_transform_combines_both_sources_into_one_table():
    raw_fx = {
        "base": "USD", "date": "2026-06-24",
        "rates": {"INR": 83.42, "EUR": 0.93},
        "fetched_at": "2026-06-24T07:00:00+00:00",
    }
    raw_crypto = {
        "vs_currency": "usd",
        "prices": {"bitcoin": 68000.0},
        "fetched_at": "2026-06-24T07:00:00+00:00",
    }
    result = transform(raw_fx, raw_crypto, previous_prices={})
    assert len(result) == 3  # 2 FX rows + 1 crypto row
    assert set(result["asset_type"]) == {"fx", "crypto"}
