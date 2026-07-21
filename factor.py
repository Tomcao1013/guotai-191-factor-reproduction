import numpy as np
import pandas as pd

from factor_operators import *


def _require_panel_columns(data: pd.DataFrame) -> None:
    required_columns = {"trade_date", "trade_symbol"}
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        raise ValueError(
            "Cross-sectional factors require columns: "
            + ", ".join(sorted(missing_columns))
        )


def _by_symbol(
    data: pd.DataFrame,
    series: pd.Series,
    transform,
) -> pd.Series:
    _require_panel_columns(data)
    return series.groupby(
        data["trade_symbol"],
        sort=False,
    ).transform(transform)


def _by_symbol_pair(
    data: pd.DataFrame,
    series_a: pd.Series,
    series_b: pd.Series,
    transform,
) -> pd.Series:
    _require_panel_columns(data)
    result = pd.Series(np.nan, index=data.index, dtype=float)

    for _, group_index in data.groupby(
        "trade_symbol",
        sort=False,
    ).groups.items():
        result.loc[group_index] = transform(
            series_a.loc[group_index],
            series_b.loc[group_index],
        )

    return result


def _cross_sectional_rank(
    data: pd.DataFrame,
    series: pd.Series,
) -> pd.Series:
    _require_panel_columns(data)
    return RANK(series, data["trade_date"])


def alpha2(data: pd.DataFrame) -> pd.Series:
    """
    Alpha2 = -DELTA(
        ((CLOSE - LOW) - (HIGH - CLOSE)) / (HIGH - LOW),
        1,
    )
    """
    price_range = (data["high"] - data["low"]).replace(0, np.nan)
    close_location = (
        (data["close"] - data["low"]) - (data["high"] - data["close"])
    ) / price_range

    return (-DELTA(close_location, periods=1)).rename("Alpha2")


def alpha3(data: pd.DataFrame) -> pd.Series:
    """
    Alpha3 = SUM(
        CLOSE == DELAY(CLOSE, 1)
        ? 0
        : CLOSE - (
            CLOSE > DELAY(CLOSE, 1)
            ? MIN(LOW, DELAY(CLOSE, 1))
            : MAX(HIGH, DELAY(CLOSE, 1))
        ),
        6,
    )
    """
    previous_close = DELAY(data["close"], 1)
    has_previous = previous_close.notna()

    is_up = data["close"] > previous_close
    is_down = data["close"] < previous_close

    daily_value = pd.Series(
        0.0,
        index=data.index,
    )

    daily_value = daily_value.mask(
        is_up,
        data["close"] - np.minimum(data["low"], previous_close),
    )

    daily_value = daily_value.mask(
        is_down,
        data["close"] - np.maximum(data["high"], previous_close),
    )

    daily_value = daily_value.where(has_previous)

    return SUM(daily_value, periods=6).rename("Alpha3")


def alpha5(data: pd.DataFrame) -> pd.Series:
    """
    Alpha5 = -TSMAX(
        CORR(TSRANK(VOLUME, 5), TSRANK(HIGH, 5), 5),
        3,
    )
    """
    price_volume_corr = CORR(TSRANK(data['volume'], 5), TSRANK(data['high'], 5), 5)
    return (-TSMAX(price_volume_corr, 3)).rename('Alpha5')


def alpha6(data: pd.DataFrame) -> pd.Series:
    """
    Alpha6 = -RANK(
        SIGN(
            DELTA(
                OPEN * 0.85 + HIGH * 0.15,
                4,
            )
        )
    )
    """
    blended_price = (
        data["open"] * 0.85
        + data["high"] * 0.15
    )
    price_change_4d = _by_symbol(
        data,
        blended_price,
        lambda series: DELTA(series, 4),
    )

    return (
        -_cross_sectional_rank(
            data,
            SIGN(price_change_4d),
        )
    ).rename("Alpha6")


def alpha9(data: pd.DataFrame) -> pd.Series:
    """
    Alpha9 = SMA(
        (
            (HIGH + LOW) / 2
            - (DELAY(HIGH, 1) + DELAY(LOW, 1)) / 2
        )
        * (HIGH - LOW)
        / VOLUME,
        7,
        2,
    )
    """
    change = (data['high'] + data['low']) / 2
    delay_change = -DELAY(data['high'] + data['low']) / 2
    return SMA((change + delay_change) * (data['high'] - data['low']) / data['volume'], 7, 2).rename('Alpha9')


def alpha11(data: pd.DataFrame) -> pd.Series:
    """
    Alpha11 = SUM(
        ((CLOSE - LOW) - (HIGH - CLOSE))
        / (HIGH - LOW)
        * VOLUME,
        6,
    )
    """
    tail = data['close'] - data['low'] #下影线
    head = data['high'] - data['close'] #上影线
    range = (data['high'] - data['low']).replace(0, np.nan) #极差
    weighted_clv = ((tail - head) / range) * data['volume']
    r"""
    Close Location Value（CLV，收盘位置值）
    它的核心意义是衡量：当天交易结束时，多空双方谁更占优势。
    收盘接近最高价：说明临近收盘仍有人愿意追高买入，买方相对强，指标接近 1
    收盘接近最低价：说明临近收盘卖压较强，指标接近 -1
    收盘处于中间：多空相对均衡，指标接近 0
    在因子中，它通常被理解为日内收盘强度：
    \[
    \text{收盘强度}
    =
    \frac{\text{向上走过的距离}-\text{距离最高价的回落}}{\text{全天振幅}}
    \]例如两只股票当天都涨了 2%：
    A 尾盘收在最高价附近，可能表示上涨力量持续到了收盘
    B 盘中一度大涨但收在最低价附近，可能表示冲高回落、卖压较大
    因此它可以用来：
    判断日内强弱或尾盘买卖压力。
    作为短期动量信号：高值可能意味着强势延续。
    作为反转信号：极端高值或低值在某些市场也可能意味着短期过热或过度抛售。
    与成交量结合，区分“有量的强收盘”和“无量的价格波动”。
    """
    return SUM(weighted_clv, 6).rename('Alpha11')


def alpha13(data: pd.DataFrame) -> pd.Series:
    """
    Alpha13 = (
        (HIGH * LOW) ^ 0.5
        - VWAP
    )
    """
    return(
        (data['high'] * data['low']) ** 0.5
        - data['vwap']
    ).rename('Alpha13')


def alpha14(data: pd.DataFrame) -> pd.Series:
    """
    Alpha14 = CLOSE - DELAY(CLOSE, 5)
    """
    return(data['close'] - DELAY(data['close'], 5)).rename('Alpha14')


def alpha15(data: pd.DataFrame) -> pd.Series:
    """
    Alpha15 = OPEN / DELAY(CLOSE, 1) - 1
    """
    return(data['open'] / DELAY(data['close'], 1) - 1).rename('Alpha15')


def alpha18(data: pd.DataFrame) -> pd.Series:
    """
    Alpha18 = CLOSE / DELAY(CLOSE, 5)
    """
    previous_5_close = DELAY(data['close'], 5)
    return (data['close'] / previous_5_close).rename('Alpha18')


def alpha19(data: pd.DataFrame) -> pd.Series:
    """
    Alpha19 = (
        CLOSE < DELAY(CLOSE, 5)
        ? (CLOSE - DELAY(CLOSE, 5)) / DELAY(CLOSE, 5)
        : (
            CLOSE == DELAY(CLOSE, 5)
            ? 0
            : (CLOSE - DELAY(CLOSE, 5)) / CLOSE
        )
    )
    """
    # TODO: Implement the conditional branches with the formula's
    # different denominators for the down and non-down cases.
    pass


def alpha20(data: pd.DataFrame) -> pd.Series:
    """
    Alpha20 = (
        (CLOSE - DELAY(CLOSE, 6))
        / DELAY(CLOSE, 6)
        * 100
    )
    """
    change_in_6 = data['close'] - DELAY(data['close'], 6)
    change_in_6_pct = change_in_6 / DELAY(data['close'], 6) * 100
    return(change_in_6_pct).rename('Alpha20')


def alpha21(data: pd.DataFrame) -> pd.Series:
    """
    Alpha21 = REGBETA(
        MEAN(CLOSE, 6),
        SEQUENCE(6),
    )
    """
    avg_close_6d = MEAN(data['close'], 6)
    return(REGBETA(
        avg_close_6d,
        SEQUENCE(6)
    )).rename('Alpha21')


def alpha24(data: pd.DataFrame) -> pd.Series:
    """
    Alpha24 = SMA(
        CLOSE - DELAY(CLOSE, 5),
        5,
        1,
    )
    """
    previous_5_close = DELAY(data['close'], 5)
    return(
        SMA(
            data['close'] - previous_5_close,
            5,
            1,
        )
    ).rename('Alpha24')


