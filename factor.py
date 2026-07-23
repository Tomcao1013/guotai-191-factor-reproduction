import numpy as np
import pandas as pd

from factor_operators import *


def alpha1(data: pd.DataFrame) -> pd.Series:
    """
    Alpha1 = (-1*CORR(RANK(DELTA(LOG(VOLUME),1)),RANK(((CLOSE-OPEN)/OPEN)),6))
    """
    volume_change = DELTA(LOG(data["volume"]), 1)
    open_price = data["open"].replace(0, np.nan)
    close_open_return = (
        data["close"] - data["open"]
    ) / open_price

    return (
        -CORR(
            RANK(volume_change),
            RANK(close_open_return),
            6,
        )
    ).rename("Alpha1")


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


def alpha4(data: pd.DataFrame) -> pd.Series:
    """
    Alpha4 = (
        MEAN(CLOSE, 8) + STD(CLOSE, 8) < MEAN(CLOSE, 2)
        ? -1
        : (
            MEAN(CLOSE, 2) < MEAN(CLOSE, 8) - STD(CLOSE, 8)
            ? 1
            : (VOLUME / MEAN(VOLUME, 20) >= 1 ? 1 : -1)
        )
    )
    """
    average_close_8d = MEAN(data["close"], 8)
    close_std_8d = STD(data["close"], 8)
    average_close_2d = MEAN(data["close"], 2)
    volume_ratio = (
        data["volume"]
        / MEAN(data["volume"], 20)
    )
    price_inputs_valid = (
        average_close_8d.notna()
        & close_std_8d.notna()
        & average_close_2d.notna()
    )
    short_term_above_band = (
        average_close_8d + close_std_8d
        < average_close_2d
    )
    short_term_below_band = (
        average_close_2d
        < average_close_8d - close_std_8d
    )
    valid = (
        price_inputs_valid
        & (
            short_term_above_band
            | short_term_below_band
            | volume_ratio.notna()
        )
    )
    result = pd.Series(
        np.select(
            [
                short_term_above_band,
                short_term_below_band,
                volume_ratio >= 1,
            ],
            [-1.0, 1.0, 1.0],
            default=-1.0,
        ),
        index=data.index,
    )

    return result.where(valid).rename("Alpha4")


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
    price_change_4d = DELTA(blended_price, 4)

    return (
        -RANK(SIGN(price_change_4d))
    ).rename("Alpha6")


def alpha7(data: pd.DataFrame) -> pd.Series:
    """
    Alpha7 = (
        RANK(MAX(VWAP - CLOSE, 3))
        + RANK(MIN(VWAP - CLOSE, 3))
    ) * RANK(DELTA(VOLUME, 3))
    """
    vwap_close_difference = data["vwap"] - data["close"]
    maximum_difference = MAX(vwap_close_difference, 3)
    minimum_difference = MIN(vwap_close_difference, 3)
    volume_change = DELTA(data["volume"], 3)

    return (
        (
            RANK(maximum_difference)
            + RANK(minimum_difference)
        )
        * RANK(volume_change)
    ).rename("Alpha7")


def alpha8(data: pd.DataFrame) -> pd.Series:
    """
    Alpha8 = RANK(
        -DELTA(
            (HIGH + LOW) / 2 * 0.2
            + VWAP * 0.8,
            4,
        )
    )
    """
    blended_price = (
        (data["high"] + data["low"]) / 2 * 0.2
        + data["vwap"] * 0.8
    )
    price_change_4d = DELTA(blended_price, 4)

    return RANK(-price_change_4d).rename("Alpha8")


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
    delay_change = -DELAY(data['high'] + data['low'], 1) / 2
    return SMA((change + delay_change) * (data['high'] - data['low']) / data['volume'], 7, 2).rename('Alpha9')


def alpha10(data: pd.DataFrame) -> pd.Series:
    """
    Alpha10 = (RANK(MAX(((RET<0)?STD(RET,20):CLOSE)^2),5))
    """
    daily_return = RET(data["close"])
    return_std_20d = STD(daily_return, 20)
    conditional_value = data["close"].mask(
        daily_return < 0,
        return_std_20d,
    )
    squared_value = conditional_value ** 2

    return RANK(
        MAX(squared_value, 5)
    ).rename("Alpha10")


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


def alpha12(data: pd.DataFrame) -> pd.Series:
    """
    Alpha12 = (
        RANK(OPEN - SUM(VWAP, 10) / 10)
        * -RANK(ABS(CLOSE - VWAP))
    )
    """
    average_vwap_10d = SUM(data["vwap"], 10) / 10
    ranked_open_deviation = RANK(
        data["open"] - average_vwap_10d,
    )
    ranked_close_vwap_distance = RANK(
        ABS(data["close"] - data["vwap"]),
    )

    return (
        -ranked_open_deviation
        * ranked_close_vwap_distance
    ).rename("Alpha12")


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


def alpha16(data: pd.DataFrame) -> pd.Series:
    """
    Alpha16 = (-1*TSMAX(RANK(CORR(RANK(VOLUME),RANK(VWAP),5)),5))
    """
    ranked_correlation = RANK(
        CORR(
            RANK(data["volume"]),
            RANK(data["vwap"]),
            5,
        )
    )

    return (-TSMAX(ranked_correlation, 5)).rename("Alpha16")


def alpha17(data: pd.DataFrame) -> pd.Series:
    """
    Alpha17 = RANK((VWAP - MAX(VWAP, 15))) ^ DELTA(CLOSE, 5)
    """
    vwap_maximum = MAX(data["vwap"], 15)
    vwap_deviation = data["vwap"] - vwap_maximum

    return (
        RANK(vwap_deviation)
        ** DELTA(data["close"], 5)
    ).rename("Alpha17")


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
    previous_close = DELAY(data["close"], 5)
    close_change = data["close"] - previous_close

    result = pd.Series(
        np.nan,
        index=data.index,
        dtype=float,
    )
    result = result.mask(
        data["close"] < previous_close,
        close_change / previous_close,
    )
    result = result.mask(
        data["close"] == previous_close,
        0.0,
    )
    result = result.mask(
        data["close"] > previous_close,
        close_change / data["close"],
    )

    return result.rename("Alpha19")


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
        SEQUENCE(6),
        6,
    )).rename('Alpha21')


def alpha22(data: pd.DataFrame) -> pd.Series:
    """
    Alpha22 = SMA(
        (
            (CLOSE - MEAN(CLOSE, 6)) / MEAN(CLOSE, 6)
            - DELAY(
                (CLOSE - MEAN(CLOSE, 6)) / MEAN(CLOSE, 6),
                3,
            )
        ),
        12,
        1,
    )
    """
    average_close_6d = MEAN(data["close"], 6)
    close_deviation = (
        data["close"] - average_close_6d
    ) / average_close_6d

    return SMA(
        close_deviation - DELAY(close_deviation, 3),
        12,
        1,
    ).rename("Alpha22")


def alpha23(data: pd.DataFrame) -> pd.Series:
    """
    Alpha23 = (
        SMA(
            CLOSE > DELAY(CLOSE, 1) ? STD(CLOSE, 20) : 0,
            20,
            1,
        )
        / (
            SMA(
                CLOSE > DELAY(CLOSE, 1) ? STD(CLOSE, 20) : 0,
                20,
                1,
            )
            + SMA(
                CLOSE <= DELAY(CLOSE, 1) ? STD(CLOSE, 20) : 0,
                20,
                1,
            )
        )
        * 100
    )
    """
    previous_close = DELAY(data["close"], 1)
    close_std_20d = STD(data["close"], 20)
    upward_volatility = close_std_20d.where(
        data["close"] > previous_close,
        0.0,
    )
    downward_volatility = close_std_20d.where(
        data["close"] <= previous_close,
        0.0,
    )
    smoothed_upward = SMA(
        upward_volatility,
        20,
        1,
    )
    smoothed_downward = SMA(
        downward_volatility,
        20,
        1,
    )
    denominator = (
        smoothed_upward + smoothed_downward
    ).replace(0, np.nan)

    return (
        smoothed_upward / denominator * 100
    ).where(close_std_20d.notna()).rename("Alpha23")


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
    average_volume_20d = MEAN(data["volume"], 20)
    relative_volume = data["volume"] / average_volume_20d
    decayed_relative_volume = DECAYLINEAR(relative_volume, 9)
    ranked_decayed_volume = RANK(decayed_relative_volume)

    close_change_7d = DELTA(data["close"], 7)
    ranked_price_volume_signal = RANK(
        close_change_7d * (1 - ranked_decayed_volume),
    )

    daily_return = RET(data["close"])
    return_sum_250d = SUM(daily_return, 250)
    ranked_long_return = RANK(return_sum_250d)

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


def alpha28(data: pd.DataFrame) -> pd.Series:
    """
    Alpha28 = (
        3
        * SMA(
            (CLOSE - TSMIN(LOW, 9))
            / (TSMAX(HIGH, 9) - TSMIN(LOW, 9))
            * 100,
            3,
            1,
        )
        - 2
        * SMA(
            SMA(
                (CLOSE - TSMIN(LOW, 9))
                / (TSMAX(HIGH, 9) - TSMAX(LOW, 9))
                * 100,
                3,
                1,
            ),
            3,
            1,
        )
    )
    """
    minimum_low_9d = TSMIN(data["low"], 9)
    maximum_high_9d = TSMAX(data["high"], 9)
    maximum_low_9d = TSMAX(data["low"], 9)
    fast_input = (
        (data["close"] - minimum_low_9d)
        / (
            maximum_high_9d - minimum_low_9d
        ).replace(0, np.nan)
        * 100
    )
    slow_input = (
        (data["close"] - minimum_low_9d)
        / (
            maximum_high_9d - maximum_low_9d
        ).replace(0, np.nan)
        * 100
    )

    return (
        3 * SMA(fast_input, 3, 1)
        - 2 * SMA(
            SMA(slow_input, 3, 1),
            3,
            1,
        )
    ).rename("Alpha28")


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


