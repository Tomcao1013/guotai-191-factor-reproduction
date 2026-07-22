import numpy as np
import pandas as pd
import pytest

import factor
from factor import (
    FACTORS,
    alpha2,
    alpha19,
    alpha38,
    alpha52,
    alpha94,
    alpha110,
    alpha117,
    alpha129,
    alpha162,
    alpha167,
    alpha187,
    calculate_factors,
)


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

NEW_FACTOR_FUNCTIONS = {
    "Alpha19": alpha19,
    "Alpha38": alpha38,
    "Alpha94": alpha94,
    "Alpha129": alpha129,
    "Alpha162": alpha162,
    "Alpha167": alpha167,
    "Alpha187": alpha187,
}


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
            "vwap": [10.5, 10.5],
            "volume": [1000.0, 1200.0],
            "amount": [10500.0, 12600.0],
            "benchmark_open": [4000.0, 4010.0],
            "benchmark_close": [4010.0, 4000.0],
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


def test_alpha110_sums_only_positive_price_excursions():
    data = pd.DataFrame(
        {
            "close": [100.0, *([10.0] * 20)],
            "high": [101.0, *([11.0] * 20)],
            "low": [99.0, *([9.0] * 20)],
        }
    )

    result = alpha110(data)

    expected_last_value = 19.0 / 110.0 * 100
    assert result.first_valid_index() == 20
    assert result.iloc[-1] == pytest.approx(expected_last_value)


def test_alpha52_uses_positive_up_and_down_pressures():
    rows = 28
    close = [10.0 + (index % 2) for index in range(rows)]
    data = pd.DataFrame(
        {
            "high": [value + 1.0 for value in close],
            "low": [value - 1.0 for value in close],
            "close": close,
        }
    )

    result = alpha52(data)

    assert result.first_valid_index() == 26
    assert result.iloc[-1] == pytest.approx(100.0)


def test_alpha117_accepts_close_series_for_returns():
    rows = 34
    data = pd.DataFrame(
        {
            "high": [12.0 + index for index in range(rows)],
            "low": [9.0 + index for index in range(rows)],
            "close": [10.0 + index for index in range(rows)],
            "volume": [100.0 + index for index in range(rows)],
        }
    )

    result = alpha117(data)

    assert result.notna().iloc[-1]


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


def test_new_factors_are_registered():
    for factor_name, factor_func in NEW_FACTOR_FUNCTIONS.items():
        assert FACTORS[factor_name] is factor_func


def test_alpha19_uses_the_formula_denominator_for_each_branch():
    data = pd.DataFrame(
        {
            "close": [
                100.0,
                90.0,
                90.0,
                90.0,
                90.0,
                90.0,
                90.0,
                100.0,
            ]
        }
    )

    result = alpha19(data)

    expected = pd.Series(
        [
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            np.nan,
            -0.1,
            0.0,
            0.1,
        ],
        name="Alpha19",
    )
    pd.testing.assert_series_equal(result, expected)


def test_alpha38_applies_negative_high_delta_after_full_threshold_window():
    data = pd.DataFrame(
        {
            "high": [
                *range(1, 21),
                30.0,
                5.0,
            ]
        }
    )

    result = alpha38(data)

    assert result.first_valid_index() == 19
    assert result.iloc[19] == pytest.approx(-2.0)
    assert result.iloc[20] == pytest.approx(-11.0)
    assert result.iloc[21] == pytest.approx(0.0)


def test_alpha94_sums_thirty_days_of_signed_volume():
    close = [10.0, *([11.0, 10.0, 10.0] * 10)]
    volume = [float(value) for value in range(1, 32)]
    data = pd.DataFrame(
        {
            "close": close,
            "volume": volume,
        }
    )

    result = alpha94(data)

    expected_last = sum(
        volume[index]
        if close[index] > close[index - 1]
        else -volume[index]
        if close[index] < close[index - 1]
        else 0.0
        for index in range(1, len(close))
    )
    assert result.first_valid_index() == 30
    assert result.iloc[-1] == pytest.approx(expected_last)


def test_alpha129_sums_only_absolute_negative_close_changes():
    close = [
        10.0,
        12.0,
        11.0,
        11.0,
        14.0,
        10.0,
        12.0,
        9.0,
        9.0,
        15.0,
        13.0,
        14.0,
        8.0,
    ]
    data = pd.DataFrame({"close": close})

    result = alpha129(data)

    expected_last = sum(
        close[index - 1] - close[index]
        for index in range(1, len(close))
        if close[index] < close[index - 1]
    )
    assert result.first_valid_index() == 12
    assert result.iloc[-1] == pytest.approx(expected_last)


def test_alpha162_normalizes_smoothed_up_move_ratio_over_twelve_days():
    close = pd.Series(
        [
            10.0,
            12.0,
            11.0,
            14.0,
            13.0,
            15.0,
            12.0,
            16.0,
            15.0,
            18.0,
            14.0,
            17.0,
            16.0,
            20.0,
            19.0,
            21.0,
            18.0,
            22.0,
        ]
    )
    data = pd.DataFrame({"close": close})

    result = alpha162(data)

    close_change = close.diff()
    smoothed_up_move = close_change.clip(lower=0).ewm(
        alpha=1 / 12,
        adjust=False,
        min_periods=1,
    ).mean()
    smoothed_absolute_move = close_change.abs().ewm(
        alpha=1 / 12,
        adjust=False,
        min_periods=1,
    ).mean()
    relative_strength = smoothed_up_move / smoothed_absolute_move * 100
    rolling_min = relative_strength.rolling(
        window=12,
        min_periods=12,
    ).min()
    rolling_max = relative_strength.rolling(
        window=12,
        min_periods=12,
    ).max()
    expected = (
        (relative_strength - rolling_min)
        / (rolling_max - rolling_min).replace(0, np.nan)
    ).rename("Alpha162")

    pd.testing.assert_series_equal(result, expected)


def test_alpha167_sums_only_positive_close_changes():
    close = [
        10.0,
        12.0,
        11.0,
        11.0,
        14.0,
        10.0,
        12.0,
        9.0,
        9.0,
        15.0,
        13.0,
        14.0,
        8.0,
    ]
    data = pd.DataFrame({"close": close})

    result = alpha167(data)

    expected_last = sum(
        close[index] - close[index - 1]
        for index in range(1, len(close))
        if close[index] > close[index - 1]
    )
    assert result.first_valid_index() == 12
    assert result.iloc[-1] == pytest.approx(expected_last)


def test_alpha187_sums_twenty_days_of_positive_open_movement():
    open_price = [
        10.0,
        12.0,
        11.0,
        13.0,
        13.0,
        14.0,
        12.0,
        15.0,
        16.0,
        15.0,
        17.0,
        16.0,
        18.0,
        18.0,
        20.0,
        19.0,
        21.0,
        22.0,
        20.0,
        23.0,
        24.0,
    ]
    high = [
        price + offset
        for price, offset in zip(
            open_price,
            [1.0, 1.0, 1.0, 4.0, 1.0, 1.0, 1.0] * 3,
        )
    ]
    data = pd.DataFrame(
        {
            "open": open_price,
            "high": high,
        }
    )

    result = alpha187(data)

    expected_last = sum(
        max(
            high[index] - open_price[index],
            open_price[index] - open_price[index - 1],
        )
        if open_price[index] > open_price[index - 1]
        else 0.0
        for index in range(1, len(open_price))
    )
    assert result.first_valid_index() == 20
    assert result.iloc[-1] == pytest.approx(expected_last)
