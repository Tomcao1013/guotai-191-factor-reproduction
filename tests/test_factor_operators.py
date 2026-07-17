import pandas as pd

from factor_operators import delta


def test_delta_subtracts_the_lagged_series():
    series = pd.Series([10.0, 12.5, 11.0])

    result = delta(series, periods=1)

    expected = pd.Series([float("nan"), 2.5, -1.5])
    pd.testing.assert_series_equal(result, expected)
