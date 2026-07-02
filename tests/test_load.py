import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from load import get_engine, create_table, get_previous_prices, load
from transform import transform


@pytest.fixture
def engine():
    return get_engine(connection_url="sqlite:///:memory:")


def test_table_is_created_if_missing(engine):
    create_table(engine)
    # Calling it again should not raise an error (IF NOT EXISTS works)
    create_table(engine)


def test_previous_prices_empty_on_first_run(engine):
    prices = get_previous_prices(engine)
    assert prices == {}


def test_load_inserts_new_rows(engine):
    raw_fx = {"base": "USD", "date": "2026-06-24",
              "rates": {"INR": 83.42}, "fetched_at": "2026-06-24T07:00:00+00:00"}
    raw_crypto = {"vs_currency": "usd", "prices": {"bitcoin": 68000.0},
                  "fetched_at": "2026-06-24T07:00:00+00:00"}

    df = transform(raw_fx, raw_crypto, previous_prices={})
    inserted = load(df, engine)
    assert inserted == 2


def test_load_is_idempotent_on_rerun(engine):
    raw_fx = {"base": "USD", "date": "2026-06-24",
              "rates": {"INR": 83.42}, "fetched_at": "2026-06-24T07:00:00+00:00"}
    raw_crypto = {"vs_currency": "usd", "prices": {},
                  "fetched_at": "2026-06-24T07:00:00+00:00"}

    df = transform(raw_fx, raw_crypto, previous_prices={})

    first_run_inserted = load(df, engine)
    second_run_inserted = load(df, engine)  # identical data, same day

    assert first_run_inserted == 1
    assert second_run_inserted == 0  # nothing new -- duplicates skipped


def test_previous_prices_reflects_most_recent_load(engine):
    raw_fx = {"base": "USD", "date": "2026-06-24",
              "rates": {"INR": 83.42}, "fetched_at": "2026-06-24T07:00:00+00:00"}
    raw_crypto = {"vs_currency": "usd", "prices": {},
                  "fetched_at": "2026-06-24T07:00:00+00:00"}

    df = transform(raw_fx, raw_crypto, previous_prices={})
    load(df, engine)

    previous = get_previous_prices(engine)
    assert previous == {"INR": 83.42}