def alpha25(data: pd.DataFrame) -> pd.Series:
    """
    Alpha25 = (
        -1
        * RANK(
            DELTA(CLOSE, 7)
            * (
                1
                - RANK(
                    DECAYLINEAR(
                        VOLUME / MEAN(VOLUME, 20),
                        9,
                    )
                )
            )
        )
        * (1 + RANK(SUM(RET, 250)))
    )
    """
    average_volume_20d = _by_symbol(
        data,
        data["volume"],
        lambda series: MEAN(series, 20),
    )
    relative_volume = data["volume"] / average_volume_20d
    decayed_relative_volume = _by_symbol(
        data,
        relative_volume,
        lambda series: DECAYLINEAR(series, 9),
    )
    ranked_decayed_volume = _cross_sectional_rank(
        data,
        decayed_relative_volume,
    )

    close_change_7d = _by_symbol(
        data,
        data["close"],
        lambda series: DELTA(series, 7),
    )
    ranked_price_volume_signal = _cross_sectional_rank(
        data,
        close_change_7d * (1 - ranked_decayed_volume),
    )

    daily_return = _by_symbol(
        data,
        data["close"],
        RET,
    )
    return_sum_250d = _by_symbol(
        data,
        daily_return,
        lambda series: SUM(series, 250),
    )
    ranked_long_return = _cross_sectional_rank(
        data,
        return_sum_250d,
    )

    return (
        -ranked_price_volume_signal
        * (1 + ranked_long_return)
    ).rename("Alpha25")


def alpha26(data: pd.DataFrame) -> pd.Series:
    """
    Alpha26 = (
        SUM(CLOSE, 7) / 7
        - CLOSE
        + CORR(VWAP, DELAY(CLOSE, 5), 230)
    )
    """
    close_mean_7d = SUM(data['close'], 7) / 7
    vwap_close_correlation = CORR(
        data['vwap'],
        DELAY(data['close'], 5),
        230,
    )

    return(
        close_mean_7d
        - data['close']
        + vwap_close_correlation
    ).rename('Alpha26')


def alpha27(data: pd.DataFrame) -> pd.Series:
    """
    Alpha27 = WMA(
        (
            (CLOSE - DELAY(CLOSE, 3))
            / DELAY(CLOSE, 3)
            * 100
        )
        + (
            (CLOSE - DELAY(CLOSE, 6))
            / DELAY(CLOSE, 6)
            * 100
        ),
        12,
    )
    """
    return_3d = (
        (data["close"] - DELAY(data["close"], 3))
        / DELAY(data["close"], 3)
        * 100
    )
    return_6d = (
        (data["close"] - DELAY(data["close"], 6))
        / DELAY(data["close"], 6)
        * 100
    )

    return WMA(
        return_3d + return_6d,
        12,
    ).rename("Alpha27")


def alpha29(data: pd.DataFrame) -> pd.Series:
    """
    Alpha29 = (
        (CLOSE - DELAY(CLOSE, 6))
        / DELAY(CLOSE, 6)
        * VOLUME
    )
    """
    change_in_6 = data['close'] - DELAY(data['close'], 6)
    change_in_6_volume = change_in_6 / DELAY(data['close'], 6) * data['volume']
    return(change_in_6_volume).rename('Alpha29')

def alpha31(data: pd.DataFrame) -> pd.Series:
    """
    Alpha31 = (
        (CLOSE - MEAN(CLOSE, 12))
        / MEAN(CLOSE, 12)
        * 100
    )
    """
    mean_close = MEAN(data['close'], 12)
    deviation = (data["close"] - mean_close) / mean_close
    return(deviation * 100).rename('Alpha31')


def alpha34(data: pd.DataFrame) -> pd.Series:
    """
    Alpha34 = MEAN(CLOSE, 12) / CLOSE
    """
    return(
        MEAN(data['close'], 12) / data['close']
    ).rename('Alpha34')


def alpha38(data: pd.DataFrame) -> pd.Series:
    """
    Alpha38 = (
        SUM(HIGH, 20) / 20 < HIGH
        ? -DELTA(HIGH, 2)
        : 0
    )
    """
    # TODO: Implement the 20-period HIGH mean threshold and the
    # conditional negative two-period HIGH delta.
    pass


def alpha40(data: pd.DataFrame) -> pd.Series:
    """
    Alpha40 =
        SUM(CLOSE > DELAY(CLOSE, 1) ? VOLUME : 0, 26)
        / SUM(CLOSE <= DELAY(CLOSE, 1) ? VOLUME : 0, 26)
        * 100
    """
    previous_close = DELAY(data["close"], 1)
    has_previous = previous_close.notna()

    is_up = (data["close"] > previous_close) & has_previous
    is_down_or_flat = (data["close"] <= previous_close) & has_previous

    up_volume = data["volume"].where(is_up, 0)
    down_or_flat_volume = data["volume"].where(is_down_or_flat, 0)

    up_volume_sum = SUM(up_volume, periods=26)
    down_or_flat_volume_sum = SUM(
        down_or_flat_volume,
        periods=26,
    ).replace(0, np.nan)

    result = up_volume_sum / down_or_flat_volume_sum * 100

    return result.rename("Alpha40")

def alpha43(data: pd.DataFrame) -> pd.Series:
    """
    Alpha43 = SUM(
        CLOSE > DELAY(CLOSE, 1)
        ? VOLUME
        : (
            CLOSE < DELAY(CLOSE, 1)
            ? -VOLUME
            : 0
        ),
        6,
    )
    """
    previous_close = DELAY(data['close'], 1)
    is_higher_close = data['close'] > previous_close
    has_previous = previous_close.notna()

    signed_volume = pd.Series(0.0, index=data.index)
    signed_volume = signed_volume.where(has_previous)
    signed_volume = signed_volume.mask(is_higher_close, data["volume"])

    is_lower_close = data['close'] < previous_close
    signed_volume = signed_volume.mask(is_lower_close, -data["volume"])

    result = SUM(signed_volume, periods=6)

    return result.rename("Alpha43")


def alpha44(data: pd.DataFrame) -> pd.Series:
    """
    Alpha44 = (
        TSRANK(
            DECAYLINEAR(
                CORR(LOW, MEAN(VOLUME, 10), 7),
                6,
            ),
            4,
        )
        + TSRANK(
            DECAYLINEAR(DELTA(VWAP, 3), 10),
            15,
        )
    )
    """
    low_volume_correlation = CORR(
        data["low"],
        MEAN(data["volume"], 10),
        7,
    )
    decayed_correlation = DECAYLINEAR(
        low_volume_correlation,
        6,
    )
    decayed_vwap_change = DECAYLINEAR(
        DELTA(data["vwap"], 3),
        10,
    )

    return (
        TSRANK(decayed_correlation, 4)
        + TSRANK(decayed_vwap_change, 15)
    ).rename("Alpha44")


def alpha46(data: pd.DataFrame) -> pd.Series:
    """
    Alpha46 = (
        MEAN(CLOSE, 3)
        + MEAN(CLOSE, 6)
        + MEAN(CLOSE, 12)
        + MEAN(CLOSE, 24)
    ) / (4 * CLOSE)
    """
    means = MEAN(data['close'], 3) + MEAN(data['close'], 6) + MEAN(data['close'], 12)+ MEAN(data['close'], 24)
    return(means / (4 * data['close'])).rename('Alpha46')


def alpha47(data: pd.DataFrame) -> pd.Series:
    """
    Alpha47 = SMA(
        (TSMAX(HIGH, 6) - CLOSE)
        / (TSMAX(HIGH, 6) - TSMIN(LOW, 6))
        * 100,
        9,
        1,
    )
    """
    high_6d_max = TSMAX(data['high'], 6)
    high_6d_minus_close = high_6d_max - data['close']
    low_6d_min = TSMIN(data['low'], 6)
    max_minus_min_6d = high_6d_max - low_6d_min
    return(
        SMA(
            high_6d_minus_close / max_minus_min_6d * 100,
            9,
            1,
        )
    ).rename('Alpha47')