def alpha32(data: pd.DataFrame) -> pd.Series:
    """
    Alpha32 = (-1*SUM(RANK(CORR(RANK(HIGH),RANK(VOLUME),3)),3))
    """
    ranked_correlation = RANK(
        CORR(
            RANK(data["high"]),
            RANK(data["volume"]),
            3,
        )
    )

    return (-SUM(ranked_correlation, 3)).rename("Alpha32")


def alpha33(data: pd.DataFrame) -> pd.Series:
    """
    Alpha33 = ((((-1*TSMIN(LOW,5))+DELAY(TSMIN(LOW,5),5))
    *RANK(((SUM(RET,240)-SUM(RET,20))/220)))*TSRANK(VOLUME,5))
    """
    minimum_low = TSMIN(data["low"], 5)
    daily_return = RET(data["close"]).replace(
        [np.inf, -np.inf],
        np.nan,
    )
    return (
        (
            -minimum_low
            + DELAY(minimum_low, 5)
        )
        * RANK(
            (
                SUM(daily_return, 240)
                - SUM(daily_return, 20)
            ) / 220
        )
        * TSRANK(data["volume"], 5)
    ).rename("Alpha33")


def alpha34(data: pd.DataFrame) -> pd.Series:
    """
    Alpha34 = MEAN(CLOSE, 12) / CLOSE
    """
    return(
        MEAN(data['close'], 12) / data['close']
    ).rename('Alpha34')


def alpha35(data: pd.DataFrame) -> pd.Series:
    """
    Alpha35 = (MIN(RANK(DECAYLINEAR(DELTA(OPEN,1),15)),
    RANK(DECAYLINEAR(CORR((VOLUME),((OPEN*0.65)+(OPEN*0.35)),17),7)))*-1)
    """
    open_blend = (
        data["open"] * 0.65
        + data["open"] * 0.35
    )
    first_rank = RANK(
        DECAYLINEAR(
            DELTA(data["open"], 1),
            15,
        )
    )
    second_rank = RANK(
        DECAYLINEAR(
            CORR(
                data["volume"],
                open_blend,
                17,
            ),
            7,
        )
    )

    return (-MIN(first_rank, second_rank)).rename("Alpha35")


def alpha36(data: pd.DataFrame) -> pd.Series:
    """
    Alpha36 = RANK(
        SUM(
            CORR(RANK(VOLUME), RANK(VWAP), 6),
            2,
        )
    )
    """
    ranked_volume = RANK(data["volume"])
    ranked_vwap = RANK(data["vwap"])
    rank_correlation = CORR(
        ranked_volume,
        ranked_vwap,
        6,
    )

    return RANK(
        SUM(rank_correlation, 2)
    ).rename("Alpha36")


def alpha37(data: pd.DataFrame) -> pd.Series:
    """
    Alpha37 = -RANK(
        SUM(OPEN, 5) * SUM(RET, 5)
        - DELAY(SUM(OPEN, 5) * SUM(RET, 5), 10)
    )
    """
    open_sum_5d = SUM(data["open"], 5)
    daily_return = RET(data["close"])
    return_sum_5d = SUM(daily_return, 5)
    product = open_sum_5d * return_sum_5d
    delayed_product = DELAY(product, 10)

    return (
        -RANK(product - delayed_product)
    ).rename("Alpha37")


def alpha38(data: pd.DataFrame) -> pd.Series:
    """
    Alpha38 = (
        SUM(HIGH, 20) / 20 < HIGH
        ? -DELTA(HIGH, 2)
        : 0
    )
    """
    average_high_20d = SUM(data["high"], 20) / 20
    high_change_2d = DELTA(data["high"], 2)

    result = (-high_change_2d).where(
        average_high_20d < data["high"],
        0.0,
    )

    return result.where(
        average_high_20d.notna(),
    ).rename("Alpha38")


def alpha39(data: pd.DataFrame) -> pd.Series:
    """
    Alpha39 = ((RANK(DECAYLINEAR(DELTA((CLOSE),2),8))
    -RANK(DECAYLINEAR(CORR(((VWAP*0.3)+(OPEN*0.7)),
    SUM(MEAN(VOLUME,180),37),14),12)))*-1)
    """
    blended_price = (
        data["vwap"] * 0.3
        + data["open"] * 0.7
    )
    first_rank = RANK(
        DECAYLINEAR(
            DELTA(data["close"], 2),
            8,
        )
    )
    second_rank = RANK(
        DECAYLINEAR(
            CORR(
                blended_price,
                SUM(MEAN(data["volume"], 180), 37),
                14,
            ),
            12,
        )
    )

    return (-(first_rank - second_rank)).rename("Alpha39")


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

def alpha41(data: pd.DataFrame) -> pd.Series:
    """
    Alpha41 = -RANK(
        TSMAX(DELTA(VWAP, 3), 5)
    )
    """
    vwap_change_3d = DELTA(data["vwap"], 3)
    maximum_change_5d = TSMAX(vwap_change_3d, 5)

    return (
        -RANK(maximum_change_5d)
    ).rename("Alpha41")


def alpha42(data: pd.DataFrame) -> pd.Series:
    """
    Alpha42 = (
        -RANK(STD(HIGH, 10))
        * CORR(HIGH, VOLUME, 10)
    )
    """
    high_std_10d = STD(data["high"], 10)
    high_volume_correlation = CORR(
        data["high"],
        data["volume"],
        10,
    )

    return (
        -RANK(high_std_10d)
        * high_volume_correlation
    ).rename("Alpha42")

# def alpha999(data: pd.DataFrame) -> pd.Series:
#     """
#     Alpha42 = (
#         -RANK(STD(HIGH, 10))
#         * CORR(HIGH, VOLUME, 10)
#     )
#     """
#     return(
#         - _cross_sectional_rank(data, STD(data['high'], 10))
#         * CORR(data['high'], data['volume'], 10)
#     ).rename('Alpha999')

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


def alpha45(data: pd.DataFrame) -> pd.Series:
    """
    Alpha45 = (RANK(DELTA((((CLOSE*0.6)+(OPEN*0.4))),1))
    *RANK(CORR(VWAP,MEAN(VOLUME,150),15)))
    """
    blended_close = (
        data["close"] * 0.6
        + data["open"] * 0.4
    )

    return (
        RANK(DELTA(blended_close, 1))
        * RANK(
            CORR(
                data["vwap"],
                MEAN(data["volume"], 150),
                15,
            )
        )
    ).rename("Alpha45")


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
    previous_close_1d = DELAY(data["close"], 1)
    previous_close_2d = DELAY(data["close"], 2)
    previous_close_3d = DELAY(data["close"], 3)

    direction_signal = (
        SIGN(data["close"] - previous_close_1d)
        + SIGN(previous_close_1d - previous_close_2d)
        + SIGN(previous_close_2d - previous_close_3d)
    )
    ranked_direction = RANK(direction_signal)
    volume_sum_5d = SUM(data["volume"], 5)
    volume_sum_20d = SUM(data["volume"], 20).replace(0, np.nan)

    return (
        -ranked_direction
        * volume_sum_5d
        / volume_sum_20d
    ).rename("Alpha48")



def alpha49(data: pd.DataFrame) -> pd.Series:
    """
    Alpha49 = SUM(DOWNWARD_MOVE, 12) / (
        SUM(DOWNWARD_MOVE, 12)
        + SUM(UPWARD_MOVE, 12)
    )
    """
    previous_high = DELAY(data["high"], 1)
    previous_low = DELAY(data["low"], 1)
    current_price_sum = data["high"] + data["low"]
    previous_price_sum = previous_high + previous_low
    movement = MAX(
        ABS(data["high"] - previous_high),
        ABS(data["low"] - previous_low),
    )
    downward_movement = movement.where(
        current_price_sum < previous_price_sum,
        0.0,
    ).where(previous_price_sum.notna())
    upward_movement = movement.where(
        current_price_sum > previous_price_sum,
        0.0,
    ).where(previous_price_sum.notna())
    downward_sum = SUM(downward_movement, 12)
    upward_sum = SUM(upward_movement, 12)
    total_movement = (
        downward_sum + upward_sum
    ).replace(0, np.nan)

    return (
        downward_sum / total_movement
    ).rename("Alpha49")


def alpha50(data: pd.DataFrame) -> pd.Series:
    """
    Alpha50 = Alpha51 - Alpha49
    """
    return (
        alpha51(data) - alpha49(data)
    ).rename("Alpha50")


def alpha51(data: pd.DataFrame) -> pd.Series:
    """
    Alpha51 = SUM(UPWARD_MOVE, 12) / (
        SUM(UPWARD_MOVE, 12)
        + SUM(DOWNWARD_MOVE, 12)
    )
    """
    previous_high = DELAY(data["high"], 1)
    previous_low = DELAY(data["low"], 1)
    current_price_sum = data["high"] + data["low"]
    previous_price_sum = previous_high + previous_low
    movement = MAX(
        ABS(data["high"] - previous_high),
        ABS(data["low"] - previous_low),
    )
    upward_movement = movement.where(
        current_price_sum > previous_price_sum,
        0.0,
    ).where(previous_price_sum.notna())
    downward_movement = movement.where(
        current_price_sum < previous_price_sum,
        0.0,
    ).where(previous_price_sum.notna())
    upward_sum = SUM(upward_movement, 12)
    downward_sum = SUM(downward_movement, 12)
    total_movement = (
        upward_sum + downward_sum
    ).replace(0, np.nan)

    return (
        upward_sum / total_movement
    ).rename("Alpha51")


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


def alpha54(data: pd.DataFrame) -> pd.Series:
    """
    Alpha54 = -RANK(
        STD(ABS(CLOSE - OPEN), 10)
        + (CLOSE - OPEN)
        + CORR(CLOSE, OPEN, 10)
    )
    """
    candle_body = data["close"] - data["open"]
    body_std_10d = STD(ABS(candle_body), 10)
    close_open_correlation = CORR(
        data["close"],
        data["open"],
        10,
    )
    signal = (
        body_std_10d
        + candle_body
        + close_open_correlation
    )

    return (
        -RANK(signal)
    ).rename("Alpha54")


