import pandas as pd

from factor_operators import COUNT, DELTA


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