def alpha48(data: pd.DataFrame) -> pd.Series:
    """
    Alpha48 = (
        -RANK(
            SIGN(CLOSE - DELAY(CLOSE, 1))
            + SIGN(DELAY(CLOSE, 1) - DELAY(CLOSE, 2))
            + SIGN(DELAY(CLOSE, 2) - DELAY(CLOSE, 3))
        )
        * SUM(VOLUME, 5)
        / SUM(VOLUME, 20)
    )
    """
    previous_close_1d = _by_symbol(
        data,
        data["close"],
        lambda series: DELAY(series, 1),
    )
    previous_close_2d = _by_symbol(
        data,
        data["close"],
        lambda series: DELAY(series, 2),
    )
    previous_close_3d = _by_symbol(
        data,
        data["close"],
        lambda series: DELAY(series, 3),
    )

    direction_signal = (
        SIGN(data["close"] - previous_close_1d)
        + SIGN(previous_close_1d - previous_close_2d)
        + SIGN(previous_close_2d - previous_close_3d)
    )
    ranked_direction = _cross_sectional_rank(
        data,
        direction_signal,
    )
    volume_sum_5d = _by_symbol(
        data,
        data["volume"],
        lambda series: SUM(series, 5),
    )
    volume_sum_20d = _by_symbol(
        data,
        data["volume"],
        lambda series: SUM(series, 20),
    ).replace(0, np.nan)

    return (
        -ranked_direction
        * volume_sum_5d
        / volume_sum_20d
    ).rename("Alpha48")



def alpha52(data: pd.DataFrame) -> pd.Series:
    """
    Alpha52 = (
        SUM(
            MAX(
                0,
                HIGH - DELAY((HIGH + LOW + CLOSE) / 3, 1),
            ),
            26,
        )
        / SUM(
            MAX(
                0,
                DELAY((HIGH + LOW + CLOSE) / 3, 1) - LOW,
            ),
            26,
        )
        * 100
    )
    """
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    previous_typical_price = DELAY(typical_price, 1)
    total_up_pressure_26d = SUM(MAX(0, data['high'] - previous_typical_price), 26)
    total_down_pressure_26d = SUM(
        MAX(0, previous_typical_price - data['low']),
        26,
    )

    return(total_up_pressure_26d / total_down_pressure_26d * 100).rename('Alpha52')

def alpha53(data: pd.DataFrame) -> pd.Series:
    """
    Alpha53 = COUNT(CLOSE > DELAY(CLOSE, 1), 12) / 12 * 100
    """
    previous_close = DELAY(data["close"], 1)
    condition = (data["close"] > previous_close).where(previous_close.notna())
    return (COUNT(condition, periods=12) / 12 * 100).rename("Alpha53")


def alpha57(data: pd.DataFrame) -> pd.Series:
    """
    Alpha57 = SMA(
        (CLOSE - TSMIN(LOW, 9))
        / (TSMAX(HIGH, 9) - TSMIN(LOW, 9))
        * 100,
        3,
        1,
    )
    """
    min_low_9d = TSMIN(data['low'], 9)
    close_minus_min_low = data['close'] - min_low_9d

    max_high_9d = TSMAX(data['high'], 9)
    max_minus_min = max_high_9d - min_low_9d

    return(
        SMA(
            close_minus_min_low / max_minus_min * 100,
            3,
            1
        )
    ).rename('Alpha57')


def alpha58(data: pd.DataFrame) -> pd.Series:
    """
    Alpha58 = COUNT(CLOSE > DELAY(CLOSE, 1), 20) / 20 * 100
    """
    previous_close = DELAY(data["close"], 1)
    condition = (data["close"] > previous_close).where(previous_close.notna())
    return (COUNT(condition, periods=20) / 20 * 100).rename("Alpha58")


def alpha59(data: pd.DataFrame) -> pd.Series:
    """
    Alpha59 = SUM(
        CLOSE == DELAY(CLOSE, 1)
        ? 0
        : CLOSE - (
            CLOSE > DELAY(CLOSE, 1)
            ? MIN(LOW, DELAY(CLOSE, 1))
            : MAX(HIGH, DELAY(CLOSE, 1))
        ),
        20,
    )
    """
    previous_close = DELAY(data["close"], 1)
    has_previous = previous_close.notna()

    is_up = data["close"] > previous_close
    is_down = data["close"] < previous_close

    daily_value = pd.Series(
        0.0,
        index=data.index,
    )

    daily_value = daily_value.mask(
        is_up,
        data["close"] - np.minimum(data["low"], previous_close),
    )

    daily_value = daily_value.mask(
        is_down,
        data["close"] - np.maximum(data["high"], previous_close),
    )

    daily_value = daily_value.where(has_previous)

    return SUM(daily_value, periods=20).rename("Alpha59")


def alpha60(data: pd.DataFrame) -> pd.Series:
    """
    Alpha60 = SUM(
        ((CLOSE - LOW) - (HIGH - CLOSE))
        / (HIGH - LOW)
        * VOLUME,
        20,
    )
    """
    tail = data['close'] - data['low'] #下影线
    head = data['high'] - data['close'] #上影线
    range = (data['high'] - data['low']).replace(0, np.nan) #极差
    weighted_clv = ((tail - head) / range) * data['volume']
    return SUM(weighted_clv, 20).rename('Alpha60')


def alpha63(data: pd.DataFrame) -> pd.Series:
    """
    Alpha63 = (
        SMA(MAX(CLOSE - DELAY(CLOSE, 1), 0), 6, 1)
        / SMA(ABS(CLOSE - DELAY(CLOSE, 1)), 6, 1)
        * 100
    )
    """
    prev_close = DELAY(data['close'], 1)
    close_change = data['close'] - prev_close

    positive_close_change = MAX(data['close'] - prev_close, 0)
    abs_close_change = ABS(close_change)

    return(
        SMA(positive_close_change, 6, 1)
        / SMA(abs_close_change, 6, 1)
        * 100
    ).rename('Alpha63')



def alpha65(data: pd.DataFrame) -> pd.Series:
    """
    Alpha65 = MEAN(CLOSE, 6) / CLOSE
    """
    return(MEAN(data['close'], 6) / data['close']).rename('Alpha65')


def alpha66(data: pd.DataFrame) -> pd.Series:
    """
    Alpha66 = (
        (CLOSE - MEAN(CLOSE, 6))
        / MEAN(CLOSE, 6)
        * 100
    )
    """
    avg_close_6 = MEAN(data['close'], 6)
    return(
        (data['close'] - avg_close_6)
        / avg_close_6
        * 100
    ).rename('Alpha66')


def alpha67(data: pd.DataFrame) -> pd.Series:
    """
    Alpha67 = (
        SMA(MAX(CLOSE - DELAY(CLOSE, 1), 0), 24, 1)
        / SMA(ABS(CLOSE - DELAY(CLOSE, 1)), 24, 1)
        * 100
    )
    """
    prev_close = DELAY(data['close'], 1)
    close_change = data['close'] - prev_close

    positive_close_change = MAX(data['close'] - prev_close, 0)
    abs_close_change = ABS(close_change)

    return(
        SMA(positive_close_change, 24, 1)
        / SMA(abs_close_change, 24, 1)
        * 100
    ).rename('Alpha67')


def alpha68(data: pd.DataFrame) -> pd.Series:
    """
    Alpha68 = SMA(
        (
            (HIGH + LOW) / 2
            - (DELAY(HIGH, 1) + DELAY(LOW, 1)) / 2
        )
        * (HIGH - LOW)
        / VOLUME,
        15,
        2,
    )
    """
    change = (data['high'] + data['low']) / 2
    delay_change = -DELAY(data['high'] + data['low']) / 2
    return SMA((change + delay_change) * (data['high'] - data['low']) / data['volume'], 15, 2).rename('Alpha68')


def alpha69(data: pd.DataFrame) -> pd.Series:
    """
    Alpha69 = directional movement balance calculated from 20-period DTM and DBM sums.
    """
    #DTM
    """
        DTM = (
        OPEN <= DELAY(OPEN, 1)
        ? 0
        : MAX(HIGH - OPEN, OPEN - DELAY(OPEN, 1))
    )
    """
    previous_open = DELAY(data["open"], 1)
    has_previous = previous_open.notna()

    is_higher_open = data["open"] > previous_open

    high_move = data["high"] - data["open"]
    open_gap = data["open"] - previous_open

    max_move_up = np.maximum(high_move, open_gap)

    dtm = pd.Series(max_move_up, index=data.index)
    dtm = dtm.where(is_higher_open, 0)
    dtm = dtm.where(has_previous)

    #DBM
    """
    DBM = (
        OPEN >= DELAY(OPEN, 1)
        ? 0
        : MAX(OPEN - LOW, OPEN - DELAY(OPEN, 1))
    )
    """
    previous_open = DELAY(data["open"], 1)
    has_previous = previous_open.notna()

    is_lower_open = data["open"] < previous_open

    low_move = data["open"] - data["low"]
    open_gap = data["open"] - previous_open

    max_move_down = np.maximum(low_move, open_gap)

    dbm = pd.Series(max_move_down, index=data.index)
    dbm = dbm.where(is_lower_open, 0)
    dbm = dbm.where(has_previous)

    """
    Alpha69 = (
        SUM(DTM, 20) > SUM(DBM, 20)
        ? (SUM(DTM, 20) - SUM(DBM, 20)) / SUM(DTM, 20)
        : (
            SUM(DTM, 20) == SUM(DBM, 20)
            ? 0
            : (SUM(DTM, 20) - SUM(DBM, 20)) / SUM(DBM, 20)
        )
    )
    """
    dtm_sum = SUM(dtm, periods=20)
    dbm_sum = SUM(dbm, periods=20)

    difference = dtm_sum - dbm_sum

    is_dtm_greater = dtm_sum > dbm_sum
    is_equal = dtm_sum == dbm_sum
    is_dbm_greater = dtm_sum < dbm_sum

    result = pd.Series(
        np.nan,
        index=data.index,
        dtype=float,
    )

    result.loc[is_dtm_greater] = (
        difference.loc[is_dtm_greater]
        / dtm_sum.loc[is_dtm_greater]
    )

    result.loc[is_equal] = 0.0

    result.loc[is_dbm_greater] = (
        difference.loc[is_dbm_greater]
        / dbm_sum.loc[is_dbm_greater]
    )

    return result.rename("Alpha69")


