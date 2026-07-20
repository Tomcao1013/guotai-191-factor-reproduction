import numpy as np
import pandas as pd
import pytest

import factor
from factor import FACTORS, alpha2, calculate_factors


REQUESTED_FACTORS = [
    2,
    3,
    5,
    9,
    11,
    14,
    15,
    20,
    29,
    31,
    40,
    43,
    46,
    53,
    60,
    69,
    80,
    84,
    168,
    191,
]


@pytest.mark.parametrize("factor_number", REQUESTED_FACTORS)
def test_requested_factor_function_has_formula_docstring(factor_number):
    factor_func = getattr(factor, f"alpha{factor_number}")

    assert callable(factor_func)
    assert f"Alpha{factor_number} =" in factor_func.__doc__


def test_alpha2_applies_negative_one_day_delta():
    data = pd.DataFrame(
        {
            "high": [12.0, 13.0, 15.0],
            "low": [8.0, 9.0, 9.0],
            "close": [11.0, 10.0, 12.0],
        }
    )

    result = alpha2(data)

    expected = pd.Series([np.nan, 1.0, -0.5], name="Alpha2")
    pd.testing.assert_series_equal(result, expected)


def test_calculate_factors_adds_registered_factors_without_mutating_input():
    data = pd.DataFrame(
        {
            "open": [10.0, 11.0],
            "high": [12.0, 13.0],
            "low": [8.0, 9.0],
            "close": [11.0, 10.0],
            "volume": [1000.0, 1200.0],
        }
    )
    original = data.copy()

    result = calculate_factors(data)

    assert result.columns.tolist() == [*data.columns, *FACTORS]
    pd.testing.assert_frame_equal(data, original)


def test_alpha2_returns_nan_when_high_equals_low():
    data = pd.DataFrame(
        {
            "high": [12.0, 13.0, 10.0],
            "low": [8.0, 9.0, 10.0],
            "close": [11.0, 10.0, 10.0],
        }
    )

    result = alpha2(data)

    assert np.isnan(result.iloc[-1])


def test_calculate_factors_uses_registered_factor(monkeypatch):
    data = pd.DataFrame(
        {
            "close": [10.0, 11.0],
        }
    )

    def alpha_test(frame: pd.DataFrame) -> pd.Series:
        return (frame["close"] * 2).rename("AlphaTest")

    monkeypatch.setattr(factor, "FACTORS", {"AlphaTest": alpha_test})

    result = calculate_factors(data)

    expected = pd.Series([20.0, 22.0], name="AlphaTest")
    pd.testing.assert_series_equal(result["AlphaTest"], expected)
