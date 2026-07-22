import numpy as np
import pandas as pd
import pytest

import factor
from factor import FACTORS


TARGET_FACTOR_NUMBERS = [
    4,
    22,
    23,
    28,
    49,
    50,
    51,
    55,
    78,
    86,
    98,
    112,
    127,
    128,
    137,
    143,
    146,
    159,
    160,
    164,
    165,
    166,
    172,
    174,
    183,
    186,
]


def _factor_result(
    factor_number: int,
    data: pd.DataFrame,
) -> pd.Series:
    factor_func = getattr(
        factor,
        f"alpha{factor_number}",
        None,
    )
    assert callable(factor_func), f"alpha{factor_number} is not implemented"
    return factor_func(data)


def _sma(
    series: pd.Series,
    periods: int,
    weight: int,
) -> pd.Series:
    return series.ewm(
        alpha=weight / periods,
        adjust=False,
        min_periods=1,
    ).mean()


def _sample_price_data(rows: int = 240) -> pd.DataFrame:
    position = np.arange(rows, dtype=float)
    close = (
        100.0
        + position * 0.08
        + np.sin(position / 2.7) * 3.0
        + np.cos(position / 7.0) * 1.5
    )
    open_price = close + np.where(
        (position.astype(int) % 3) == 0,
        -0.8,
        0.6,
    )
    high = np.maximum(open_price, close) + 1.0 + position % 4 * 0.15
    low = np.minimum(open_price, close) - 1.1 - position % 5 * 0.12
    volume = 1000.0 + position * 5.0 + position % 11 * 70.0

    return pd.DataFrame(
        {
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def _alpha49_move_sums(
    data: pd.DataFrame,
) -> tuple[pd.Series, pd.Series]:
    high = data["high"]
    low = data["low"]
    previous_high = high.shift(1)
    previous_low = low.shift(1)
    current_sum = high + low
    previous_sum = previous_high + previous_low
    movement = np.maximum(
        (high - previous_high).abs(),
        (low - previous_low).abs(),
    )

    upward = movement.where(
        current_sum > previous_sum,
        0.0,
    ).where(previous_sum.notna())
    downward = movement.where(
        current_sum < previous_sum,
        0.0,
    ).where(previous_sum.notna())

    return (
        upward.rolling(12, min_periods=12).sum(),
        downward.rolling(12, min_periods=12).sum(),
    )


def _alpha137_daily_term(
    data: pd.DataFrame,
) -> pd.Series:
    previous_close = data["close"].shift(1)
    previous_open = data["open"].shift(1)
    previous_low = data["low"].shift(1)

    high_to_previous_close = (
        data["high"] - previous_close
    ).abs()
    low_to_previous_close = (
        data["low"] - previous_close
    ).abs()
    high_to_previous_low = (
        data["high"] - previous_low
    ).abs()
    previous_body = (
        previous_close - previous_open
    ).abs()

    denominator = pd.Series(
        np.select(
            [
                (
                    (high_to_previous_close > low_to_previous_close)
                    & (high_to_previous_close > high_to_previous_low)
                ),
                (
                    (low_to_previous_close > high_to_previous_low)
                    & (low_to_previous_close > high_to_previous_close)
                ),
            ],
            [
                (
                    high_to_previous_close
                    + low_to_previous_close / 2
                    + previous_body / 4
                ),
                (
                    low_to_previous_close
                    + high_to_previous_close / 2
                    + previous_body / 4
                ),
            ],
            default=high_to_previous_low + previous_body / 4,
        ),
        index=data.index,
    )
    scale = np.maximum(
        high_to_previous_close,
        low_to_previous_close,
    )
    numerator = (
        data["close"]
        - previous_close
        + (data["close"] - data["open"]) / 2
        + previous_close
        - previous_open
    )
    result = (
        16
        * numerator
        / denominator.replace(0, np.nan)
        * scale
    )

    return result.where(
        previous_close.notna()
        & previous_open.notna()
        & previous_low.notna()
    )


def test_alpha4_follows_nested_price_and_volume_conditions():
    data = _sample_price_data(50)
    average_close_8d = data["close"].rolling(
        8,
        min_periods=8,
    ).mean()
    close_std_8d = data["close"].rolling(
        8,
        min_periods=8,
    ).std(ddof=1)
    average_close_2d = data["close"].rolling(
        2,
        min_periods=2,
    ).mean()
    volume_ratio = (
        data["volume"]
        / data["volume"].rolling(20, min_periods=20).mean()
    )
    valid = (
        average_close_8d.notna()
        & close_std_8d.notna()
        & average_close_2d.notna()
        & volume_ratio.notna()
    )
    expected = pd.Series(
        np.select(
            [
                average_close_8d + close_std_8d < average_close_2d,
                average_close_2d < average_close_8d - close_std_8d,
                volume_ratio >= 1,
            ],
            [-1.0, 1.0, 1.0],
            default=-1.0,
        ),
        index=data.index,
    ).where(valid).rename("Alpha4")

    result = _factor_result(4, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha22_smooths_the_three_day_change_in_close_deviation():
    data = _sample_price_data(45)
    average_close_6d = data["close"].rolling(
        6,
        min_periods=6,
    ).mean()
    deviation = (
        data["close"] - average_close_6d
    ) / average_close_6d
    expected = _sma(
        deviation - deviation.shift(3),
        12,
        1,
    ).rename("Alpha22")

    result = _factor_result(22, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha23_splits_smoothed_volatility_by_close_direction():
    data = _sample_price_data(60)
    previous_close = data["close"].shift(1)
    close_std_20d = data["close"].rolling(
        20,
        min_periods=20,
    ).std(ddof=1)
    upward_volatility = close_std_20d.where(
        data["close"] > previous_close,
        0.0,
    )
    downward_volatility = close_std_20d.where(
        data["close"] <= previous_close,
        0.0,
    )
    smoothed_upward = _sma(
        upward_volatility,
        20,
        1,
    )
    smoothed_downward = _sma(
        downward_volatility,
        20,
        1,
    )
    expected = (
        smoothed_upward
        / (smoothed_upward + smoothed_downward).replace(0, np.nan)
        * 100
    ).where(close_std_20d.notna()).rename("Alpha23")

    result = _factor_result(23, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha28_combines_single_and_double_smoothed_oscillators():
    data = _sample_price_data(45)
    minimum_low_9d = data["low"].rolling(
        9,
        min_periods=9,
    ).min()
    maximum_high_9d = data["high"].rolling(
        9,
        min_periods=9,
    ).max()
    maximum_low_9d = data["low"].rolling(
        9,
        min_periods=9,
    ).max()
    fast_input = (
        (data["close"] - minimum_low_9d)
        / (maximum_high_9d - minimum_low_9d).replace(0, np.nan)
        * 100
    )
    slow_input = (
        (data["close"] - minimum_low_9d)
        / (maximum_high_9d - maximum_low_9d).replace(0, np.nan)
        * 100
    )
    expected = (
        3 * _sma(fast_input, 3, 1)
        - 2 * _sma(
            _sma(slow_input, 3, 1),
            3,
            1,
        )
    ).rename("Alpha28")

    result = _factor_result(28, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha49_alpha50_alpha51_share_directional_move_components():
    data = _sample_price_data(45)
    upward_sum, downward_sum = _alpha49_move_sums(data)
    total = (upward_sum + downward_sum).replace(0, np.nan)
    expected = {
        49: (downward_sum / total).rename("Alpha49"),
        50: (
            upward_sum / total - downward_sum / total
        ).rename("Alpha50"),
        51: (upward_sum / total).rename("Alpha51"),
    }

    for factor_number, expected_result in expected.items():
        result = _factor_result(factor_number, data)
        pd.testing.assert_series_equal(
            result,
            expected_result,
        )


def test_alpha55_is_the_twenty_day_sum_of_alpha137_daily_term():
    data = _sample_price_data(50)
    daily_term = _alpha137_daily_term(data)
    expected_alpha137 = daily_term.rename("Alpha137")
    expected_alpha55 = daily_term.rolling(
        20,
        min_periods=20,
    ).sum().rename("Alpha55")

    pd.testing.assert_series_equal(
        _factor_result(137, data),
        expected_alpha137,
    )
    pd.testing.assert_series_equal(
        _factor_result(55, data),
        expected_alpha55,
    )


def test_alpha78_normalizes_typical_price_deviation():
    data = _sample_price_data(50)
    typical_price = (
        data["high"]
        + data["low"]
        + data["close"]
    ) / 3
    average_typical_price_12d = typical_price.rolling(
        12,
        min_periods=12,
    ).mean()
    mean_absolute_deviation = (
        data["close"] - average_typical_price_12d
    ).abs().rolling(
        12,
        min_periods=12,
    ).mean()
    expected = (
        (typical_price - average_typical_price_12d)
        / (0.015 * mean_absolute_deviation).replace(0, np.nan)
    ).rename("Alpha78")

    result = _factor_result(78, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha86_applies_all_three_acceleration_branches():
    data = _sample_price_data(60)
    close = data["close"]
    acceleration = (
        (close.shift(20) - close.shift(10)) / 10
        - (close.shift(10) - close) / 10
    )
    expected = pd.Series(
        np.select(
            [
                acceleration > 0.25,
                acceleration < 0,
            ],
            [
                -1.0,
                1.0,
            ],
            default=-(close - close.shift(1)),
        ),
        index=data.index,
    ).where(acceleration.notna()).rename("Alpha86")

    result = _factor_result(86, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha98_switches_between_drawdown_and_three_day_change():
    data = _sample_price_data(230)
    close = data["close"]
    average_close_100d = close.rolling(
        100,
        min_periods=100,
    ).sum() / 100
    trend = (
        average_close_100d - average_close_100d.shift(100)
    ) / close.shift(100)
    drawdown = -(
        close
        - close.rolling(100, min_periods=100).min()
    )
    change_3d = -(close - close.shift(3))
    expected = change_3d.where(
        trend > 0.05,
        drawdown,
    ).where(trend.notna()).rename("Alpha98")

    result = _factor_result(98, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha112_balances_positive_and_negative_close_changes():
    data = _sample_price_data(45)
    close_change = data["close"].diff()
    upward = close_change.where(
        close_change > 0,
        0.0,
    ).where(close_change.notna())
    downward = (-close_change).where(
        close_change < 0,
        0.0,
    ).where(close_change.notna())
    upward_sum = upward.rolling(
        12,
        min_periods=12,
    ).sum()
    downward_sum = downward.rolling(
        12,
        min_periods=12,
    ).sum()
    expected = (
        (upward_sum - downward_sum)
        / (upward_sum + downward_sum).replace(0, np.nan)
        * 100
    ).rename("Alpha112")

    result = _factor_result(112, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha127_is_twelve_day_root_mean_square_drawdown():
    data = _sample_price_data(50)
    maximum_close_12d = data["close"].rolling(
        12,
        min_periods=12,
    ).max()
    squared_drawdown = (
        100
        * (data["close"] - maximum_close_12d)
        / maximum_close_12d.replace(0, np.nan)
    ) ** 2
    expected = np.sqrt(
        squared_drawdown.rolling(
            12,
            min_periods=12,
        ).mean()
    ).rename("Alpha127")

    result = _factor_result(127, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha128_uses_fourteen_day_positive_and_negative_money_flow():
    data = _sample_price_data(50)
    typical_price = (
        data["high"]
        + data["low"]
        + data["close"]
    ) / 3
    previous_typical_price = typical_price.shift(1)
    money_flow = typical_price * data["volume"]
    positive_flow = money_flow.where(
        typical_price > previous_typical_price,
        0.0,
    ).where(previous_typical_price.notna())
    negative_flow = money_flow.where(
        typical_price < previous_typical_price,
        0.0,
    ).where(previous_typical_price.notna())
    positive_sum = positive_flow.rolling(
        14,
        min_periods=14,
    ).sum()
    negative_sum = negative_flow.rolling(
        14,
        min_periods=14,
    ).sum()
    money_flow_ratio = (
        positive_sum
        / negative_sum.replace(0, np.nan)
    )
    expected = (
        100 - 100 / (1 + money_flow_ratio)
    ).rename("Alpha128")

    result = _factor_result(128, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha143_recurses_from_a_unit_seed():
    close = pd.Series(
        [
            10.0,
            11.0,
            10.0,
            12.0,
            12.0,
            15.0,
        ]
    )
    data = pd.DataFrame({"close": close})
    expected = pd.Series(
        [
            1.0,
            0.1,
            0.1,
            0.02,
            0.02,
            0.005,
        ],
        name="Alpha143",
    )

    result = _factor_result(143, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha159_combines_six_twelve_and_twenty_four_day_ranges():
    data = _sample_price_data(60)
    previous_close = data["close"].shift(1)
    lower_bound = np.minimum(
        data["low"],
        previous_close,
    )
    upper_bound = np.maximum(
        data["high"],
        previous_close,
    )

    def component(periods: int) -> pd.Series:
        lower_sum = lower_bound.rolling(
            periods,
            min_periods=periods,
        ).sum()
        range_sum = (
            upper_bound - lower_bound
        ).rolling(
            periods,
            min_periods=periods,
        ).sum()
        return (
            data["close"] - lower_sum
        ) / range_sum.replace(0, np.nan)

    expected = (
        (
            component(6) * 12 * 24
            + component(12) * 6 * 24
            + component(24) * 6 * 24
        )
        * 100
        / (6 * 12 + 6 * 24 + 12 * 24)
    ).rename("Alpha159")

    result = _factor_result(159, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha160_and_alpha174_split_volatility_by_direction():
    data = _sample_price_data(60)
    previous_close = data["close"].shift(1)
    close_std_20d = data["close"].rolling(
        20,
        min_periods=20,
    ).std(ddof=1)
    expected_alpha160 = _sma(
        close_std_20d.where(
            data["close"] <= previous_close,
            0.0,
        ),
        20,
        1,
    ).where(close_std_20d.notna()).rename("Alpha160")
    expected_alpha174 = _sma(
        close_std_20d.where(
            data["close"] > previous_close,
            0.0,
        ),
        20,
        1,
    ).where(close_std_20d.notna()).rename("Alpha174")

    pd.testing.assert_series_equal(
        _factor_result(160, data),
        expected_alpha160,
    )
    pd.testing.assert_series_equal(
        _factor_result(174, data),
        expected_alpha174,
    )


def test_alpha164_smooths_normalized_inverse_positive_change():
    data = _sample_price_data(60)
    close_change = data["close"].diff()
    inverse_change = pd.Series(
        1.0,
        index=data.index,
    ).mask(
        close_change > 0,
        1 / close_change,
    )
    minimum_inverse_12d = inverse_change.rolling(
        12,
        min_periods=12,
    ).min()
    normalized = (
        (inverse_change - minimum_inverse_12d)
        / (data["high"] - data["low"]).replace(0, np.nan)
        * 100
    )
    expected = _sma(
        normalized,
        13,
        2,
    ).rename("Alpha164")

    result = _factor_result(164, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha146_scales_return_deviation_by_smoothed_variance():
    data = _sample_price_data(120)
    daily_return = data["close"] / data["close"].shift(1) - 1
    smoothed_return = _sma(
        daily_return,
        61,
        2,
    )
    return_deviation = daily_return - smoothed_return
    mean_deviation_20d = return_deviation.rolling(
        20,
        min_periods=20,
    ).mean()
    smoothed_variance = _sma(
        (
            daily_return
            - (daily_return - smoothed_return)
        ) ** 2,
        60,
        2,
    )
    expected = (
        mean_deviation_20d
        * return_deviation
        / smoothed_variance.replace(0, np.nan)
    ).rename("Alpha146")

    result = _factor_result(146, data)

    pd.testing.assert_series_equal(result, expected)


@pytest.mark.parametrize(
    ("factor_number", "periods"),
    [
        (165, 48),
        (183, 24),
    ],
)
def test_alpha165_and_alpha183_use_cumulative_rescaled_range(
    factor_number,
    periods,
):
    data = _sample_price_data(120)
    average_close = data["close"].rolling(
        periods,
        min_periods=periods,
    ).mean()
    cumulative_deviation = (
        data["close"] - average_close
    ).cumsum()
    cumulative_range = (
        cumulative_deviation.cummax()
        - cumulative_deviation.cummin()
    )
    close_std = data["close"].rolling(
        periods,
        min_periods=periods,
    ).std(ddof=1)
    expected = (
        cumulative_range
        / close_std.replace(0, np.nan)
    ).rename(f"Alpha{factor_number}")

    result = _factor_result(factor_number, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha166_matches_the_twenty_day_standardized_return_statistic():
    data = _sample_price_data(120)
    daily_return = data["close"] / data["close"].shift(1) - 1
    average_return_20d = daily_return.rolling(
        20,
        min_periods=20,
    ).mean()
    return_deviation = daily_return - average_return_20d
    deviation_sum = return_deviation.rolling(
        20,
        min_periods=20,
    ).sum()
    squared_deviation_sum = (
        return_deviation ** 2
    ).rolling(
        20,
        min_periods=20,
    ).sum()
    numerator = (
        -20
        * (20 - 1) ** 1.5
        * deviation_sum
    )
    denominator = (
        (20 - 1)
        * (20 - 2)
        * squared_deviation_sum ** 1.5
    ).replace(0, np.nan)
    expected = (
        numerator / denominator
    ).rename("Alpha166")

    result = _factor_result(166, data)

    pd.testing.assert_series_equal(result, expected)


def test_alpha172_and_alpha186_use_directional_movement_index():
    data = _sample_price_data(80)
    previous_close = data["close"].shift(1)
    true_range = np.maximum(
        np.maximum(
            data["high"] - data["low"],
            (data["high"] - previous_close).abs(),
        ),
        (data["low"] - previous_close).abs(),
    )
    high_direction = data["high"].diff()
    low_direction = data["low"].shift(1) - data["low"]
    positive_low_direction = low_direction.where(
        (low_direction > 0)
        & (low_direction > high_direction),
        0.0,
    ).where(previous_close.notna())
    positive_high_direction = high_direction.where(
        (high_direction > 0)
        & (high_direction > low_direction),
        0.0,
    ).where(previous_close.notna())
    true_range_sum = true_range.rolling(
        14,
        min_periods=14,
    ).sum().replace(0, np.nan)
    low_index = (
        positive_low_direction.rolling(
            14,
            min_periods=14,
        ).sum()
        * 100
        / true_range_sum
    )
    high_index = (
        positive_high_direction.rolling(
            14,
            min_periods=14,
        ).sum()
        * 100
        / true_range_sum
    )
    directional_index = (
        (low_index - high_index).abs()
        / (low_index + high_index).replace(0, np.nan)
        * 100
    )
    average_directional_index = directional_index.rolling(
        6,
        min_periods=6,
    ).mean()
    expected_alpha172 = average_directional_index.rename(
        "Alpha172"
    )
    expected_alpha186 = (
        (
            average_directional_index
            + average_directional_index.shift(6)
        )
        / 2
    ).rename("Alpha186")

    pd.testing.assert_series_equal(
        _factor_result(172, data),
        expected_alpha172,
    )
    pd.testing.assert_series_equal(
        _factor_result(186, data),
        expected_alpha186,
    )


@pytest.mark.parametrize(
    "factor_number",
    TARGET_FACTOR_NUMBERS,
)
def test_requested_expansion_factor_is_registered(factor_number):
    factor_func = getattr(
        factor,
        f"alpha{factor_number}",
        None,
    )

    assert callable(factor_func)
    assert FACTORS[f"Alpha{factor_number}"] is factor_func