def alpha70(data: pd.DataFrame) -> pd.Series:
    """
    Alpha70 = STD(AMOUNT, 6)
    """
    return(STD(data['amount'], 6)).rename('Alpha70')


def alpha71(data: pd.DataFrame) -> pd.Series:
    """
    Alpha71 = (
        (CLOSE - MEAN(CLOSE, 24))
        / MEAN(CLOSE, 24)
        * 100
    )
    """
    avg_close_24 = MEAN(data['close'], 24)
    return(
        (data['close'] - avg_close_24)
        / avg_close_24
        * 100
    ).rename('Alpha71')


def alpha72(data: pd.DataFrame) -> pd.Series:
    """
    Alpha72 = SMA(
        (TSMAX(HIGH, 6) - CLOSE)
        / (TSMAX(HIGH, 6) - TSMIN(LOW, 6))
        * 100,
        15,
        1,
    )
    """
    max_high_6d = TSMAX(data['high'], 6)
    max_high_minus_close = max_high_6d - data['close']

    min_low_6d = TSMIN(data['low'], 6)
    max_minus_min = max_high_6d - min_low_6d

    return(
        SMA(
            max_high_minus_close / max_minus_min * 100,
            15,
            1
        )
    ).rename('Alpha72')




def alpha75(data: pd.DataFrame) -> pd.Series:
    """
    Alpha75 = (
        COUNT(
            CLOSE > OPEN
            & BANCHMARKINDEXCLOSE < BANCHMARKINDEXOPEN,
            50,
        )
        / COUNT(
            BANCHMARKINDEXCLOSE < BANCHMARKINDEXOPEN,
            50,
        )
    )
    """
    benchmark_down = (
        data["benchmark_close"]
        < data["benchmark_open"]
    )
    stock_up_benchmark_down = (
        (data["close"] > data["open"])
        & benchmark_down
    )
    benchmark_down_count = COUNT(
        benchmark_down,
        50,
    ).replace(0, np.nan)

    return (
        COUNT(stock_up_benchmark_down, 50)
        / benchmark_down_count
    ).rename("Alpha75")


def alpha76(data: pd.DataFrame) -> pd.Series:
    """
    Alpha76 = (
        STD(
            ABS(CLOSE / DELAY(CLOSE, 1) - 1) / VOLUME,
            20,
        )
        / MEAN(
            ABS(CLOSE / DELAY(CLOSE, 1) - 1) / VOLUME,
            20,
        )
    )
    """
    prev_close_1d = DELAY(data['close'], 1)
    return(
        STD(ABS((data['close'] / prev_close_1d) - 1) / data['volume'], 20)
        / MEAN(ABS((data['close'] / prev_close_1d) - 1) / data['volume'], 20)
    ).rename('Alpha76')


def alpha79(data: pd.DataFrame) -> pd.Series:
    """
    Alpha79 = (
        SMA(MAX(CLOSE - DELAY(CLOSE, 1), 0), 12, 1)
        / SMA(ABS(CLOSE - DELAY(CLOSE, 1)), 12, 1)
        * 100
    )
    """
    prev_close = DELAY(data['close'], 1)
    close_change = data['close'] - prev_close

    positive_close_change = MAX(data['close'] - prev_close, 0)
    abs_close_change = ABS(close_change)

    return(
        SMA(positive_close_change, 12, 1)
        / SMA(abs_close_change, 12, 1)
        * 100
    ).rename('Alpha79')


def alpha80(data: pd.DataFrame) -> pd.Series:
    """
    Alpha80 = (
        (VOLUME - DELAY(VOLUME, 5))
        / DELAY(VOLUME, 5)
        * 100
    )
    """
    return((data['volume'] - DELAY(data['volume'], 5))
           / DELAY(data['volume'], 5)
           * 100).rename('Alpha80')


def alpha81(data: pd.DataFrame) -> pd.Series:
    """
    Alpha81 = SMA(VOLUME, 21, 2)
    """
    return(SMA(data['volume'], 21, 2)).rename('Alpha81')


def alpha82(data: pd.DataFrame) -> pd.Series:
    """
    Alpha82 = SMA(
        (TSMAX(HIGH, 6) - CLOSE)
        / (TSMAX(HIGH, 6) - TSMIN(LOW, 6))
        * 100,
        20,
        1,
    )
    """
    max_high_6d = TSMAX(data['high'], 6)
    max_close_change = max_high_6d - data['close']

    min_low_6d = TSMIN(data['low'], 6)
    max_change = max_high_6d - min_low_6d

    return(
        SMA(max_close_change / max_change * 100, 20, 1)
    ).rename('Alpha82')


def alpha83(data: pd.DataFrame) -> pd.Series:
    """
    Alpha83 = -RANK(
        COVIANCE(
            RANK(HIGH),
            RANK(VOLUME),
            5,
        )
    )
    """
    ranked_high = _cross_sectional_rank(
        data,
        data["high"],
    )
    ranked_volume = _cross_sectional_rank(
        data,
        data["volume"],
    )
    rolling_covariance = _by_symbol_pair(
        data,
        ranked_high,
        ranked_volume,
        lambda high, volume: COVIANCE(
            high,
            volume,
            5,
        ),
    )

    return (
        -_cross_sectional_rank(
            data,
            rolling_covariance,
        )
    ).rename("Alpha83")


def alpha84(data: pd.DataFrame) -> pd.Series:
    """
    Alpha84 = SUM(
        CLOSE > DELAY(CLOSE, 1)
        ? VOLUME
        : (
            CLOSE < DELAY(CLOSE, 1)
            ? -VOLUME
            : 0
        ),
        20,
    )
    """
    previous_close = DELAY(data["close"], 1)
    has_previous = previous_close.notna()

    signed_volume = pd.Series(0.0, index=data.index)

    signed_volume = signed_volume.mask(
        data["close"] > previous_close,
        data["volume"],
    )
    signed_volume = signed_volume.mask(
        data["close"] < previous_close,
        -data["volume"],
    )

    signed_volume = signed_volume.where(has_previous)

    return SUM(signed_volume, periods=20).rename("Alpha84")


def alpha85(data: pd.DataFrame) -> pd.Series:
    """
    Alpha85 = (
        TSRANK(VOLUME / MEAN(VOLUME, 20), 20)
        * TSRANK(-DELTA(CLOSE, 7), 8)
    )
    """
    avg_volume_20d = MEAN(data['volume'], 20)
    prev_close_7d = -DELTA(data['close'], 7)
    return(
        TSRANK(data['volume'] / avg_volume_20d, 20)
        * TSRANK(prev_close_7d, 8)
    ).rename('Alpha85')


def alpha88(data: pd.DataFrame) -> pd.Series:
    """
    Alpha88 = (
        (CLOSE - DELAY(CLOSE, 20))
        / DELAY(CLOSE, 20)
        * 100
    )
    """
    pre_close_20 = DELAY(data["close"], 20)

    return (
        (data["close"] - pre_close_20)
        / pre_close_20
        * 100
    ).rename("Alpha88")


def alpha89(data: pd.DataFrame) -> pd.Series:
    """
    Alpha89 = 2 * (
        SMA(CLOSE, 13, 2)
        - SMA(CLOSE, 27, 2)
        - SMA(
            SMA(CLOSE, 13, 2) - SMA(CLOSE, 27, 2),
            10,
            2,
        )
    )
    """
    sma_close_13d = SMA(data['close'], 13, 2)
    sma_close_27d = SMA(data['close'], 27, 2)
    sma_change = sma_close_13d - sma_close_27d

    return(
        2 *
        (
            sma_close_13d - sma_close_27d - SMA(sma_change, 10, 2)
        )
    ).rename('Alpha89')



