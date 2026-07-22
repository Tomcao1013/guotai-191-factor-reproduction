import numpy as np
import pandas as pd

import factor_operators
from factor_operators import (
    ABS,
    COUNT,
    DECAYLINEAR,
    DELTA,
    FILTER,
    HIGHDAY,
    LOWDAY,
    RANK,
    REGBETA,
    SEQUENCE,
    SUMIF,
    WMA,
)


def test_abs_returns_elementwise_absolute_values():
    series = pd.Series([-2.0, 0.0, 3.5, np.nan])

    result = ABS(series)

    expected = pd.Series([2.0, 0.0, 3.5, np.nan])
    pd.testing.assert_series_equal(result, expected)


def test_delta_subtracts_the_lagged_series():
    series = pd.Series([10.0, 12.5, 11.0])

    result = DELTA(series, periods=1)

    expected = pd.Series([float("nan"), 2.5, -1.5])
    pd.testing.assert_series_equal(result, expected)


def test_count_sums_true_values_in_a_complete_window():
    series = pd.Series([True, False, True])

    result = COUNT(series, periods=2)

    expected = pd.Series([float("nan"), 1.0, 1.0])
    pd.testing.assert_series_equal(result, expected)


def test_regbeta_returns_the_rolling_slope_of_a_on_b():
    series_b = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    series_a = 2.0 * series_b + 3.0

    result = REGBETA(series_a, series_b, periods=3)

    expected = pd.Series([np.nan, np.nan, 2.0, 2.0, 2.0])
    pd.testing.assert_series_equal(result, expected)


def test_regbeta_returns_nan_when_the_independent_variable_is_constant():
    series_a = pd.Series([1.0, 2.0, 3.0])
    series_b = pd.Series([5.0, 5.0, 5.0])

    result = REGBETA(series_a, series_b, periods=3)

    assert np.isnan(result.iloc[-1])


def test_regbeta_accepts_a_fixed_sequence_window():
    series = pd.Series([1.0, 3.0, 5.0, 7.0])

    result = REGBETA(series, SEQUENCE(3))

    expected = pd.Series([np.nan, np.nan, 2.0, 2.0])
    pd.testing.assert_series_equal(result, expected)


def test_rank_is_cross_sectional_within_each_group():
    series = pd.Series([3.0, 1.0, 2.0, 10.0, 20.0])
    groups = pd.Series(["a", "a", "a", "b", "b"])

    result = RANK(series, groups)

    expected = pd.Series([1.0, 1 / 3, 2 / 3, 0.5, 1.0])
    pd.testing.assert_series_equal(result, expected)


def test_weighted_averages_give_more_weight_to_recent_values():
    series = pd.Series([1.0, 2.0, 3.0])

    wma_result = WMA(series, 3)
    decay_result = DECAYLINEAR(series, 3)

    wma_weights = np.array([0.9**2, 0.9, 1.0])
    expected_wma = np.dot(series, wma_weights / wma_weights.sum())
    expected_decay = np.dot(series, np.array([1, 2, 3]) / 6)

    assert wma_result.iloc[-1] == expected_wma
    assert decay_result.iloc[-1] == expected_decay


def test_extreme_day_uses_the_most_recent_tied_extreme():
    series = pd.Series([3.0, 1.0, 3.0])

    high_day = HIGHDAY(series, 3)
    low_day = LOWDAY(series, 3)

    assert high_day.iloc[-1] == 0.0
    assert low_day.iloc[-1] == 1.0


def test_sumif_sums_only_rows_matching_the_condition():
    series = pd.Series([1.0, 2.0, 3.0])
    condition = pd.Series([True, False, True])

    result = SUMIF(series, 3, condition)

    expected = pd.Series([np.nan, np.nan, 4.0])
    pd.testing.assert_series_equal(result, expected)


def test_filter_keeps_only_matching_rows():
    series = pd.Series([1.0, 2.0, 3.0])
    condition = pd.Series([False, True, True])

    result = FILTER(series, condition)

    expected = pd.Series([2.0, 3.0], index=[1, 2])
    pd.testing.assert_series_equal(result, expected)


def _operator(name: str):
    operator = getattr(
        factor_operators,
        name,
        None,
    )
    assert callable(operator), f"{name} is not implemented"
    return operator


def test_sumac_returns_the_cumulative_sum():
    series = pd.Series([1.0, 2.0, np.nan, 3.0])

    result = _operator("SUMAC")(series)

    expected = pd.Series([1.0, 3.0, np.nan, 6.0])
    pd.testing.assert_series_equal(result, expected)


def test_tr_hd_ld_match_the_report_definitions():
    high = pd.Series([11.0, 13.0, 12.0])
    low = pd.Series([9.0, 10.0, 8.0])
    close = pd.Series([10.0, 12.0, 9.0])

    true_range = _operator("TR")(high, low, close)
    high_direction = _operator("HD")(high)
    low_direction = _operator("LD")(low)

    pd.testing.assert_series_equal(
        true_range,
        pd.Series([np.nan, 3.0, 4.0]),
    )
    pd.testing.assert_series_equal(
        high_direction,
        pd.Series([np.nan, 2.0, -1.0]),
    )
    pd.testing.assert_series_equal(
        low_direction,
        pd.Series([np.nan, -1.0, 2.0]),
    )