def alpha55(data: pd.DataFrame) -> pd.Series:
    """
    Alpha55 = SUM(Alpha137 daily term, 20)
    """
    return SUM(
        alpha137(data),
        20,
    ).rename("Alpha55")


def alpha56(data: pd.DataFrame) -> pd.Series:
    """
    Alpha56 = (RANK((OPEN-TSMIN(OPEN,12)))<RANK((RANK(CORR(
    SUM(((HIGH+LOW)/2),19),SUM(MEAN(VOLUME,40),19),13))^5)))
    """
    left_rank = RANK(
        data["open"] - TSMIN(data["open"], 12)
    )
    correlation_rank = RANK(
        CORR(
            SUM((data["high"] + data["low"]) / 2, 19),
            SUM(MEAN(data["volume"], 40), 19),
            13,
        )
    )
    right_rank = RANK(correlation_rank ** 5)

    return (left_rank < right_rank).rename("Alpha56")


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


def alpha61(data: pd.DataFrame) -> pd.Series:
    """
    Alpha61 = (MAX(RANK(DECAYLINEAR(DELTA(VWAP,1),12)),
    RANK(DECAYLINEAR(RANK(CORR((LOW),MEAN(VOLUME,80),8)),17)))*-1)
    """
    first_rank = RANK(
        DECAYLINEAR(
            DELTA(data["vwap"], 1),
            12,
        )
    )
    second_rank = RANK(
        DECAYLINEAR(
            RANK(
                CORR(
                    data["low"],
                    MEAN(data["volume"], 80),
                    8,
                )
            ),
            17,
        )
    )

    return (-MAX(first_rank, second_rank)).rename("Alpha61")


def alpha62(data: pd.DataFrame) -> pd.Series:
    """
    Alpha62 = -CORR(
        HIGH,
        RANK(VOLUME),
        5,
    )
    """
    ranked_volume = RANK(data["volume"])
    high_volume_rank_correlation = CORR(
        data["high"],
        ranked_volume,
        5,
    )

    return (
        -high_volume_rank_correlation
    ).rename("Alpha62")


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



def alpha64(data: pd.DataFrame) -> pd.Series:
    """
    Alpha64 = (
        MAX(
            RANK(
                DECAYLINEAR(
                    CORR(RANK(VWAP), RANK(VOLUME), 4),
                    4,
                )
            ),
            RANK(
                DECAYLINEAR(
                    MAX(
                        CORR(
                            RANK(CLOSE),
                            RANK(MEAN(VOLUME, 60)),
                            4,
                        ),
                        13,
                    ),
                    14,
                )
            ),
        )
        * -1
    )
    """
    first_rank = RANK(
        DECAYLINEAR(
            CORR(
                RANK(data["vwap"]),
                RANK(data["volume"]),
                4,
            ),
            4,
        )
    )
    close_volume_correlation = CORR(
        RANK(data["close"]),
        RANK(MEAN(data["volume"], 60)),
        4,
    )
    second_rank = RANK(
        DECAYLINEAR(
            MAX(close_volume_correlation, 13),
            14,
        )
    )

    return (
        -MAX(first_rank, second_rank)
    ).rename("Alpha64")


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
    delay_change = -DELAY(data['high'] + data['low'], 1) / 2
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


def alpha73(data: pd.DataFrame) -> pd.Series:
    """
    Alpha73 = ((TSRANK(DECAYLINEAR(DECAYLINEAR(CORR((CLOSE),
    VOLUME,10),16),4),5)-RANK(DECAYLINEAR(CORR(VWAP,
    MEAN(VOLUME,30),4),3)))*-1)
    """
    left_rank = TSRANK(
        DECAYLINEAR(
            DECAYLINEAR(
                CORR(
                    data["close"],
                    data["volume"],
                    10,
                ),
                16,
            ),
            4,
        ),
        5,
    )
    right_rank = RANK(
        DECAYLINEAR(
            CORR(
                data["vwap"],
                MEAN(data["volume"], 30),
                4,
            ),
            3,
        )
    )

    return (-(left_rank - right_rank)).rename("Alpha73")


def alpha74(data: pd.DataFrame) -> pd.Series:
    """
    Alpha74 = (RANK(CORR(SUM(((LOW*0.35)+(VWAP*0.65)),20),
    SUM(MEAN(VOLUME,40),20),7))+RANK(CORR(RANK(VWAP),
    RANK(VOLUME),6)))
    """
    blended_price = (
        data["low"] * 0.35
        + data["vwap"] * 0.65
    )
    first_rank = RANK(
        CORR(
            SUM(blended_price, 20),
            SUM(MEAN(data["volume"], 40), 20),
            7,
        )
    )
    second_rank = RANK(
        CORR(
            RANK(data["vwap"]),
            RANK(data["volume"]),
            6,
        )
    )

    return (first_rank + second_rank).rename("Alpha74")


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


def alpha77(data: pd.DataFrame) -> pd.Series:
    """
    Alpha77 = MIN(RANK(DECAYLINEAR(((((HIGH+LOW)/2)+HIGH)
    -(VWAP+HIGH)),20)),RANK(DECAYLINEAR(CORR(((HIGH+LOW)/2),
    MEAN(VOLUME,40),3),6)))
    """
    midpoint_price = (
        data["high"] + data["low"]
    ) / 2
    first_signal = (
        (midpoint_price + data["high"])
        - (data["vwap"] + data["high"])
    )
    first_rank = RANK(
        DECAYLINEAR(first_signal, 20)
    )
    second_rank = RANK(
        DECAYLINEAR(
            CORR(
                midpoint_price,
                MEAN(data["volume"], 40),
                3,
            ),
            6,
        )
    )

    return MIN(first_rank, second_rank).rename("Alpha77")


