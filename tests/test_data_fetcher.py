# tests/test_data_fetcher.py
# Run test normally:
# pytest tests/

import sys
import os

# Go one level up (..)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import pytest
from datetime import datetime, timedelta, timezone
from data_fetcher import get_dynamic_date_range, fetch_weather_data

import requests
import requests_mock
import pandas as pd


def test_get_dynamic_date_range_exact_days():
    days_back = 10
    buffer_days = 0
    start_str, end_str = get_dynamic_date_range(days_back=days_back, buffer_days=buffer_days)

    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    end = datetime.strptime(end_str, "%Y-%m-%d").date()

    assert (end - start).days == days_back
    assert end == datetime.now(timezone.utc).date()


def test_get_dynamic_date_range_with_buffer():
    days_back = 7
    buffer_days = 2
    start_str, end_str = get_dynamic_date_range(days_back=days_back, buffer_days=buffer_days)

    today = datetime.now(timezone.utc).date()
    expected_end = today - timedelta(days=buffer_days)
    expected_start = expected_end - timedelta(days=days_back)

    assert start_str == expected_start.strftime('%Y-%m-%d')
    assert end_str == expected_end.strftime('%Y-%m-%d')


def test_fetch_weather_data_mocked():
    # Arrange
    dummy_response = {
        "hourly": {
            "time": ["2023-01-01T00:00", "2023-01-01T01:00"],
            "temperature_2m": [20.5, 21.0],
            "relative_humidity_2m": [80, 82]
        }
    }

    hourly_vars = ["temperature_2m", "relative_humidity_2m"]
    start_date = "2023-01-01"
    end_date = "2023-01-01"

    with requests_mock.Mocker() as mock:
        mock.get(requests_mock.ANY, json=dummy_response)

        # Act
        df = fetch_weather_data(
            latitude=23.8041,
            longitude=90.4152,
            hourly_variables=hourly_vars,
            start_date=start_date,
            end_date=end_date,
            timezone="Asia/Dhaka"
        )

        # Assert
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "temperature_2m" in df.columns
        assert "relative_humidity_2m" in df.columns
        assert df.shape[0] == 2
