import numpy as np
import pandas as pd

from factor_operators import ABS, COUNT, DELTA, REGBETA


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