def alpha78(data: pd.DataFrame) -> pd.Series:
    """
    Alpha78 = (
        TYPICAL_PRICE - MEAN(TYPICAL_PRICE, 12)
    ) / (
        0.015
        * MEAN(
            ABS(CLOSE - MEAN(TYPICAL_PRICE, 12)),
            12,
        )
    )

    TYPICAL_PRICE = (HIGH + LOW + CLOSE) / 3
    """
    typical_price = (
        data["high"]
        + data["low"]
        + data["close"]
    ) / 3
    average_typical_price_12d = MEAN(
        typical_price,
        12,
    )
    mean_absolute_deviation = MEAN(
        ABS(
            data["close"]
            - average_typical_price_12d
        ),
        12,
    )

    return (
        (typical_price - average_typical_price_12d)
        / (
            0.015 * mean_absolute_deviation
        ).replace(0, np.nan)
    ).rename("Alpha78")


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
    ranked_high = RANK(data["high"])
    ranked_volume = RANK(data["volume"])
    rolling_covariance = COVIANCE(
        ranked_high,
        ranked_volume,
        5,
    )

    return (
        -RANK(rolling_covariance)
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


def alpha86(data: pd.DataFrame) -> pd.Series:
    """
    Alpha86 = (
        ACCELERATION > 0.25
        ? -1
        : (
            ACCELERATION < 0
            ? 1
            : -(CLOSE - DELAY(CLOSE, 1))
        )
    )

    ACCELERATION = (
        (DELAY(CLOSE, 20) - DELAY(CLOSE, 10)) / 10
        - (DELAY(CLOSE, 10) - CLOSE) / 10
    )
    """
    acceleration = (
        (
            DELAY(data["close"], 20)
            - DELAY(data["close"], 10)
        )
        / 10
        - (
            DELAY(data["close"], 10)
            - data["close"]
        )
        / 10
    )
    result = pd.Series(
        np.select(
            [
                acceleration > 0.25,
                acceleration < 0,
            ],
            [-1.0, 1.0],
            default=-DELTA(data["close"], 1),
        ),
        index=data.index,
    )

    return result.where(
        acceleration.notna(),
    ).rename("Alpha86")


def alpha87(data: pd.DataFrame) -> pd.Series:
    """
    Alpha87 = ((RANK(DECAYLINEAR(DELTA(VWAP,4),7))
    +TSRANK(DECAYLINEAR(((((LOW*0.9)+(LOW*0.1))-VWAP)
    /(OPEN-((HIGH+LOW)/2))),11),7))*-1)
    """
    relative_price_denominator = (
        data["open"]
        - (data["high"] + data["low"]) / 2
    ).replace(0, np.nan)
    relative_price = (
        (
            data["low"] * 0.9
            + data["low"] * 0.1
            - data["vwap"]
        )
        / relative_price_denominator
    )
    first_rank = RANK(
        DECAYLINEAR(
            DELTA(data["vwap"], 4),
            7,
        )
    )
    second_rank = TSRANK(
        DECAYLINEAR(relative_price, 11),
        7,
    )

    return (-(first_rank + second_rank)).rename("Alpha87")


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



def alpha90(data: pd.DataFrame) -> pd.Series:
    """
    Alpha90 = -RANK(
        CORR(
            RANK(VWAP),
            RANK(VOLUME),
            5,
        )
    )
    """
    ranked_vwap = RANK(data["vwap"])
    ranked_volume = RANK(data["volume"])
    rank_correlation = CORR(
        ranked_vwap,
        ranked_volume,
        5,
    )

    return (
        -RANK(rank_correlation)
    ).rename("Alpha90")


def alpha91(data: pd.DataFrame) -> pd.Series:
    """
    Alpha91 = (
        RANK(CLOSE - MAX(CLOSE, 5))
        * RANK(CORR(MEAN(VOLUME, 40), LOW, 5))
    ) * -1
    """
    close_deviation = (
        data["close"] - MAX(data["close"], 5)
    )
    volume_low_correlation = CORR(
        MEAN(data["volume"], 40),
        data["low"],
        5,
    )

    return (
        -(
            RANK(close_deviation)
            * RANK(volume_low_correlation)
        )
    ).rename("Alpha91")


def alpha92(data: pd.DataFrame) -> pd.Series:
    """
    Alpha92 = (MAX(RANK(DECAYLINEAR(DELTA(((CLOSE*0.35)
    +(VWAP*0.65)),2),3)),TSRANK(DECAYLINEAR(ABS(CORR(
    (MEAN(VOLUME,180)),CLOSE,13)),5),15))*-1)
    """
    blended_price = (
        data["close"] * 0.35
        + data["vwap"] * 0.65
    )
    first_rank = RANK(
        DECAYLINEAR(
            DELTA(blended_price, 2),
            3,
        )
    )
    second_rank = TSRANK(
        DECAYLINEAR(
            ABS(
                CORR(
                    MEAN(data["volume"], 180),
                    data["close"],
                    13,
                )
            ),
            5,
        ),
        15,
    )

    return (-MAX(first_rank, second_rank)).rename("Alpha92")


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
    previous_close = DELAY(data["close"], 1)
    signed_volume = pd.Series(
        0.0,
        index=data.index,
    )
    signed_volume = signed_volume.mask(
        data["close"] > previous_close,
        data["volume"],
    )
    signed_volume = signed_volume.mask(
        data["close"] < previous_close,
        -data["volume"],
    )
    signed_volume = signed_volume.where(
        previous_close.notna(),
    )

    return SUM(
        signed_volume,
        30,
    ).rename("Alpha94")


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


def alpha98(data: pd.DataFrame) -> pd.Series:
    """
    Alpha98 = (
        DELTA(SUM(CLOSE, 100) / 100, 100)
        / DELAY(CLOSE, 100)
        <= 0.05
        ? -(CLOSE - TSMIN(CLOSE, 100))
        : -DELTA(CLOSE, 3)
    )
    """
    average_close_100d = (
        SUM(data["close"], 100) / 100
    )
    trend = (
        DELTA(average_close_100d, 100)
        / DELAY(data["close"], 100)
    )
    drawdown = -(
        data["close"]
        - TSMIN(data["close"], 100)
    )
    change_3d = -DELTA(data["close"], 3)

    return change_3d.where(
        trend > 0.05,
        drawdown,
    ).where(trend.notna()).rename("Alpha98")


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
    ranked_close = RANK(data["close"])
    ranked_volume = RANK(data["volume"])
    rolling_covariance = COVIANCE(
        ranked_close,
        ranked_volume,
        5,
    )

    return (
        -RANK(rolling_covariance)
    ).rename("Alpha99")


def alpha100(data: pd.DataFrame) -> pd.Series:
    """
    Alpha100 = STD(VOLUME, 20)
    """
    return(STD(data['volume'], 20)).rename('Alpha100')


def alpha101(data: pd.DataFrame) -> pd.Series:
    """
    Alpha101 = ((RANK(CORR(CLOSE,SUM(MEAN(VOLUME,30),37),15))
    <RANK(CORR(RANK(((HIGH*0.1)+(VWAP*0.9))),RANK(VOLUME),11)))*-1)
    """
    left_rank = RANK(
        CORR(
            data["close"],
            SUM(MEAN(data["volume"], 30), 37),
            15,
        )
    )
    weighted_price = (
        data["high"] * 0.1
        + data["vwap"] * 0.9
    )
    right_rank = RANK(
        CORR(
            RANK(weighted_price),
            RANK(data["volume"]),
            11,
        )
    )

    return ((left_rank < right_rank) * -1).rename("Alpha101")


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


def alpha104(data: pd.DataFrame) -> pd.Series:
    """
    Alpha104 = (-1*(DELTA(CORR(HIGH,VOLUME,5),5)
    *RANK(STD(CLOSE,20))))
    """
    correlation_change = DELTA(
        CORR(data["high"], data["volume"], 5),
        5,
    )
    ranked_close_volatility = RANK(
        STD(data["close"], 20)
    )

    return (
        -(correlation_change * ranked_close_volatility)
    ).rename("Alpha104")


def alpha105(data: pd.DataFrame) -> pd.Series:
    """
    Alpha105 = -CORR(
        RANK(OPEN),
        RANK(VOLUME),
        10,
    )
    """
    ranked_open = RANK(data["open"])
    ranked_volume = RANK(data["volume"])
    rank_correlation = CORR(
        ranked_open,
        ranked_volume,
        10,
    )

    return (-rank_correlation).rename("Alpha105")


def alpha106(data: pd.DataFrame) -> pd.Series:
    """
    Alpha106 = CLOSE - DELAY(CLOSE, 20)
    """
    previous_close_20 = DELAY(data['close'], 20)
    return(
        data['close'] - previous_close_20
    ).rename('Alpha106')


def alpha107(data: pd.DataFrame) -> pd.Series:
    """
    Alpha107 = (
        -RANK(OPEN - DELAY(HIGH, 1))
        * RANK(OPEN - DELAY(CLOSE, 1))
        * RANK(OPEN - DELAY(LOW, 1))
    )
    """
    previous_high = DELAY(data["high"], 1)
    previous_close = DELAY(data["close"], 1)
    previous_low = DELAY(data["low"], 1)

    return (
        -RANK(
            data["open"] - previous_high,
        )
        * RANK(
            data["open"] - previous_close,
        )
        * RANK(
            data["open"] - previous_low,
        )
    ).rename("Alpha107")


def alpha108(data: pd.DataFrame) -> pd.Series:
    """
    Alpha108 = (
        RANK(HIGH - MIN(HIGH, 2))
        ^ RANK(CORR(VWAP, MEAN(VOLUME, 120), 6))
    ) * -1
    """
    high_deviation = (
        data["high"] - MIN(data["high"], 2)
    )
    vwap_volume_correlation = CORR(
        data["vwap"],
        MEAN(data["volume"], 120),
        6,
    )

    return (
        -(
            RANK(high_deviation)
            ** RANK(vwap_volume_correlation)
        )
    ).rename("Alpha108")


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


def alpha112(data: pd.DataFrame) -> pd.Series:
    """
    Alpha112 = (
        SUM(POSITIVE_CHANGE, 12)
        - SUM(NEGATIVE_CHANGE, 12)
    ) / (
        SUM(POSITIVE_CHANGE, 12)
        + SUM(NEGATIVE_CHANGE, 12)
    ) * 100
    """
    close_change = DELTA(data["close"], 1)
    positive_change = close_change.where(
        close_change > 0,
        0.0,
    ).where(close_change.notna())
    negative_change = ABS(close_change).where(
        close_change < 0,
        0.0,
    ).where(close_change.notna())
    positive_sum = SUM(positive_change, 12)
    negative_sum = SUM(negative_change, 12)
    total_change = (
        positive_sum + negative_sum
    ).replace(0, np.nan)

    return (
        (positive_sum - negative_sum)
        / total_change
        * 100
    ).rename("Alpha112")


def alpha113(data: pd.DataFrame) -> pd.Series:
    """
    Alpha113 = (-1*((RANK((SUM(DELAY(CLOSE,5),20)/20))
    *CORR(CLOSE,VOLUME,2))*RANK(CORR(SUM(CLOSE,5),
    SUM(CLOSE,20),2))))
    """
    first_rank = RANK(
        SUM(DELAY(data["close"], 5), 20) / 20
    )
    second_signal = CORR(
        data["close"],
        data["volume"],
        2,
    )
    third_rank = RANK(
        CORR(
            SUM(data["close"], 5),
            SUM(data["close"], 20),
            2,
        )
    )

    return (-(first_rank * second_signal * third_rank)).rename(
        "Alpha113"
    )


def alpha114(data: pd.DataFrame) -> pd.Series:
    """
    Alpha114 = ((RANK(DELAY(((HIGH-LOW)/(SUM(CLOSE,5)/5)),2))
    *RANK(RANK(VOLUME)))/(((HIGH-LOW)/(SUM(CLOSE,5)/5))
    /(VWAP-CLOSE)))
    """
    average_close_5d = (
        SUM(data["close"], 5) / 5
    ).replace(0, np.nan)
    range_ratio = (
        data["high"] - data["low"]
    ) / average_close_5d
    vwap_close_gap = (
        data["vwap"] - data["close"]
    ).replace(0, np.nan)
    denominator = (
        range_ratio / vwap_close_gap
    ).replace(0, np.nan)

    result = (
        RANK(DELAY(range_ratio, 2))
        * RANK(RANK(data["volume"]))
        / denominator
    )

    return result.replace(
        [np.inf, -np.inf],
        np.nan,
    ).rename("Alpha114")


def alpha115(data: pd.DataFrame) -> pd.Series:
    """
    Alpha115 = (RANK(CORR(((HIGH*0.9)+(CLOSE*0.1)),
    MEAN(VOLUME,30),10))^RANK(CORR(TSRANK(((HIGH+LOW)/2),4),
    TSRANK(VOLUME,10),7)))
    """
    first_rank = RANK(
        CORR(
            data["high"] * 0.9
            + data["close"] * 0.1,
            MEAN(data["volume"], 30),
            10,
        )
    )
    second_rank = RANK(
        CORR(
            TSRANK((data["high"] + data["low"]) / 2, 4),
            TSRANK(data["volume"], 10),
            7,
        )
    )

    return (first_rank ** second_rank).rename("Alpha115")


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
        20,
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


def alpha119(data: pd.DataFrame) -> pd.Series:
    """
    Alpha119 = (
        RANK(
            DECAYLINEAR(
                CORR(VWAP, SUM(MEAN(VOLUME, 5), 26), 5),
                7,
            )
        )
        - RANK(
            DECAYLINEAR(
                TSRANK(
                    MIN(
                        CORR(
                            RANK(OPEN),
                            RANK(MEAN(VOLUME, 15)),
                            21,
                        ),
                        9,
                    ),
                    7,
                ),
                8,
            )
        )
    )
    """
    first_rank = RANK(
        DECAYLINEAR(
            CORR(
                data["vwap"],
                SUM(MEAN(data["volume"], 5), 26),
                5,
            ),
            7,
        )
    )
    ranked_open_volume_correlation = CORR(
        RANK(data["open"]),
        RANK(MEAN(data["volume"], 15)),
        21,
    )
    second_rank = RANK(
        DECAYLINEAR(
            TSRANK(
                MIN(ranked_open_volume_correlation, 9),
                7,
            ),
            8,
        )
    )

    return (
        first_rank - second_rank
    ).rename("Alpha119")


def alpha120(data: pd.DataFrame) -> pd.Series:
    """
    Alpha120 = (
        RANK(VWAP - CLOSE)
        / RANK(VWAP + CLOSE)
    )
    """
    ranked_difference = RANK(
        data["vwap"] - data["close"],
    )
    ranked_sum = RANK(
        data["vwap"] + data["close"],
    ).replace(0, np.nan)

    return (
        ranked_difference / ranked_sum
    ).rename("Alpha120")


def alpha121(data: pd.DataFrame) -> pd.Series:
    """
    Alpha121 = (
        RANK(VWAP - MIN(VWAP, 12))
        ^ TSRANK(
            CORR(
                TSRANK(VWAP, 20),
                TSRANK(MEAN(VOLUME, 60), 2),
                18,
            ),
            3,
        )
    ) * -1
    """
    vwap_deviation = (
        data["vwap"] - MIN(data["vwap"], 12)
    )
    rank_correlation = CORR(
        TSRANK(data["vwap"], 20),
        TSRANK(MEAN(data["volume"], 60), 2),
        18,
    )
    correlation_time_rank = TSRANK(
        rank_correlation,
        3,
    )

    return (
        -(
            RANK(vwap_deviation)
            ** correlation_time_rank
        )
    ).rename("Alpha121")


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


def alpha123(data: pd.DataFrame) -> pd.Series:
    """
    Alpha123 = ((RANK(CORR(SUM(((HIGH+LOW)/2),20),
    SUM(MEAN(VOLUME,60),20),9))<RANK(CORR(LOW,VOLUME,6)))*-1)
    """
    left_rank = RANK(
        CORR(
            SUM((data["high"] + data["low"]) / 2, 20),
            SUM(MEAN(data["volume"], 60), 20),
            9,
        )
    )
    right_rank = RANK(
        CORR(
            data["low"],
            data["volume"],
            6,
        )
    )

    return ((left_rank < right_rank) * -1).rename("Alpha123")


def alpha124(data: pd.DataFrame) -> pd.Series:
    """
    Alpha124 = (CLOSE-VWAP)/DECAYLINEAR(RANK(TSMAX(CLOSE,30)),2)
    """
    denominator = DECAYLINEAR(
        RANK(TSMAX(data["close"], 30)),
        2,
    ).replace(0, np.nan)

    return (
        (data["close"] - data["vwap"]) / denominator
    ).rename("Alpha124")


def alpha125(data: pd.DataFrame) -> pd.Series:
    """
    Alpha125 = (RANK(DECAYLINEAR(CORR((VWAP),
    MEAN(VOLUME,80),17),20))/RANK(DECAYLINEAR(
    DELTA(((CLOSE*0.5)+(VWAP*0.5)),3),16)))
    """
    numerator = RANK(
        DECAYLINEAR(
            CORR(
                data["vwap"],
                MEAN(data["volume"], 80),
                17,
            ),
            20,
        )
    )
    blended_price = (
        data["close"] * 0.5
        + data["vwap"] * 0.5
    )
    denominator = RANK(
        DECAYLINEAR(
            DELTA(blended_price, 3),
            16,
        )
    ).replace(0, np.nan)

    return (numerator / denominator).rename("Alpha125")


def alpha126(data: pd.DataFrame) -> pd.Series:
    """
    Alpha126 = (CLOSE + HIGH + LOW) / 3
    """
    return(
        (data['close'] + data['high'] + data['low'])
        / 3
    ).rename('Alpha126')


def alpha127(data: pd.DataFrame) -> pd.Series:
    """
    Alpha127 = SQRT(
        MEAN(
            (
                100
                * (CLOSE - TSMAX(CLOSE, 12))
                / TSMAX(CLOSE, 12)
            ) ^ 2,
            12,
        )
    )
    """
    maximum_close_12d = TSMAX(
        data["close"],
        12,
    ).replace(0, np.nan)
    squared_drawdown = (
        100
        * (
            data["close"] - maximum_close_12d
        )
        / maximum_close_12d
    ) ** 2

    return np.sqrt(
        MEAN(squared_drawdown, 12)
    ).rename("Alpha127")


def alpha128(data: pd.DataFrame) -> pd.Series:
    """
    Alpha128 = 100 - 100 / (
        1
        + SUM(POSITIVE_MONEY_FLOW, 14)
        / SUM(NEGATIVE_MONEY_FLOW, 14)
    )

    MONEY_FLOW = (HIGH + LOW + CLOSE) / 3 * VOLUME
    """
    typical_price = (
        data["high"]
        + data["low"]
        + data["close"]
    ) / 3
    previous_typical_price = DELAY(
        typical_price,
        1,
    )
    money_flow = typical_price * data["volume"]
    positive_money_flow = money_flow.where(
        typical_price > previous_typical_price,
        0.0,
    ).where(previous_typical_price.notna())
    negative_money_flow = money_flow.where(
        typical_price < previous_typical_price,
        0.0,
    ).where(previous_typical_price.notna())
    positive_sum = SUM(
        positive_money_flow,
        14,
    )
    negative_sum = SUM(
        negative_money_flow,
        14,
    ).replace(0, np.nan)
    money_flow_ratio = positive_sum / negative_sum

    return (
        100 - 100 / (1 + money_flow_ratio)
    ).rename("Alpha128")


def alpha129(data: pd.DataFrame) -> pd.Series:
    """
    Alpha129 = SUM(
        CLOSE - DELAY(CLOSE, 1) < 0
        ? ABS(CLOSE - DELAY(CLOSE, 1))
        : 0,
        12,
    )
    """
    close_change = data["close"] - DELAY(
        data["close"],
        1,
    )
    negative_change = ABS(close_change).where(
        close_change < 0,
        0.0,
    )
    negative_change = negative_change.where(
        close_change.notna(),
    )

    return SUM(
        negative_change,
        12,
    ).rename("Alpha129")


def alpha130(data: pd.DataFrame) -> pd.Series:
    """
    Alpha130 = (RANK(DECAYLINEAR(CORR(((HIGH+LOW)/2),
    MEAN(VOLUME,40),9),10))/RANK(DECAYLINEAR(
    CORR(RANK(VWAP),RANK(VOLUME),7),3)))
    """
    numerator = RANK(
        DECAYLINEAR(
            CORR(
                (data["high"] + data["low"]) / 2,
                MEAN(data["volume"], 40),
                9,
            ),
            10,
        )
    )
    denominator = RANK(
        DECAYLINEAR(
            CORR(
                RANK(data["vwap"]),
                RANK(data["volume"]),
                7,
            ),
            3,
        )
    ).replace(0, np.nan)

    return (numerator / denominator).rename("Alpha130")


def alpha131(data: pd.DataFrame) -> pd.Series:
    """
    Alpha131 = (
        RANK(DELTA(VWAP, 1))
        ^ TSRANK(CORR(CLOSE, MEAN(VOLUME, 50), 18), 18)
    )
    """
    ranked_vwap_change = RANK(
        DELTA(data["vwap"], 1)
    )
    correlation_time_rank = TSRANK(
        CORR(
            data["close"],
            MEAN(data["volume"], 50),
            18,
        ),
        18,
    )

    return (
        ranked_vwap_change ** correlation_time_rank
    ).rename("Alpha131")


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


def alpha136(data: pd.DataFrame) -> pd.Series:
    """
    Alpha136 = (
        -RANK(DELTA(RET, 3))
        * CORR(OPEN, VOLUME, 10)
    )
    """
    daily_return = RET(data["close"])
    return_change_3d = DELTA(daily_return, 3)
    open_volume_correlation = CORR(
        data["open"],
        data["volume"],
        10,
    )

    return (
        -RANK(return_change_3d)
        * open_volume_correlation
    ).rename("Alpha136")


def alpha137(data: pd.DataFrame) -> pd.Series:
    """
    Alpha137 = (
        16
        * (
            CLOSE - DELAY(CLOSE, 1)
            + (CLOSE - OPEN) / 2
            + DELAY(CLOSE, 1) - DELAY(OPEN, 1)
        )
        / DENOMINATOR
        * MAX(
            ABS(HIGH - DELAY(CLOSE, 1)),
            ABS(LOW - DELAY(CLOSE, 1)),
        )
    )
    """
    previous_close = DELAY(data["close"], 1)
    previous_open = DELAY(data["open"], 1)
    previous_low = DELAY(data["low"], 1)
    high_to_previous_close = ABS(
        data["high"] - previous_close
    )
    low_to_previous_close = ABS(
        data["low"] - previous_close
    )
    high_to_previous_low = ABS(
        data["high"] - previous_low
    )
    previous_body = ABS(
        previous_close - previous_open
    )
    denominator = pd.Series(
        np.select(
            [
                (
                    (
                        high_to_previous_close
                        > low_to_previous_close
                    )
                    & (
                        high_to_previous_close
                        > high_to_previous_low
                    )
                ),
                (
                    (
                        low_to_previous_close
                        > high_to_previous_low
                    )
                    & (
                        low_to_previous_close
                        > high_to_previous_close
                    )
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
            default=(
                high_to_previous_low
                + previous_body / 4
            ),
        ),
        index=data.index,
    )
    scale = MAX(
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
    ).rename("Alpha137")


def alpha138(data: pd.DataFrame) -> pd.Series:
    """
    Alpha138 = ((RANK(DECAYLINEAR(DELTA((((LOW*0.7)
    +(VWAP*0.3))),3),20))-TSRANK(DECAYLINEAR(
    TSRANK(CORR(TSRANK(LOW,8),TSRANK(MEAN(VOLUME,60),17),5),19),
    16),7))*-1)
    """
    first_rank = RANK(
        DECAYLINEAR(
            DELTA(
                data["low"] * 0.7
                + data["vwap"] * 0.3,
                3,
            ),
            20,
        )
    )
    nested_correlation = TSRANK(
        CORR(
            TSRANK(data["low"], 8),
            TSRANK(MEAN(data["volume"], 60), 17),
            5,
        ),
        19,
    )
    second_rank = TSRANK(
        DECAYLINEAR(nested_correlation, 16),
        7,
    )

    return (-(first_rank - second_rank)).rename("Alpha138")


def alpha139(data: pd.DataFrame) -> pd.Series:
    """
    Alpha139 = -CORR(OPEN, VOLUME, 10)
    """
    return(
        -CORR(data['open'], data['volume'], 10)
    ).rename('Alpha139')


def alpha140(data: pd.DataFrame) -> pd.Series:
    """
    Alpha140 = MIN(RANK(DECAYLINEAR(((RANK(OPEN)+RANK(LOW))
    -(RANK(HIGH)+RANK(CLOSE))),8)),TSRANK(DECAYLINEAR(
    CORR(TSRANK(CLOSE,8),TSRANK(MEAN(VOLUME,60),20),8),7),3))
    """
    ranked_price_signal = (
        RANK(data["open"])
        + RANK(data["low"])
        - RANK(data["high"])
        - RANK(data["close"])
    )
    first_rank = RANK(
        DECAYLINEAR(ranked_price_signal, 8)
    )
    second_rank = TSRANK(
        DECAYLINEAR(
            CORR(
                TSRANK(data["close"], 8),
                TSRANK(MEAN(data["volume"], 60), 20),
                8,
            ),
            7,
        ),
        3,
    )

    return MIN(first_rank, second_rank).rename("Alpha140")


def alpha141(data: pd.DataFrame) -> pd.Series:
    """
    Alpha141 = -RANK(
        CORR(
            RANK(HIGH),
            RANK(MEAN(VOLUME, 15)),
            9,
        )
    )
    """
    average_volume_15d = MEAN(data["volume"], 15)
    ranked_high = RANK(data["high"])
    ranked_average_volume = RANK(average_volume_15d)
    rank_correlation = CORR(
        ranked_high,
        ranked_average_volume,
        9,
    )

    return (
        -RANK(rank_correlation)
    ).rename("Alpha141")


def alpha142(data: pd.DataFrame) -> pd.Series:
    """
    Alpha142 = (((-1*RANK(TSRANK(CLOSE,10)))
    *RANK(DELTA(DELTA(CLOSE,1),1)))*RANK(
    TSRANK((VOLUME/MEAN(VOLUME,20)),5)))
    """
    average_volume_20d = MEAN(
        data["volume"],
        20,
    ).replace(0, np.nan)

    return (
        -RANK(TSRANK(data["close"], 10))
        * RANK(DELTA(DELTA(data["close"], 1), 1))
        * RANK(
            TSRANK(
                data["volume"] / average_volume_20d,
                5,
            )
        )
    ).rename("Alpha142")


def alpha143(data: pd.DataFrame) -> pd.Series:
    """
    Alpha143 = (
        CLOSE > DELAY(CLOSE, 1)
        ? (
            (CLOSE - DELAY(CLOSE, 1))
            / DELAY(CLOSE, 1)
            * SELF
        )
        : SELF
    )

    SELF is the previous Alpha143 value. The first value is seeded at 1.
    """
    result = pd.Series(
        np.nan,
        index=data.index,
        dtype=float,
    )
    if data.empty:
        return result.rename("Alpha143")

    result.iloc[0] = 1.0
    close = data["close"]

    for position in range(1, len(data)):
        previous_factor = result.iloc[position - 1]
        current_close = close.iloc[position]
        previous_close = close.iloc[position - 1]

        if (
            pd.notna(current_close)
            and pd.notna(previous_close)
            and current_close > previous_close
            and previous_close != 0
        ):
            result.iloc[position] = (
                (current_close - previous_close)
                / previous_close
                * previous_factor
            )
        else:
            result.iloc[position] = previous_factor

    return result.rename("Alpha143")


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


def alpha146(data: pd.DataFrame) -> pd.Series:
    """
    Alpha146 = (
        MEAN(RET - SMA(RET, 61, 2), 20)
        * (RET - SMA(RET, 61, 2))
        / SMA(
            (
                RET - (RET - SMA(RET, 61, 2))
            ) ^ 2,
            60,
            2,
        )
    )

    RET = CLOSE / DELAY(CLOSE, 1) - 1
    """
    daily_return = RET(data["close"])
    smoothed_return = SMA(
        daily_return,
        61,
        2,
    )
    return_deviation = (
        daily_return - smoothed_return
    )
    mean_deviation_20d = MEAN(
        return_deviation,
        20,
    )
    smoothed_variance = SMA(
        (
            daily_return
            - (daily_return - smoothed_return)
        ) ** 2,
        60,
        2,
    ).replace(0, np.nan)

    return (
        mean_deviation_20d
        * return_deviation
        / smoothed_variance
    ).rename("Alpha146")


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
        12,
    ).rename("Alpha147")


def alpha148(data: pd.DataFrame) -> pd.Series:
    """
    Alpha148 = (
        RANK(
            CORR(
                OPEN,
                SUM(MEAN(VOLUME, 60), 9),
                6,
            )
        )
        < RANK(OPEN - TSMIN(OPEN, 14))
    ) * -1
    """
    average_volume_60d = MEAN(data["volume"], 60)
    summed_average_volume = SUM(average_volume_60d, 9)
    open_volume_correlation = CORR(
        data["open"],
        summed_average_volume,
        6,
    )
    correlation_rank = RANK(open_volume_correlation)
    minimum_open_14d = TSMIN(data["open"], 14)
    open_range_rank = RANK(
        data["open"] - minimum_open_14d,
    )
    has_required_history = (
        correlation_rank.notna()
        & open_range_rank.notna()
    )

    return (
        (correlation_rank < open_range_rank)
        .astype(float)
        .mul(-1)
        .where(has_required_history)
        .rename("Alpha148")
    )


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


def alpha156(data: pd.DataFrame) -> pd.Series:
    """
    Alpha156 = (MAX(RANK(DECAYLINEAR(DELTA(VWAP,5),3)),
    RANK(DECAYLINEAR(((DELTA(((OPEN*0.15)+(LOW*0.85)),2)
    /((OPEN*0.15)+(LOW*0.85)))*-1),3)))*-1)
    """
    first_rank = RANK(
        DECAYLINEAR(
            DELTA(data["vwap"], 5),
            3,
        )
    )
    blended_price = (
        data["open"] * 0.15
        + data["low"] * 0.85
    )
    nonzero_blended_price = blended_price.replace(0, np.nan)
    second_rank = RANK(
        DECAYLINEAR(
            (
                DELTA(blended_price, 2)
                / nonzero_blended_price
            ) * -1,
            3,
        )
    )

    return (-MAX(first_rank, second_rank)).rename("Alpha156")


def alpha157(data: pd.DataFrame) -> pd.Series:
    """
    Alpha157 = (
        MIN(
            PROD(
                RANK(
                    RANK(
                        LOG(
                            SUM(
                                TSMIN(
                                    RANK(
                                        RANK(
                                            -RANK(
                                                DELTA(CLOSE - 1, 5)
                                            )
                                        )
                                    ),
                                    2,
                                ),
                                1,
                            )
                        )
                    )
                ),
                1,
            ),
            5,
        )
        + TSRANK(DELAY(-RET, 6), 5)
    )
    """
    close_change = DELTA(
        data["close"] - 1,
        5,
    )
    nested_rank = RANK(
        RANK(
            -RANK(close_change)
        )
    )
    minimum_rank_2d = TSMIN(
        nested_rank,
        2,
    )
    logged_rank_sum = LOG(
        SUM(minimum_rank_2d, 1)
    )
    ranked_log_sum = RANK(
        RANK(logged_rank_sum)
    )
    product_rank = PROD(
        ranked_log_sum,
        1,
    )
    return_time_rank = TSRANK(
        DELAY(
            -RET(data["close"]),
            6,
        ),
        5,
    )

    return (
        MIN(product_rank, 5)
        + return_time_rank
    ).rename("Alpha157")


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


def alpha159(data: pd.DataFrame) -> pd.Series:
    """
    Alpha159 = weighted combination of 6-, 12-, and 24-day
    close positions within previous-close-adjusted price ranges.
    """
    previous_close = DELAY(data["close"], 1)
    lower_bound = MIN(
        data["low"],
        previous_close,
    )
    upper_bound = MAX(
        data["high"],
        previous_close,
    )

    def component(periods: int) -> pd.Series:
        lower_sum = SUM(lower_bound, periods)
        range_sum = SUM(
            upper_bound - lower_bound,
            periods,
        ).replace(0, np.nan)
        return (
            data["close"] - lower_sum
        ) / range_sum

    return (
        (
            component(6) * 12 * 24
            + component(12) * 6 * 24
            + component(24) * 6 * 24
        )
        * 100
        / (6 * 12 + 6 * 24 + 12 * 24)
    ).rename("Alpha159")


def alpha160(data: pd.DataFrame) -> pd.Series:
    """
    Alpha160 = SMA(
        CLOSE <= DELAY(CLOSE, 1) ? STD(CLOSE, 20) : 0,
        20,
        1,
    )
    """
    previous_close = DELAY(data["close"], 1)
    close_std_20d = STD(data["close"], 20)
    downward_volatility = close_std_20d.where(
        data["close"] <= previous_close,
        0.0,
    )

    return SMA(
        downward_volatility,
        20,
        1,
    ).where(close_std_20d.notna()).rename("Alpha160")


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
    close_change = data["close"] - DELAY(
        data["close"],
        1,
    )
    smoothed_up_move = SMA(
        MAX(close_change, 0),
        12,
        1,
    )
    smoothed_absolute_move = SMA(
        ABS(close_change),
        12,
        1,
    ).replace(0, np.nan)

    relative_strength = (
        smoothed_up_move
        / smoothed_absolute_move
        * 100
    )
    relative_strength_min_12d = TSMIN(
        relative_strength,
        12,
    )
    relative_strength_max_12d = TSMAX(
        relative_strength,
        12,
    )
    relative_strength_range = (
        relative_strength_max_12d
        - relative_strength_min_12d
    ).replace(0, np.nan)

    return (
        (relative_strength - relative_strength_min_12d)
        / relative_strength_range
    ).rename("Alpha162")


def alpha163(data: pd.DataFrame) -> pd.Series:
    """
    Alpha163 = RANK(
        -RET
        * MEAN(VOLUME, 20)
        * VWAP
        * (HIGH - CLOSE)
    )
    """
    daily_return = RET(data["close"])
    average_volume_20d = MEAN(data["volume"], 20)
    signal = (
        -daily_return
        * average_volume_20d
        * data["vwap"]
        * (data["high"] - data["close"])
    )

    return RANK(signal).rename("Alpha163")


def alpha164(data: pd.DataFrame) -> pd.Series:
    """
    Alpha164 = SMA(
        (
            (
                CLOSE > DELAY(CLOSE, 1)
                ? 1 / (CLOSE - DELAY(CLOSE, 1))
                : 1
            )
            - TSMIN(
                CLOSE > DELAY(CLOSE, 1)
                ? 1 / (CLOSE - DELAY(CLOSE, 1))
                : 1,
                12,
            )
        )
        / (HIGH - LOW)
        * 100,
        13,
        2,
    )
    """
    close_change = DELTA(data["close"], 1)
    inverse_change = pd.Series(
        1.0,
        index=data.index,
    ).mask(
        close_change > 0,
        1 / close_change,
    )
    minimum_inverse_12d = TSMIN(
        inverse_change,
        12,
    )
    normalized_inverse = (
        (inverse_change - minimum_inverse_12d)
        / (
            data["high"] - data["low"]
        ).replace(0, np.nan)
        * 100
    )

    return SMA(
        normalized_inverse,
        13,
        2,
    ).rename("Alpha164")


def alpha165(data: pd.DataFrame) -> pd.Series:
    """
    Alpha165 = (
        MAX(SUMAC(CLOSE - MEAN(CLOSE, 48)))
        - MIN(SUMAC(CLOSE - MEAN(CLOSE, 48)))
    ) / STD(CLOSE, 48)
    """
    centered_close = (
        data["close"]
        - MEAN(data["close"], 48)
    )
    cumulative_deviation = SUMAC(centered_close)
    cumulative_range = (
        cumulative_deviation.cummax()
        - cumulative_deviation.cummin()
    )

    return (
        cumulative_range
        / STD(data["close"], 48).replace(0, np.nan)
    ).rename("Alpha165")


def alpha166(data: pd.DataFrame) -> pd.Series:
    """
    Alpha166 = (
        -20
        * (20 - 1) ^ 1.5
        * SUM(RET - MEAN(RET, 20), 20)
        / (
            (20 - 1)
            * (20 - 2)
            * SUM((RET - MEAN(RET, 20)) ^ 2, 20) ^ 1.5
        )
    )

    RET = CLOSE / DELAY(CLOSE, 1) - 1
    """
    daily_return = RET(data["close"])
    average_return_20d = MEAN(
        daily_return,
        20,
    )
    return_deviation = (
        daily_return - average_return_20d
    )
    deviation_sum = SUM(
        return_deviation,
        20,
    )
    squared_deviation_sum = SUM(
        return_deviation ** 2,
        20,
    )
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

    return (
        numerator / denominator
    ).rename("Alpha166")


def alpha167(data: pd.DataFrame) -> pd.Series:
    """
    Alpha167 = SUM(
        CLOSE - DELAY(CLOSE, 1) > 0
        ? CLOSE - DELAY(CLOSE, 1)
        : 0,
        12,
    )
    """
    close_change = data["close"] - DELAY(
        data["close"],
        1,
    )
    positive_change = close_change.where(
        close_change > 0,
        0.0,
    )
    positive_change = positive_change.where(
        close_change.notna(),
    )

    return SUM(
        positive_change,
        12,
    ).rename("Alpha167")


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
    prev_close_1d = DELAY(data['close'], 1)
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


def alpha170(data: pd.DataFrame) -> pd.Series:
    """
    Alpha170 = (
        (
            RANK(1 / CLOSE)
            * VOLUME
            / MEAN(VOLUME, 20)
        )
        * (
            HIGH
            * RANK(HIGH - CLOSE)
            / (SUM(HIGH, 5) / 5)
        )
        - RANK(VWAP - DELAY(VWAP, 5))
    )
    """
    average_volume_20d = MEAN(data["volume"], 20).replace(0, np.nan)
    average_high_5d = MEAN(data["high"], 5).replace(0, np.nan)
    previous_vwap_5d = DELAY(data["vwap"], 5)
    inverse_close_rank = RANK(
        1 / data["close"].replace(0, np.nan),
    )
    high_close_rank = RANK(
        data["high"] - data["close"],
    )
    vwap_change_rank = RANK(
        data["vwap"] - previous_vwap_5d,
    )

    return (
        (
            inverse_close_rank
            * data["volume"]
            / average_volume_20d
        )
        * (
            data["high"]
            * high_close_rank
            / average_high_5d
        )
        - vwap_change_rank
    ).rename("Alpha170")


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



def alpha172(data: pd.DataFrame) -> pd.Series:
    """
    Alpha172 = MEAN(
        ABS(LDI - HDI) / (LDI + HDI) * 100,
        6,
    )

    LDI = SUM((LD > 0 & LD > HD) ? LD : 0, 14) * 100 / SUM(TR, 14)
    HDI = SUM((HD > 0 & HD > LD) ? HD : 0, 14) * 100 / SUM(TR, 14)
    """
    true_range = TR(
        data["high"],
        data["low"],
        data["close"],
    )
    high_direction = HD(data["high"])
    low_direction = LD(data["low"])
    has_previous = DELAY(
        data["close"],
        1,
    ).notna()
    positive_low_direction = low_direction.where(
        (low_direction > 0)
        & (low_direction > high_direction),
        0.0,
    ).where(has_previous)
    positive_high_direction = high_direction.where(
        (high_direction > 0)
        & (high_direction > low_direction),
        0.0,
    ).where(has_previous)
    true_range_sum = SUM(
        true_range,
        14,
    ).replace(0, np.nan)
    low_index = (
        SUM(positive_low_direction, 14)
        * 100
        / true_range_sum
    )
    high_index = (
        SUM(positive_high_direction, 14)
        * 100
        / true_range_sum
    )
    directional_index = (
        ABS(low_index - high_index)
        / (
            low_index + high_index
        ).replace(0, np.nan)
        * 100
    )

    return MEAN(
        directional_index,
        6,
    ).rename("Alpha172")


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


def alpha174(data: pd.DataFrame) -> pd.Series:
    """
    Alpha174 = SMA(
        CLOSE > DELAY(CLOSE, 1) ? STD(CLOSE, 20) : 0,
        20,
        1,
    )
    """
    previous_close = DELAY(data["close"], 1)
    close_std_20d = STD(data["close"], 20)
    upward_volatility = close_std_20d.where(
        data["close"] > previous_close,
        0.0,
    )

    return SMA(
        upward_volatility,
        20,
        1,
    ).where(close_std_20d.notna()).rename("Alpha174")


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


def alpha176(data: pd.DataFrame) -> pd.Series:
    """
    Alpha176 = CORR(RANK(((CLOSE-TSMIN(LOW,12))
    /(TSMAX(HIGH,12)-TSMIN(LOW,12)))),RANK(VOLUME),6)
    """
    minimum_low = TSMIN(data["low"], 12)
    price_range = (
        TSMAX(data["high"], 12) - minimum_low
    ).replace(0, np.nan)
    location = (
        data["close"] - minimum_low
    ) / price_range

    return CORR(RANK(location), RANK(data["volume"]), 6).rename(
        "Alpha176"
    )


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


def alpha179(data: pd.DataFrame) -> pd.Series:
    """
    Alpha179 = (RANK(CORR(VWAP,VOLUME,4))
    *RANK(CORR(RANK(LOW),RANK(MEAN(VOLUME,50)),12)))
    """
    return (
        RANK(CORR(data["vwap"], data["volume"], 4))
        * RANK(
            CORR(
                RANK(data["low"]),
                RANK(MEAN(data["volume"], 50)),
                12,
            )
        )
    ).rename("Alpha179")


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


def alpha181(data: pd.DataFrame) -> pd.Series:
    """
    Alpha181 = (
        SUM(
            (
                RET - MEAN(RET, 20)
            )
            - (
                BANCHMARKINDEXCLOSE
                - MEAN(BANCHMARKINDEXCLOSE, 20)
            ) ^ 2,
            20,
        )
        / SUM(
            (
                BANCHMARKINDEXCLOSE
                - MEAN(BANCHMARKINDEXCLOSE, 20)
            ) ^ 3
        )
    )
    """
    daily_return = RET(data["close"])
    centered_return = (
        daily_return - MEAN(daily_return, 20)
    )
    benchmark_deviation = (
        data["benchmark_close"]
        - MEAN(data["benchmark_close"], 20)
    )
    numerator = SUM(
        centered_return - benchmark_deviation ** 2,
        20,
    )
    denominator = SUM(
        benchmark_deviation ** 3,
    ).replace(0, np.nan)

    return (
        numerator / denominator
    ).replace(
        [np.inf, -np.inf],
        np.nan,
    ).rename("Alpha181")


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


def alpha183(data: pd.DataFrame) -> pd.Series:
    """
    Alpha183 = (
        MAX(SUMAC(CLOSE - MEAN(CLOSE, 24)))
        - MIN(SUMAC(CLOSE - MEAN(CLOSE, 24)))
    ) / STD(CLOSE, 24)
    """
    centered_close = (
        data["close"]
        - MEAN(data["close"], 24)
    )
    cumulative_deviation = SUMAC(centered_close)
    cumulative_range = (
        cumulative_deviation.cummax()
        - cumulative_deviation.cummin()
    )

    return (
        cumulative_range
        / STD(data["close"], 24).replace(0, np.nan)
    ).rename("Alpha183")


def alpha184(data: pd.DataFrame) -> pd.Series:
    """
    Alpha184 = (
        RANK(
            CORR(
                DELAY(OPEN - CLOSE, 1),
                CLOSE,
                200,
            )
        )
        + RANK(OPEN - CLOSE)
    )
    """
    candle_body = data["open"] - data["close"]
    delayed_body = DELAY(candle_body, 1)
    body_close_correlation = CORR(
        delayed_body,
        data["close"],
        200,
    )

    return (
        RANK(body_close_correlation)
        + RANK(candle_body)
    ).rename("Alpha184")


def alpha185(data: pd.DataFrame) -> pd.Series:
    """
    Alpha185 = RANK(
        -1 * (1 - OPEN / CLOSE) ^ 2
    )
    """
    intraday_reversal = -(
        1 - data["open"] / data["close"]
    ) ** 2

    return RANK(intraday_reversal).rename("Alpha185")


def alpha186(data: pd.DataFrame) -> pd.Series:
    """
    Alpha186 = (
        Alpha172
        + DELAY(Alpha172, 6)
    ) / 2
    """
    average_directional_index = alpha172(data)

    return (
        (
            average_directional_index
            + DELAY(average_directional_index, 6)
        )
        / 2
    ).rename("Alpha186")


def alpha187(data: pd.DataFrame) -> pd.Series:
    """
    Alpha187 = SUM(
        OPEN <= DELAY(OPEN, 1)
        ? 0
        : MAX(HIGH - OPEN, OPEN - DELAY(OPEN, 1)),
        20,
    )
    """
    previous_open = DELAY(data["open"], 1)
    open_change = data["open"] - previous_open
    upward_movement = MAX(
        data["high"] - data["open"],
        open_change,
    )
    daily_movement = pd.Series(
        0.0,
        index=data.index,
    )
    daily_movement = daily_movement.mask(
        data["open"] > previous_open,
        upward_movement,
    )
    daily_movement = daily_movement.where(
        previous_open.notna(),
    )

    return SUM(
        daily_movement,
        20,
    ).rename("Alpha187")


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
        "Alpha1",
        "Alpha6",
        "Alpha7",
        "Alpha8",
        "Alpha10",
        "Alpha12",
        "Alpha16",
        "Alpha17",
        "Alpha25",
        "Alpha32",
        "Alpha33",
        "Alpha35",
        "Alpha36",
        "Alpha37",
        "Alpha39",
        "Alpha41",
        "Alpha42",
        "Alpha45",
        "Alpha48",
        "Alpha54",
        "Alpha56",
        "Alpha61",
        "Alpha62",
        "Alpha64",
        "Alpha73",
        "Alpha74",
        "Alpha77",
        "Alpha83",
        "Alpha87",
        "Alpha90",
        "Alpha91",
        "Alpha92",
        "Alpha99",
        "Alpha101",
        "Alpha104",
        "Alpha105",
        "Alpha107",
        "Alpha108",
        "Alpha113",
        "Alpha114",
        "Alpha115",
        "Alpha119",
        "Alpha120",
        "Alpha121",
        "Alpha123",
        "Alpha124",
        "Alpha125",
        "Alpha130",
        "Alpha131",
        "Alpha136",
        "Alpha138",
        "Alpha140",
        "Alpha141",
        "Alpha142",
        "Alpha148",
        "Alpha156",
        "Alpha157",
        "Alpha163",
        "Alpha170",
        "Alpha176",
        "Alpha179",
        "Alpha184",
        "Alpha185",
    }
)