def alpha93(data: pd.DataFrame) -> pd.Series:
    """
    Alpha93 = SUM(
        OPEN >= DELAY(OPEN, 1)
        ? 0
        : MAX(OPEN - LOW, OPEN - DELAY(OPEN, 1)),
        20,
    )
    """
    previous_open = DELAY(data['open'], 1)
    is_flat_or_up = data['open'] >= previous_open

    max_down= np.maximum(
        data['open'] - data['low'],
        data['open'] - previous_open
    )

    term = pd.Series(
        np.where(is_flat_or_up, 0, max_down,),
        index=data.index
    )

    return(SUM(term, 20)).rename('Alpha93')


def alpha94(data: pd.DataFrame) -> pd.Series:
    """
    Alpha94 = SUM(
        CLOSE > DELAY(CLOSE, 1)
        ? VOLUME
        : (
            CLOSE < DELAY(CLOSE, 1)
            ? -VOLUME
            : 0
        ),
        30,
    )
    """
    # TODO: Implement signed volume (+VOLUME/-VOLUME/0) with a
    # 30-period rolling sum.
    pass


def alpha95(data: pd.DataFrame) -> pd.Series:
    """
    Alpha95 = STD(AMOUNT, 20)
    """
    return(STD(data['amount'], 20)).rename('Alpha95')


def alpha96(data: pd.DataFrame) -> pd.Series:
    """
    Alpha96 = SMA(
        SMA(
            (CLOSE - TSMIN(LOW, 9))
            / (TSMAX(HIGH, 9) - TSMIN(LOW, 9))
            * 100,
            3,
            1,
        ),
        3,
        1,
    )
    """
    min_low_9d = TSMIN(data['low'], 9)
    max_high_9d = TSMAX(data['high'], 9)
    max_change = max_high_9d - min_low_9d
    close_9d_pos = (
        (data['close'] - min_low_9d)
        / max_change
        * 100
    )

    return(SMA(
        SMA(close_9d_pos, 3, 1),
        3,
        1
    )).rename('Alpha96')


def alpha97(data: pd.DataFrame) -> pd.Series:
    """
    Alpha97 = STD(VOLUME, 10)
    """
    return(STD(data['volume'], 10)).rename('Alpha97')


def alpha99(data: pd.DataFrame) -> pd.Series:
    """
    Alpha99 = -RANK(
        COVIANCE(
            RANK(CLOSE),
            RANK(VOLUME),
            5,
        )
    )
    """
    ranked_close = _cross_sectional_rank(
        data,
        data["close"],
    )
    ranked_volume = _cross_sectional_rank(
        data,
        data["volume"],
    )
    rolling_covariance = _by_symbol_pair(
        data,
        ranked_close,
        ranked_volume,
        lambda close, volume: COVIANCE(
            close,
            volume,
            5,
        ),
    )

    return (
        -_cross_sectional_rank(
            data,
            rolling_covariance,
        )
    ).rename("Alpha99")


def alpha100(data: pd.DataFrame) -> pd.Series:
    """
    Alpha100 = STD(VOLUME, 20)
    """
    return(STD(data['volume'], 20)).rename('Alpha100')


def alpha102(data: pd.DataFrame) -> pd.Series:
    """
    Alpha102 = (
        SMA(MAX(VOLUME - DELAY(VOLUME, 1), 0), 6, 1)
        / SMA(ABS(VOLUME - DELAY(VOLUME, 1)), 6, 1)
        * 100
    )
    """
    prev_volume_1d = DELAY(data['volume'], 1)
    positive_volume_change = MAX(data['volume'] - prev_volume_1d, 0)
    abs_volume_change = ABS(data['volume'] - prev_volume_1d)

    return(
        SMA(positive_volume_change, 6, 1)
        / SMA(abs_volume_change, 6, 1)
        * 100
    ).rename('Alpha102')


def alpha103(data: pd.DataFrame) -> pd.Series:
    """
    Alpha103 = (
        (20 - LOWDAY(LOW, 20))
        / 20
        * 100
    )
    """
    return (
        (20 - LOWDAY(data["low"], 20))
        / 20
        * 100
    ).rename("Alpha103")


def alpha106(data: pd.DataFrame) -> pd.Series:
    """
    Alpha106 = CLOSE - DELAY(CLOSE, 20)
    """
    previous_close_20 = DELAY(data['close'], 20)
    return(
        data['close'] - previous_close_20
    ).rename('Alpha106')


def alpha109(data: pd.DataFrame) -> pd.Series:
    """
    Alpha109 = (
        SMA(HIGH - LOW, 10, 2)
        / SMA(SMA(HIGH - LOW, 10, 2), 10, 2)
    )
    """
    change = data['high'] - data['low']
    sma_change = SMA(change, 10, 2)
    return(
        sma_change / SMA(sma_change, 10, 2)
    ).rename('Alpha109')


def alpha110(data: pd.DataFrame) -> pd.Series:
    """
    Alpha110 = (
        SUM(MAX(0, HIGH - DELAY(CLOSE, 1)), 20)
        / SUM(MAX(0, DELAY(CLOSE, 1) - LOW), 20)
        * 100
    )
    """
    previous_close = DELAY(data['close'], 1)
    upside_excursion = data['high'] - previous_close
    downside_excursion = previous_close - data['low']

    positive_upside_excursion = MAX(0, upside_excursion)
    positive_downside_excursion = MAX(0, downside_excursion)

    upside_pressure_20d = SUM(
        positive_upside_excursion,
        periods=20,
    )

    downside_pressure_20d = SUM(
        positive_downside_excursion,
        periods=20,
    ).replace(0, np.nan)

    bull_bear_pressure_ratio = (
        upside_pressure_20d
        / downside_pressure_20d
        * 100
    )

    return bull_bear_pressure_ratio.rename("Alpha110")


def alpha111(data: pd.DataFrame) -> pd.Series:
    """
    Alpha111 = (
        SMA(
            VOLUME
            * ((CLOSE - LOW) - (HIGH - CLOSE))
            / (HIGH - LOW),
            11,
            2,
        )
        - SMA(
            VOLUME
            * ((CLOSE - LOW) - (HIGH - CLOSE))
            / (HIGH - LOW),
            4,
            2,
        )
    )
    """
    price_change = data['high'] - data['low']
    close_location = (
        (data['close'] - data['low'])
        - (data['high'] - data['close'])
    ) / price_change

    volume_weited_close_location = (
        data['volume'] * close_location
    )

    slow = SMA(volume_weited_close_location, 11, 2)
    fast = SMA(volume_weited_close_location, 4, 2)

    return(slow - fast).rename('Alpha111')


def alpha116(data: pd.DataFrame) -> pd.Series:
    """
    Alpha116 = REGBETA(
        CLOSE,
        SEQUENCE(20),
    )
    """
    return REGBETA(
        data["close"],
        SEQUENCE(20),
    ).rename("Alpha116")


def alpha117(data: pd.DataFrame) -> pd.Series:
    """
    Alpha117 = (
        TSRANK(VOLUME, 32)
        * (1 - TSRANK(CLOSE + HIGH - LOW, 16))
        * (1 - TSRANK(RET, 32))
    )
    """
    order_volume_32d = TSRANK(data['volume'], 32)
    return(
        order_volume_32d
        * (1 - TSRANK(data['close'] + data['high'] - data['low'], 16))
        * (1 - TSRANK(RET(data['close']), 32))
    ).rename('Alpha117')


def alpha118(data: pd.DataFrame) -> pd.Series:
    """
    Alpha118 = (
        SUM(HIGH - OPEN, 20)
        / SUM(OPEN - LOW, 20)
        * 100
    )
    """
    increase = data['high'] - data['open']
    decrease = data['open'] - data['low']

    return(
        SUM(increase, 20)
        / SUM(decrease, 20)
        * 100
    ).rename('Alpha118')


def alpha122(data: pd.DataFrame) -> pd.Series:
    """
    Alpha122 = (
        (
            SMA(
                SMA(SMA(LOG(CLOSE), 13, 2), 13, 2),
                13,
                2,
            )
            - DELAY(
                SMA(
                    SMA(SMA(LOG(CLOSE), 13, 2), 13, 2),
                    13,
                    2,
                ),
                1,
            )
        )
        / DELAY(
            SMA(
                SMA(SMA(LOG(CLOSE), 13, 2), 13, 2),
                13,
                2,
            ),
            1,
        )
    )
    """
    smoothed_log_close = SMA(
        SMA(
            SMA(LOG(data["close"]), 13, 2),
            13,
            2,
        ),
        13,
        2,
    )
    previous_smoothed_log_close = DELAY(
        smoothed_log_close,
        1,
    ).replace(0, np.nan)

    return (
        (smoothed_log_close - previous_smoothed_log_close)
        / previous_smoothed_log_close
    ).rename("Alpha122")


