import numpy as np
import pandas as pd

from factor_operators import *

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
    return (-TSMAX(price_volume_corr, 3)).rename('alpha5')


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

def alpha53(data: pd.DataFrame) -> pd.Series:
    """
    Alpha53 = COUNT(CLOSE > DELAY(CLOSE, 1), 12) / 12 * 100
    """
    previous_close = DELAY(data["close"], 1)
    condition = (data["close"] > previous_close).where(previous_close.notna())
    return (COUNT(condition, periods=12) / 12 * 100).rename("Alpha53")

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
    price_change = data["close"] - previous_close
    dir_volume = np.sign(price_change) * data["volume"]

    result = SUM(dir_volume, periods=20)
    return result.rename("Alpha84")


def alpha168(data: pd.DataFrame) -> pd.Series:
    """
    Alpha168 = -VOLUME / MEAN(VOLUME, 20)
    """
    return(-data['volume'] / MEAN(data['volume'], 20)).rename('Alpha168')


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

FACTORS = {
    "Alpha2": alpha2,
    "Alpha3": alpha3,
    "Alpha5": alpha5,
    "Alpha9": alpha9,
    "Alpha11": alpha11,
    "Alpha14": alpha14,
    "Alpha15": alpha15,
    "Alpha20": alpha20,
    "Alpha29": alpha29,
    "Alpha31": alpha31,
    "Alpha40": alpha40,
    "Alpha43": alpha43,
    "Alpha46": alpha46,
    "Alpha53": alpha53,
    "Alpha60": alpha60,
    "Alpha69": alpha69,
    "Alpha80": alpha80,
    "Alpha84": alpha84,
    "Alpha168": alpha168,
    "Alpha191": alpha191,
}

def calculate_factors(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()

    for name, factor_func in FACTORS.items():
        result[name] = factor_func(data)

    return result