FACTORS = {
    "Alpha1": alpha1,
    "Alpha2": alpha2,
    "Alpha3": alpha3,
    "Alpha4": alpha4,
    "Alpha5": alpha5,
    "Alpha6": alpha6,
    "Alpha7": alpha7,
    "Alpha8": alpha8,
    "Alpha9": alpha9,
    "Alpha10": alpha10,
    "Alpha11": alpha11,
    "Alpha12": alpha12,
    "Alpha13": alpha13,
    "Alpha14": alpha14,
    "Alpha15": alpha15,
    "Alpha16": alpha16,
    "Alpha17": alpha17,
    "Alpha18": alpha18,
    "Alpha19": alpha19,
    "Alpha20": alpha20,
    "Alpha21": alpha21,
    "Alpha22": alpha22,
    "Alpha23": alpha23,
    "Alpha24": alpha24,
    "Alpha25": alpha25,
    "Alpha26": alpha26,
    "Alpha27": alpha27,
    "Alpha28": alpha28,
    "Alpha29": alpha29,
    "Alpha31": alpha31,
    "Alpha32": alpha32,
    "Alpha33": alpha33,
    "Alpha34": alpha34,
    "Alpha35": alpha35,
    "Alpha36": alpha36,
    "Alpha37": alpha37,
    "Alpha38": alpha38,
    "Alpha39": alpha39,
    "Alpha40": alpha40,
    "Alpha41": alpha41,
    "Alpha42": alpha42,
    # "Alpha999": alpha999,
    "Alpha43": alpha43,
    "Alpha44": alpha44,
    "Alpha45": alpha45,
    "Alpha46": alpha46,
    "Alpha47": alpha47,
    "Alpha48": alpha48,
    "Alpha49": alpha49,
    "Alpha50": alpha50,
    "Alpha51": alpha51,
    "Alpha52": alpha52,
    "Alpha53": alpha53,
    "Alpha54": alpha54,
    "Alpha55": alpha55,
    "Alpha56": alpha56,
    "Alpha57": alpha57,
    "Alpha58": alpha58,
    "Alpha59": alpha59,
    "Alpha60": alpha60,
    "Alpha61": alpha61,
    "Alpha62": alpha62,
    "Alpha63": alpha63,
    "Alpha64": alpha64,
    "Alpha65": alpha65,
    "Alpha66": alpha66,
    "Alpha67": alpha67,
    "Alpha68": alpha68,
    "Alpha69": alpha69,
    "Alpha70": alpha70,
    "Alpha71": alpha71,
    "Alpha72": alpha72,
    "Alpha73": alpha73,
    "Alpha74": alpha74,
    "Alpha75": alpha75,
    "Alpha76": alpha76,
    "Alpha77": alpha77,
    "Alpha78": alpha78,
    "Alpha79": alpha79,
    "Alpha80": alpha80,
    "Alpha81": alpha81,
    "Alpha82": alpha82,
    "Alpha83": alpha83,
    "Alpha84": alpha84,
    "Alpha85": alpha85,
    "Alpha86": alpha86,
    "Alpha87": alpha87,
    "Alpha88": alpha88,
    "Alpha89": alpha89,
    "Alpha90": alpha90,
    "Alpha91": alpha91,
    "Alpha92": alpha92,
    "Alpha93": alpha93,
    "Alpha94": alpha94,
    "Alpha95": alpha95,
    "Alpha96": alpha96,
    "Alpha97": alpha97,
    "Alpha98": alpha98,
    "Alpha99": alpha99,
    "Alpha100": alpha100,
    "Alpha101": alpha101,
    "Alpha102": alpha102,
    "Alpha103": alpha103,
    "Alpha104": alpha104,
    "Alpha105": alpha105,
    "Alpha106": alpha106,
    "Alpha107": alpha107,
    "Alpha108": alpha108,
    "Alpha109": alpha109,
    "Alpha110": alpha110,
    "Alpha111": alpha111,
    "Alpha112": alpha112,
    "Alpha113": alpha113,
    "Alpha114": alpha114,
    "Alpha115": alpha115,
    "Alpha116": alpha116,
    "Alpha117": alpha117,
    "Alpha118": alpha118,
    "Alpha119": alpha119,
    "Alpha120": alpha120,
    "Alpha121": alpha121,
    "Alpha122": alpha122,
    "Alpha123": alpha123,
    "Alpha124": alpha124,
    "Alpha125": alpha125,
    "Alpha126": alpha126,
    "Alpha127": alpha127,
    "Alpha128": alpha128,
    "Alpha129": alpha129,
    "Alpha130": alpha130,
    "Alpha131": alpha131,
    "Alpha132": alpha132,
    "Alpha133": alpha133,
    "Alpha134": alpha134,
    "Alpha135": alpha135,
    "Alpha136": alpha136,
    "Alpha137": alpha137,
    "Alpha138": alpha138,
    "Alpha139": alpha139,
    "Alpha140": alpha140,
    "Alpha141": alpha141,
    "Alpha142": alpha142,
    "Alpha143": alpha143,
    "Alpha144": alpha144,
    "Alpha145": alpha145,
    "Alpha146": alpha146,
    "Alpha147": alpha147,
    "Alpha148": alpha148,
    "Alpha149": alpha149,
    "Alpha150": alpha150,
    "Alpha151": alpha151,
    "Alpha152": alpha152,
    "Alpha153": alpha153,
    "Alpha154": alpha154,
    "Alpha155": alpha155,
    "Alpha156": alpha156,
    "Alpha157": alpha157,
    "Alpha158": alpha158,
    "Alpha159": alpha159,
    "Alpha160": alpha160,
    "Alpha161": alpha161,
    "Alpha162": alpha162,
    "Alpha163": alpha163,
    "Alpha164": alpha164,
    "Alpha165": alpha165,
    "Alpha166": alpha166,
    "Alpha167": alpha167,
    "Alpha168": alpha168,
    "Alpha169": alpha169,
    "Alpha170": alpha170,
    "Alpha171": alpha171,
    "Alpha172": alpha172,
    "Alpha173": alpha173,
    "Alpha174": alpha174,
    "Alpha175": alpha175,
    "Alpha176": alpha176,
    "Alpha177": alpha177,
    "Alpha178": alpha178,
    "Alpha179": alpha179,
    "Alpha180": alpha180,
    "Alpha181": alpha181,
    "Alpha182": alpha182,
    "Alpha183": alpha183,
    "Alpha184": alpha184,
    "Alpha185": alpha185,
    "Alpha186": alpha186,
    "Alpha187": alpha187,
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