def alpha126(data: pd.DataFrame) -> pd.Series:
    """
    Alpha126 = (CLOSE + HIGH + LOW) / 3
    """
    return(
        (data['close'] + data['high'] + data['low'])
        / 3
    ).rename('Alpha126')


def alpha129(data: pd.DataFrame) -> pd.Series:
    """
    Alpha129 = SUM(
        CLOSE - DELAY(CLOSE, 1) < 0
        ? ABS(CLOSE - DELAY(CLOSE, 1))
        : 0,
        12,
    )
    """
    # TODO: Implement the 12-period sum of absolute negative close
    # changes.
    pass


def alpha132(data: pd.DataFrame) -> pd.Series:
    """
    Alpha132 = MEAN(AMOUNT, 20)
    """
    return(MEAN(data['amount'], 20)).rename('Alpha132')


def alpha133(data: pd.DataFrame) -> pd.Series:
    """
    Alpha133 = (
        (20 - HIGHDAY(HIGH, 20))
        / 20
        * 100
        - (20 - LOWDAY(LOW, 20))
        / 20
        * 100
    )
    """
    high_recency = (
        (20 - HIGHDAY(data["high"], 20))
        / 20
        * 100
    )
    low_recency = (
        (20 - LOWDAY(data["low"], 20))
        / 20
        * 100
    )

    return (
        high_recency - low_recency
    ).rename("Alpha133")


def alpha134(data: pd.DataFrame) -> pd.Series:
    """
    Alpha134 = (
        (CLOSE - DELAY(CLOSE, 12))
        / DELAY(CLOSE, 12)
        * VOLUME
    )
    """
    previous_close_12 = DELAY(data['close'], 12)
    return(
        (data['close'] - previous_close_12)
        / previous_close_12
        * data['volume']
    ).rename('Alpha134')


def alpha135(data: pd.DataFrame) -> pd.Series:
    """
    Alpha135 = SMA(
        DELAY(CLOSE / DELAY(CLOSE, 20), 1),
        20,
        1,
    )
    """
    prev_close_20d = DELAY(data['close'], 20)
    close_change_pct = data['close'] / prev_close_20d
    prev_close_change_pct = DELAY(close_change_pct, 1)

    return(SMA(prev_close_change_pct, 20, 1)).rename('Alpha135')


def alpha139(data: pd.DataFrame) -> pd.Series:
    """
    Alpha139 = -CORR(OPEN, VOLUME, 10)
    """
    return(
        -CORR(data['open'], data['volume'], 10)
    ).rename('Alpha139')


def alpha144(data: pd.DataFrame) -> pd.Series:
    """
    Alpha144 = (
        SUMIF(
            ABS(CLOSE / DELAY(CLOSE, 1) - 1) / AMOUNT,
            20,
            CLOSE < DELAY(CLOSE, 1),
        )
        / COUNT(CLOSE < DELAY(CLOSE, 1), 20)
    )
    """
    previous_close = DELAY(data["close"], 1)
    negative_return_day = data["close"] < previous_close
    return_per_amount = (
        ABS(data["close"] / previous_close - 1)
        / data["amount"].replace(0, np.nan)
    )
    negative_day_count = COUNT(
        negative_return_day,
        20,
    ).replace(0, np.nan)

    return (
        SUMIF(
            return_per_amount,
            20,
            negative_return_day,
        )
        / negative_day_count
    ).rename("Alpha144")


def alpha145(data: pd.DataFrame) -> pd.Series:
    """
    Alpha145 = (
        (MEAN(VOLUME, 9) - MEAN(VOLUME, 26))
        / MEAN(VOLUME, 12)
        * 100
    )
    """
    avg_volume_9 = MEAN(data['volume'], 9)
    avg_volume_12 = MEAN(data['volume'], 12)
    avg_volume_26 = MEAN(data['volume'], 26)
    return(
        (avg_volume_9 - avg_volume_26)
        / avg_volume_12
        *100
    ).rename('Alpha145')


def alpha147(data: pd.DataFrame) -> pd.Series:
    """
    Alpha147 = REGBETA(
        MEAN(CLOSE, 12),
        SEQUENCE(12),
    )
    """
    return REGBETA(
        MEAN(data["close"], 12),
        SEQUENCE(12),
    ).rename("Alpha147")


def alpha149(data: pd.DataFrame) -> pd.Series:
    """
    Alpha149 = REGBETA(
        FILTER(
            CLOSE / DELAY(CLOSE, 1) - 1,
            BANCHMARKINDEXCLOSE
            < DELAY(BANCHMARKINDEXCLOSE, 1),
        ),
        FILTER(
            BANCHMARKINDEXCLOSE
            / DELAY(BANCHMARKINDEXCLOSE, 1)
            - 1,
            BANCHMARKINDEXCLOSE
            < DELAY(BANCHMARKINDEXCLOSE, 1),
        ),
        252,
    )
    """
    stock_return = RET(data["close"])
    benchmark_return = RET(data["benchmark_close"])
    benchmark_down = (
        data["benchmark_close"]
        < DELAY(data["benchmark_close"], 1)
    )
    filtered_stock_return = FILTER(
        stock_return,
        benchmark_down,
    )
    filtered_benchmark_return = FILTER(
        benchmark_return,
        benchmark_down,
    )
    filtered_beta = REGBETA(
        filtered_stock_return,
        filtered_benchmark_return,
        252,
    )

    return filtered_beta.reindex(
        data.index,
    ).rename("Alpha149")


def alpha150(data: pd.DataFrame) -> pd.Series:
    """
    Alpha150 = (
        (CLOSE + HIGH + LOW)
        / 3
        * VOLUME
    )
    """
    return(
        (data['close'] + data['high'] + data['low'])
        / 3
        * data['volume']
    ).rename('Alpha150')



def alpha151(data: pd.DataFrame) -> pd.Series:
    """
    Alpha151 = SMA(
        CLOSE - DELAY(CLOSE, 20),
        20,
        1,
    )
    """
    previous_close_20 = DELAY(data['close'], 20)
    return(SMA(
        data['close'] - previous_close_20,
        20,
        1,
    )).rename('Alpha151')


def alpha152(data: pd.DataFrame) -> pd.Series:
    """
    Alpha152 = SMA(
        MEAN(
            DELAY(
                SMA(DELAY(CLOSE / DELAY(CLOSE, 9), 1), 9, 1),
                1,
            ),
            12,
        )
        - MEAN(
            DELAY(
                SMA(DELAY(CLOSE / DELAY(CLOSE, 9), 1), 9, 1),
                1,
            ),
            26,
        ),
        9,
        1,
    )
    """
    prev_close_9d = DELAY(data['close'], 9)
    close_change_9d = data['close'] / prev_close_9d
    sma = SMA(DELAY(close_change_9d, 1), 9, 1)
    prev_sma_1d = DELAY(sma, 1)
    avg_sma_12d = MEAN(prev_sma_1d, 12)
    avg_sma_26d = MEAN(prev_sma_1d, 26)
    return(SMA(
        avg_sma_12d - avg_sma_26d,
        9,
        1
    )).rename('Alpha152')


def alpha153(data: pd.DataFrame) -> pd.Series:
    """
    Alpha153 = (
        MEAN(CLOSE, 3)
        + MEAN(CLOSE, 6)
        + MEAN(CLOSE, 12)
        + MEAN(CLOSE, 24)
    ) / 4
    """
    avg_close_3 = MEAN(data['close'], 3)
    avg_close_6 = MEAN(data['close'], 6)
    avg_close_12 = MEAN(data['close'], 12)
    avg_close_24 = MEAN(data['close'], 24)
    return(
        (avg_close_3 + avg_close_6 + avg_close_12 + avg_close_24)
        / 4
    ).rename('Alpha153')


def alpha154(data: pd.DataFrame) -> pd.Series:
    """
    Alpha154 = (
        VWAP - TSMIN(VWAP, 16)
        < CORR(VWAP, MEAN(VOLUME, 180), 18)
    )
    """
    vwap_distance_from_min = (
        data['vwap']
        - TSMIN(data['vwap'], 16)
    )
    vwap_volume_correlation = CORR(
        data['vwap'],
        MEAN(data['volume'], 180),
        18,
    )
    has_required_history = (
        vwap_distance_from_min.notna()
        & vwap_volume_correlation.notna()
    )

    result = (
        vwap_distance_from_min
        < vwap_volume_correlation
    ).astype(float)

    return result.where(
        has_required_history,
    ).rename('Alpha154')


def alpha155(data: pd.DataFrame) -> pd.Series:
    """
    Alpha155 = (
        SMA(VOLUME, 13, 2)
        - SMA(VOLUME, 27, 2)
        - SMA(
            SMA(VOLUME, 13, 2) - SMA(VOLUME, 27, 2),
            10,
            2,
        )
    )
    """
    sma_volume_13d = SMA(data['volume'], 13, 2)
    sma_volume_27d = SMA(data['volume'], 27, 2)
    sma_change = SMA(
        sma_volume_13d - sma_volume_27d,
        10,
        2
        )

    return(sma_volume_13d - sma_volume_27d - sma_change).rename('Alpha155')

def alpha158(data: pd.DataFrame) -> pd.Series:
    """
    Alpha158 = (
        (HIGH - SMA(CLOSE, 15, 2))
        - (LOW - SMA(CLOSE, 15, 2))
    ) / CLOSE
    """
    return(
        (
            (data['high'] - SMA(data['close'], 15, 2))
        - (data['low'] - SMA(data['close'], 15, 2))
        )
        / data['close']
    ).rename('Alpha158')


def alpha161(data: pd.DataFrame) -> pd.Series:
    """
    Alpha161 = MEAN(
        MAX(
            MAX(
                HIGH - LOW,
                ABS(DELAY(CLOSE, 1) - HIGH),
            ),
            ABS(DELAY(CLOSE, 1) - LOW),
        ),
        12,
    )
    """
    change = data['high'] - data['low']
    prev_close = DELAY(data['close'], 1)
    positive_change_high = prev_close - data['high']
    positive_change_low = prev_close - data['low']

    return(
        MEAN(
            MAX(
                MAX(
                    change,
                    ABS(positive_change_high)
                ),ABS(positive_change_low)
            ),12
        )
    ).rename('Alpha161')


def alpha162(data: pd.DataFrame) -> pd.Series:
    """
    Alpha162 = (
        (
            SMA(MAX(CLOSE - DELAY(CLOSE, 1), 0), 12, 1)
            / SMA(ABS(CLOSE - DELAY(CLOSE, 1)), 12, 1)
            * 100
            - MIN(
                SMA(MAX(CLOSE - DELAY(CLOSE, 1), 0), 12, 1)
                / SMA(ABS(CLOSE - DELAY(CLOSE, 1)), 12, 1)
                * 100,
                12,
            )
        )
        / (
            MAX(
                SMA(MAX(CLOSE - DELAY(CLOSE, 1), 0), 12, 1)
                / SMA(ABS(CLOSE - DELAY(CLOSE, 1)), 12, 1)
                * 100,
                12,
            )
            - MIN(
                SMA(MAX(CLOSE - DELAY(CLOSE, 1), 0), 12, 1)
                / SMA(ABS(CLOSE - DELAY(CLOSE, 1)), 12, 1)
                * 100,
                12,
            )
        )
    )
    """
    # TODO: 开发中
    pass


def alpha167(data: pd.DataFrame) -> pd.Series:
    """
    Alpha167 = SUM(
        CLOSE - DELAY(CLOSE, 1) > 0
        ? CLOSE - DELAY(CLOSE, 1)
        : 0,
        12,
    )
    """
    # TODO: Implement the 12-period sum of positive close changes.
    pass


def alpha168(data: pd.DataFrame) -> pd.Series:
    """
    Alpha168 = -VOLUME / MEAN(VOLUME, 20)
    """
    return(-data['volume'] / MEAN(data['volume'], 20)).rename('Alpha168')


def alpha169(data: pd.DataFrame) -> pd.Series:
    """
    Alpha169 = SMA(
        MEAN(
            DELAY(SMA(CLOSE - DELAY(CLOSE, 1), 9, 1), 1),
            12,
        )
        - MEAN(
            DELAY(SMA(CLOSE - DELAY(CLOSE, 1), 9, 1), 1),
            26,
        ),
        10,
        1,
    )
    """
    prev_close_1d = DELAY(data['close'])
    close_change_1d = data['close'] - prev_close_1d
    sma_change_9d = SMA(close_change_1d, 9, 1)
    prev_sma_change_1d = DELAY(sma_change_9d, 1)
    return(
        SMA(
            MEAN(prev_sma_change_1d, 12) - MEAN(prev_sma_change_1d, 26),
            10,
            1
        )
    ).rename('Alpha169')


def alpha171(data: pd.DataFrame) -> pd.Series:
    """
    Alpha171 = (
        -((LOW - CLOSE) * (OPEN ^ 5))
        / ((CLOSE - HIGH) * (CLOSE ^ 5))
    )
    纯日内 K 线形态因子，它同时衡量：
    收盘价在当日最高价和最低价之间的位置；
    开盘价相对收盘价的高低；
    并通过五次方放大开盘价与收盘价的差异。
    """
    distance_from_low = data['close'] - data['low']
    distance_from_high = data['high'] -  data['close']
    close_position = distance_from_low / distance_from_high
    open_close_relation = (data['open'] / data['close']) ** 5

    return(
        -close_position * open_close_relation
    ).rename('Alpha171')



def alpha173(data: pd.DataFrame) -> pd.Series:
    """
    Alpha173 = (
        3 * SMA(CLOSE, 13, 2)
        - 2 * SMA(SMA(CLOSE, 13, 2), 13, 2)
        + SMA(
            SMA(SMA(LOG(CLOSE), 13, 2), 13, 2),
            13,
            2,
        )
    )
    """
    smoothed_close = SMA(data["close"], 13, 2)
    twice_smoothed_close = SMA(
        smoothed_close,
        13,
        2,
    )
    triple_smoothed_log_close = SMA(
        SMA(
            SMA(LOG(data["close"]), 13, 2),
            13,
            2,
        ),
        13,
        2,
    )

    return (
        3 * smoothed_close
        - 2 * twice_smoothed_close
        + triple_smoothed_log_close
    ).rename("Alpha173")


def alpha175(data: pd.DataFrame) -> pd.Series:
    """
    Alpha175 = MEAN(
        MAX(
            MAX(
                HIGH - LOW,
                ABS(DELAY(CLOSE, 1) - HIGH),
            ),
            ABS(DELAY(CLOSE, 1) - LOW),
        ),
        6,
    )
    """
    price_change = data['high'] - data['low']
    prev_close_1d = DELAY(data['close'], 1)

    prev_close_to_high = ABS(prev_close_1d - data['high'])
    prev_close_to_low = ABS(prev_close_1d - data['low'])

    max_price_change = MAX(price_change, prev_close_to_high)
    max_high_to_low = MAX(max_price_change, prev_close_to_low)

    return(MEAN(max_high_to_low, 6)).rename('Alpha175')


def alpha177(data: pd.DataFrame) -> pd.Series:
    """
    Alpha177 = (
        (20 - HIGHDAY(HIGH, 20))
        / 20
        * 100
    )
    """
    return (
        (20 - HIGHDAY(data["high"], 20))
        / 20
        * 100
    ).rename("Alpha177")


def alpha178(data: pd.DataFrame) -> pd.Series:
    """
    Alpha178 = (
        (CLOSE - DELAY(CLOSE, 1))
        / DELAY(CLOSE, 1)
        * VOLUME
    )
    """
    pre_close = DELAY(data['close'], 1)
    return(
        (data['close'] - pre_close)
        / pre_close
        * data['volume']
    ).rename('Alpha178')


def alpha180(data: pd.DataFrame) -> pd.Series:
    """
    Alpha180 = (
        MEAN(VOLUME, 20) < VOLUME
        ? (
            -TSRANK(ABS(DELTA(CLOSE, 7)), 60)
            * SIGN(DELTA(CLOSE, 7))
        )
        : -VOLUME
    )
    """
    average_volume_20d = MEAN(data["volume"], 20)
    close_change_7d = DELTA(data["close"], 7)
    ranked_absolute_change = TSRANK(
        ABS(close_change_7d),
        60,
    )
    high_volume_value = (
        -ranked_absolute_change
        * SIGN(close_change_7d)
    )

    has_volume_history = average_volume_20d.notna()
    is_high_volume = data["volume"] > average_volume_20d
    result = pd.Series(
        np.nan,
        index=data.index,
        dtype=float,
    )
    result = result.mask(
        has_volume_history & is_high_volume,
        high_volume_value,
    )
    result = result.mask(
        has_volume_history & ~is_high_volume,
        -data["volume"],
    )

    return result.rename("Alpha180")


def alpha182(data: pd.DataFrame) -> pd.Series:
    """
    Alpha182 = (
        COUNT(
            (
                CLOSE > OPEN
                & BANCHMARKINDEXCLOSE > BANCHMARKINDEXOPEN
            )
            OR (
                CLOSE < OPEN
                & BANCHMARKINDEXCLOSE < BANCHMARKINDEXOPEN
            ),
            20,
        )
        / 20
    )
    """
    stock_up = data["close"] > data["open"]
    stock_down = data["close"] < data["open"]
    benchmark_up = (
        data["benchmark_close"]
        > data["benchmark_open"]
    )
    benchmark_down = (
        data["benchmark_close"]
        < data["benchmark_open"]
    )
    same_direction = (
        (stock_up & benchmark_up)
        | (stock_down & benchmark_down)
    )

    return (
        COUNT(same_direction, 20)
        / 20
    ).rename("Alpha182")


def alpha185(data: pd.DataFrame) -> pd.Series:
    """
    Alpha185 = RANK(
        -1 * (1 - OPEN / CLOSE) ^ 2
    )
    """
    intraday_reversal = -(
        1 - data["open"] / data["close"]
    ) ** 2

    return _cross_sectional_rank(
        data,
        intraday_reversal,
    ).rename("Alpha185")


def alpha187(data: pd.DataFrame) -> pd.Series:
    """
    Alpha187 = SUM(
        OPEN <= DELAY(OPEN, 1)
        ? 0
        : MAX(HIGH - OPEN, OPEN - DELAY(OPEN, 1)),
        20,
    )
    """
    # TODO: Implement the 20-period DBM-style open movement sum.
    pass


def alpha188(data: pd.DataFrame) -> pd.Series:
    """
    Alpha188 = (
        (HIGH - LOW - SMA(HIGH - LOW, 11, 2))
        / SMA(HIGH - LOW, 11, 2)
        * 100
    )
    """
    SMA_12 = SMA(data['high'] - data['low'], 11, 2)
    return(
        (data['high'] - data['low'] - SMA_12)
        / SMA_12
        * 100
    ).rename('Alpha188')


def alpha189(data: pd.DataFrame) -> pd.Series:
    """
    Alpha189 = MEAN(
        ABS(CLOSE - MEAN(CLOSE, 6)),
        6,
    )
    """
    avg_close_6 = MEAN(data["close"], periods=6)
    absolute_deviation = ABS(data["close"] - avg_close_6)

    return MEAN(
        absolute_deviation,
        periods=6,
    ).rename("Alpha189")


def alpha190(data: pd.DataFrame) -> pd.Series:
    """
    Alpha190 = LOG(
        (
            COUNT(RET > GROWTH, 20) - 1
        )
        * SUMIF((RET - GROWTH) ^ 2, 20, RET < GROWTH)
        / (
            COUNT(RET < GROWTH, 20)
            * SUMIF((RET - GROWTH) ^ 2, 20, RET > GROWTH)
        )
    )

    GROWTH = (CLOSE / DELAY(CLOSE, 19)) ^ (1 / 20) - 1
    """
    daily_return = RET(data["close"])
    growth_rate = (
        data["close"]
        / DELAY(data["close"], 19)
    ) ** (1 / 20) - 1
    squared_deviation = (
        daily_return - growth_rate
    ) ** 2

    return_above_growth = daily_return > growth_rate
    return_below_growth = daily_return < growth_rate

    numerator = (
        COUNT(return_above_growth, 20) - 1
    ) * SUMIF(
        squared_deviation,
        20,
        return_below_growth,
    )
    denominator = (
        COUNT(return_below_growth, 20)
        * SUMIF(
            squared_deviation,
            20,
            return_above_growth,
        )
    ).replace(0, np.nan)
    log_input = numerator / denominator

    return LOG(
        log_input,
    ).rename("Alpha190")


def alpha191(data: pd.DataFrame) -> pd.Series:
    """
    Alpha191 = (
        CORR(MEAN(VOLUME, 20), LOW, 5)
        + (HIGH + LOW) / 2
        - CLOSE
    )
    """
    return(CORR(MEAN(data['volume'], 20), data['low'], 5)
           + (data['high'] + data['low']) / 2
           - data['close']).rename('Alpha191')


PANEL_FACTORS = frozenset(
    {
        "Alpha6",
        "Alpha25",
        "Alpha48",
        "Alpha83",
        "Alpha99",
        "Alpha185",
    }
)


FACTORS = {
    "Alpha2": alpha2,
    "Alpha3": alpha3,
    "Alpha5": alpha5,
    "Alpha6": alpha6,
    "Alpha9": alpha9,
    "Alpha11": alpha11,
    "Alpha13": alpha13,
    "Alpha14": alpha14,
    "Alpha15": alpha15,
    "Alpha18": alpha18,
    "Alpha20": alpha20,
    "Alpha21": alpha21,
    "Alpha24": alpha24,
    "Alpha25": alpha25,
    "Alpha26": alpha26,
    "Alpha27": alpha27,
    "Alpha29": alpha29,
    "Alpha31": alpha31,
    "Alpha34": alpha34,
    "Alpha40": alpha40,
    "Alpha43": alpha43,
    "Alpha44": alpha44,
    "Alpha46": alpha46,
    "Alpha47": alpha47,
    "Alpha48": alpha48,
    "Alpha52": alpha52,
    "Alpha53": alpha53,
    "Alpha57": alpha57,
    "Alpha58": alpha58,
    "Alpha59": alpha59,
    "Alpha60": alpha60,
    "Alpha63": alpha63,
    "Alpha65": alpha65,
    "Alpha66": alpha66,
    "Alpha67": alpha67,
    "Alpha68": alpha68,
    "Alpha69": alpha69,
    "Alpha70": alpha70,
    "Alpha71": alpha71,
    "Alpha72": alpha72,
    "Alpha75": alpha75,
    "Alpha76": alpha76,
    "Alpha79": alpha79,
    "Alpha80": alpha80,
    "Alpha81": alpha81,
    "Alpha82": alpha82,
    "Alpha83": alpha83,
    "Alpha84": alpha84,
    "Alpha85": alpha85,
    "Alpha88": alpha88,
    "Alpha89": alpha89,
    "Alpha93": alpha93,
    "Alpha95": alpha95,
    "Alpha96": alpha96,
    "Alpha97": alpha97,
    "Alpha99": alpha99,
    "Alpha100": alpha100,
    "Alpha102": alpha102,
    "Alpha103": alpha103,
    "Alpha106": alpha106,
    "Alpha109": alpha109,
    "Alpha110": alpha110,
    "Alpha111": alpha111,
    "Alpha116": alpha116,
    "Alpha117": alpha117,
    "Alpha118": alpha118,
    "Alpha122": alpha122,
    "Alpha126": alpha126,
    "Alpha132": alpha132,
    "Alpha133": alpha133,
    "Alpha134": alpha134,
    "Alpha135": alpha135,
    "Alpha139": alpha139,
    "Alpha144": alpha144,
    "Alpha145": alpha145,
    "Alpha147": alpha147,
    "Alpha149": alpha149,
    "Alpha150": alpha150,
    "Alpha151": alpha151,
    "Alpha152": alpha152,
    "Alpha153": alpha153,
    "Alpha154": alpha154,
    "Alpha155": alpha155,
    "Alpha158": alpha158,
    "Alpha161": alpha161,
    "Alpha168": alpha168,
    "Alpha169": alpha169,
    "Alpha171": alpha171,
    "Alpha173": alpha173,
    "Alpha175": alpha175,
    "Alpha177": alpha177,
    "Alpha178": alpha178,
    "Alpha180": alpha180,
    "Alpha182": alpha182,
    "Alpha185": alpha185,
    "Alpha188": alpha188,
    "Alpha189": alpha189,
    "Alpha190": alpha190,
    "Alpha191": alpha191,
}


def calculate_factors(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    has_cross_section = (
        {"trade_date", "trade_symbol"}.issubset(data.columns)
        and data["trade_symbol"].nunique() > 1
    )

    for name, factor_func in FACTORS.items():
        if name in PANEL_FACTORS and not has_cross_section:
            result[name] = pd.Series(
                np.nan,
                index=data.index,
                name=name,
            )
            continue

        if has_cross_section and name not in PANEL_FACTORS:
            factor_result = pd.Series(
                np.nan,
                index=data.index,
                name=name,
            )
            for _, group_index in data.groupby(
                "trade_symbol",
                sort=False,
            ).groups.items():
                factor_result.loc[group_index] = factor_func(
                    data.loc[group_index]
                )
            result[name] = factor_result
            continue

        result[name] = factor_func(data)

    return result

if __name__ == "__main__":
    print(f"当前已经注册了{len(FACTORS)}个因子")
